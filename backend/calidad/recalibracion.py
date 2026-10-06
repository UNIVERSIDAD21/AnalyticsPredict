# -*- coding: utf-8 -*-
"""Pipeline inicial de re-evaluación de calibración por mercado (Bloque 09)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

METODOS_DISPONIBLES = ["isotonic", "platt", "beta", "ninguno"]


def _ece_from_buckets(rows: List[Dict[str, Any]]) -> float | None:
    validos = [r for r in rows if int(r.get("n", 0) or 0) > 0
               and r.get("hit_rate") is not None and r.get("prob_media") is not None]
    total_n = float(sum(int(r["n"]) for r in validos))
    if total_n <= 0:
        return None
    ece = 0.0
    for r in validos:
        n = float(int(r.get("n", 0) or 0))
        hit_rate = float(r["hit_rate"])
        prob_media = float(r["prob_media"])
        ece += (n / total_n) * abs(hit_rate - prob_media)
    return float(round(ece, 6))


def evaluar_calibracion_mercado(conn: Any, mercado: str, n_samples: int = 5000) -> Dict[str, Any]:
    """Evalúa baseline de calibración para un mercado usando vw_calibration_scorecard.

    Args:
        conn: conexión psycopg
        mercado: nombre de mercado (ej. COMPLETO, Q1, Q2, Q3, Q4)
        n_samples: muestras máximas aproximadas (se aplica sobre periodos recientes)

    Returns:
        Dict con métricas baseline: brier, ece, log_loss, calibration_gap y n.
    """
    mercado_up = (mercado or "").strip().upper()

    sql = """
    WITH base AS (
      SELECT sport, market_type, periodo, confidence_bucket, n, hit_rate, prob_media,
             brier_score, log_loss, calibration_gap
      FROM analytics.vw_calibration_scorecard
      WHERE market_type = %s
      ORDER BY periodo DESC
      LIMIT %s
    )
    SELECT
      COALESCE(SUM(n),0)::bigint AS n_total,
      (SUM(n * brier_score) / NULLIF(SUM(n) FILTER (WHERE brier_score IS NOT NULL),0))::numeric AS brier_prom,
      (SUM(n * log_loss) / NULLIF(SUM(n) FILTER (WHERE log_loss IS NOT NULL),0))::numeric AS logloss_prom,
      (SUM(n * calibration_gap) / NULLIF(SUM(n) FILTER (WHERE calibration_gap IS NOT NULL),0))::numeric AS gap_prom
    FROM base
    """

    sql_buckets = """
    SELECT confidence_bucket, SUM(n)::bigint AS n,
           (SUM(n * hit_rate) / NULLIF(SUM(n) FILTER (WHERE hit_rate IS NOT NULL),0))::numeric AS hit_rate,
           (SUM(n * prob_media) / NULLIF(SUM(n) FILTER (WHERE prob_media IS NOT NULL),0))::numeric AS prob_media
    FROM analytics.vw_calibration_scorecard
    WHERE market_type = %s
    GROUP BY confidence_bucket
    """

    with conn.cursor() as cur:
        cur.execute(sql, (mercado_up, n_samples))
        row = cur.fetchone() or (0, None, None, None)
        cur.execute(sql_buckets, (mercado_up,))
        buckets_rows = cur.fetchall() or []

    buckets: List[Dict[str, Any]] = []
    for r in buckets_rows:
        buckets.append(
            {
                "confidence_bucket": r[0],
                "n": int(r[1] or 0),
                "hit_rate": float(r[2]) if r[2] is not None else None,
                "prob_media": float(r[3]) if r[3] is not None else None,
            }
        )

    metricas = {
        "mercado": mercado_up,
        "n_total": int(row[0] or 0),
        "brier": float(row[1]) if row[1] is not None else None,
        "ece": _ece_from_buckets(buckets),
        "logloss": float(row[2]) if row[2] is not None else None,
        "calibration_gap": float(row[3]) if row[3] is not None else None,
        "buckets": buckets,
    }

    logger.info("baseline_calibracion", extra={"mercado": mercado_up, "n": metricas["n_total"], "ece": metricas["ece"]})
    return metricas


def proponer_metodo_calibracion(metricas_baseline: Dict[str, Any]) -> str:
    """Propone método de calibración según severidad de descalibración."""
    n = int(metricas_baseline.get("n_total", 0) or 0)

    if n < 200:
        return "ninguno"
    if metricas_baseline.get("ece") is None or metricas_baseline.get("calibration_gap") is None:
        return "ninguno"
    ece = float(metricas_baseline["ece"])
    gap = abs(float(metricas_baseline["calibration_gap"]))
    if ece >= 0.08 or gap >= 0.08:
        return "isotonic"
    if ece >= 0.05 or gap >= 0.05:
        return "beta"
    if ece >= 0.03 or gap >= 0.03:
        return "platt"
    return "ninguno"

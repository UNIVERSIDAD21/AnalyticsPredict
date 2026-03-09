# -*- coding: utf-8 -*-
"""Pipeline inicial de re-evaluación de calibración por mercado (Bloque 09)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

METODOS_DISPONIBLES = ["isotonic", "platt", "beta", "ninguno"]


def _ece_from_buckets(rows: List[Dict[str, Any]]) -> float:
    total_n = float(sum(int(r.get("n", 0) or 0) for r in rows))
    if total_n <= 0:
        return 0.0
    ece = 0.0
    for r in rows:
        n = float(int(r.get("n", 0) or 0))
        hit_rate = float(r.get("hit_rate", 0.0) or 0.0)
        prob_media = float(r.get("prob_media", 0.0) or 0.0)
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
      COALESCE(AVG(brier_score),0)::numeric AS brier_prom,
      COALESCE(AVG(log_loss),0)::numeric AS logloss_prom,
      COALESCE(AVG(calibration_gap),0)::numeric AS gap_prom
    FROM base
    """

    sql_buckets = """
    SELECT confidence_bucket, SUM(n)::bigint AS n,
           AVG(hit_rate)::numeric AS hit_rate,
           AVG(prob_media)::numeric AS prob_media
    FROM analytics.vw_calibration_scorecard
    WHERE market_type = %s
    GROUP BY confidence_bucket
    """

    with conn.cursor() as cur:
        cur.execute(sql, (mercado_up, n_samples))
        row = cur.fetchone() or (0, 0, 0, 0)
        cur.execute(sql_buckets, (mercado_up,))
        buckets_rows = cur.fetchall() or []

    buckets: List[Dict[str, Any]] = []
    for r in buckets_rows:
        buckets.append(
            {
                "confidence_bucket": r[0],
                "n": int(r[1] or 0),
                "hit_rate": float(r[2] or 0.0),
                "prob_media": float(r[3] or 0.0),
            }
        )

    metricas = {
        "mercado": mercado_up,
        "n_total": int(row[0] or 0),
        "brier": float(row[1] or 0.0),
        "ece": _ece_from_buckets(buckets),
        "logloss": float(row[2] or 0.0),
        "calibration_gap": float(row[3] or 0.0),
        "buckets": buckets,
    }

    logger.info("baseline_calibracion", extra={"mercado": mercado_up, "n": metricas["n_total"], "ece": metricas["ece"]})
    return metricas


def proponer_metodo_calibracion(metricas_baseline: Dict[str, Any]) -> str:
    """Propone método de calibración según severidad de descalibración."""
    ece = float(metricas_baseline.get("ece", 0.0) or 0.0)
    gap = abs(float(metricas_baseline.get("calibration_gap", 0.0) or 0.0))
    n = int(metricas_baseline.get("n_total", 0) or 0)

    if n < 200:
        return "ninguno"
    if ece >= 0.08 or gap >= 0.08:
        return "isotonic"
    if ece >= 0.05 or gap >= 0.05:
        return "beta"
    if ece >= 0.03 or gap >= 0.03:
        return "platt"
    return "ninguno"

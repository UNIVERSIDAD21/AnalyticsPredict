#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from motor_futbol.madurez_beta import clasificar_madurez_mercado, mapear_status_promocion, aplicar_autodemotion
from motor_futbol.readiness_gate import cargar_politica_readiness, evaluar_readiness_corners


def _tabla_existe(cur, tabla: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
          SELECT 1 FROM information_schema.tables
          WHERE table_schema='public' AND table_name=%s
        ) AS ok
        """,
        [tabla],
    )
    return bool(cur.fetchone()["ok"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Monitoreo continuo y auto-demotion por mercado (fútbol)")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--out", type=str, default="docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json")
    ap.add_argument("--apply", action="store_true", help="Aplica cambios en tabla futbol_estado_operativo_mercado")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=args.days)

    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='predicciones_futbol'")
            cols = {r["column_name"] for r in cur.fetchall()}

            p_col = "prob_over_calibrada" if "prob_over_calibrada" in cols else ("prob_over" if "prob_over" in cols else None)
            fecha_col = "timestamp_generacion" if "timestamp_generacion" in cols else ("creado_en" if "creado_en" in cols else None)
            if p_col is None or fecha_col is None or "outcome_binario" not in cols:
                raise RuntimeError("predicciones_futbol sin columnas mínimas para monitoreo")

            cur.execute(
                f"""
                SELECT mercado::text AS mercado,
                       COUNT(*) AS n_total,
                       COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS n_res,
                       COUNT(DISTINCT linea) AS lineas,
                       AVG(POWER(COALESCE({p_col},0)-COALESCE(outcome_binario::int,0),2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier,
                       AVG(CASE
                         WHEN outcome_binario IS NULL THEN NULL
                         ELSE -(
                           outcome_binario::int * LN(GREATEST(COALESCE({p_col}, 0), 1e-9))
                           + (1 - outcome_binario::int) * LN(GREATEST(1 - COALESCE({p_col},0), 1e-9))
                         )
                       END) AS log_loss,
                       AVG(CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END)::numeric AS fallback_rate
                FROM predicciones_futbol
                WHERE {fecha_col} >= %s
                GROUP BY mercado
                ORDER BY mercado
                """,
                [start],
            )
            rows = cur.fetchall()

            actuales: Dict[str, str] = {}
            if _tabla_existe(cur, "futbol_estado_operativo_mercado"):
                cur.execute(
                    """
                    SELECT mercado, estado_operativo
                    FROM futbol_estado_operativo_mercado
                    WHERE vigente_hasta IS NULL
                    """
                )
                for r in cur.fetchall():
                    actuales[str(r["mercado"]).upper()] = str(r["estado_operativo"]).upper()

            politica_readiness = cargar_politica_readiness()
            scope_readiness = set(politica_readiness.get("scope", []))

            decisiones: List[Dict[str, Any]] = []
            for r in rows:
                mercado = str(r["mercado"]).upper()
                n_total = int(r["n_total"] or 0)
                n_res = int(r["n_res"] or 0)
                resolved_rate = (n_res / n_total) if n_total else 0.0
                metricas = {
                    "n_resueltas": n_res,
                    "lineas_cubiertas": int(r["lineas"] or 0),
                    "brier": float(r["brier"] or 1.0),
                    "log_loss": float(r["log_loss"] or 2.0),
                    "ece": 1.0,
                    "resolved_rate": resolved_rate,
                    "fallback_rate": float(r["fallback_rate"] or 1.0),
                    "window_drift_brier": 0.0,
                }
                nivel, motivos = clasificar_madurez_mercado(metricas, estado_mercado="verde")
                objetivo = mapear_status_promocion(nivel)

                readiness = None
                if mercado in scope_readiness:
                    readiness = evaluar_readiness_corners({
                        "emitidos": n_total,
                        "resueltos_binarios": n_res,
                        "pendientes": max(0, n_total - n_res),
                        "lineas_cubiertas": int(r["lineas"] or 0),
                    }, politica_readiness, ventanas_estables=0)
                    if not readiness["gates"]["reevaluacion"]:
                        objetivo = "BLOQUEADO"
                        motivos = ["gate_readiness_no_habilitado", *motivos]

                estado_actual = actuales.get(mercado, "LABORATORIO")
                nuevo, motivos_d = aplicar_autodemotion(estado_actual, objetivo, motivos)

                decisiones.append({
                    "mercado": mercado,
                    "estado_actual": estado_actual,
                    "estado_objetivo": objetivo,
                    "estado_nuevo": nuevo,
                    "motivos": motivos_d,
                    "metricas": metricas,
                    "readiness": readiness,
                })

                if args.apply and nuevo != estado_actual and _tabla_existe(cur, "futbol_estado_operativo_mercado"):
                    cur.execute(
                        """
                        UPDATE futbol_estado_operativo_mercado
                        SET vigente_hasta = NOW(), actualizado_en = NOW()
                        WHERE mercado = %s AND vigente_hasta IS NULL
                        """,
                        [mercado],
                    )
                    cur.execute(
                        """
                        INSERT INTO futbol_estado_operativo_mercado
                          (mercado, estado_operativo, fuente, motivos)
                        VALUES (%s, %s, 'monitor_autodemotion', %s::jsonb)
                        """,
                        [mercado, nuevo, json.dumps(motivos_d)],
                    )

            if args.apply:
                conn.commit()

    payload = {
        "generated_at": now.isoformat(),
        "window_days": args.days,
        "apply": args.apply,
        "decisiones": decisiones,
        "demotions": [d for d in decisiones if d["estado_nuevo"] != d["estado_actual"]],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Reporte monitoreo/autodemotion: {out}")


if __name__ == "__main__":
    main()

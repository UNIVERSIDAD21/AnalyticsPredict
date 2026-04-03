#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from motor_futbol.madurez_beta import clasificar_madurez_mercado, CRITERIOS_DEFAULT


def main() -> None:
    parser = argparse.ArgumentParser(description="Reporte automático de madurez beta del módulo fútbol")
    parser.add_argument("--dias", type=int, default=120)
    parser.add_argument("--out", type=str, default="docs/reportes/BLOQUE_9_MADUREZ_FUTBOL_AUTO.json")
    args = parser.parse_args()

    pool = obtener_pool()
    fin = datetime.now(timezone.utc)
    inicio = fin - timedelta(days=args.dias)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='predicciones_futbol'
                """
            )
            cols = {r["column_name"] for r in cur.fetchall()}

            if "prob_over_calibrada" in cols:
                p_col = "prob_over_calibrada"
                fallback_expr = "CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END"
            elif "prob_over" in cols:
                p_col = "prob_over"
                fallback_expr = "0"
            else:
                raise RuntimeError("predicciones_futbol no tiene columna de probabilidad utilizable")

            if "outcome_binario" not in cols:
                raise RuntimeError("predicciones_futbol no tiene outcome_binario; no se puede evaluar madurez")

            fecha_col = "fecha_prediccion" if "fecha_prediccion" in cols else ("fecha_calculo" if "fecha_calculo" in cols else None)
            where_fecha = f"WHERE {fecha_col} >= %s" if fecha_col else ""
            params = [inicio] if fecha_col else []

            cur.execute(
                f"""
                SELECT
                  mercado::text AS mercado,
                  COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS n_resueltas,
                  COUNT(*) AS n_total,
                  COUNT(DISTINCT linea) AS lineas_cubiertas,
                  AVG(POWER(COALESCE({p_col}, 0) - COALESCE(outcome_binario::int,0), 2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier,
                  AVG(CASE
                    WHEN outcome_binario IS NULL THEN NULL
                    ELSE -(
                      outcome_binario::int * LN(GREATEST(COALESCE({p_col}, 0), 1e-9))
                      + (1 - outcome_binario::int) * LN(GREATEST(1 - COALESCE({p_col}, 0), 1e-9))
                    )
                  END) AS log_loss,
                  AVG({fallback_expr})::numeric AS fallback_rate
                FROM predicciones_futbol
                {where_fecha}
                GROUP BY mercado
                ORDER BY mercado
                """,
                params,
            )
            filas = cur.fetchall()

    mercados = []
    for r in filas:
        n_total = int(r["n_total"] or 0)
        n_res = int(r["n_resueltas"] or 0)
        metricas = {
            "n_resueltas": n_res,
            "lineas_cubiertas": int(r["lineas_cubiertas"] or 0),
            "brier": float(r["brier"] or 1.0),
            "log_loss": float(r["log_loss"] or 2.0),
            "ece": 1.0,
            "resolved_rate": (n_res / n_total) if n_total else 0.0,
            "fallback_rate": float(r["fallback_rate"] or 1.0),
            "window_drift_brier": 1.0,
        }
        clasif, motivos = clasificar_madurez_mercado(metricas, estado_mercado=None)
        mercados.append({
            "mercado": r["mercado"],
            "clasificacion": clasif,
            "motivos": motivos,
            **metricas,
        })

    payload: Dict[str, Any] = {
        "generated_at": fin.isoformat(),
        "dias": args.dias,
        "criterios": CRITERIOS_DEFAULT.__dict__,
        "mercados": mercados,
        "estado_global": "BETA_LAB",
        "nota": "Sin estado_mercados histórico integrado en este reporte batch, todos los mercados se mantienen conservadoramente en beta.",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Reporte generado: {out}")


if __name__ == "__main__":
    main()

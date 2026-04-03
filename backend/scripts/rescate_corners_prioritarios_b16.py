#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from motor.resolucion_predicciones_futbol import resolver_predicciones_futbol

TARGET = ["CORNERS_1T", "CORNERS_LOCAL_1T"]


def _metricas(cur, mercados: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for m in mercados:
        cur.execute(
            """
            SELECT
              COUNT(*) AS emitidos,
              COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos,
              COUNT(*) FILTER (WHERE resuelto = true) AS cerrados_operativos,
              COUNT(*) FILTER (WHERE (resuelto = false OR resuelto IS NULL)) AS pendientes_operativos,
              COUNT(*) FILTER (WHERE outcome_binario IS NULL) AS pendientes,
              COUNT(*) FILTER (WHERE prob_over_calibrada IS NULL OR prob_under_calibrada IS NULL) AS fallback_rows,
              COUNT(DISTINCT linea) AS lineas,
              AVG(POWER(COALESCE(prob_over_calibrada, prob_over) - COALESCE(outcome_binario::int,0),2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier
            FROM predicciones_futbol
            WHERE mercado::text = %s
            """,
            [m],
        )
        r = cur.fetchone()
        emit = int(r["emitidos"] or 0)
        res = int(r["resueltos"] or 0)
        fallback_rows = int(r["fallback_rows"] or 0)
        cerrados = int(r["cerrados_operativos"] or 0)
        out[m] = {
            "emitidos": emit,
            "resueltos": res,
            "cerrados_operativos": cerrados,
            "pendientes_operativos": int(r["pendientes_operativos"] or 0),
            "pendientes": int(r["pendientes"] or 0),
            "tasa_resolucion": round((res / emit), 4) if emit else 0.0,
            "tasa_cierre_operativo": round((cerrados / emit), 4) if emit else 0.0,
            "lineas_cubiertas": int(r["lineas"] or 0),
            "fallback_rows": fallback_rows,
            "fallback_rate": round((fallback_rows / emit), 4) if emit else 0.0,
            "brier": float(r["brier"]) if r["brier"] is not None else None,
        }
    return out


def main() -> None:
    now = datetime.now(timezone.utc)
    pool = obtener_pool()

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            before = _metricas(cur, TARGET)

            # A) reducir fallback estructural en mercados objetivo (sin calibrador => usar p_raw como p_efectiva)
            cur.execute(
                """
                UPDATE predicciones_futbol
                SET prob_over_calibrada = COALESCE(prob_over_calibrada, prob_over),
                    prob_under_calibrada = COALESCE(prob_under_calibrada, prob_under),
                    actualizado_en = NOW()
                WHERE mercado::text = ANY(%s)
                  AND (prob_over_calibrada IS NULL OR prob_under_calibrada IS NULL)
                  AND prob_over IS NOT NULL
                  AND prob_under IS NOT NULL
                """,
                [TARGET],
            )
            backfill = cur.rowcount
            conn.commit()

    # B) resolver outcomes pendientes de forma focalizada
    res_resolver: Dict[str, Any] = {}
    for m in TARGET:
        resumen = resolver_predicciones_futbol(limite=50000, mercado=m)
        res_resolver[m] = resumen.to_dict()

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            after = _metricas(cur, TARGET)

    reporte = {
        "generated_at": now.isoformat(),
        "mercados_objetivo": TARGET,
        "acciones": {
            "backfill_calibradas_desde_raw": backfill,
            "resolucion_pendientes": res_resolver,
        },
        "antes": before,
        "despues": after,
    }

    out = Path("docs/reportes/BLOQUE_16_RESCATE_CORNERS_PRIORITARIOS.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reporte, indent=2, ensure_ascii=False, default=str))
    print(f"Reporte generado: {out}")


if __name__ == "__main__":
    main()

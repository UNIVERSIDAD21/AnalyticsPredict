#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool


def _collect(cur, days: int) -> List[Dict[str, Any]]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name='predicciones_futbol'
        """
    )
    cols = {r["column_name"] for r in cur.fetchall()}
    fecha_col = "timestamp_generacion" if "timestamp_generacion" in cols else "creado_en"
    columnas_prob = [col for col in ("prob_over_calibrada", "prob_over_raw", "prob_over") if col in cols]
    if not columnas_prob:
        raise RuntimeError("predicciones_futbol sin probabilidad utilizable")
    p_col = "COALESCE(" + ", ".join(columnas_prob) + ")"
    fallback_expr = (
        "AVG(CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END)::numeric"
        if "prob_over_calibrada" in cols else "NULL::numeric"
    )

    cur.execute(
        f"""
        SELECT
          mercado::text AS mercado,
          COUNT(*) AS emitidos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL AND {p_col} IS NOT NULL) AS pares_metricos,
          COUNT(*) FILTER (WHERE outcome_binario IS NULL) AS pendientes,
          COUNT(DISTINCT linea) AS lineas,
          AVG(POWER({p_col}-outcome_binario::int,2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier,
          {fallback_expr} AS fallback_rate
        FROM predicciones_futbol
        WHERE {fecha_col} >= %s
        GROUP BY mercado
        ORDER BY mercado
        """,
        [since],
    )
    out = []
    for r in cur.fetchall():
        d = dict(r)
        emit = int(d.get("emitidos") or 0)
        res = int(d.get("resueltos") or 0)
        d["tasa_resolucion"] = round((res / emit), 4) if emit else 0.0
        out.append(d)
    return out


def main() -> None:
    pool = obtener_pool()
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {"generated_at": now.isoformat(), "ventanas": {}}
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            payload["ventanas"]["semanal"] = _collect(cur, 7)
            payload["ventanas"]["quincenal"] = _collect(cur, 15)
            payload["ventanas"]["mensual"] = _collect(cur, 30)

    out = Path("docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    print(f"Reporte shadow mode: {out}")


if __name__ == "__main__":
    main()

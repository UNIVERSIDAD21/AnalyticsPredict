#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p docs/reportes
export PYTHONPATH="$ROOT_DIR/backend:$ROOT_DIR"

backend/.venv/bin/python <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from psycopg.rows import dict_row

from db import obtener_pool
from api.rutas_metricas_futbol import (
    _clasificar_estabilidad_b3,
    UMBRAL_DEGRADACION_BRIER_ABS,
    UMBRAL_DEGRADACION_BRIER_REL,
    MIN_MUESTRA_SEMANAL_B3,
)

pool = obtener_pool()

query_actual = """
    SELECT
        pf.competicion_id,
        c.codigo AS competicion_codigo,
        c.nombre AS competicion_nombre,
        COUNT(*) AS n,
        AVG(
            POWER(
                COALESCE(p.prob_over_calibrada, p.prob_over)
                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                2
            )
        ) AS brier
    FROM predicciones_futbol p
    JOIN partidos_futbol pf ON pf.id = p.partido_id
    JOIN competiciones_futbol c ON c.id = pf.competicion_id
    WHERE p.outcome_binario IS NOT NULL
      AND COALESCE(p.prob_over_calibrada, p.prob_over) IS NOT NULL
      AND pf.fecha_partido >= NOW() - INTERVAL '7 days'
    GROUP BY pf.competicion_id, c.codigo, c.nombre
"""

query_previa = """
    SELECT
        pf.competicion_id,
        c.codigo AS competicion_codigo,
        c.nombre AS competicion_nombre,
        COUNT(*) AS n,
        AVG(
            POWER(
                COALESCE(p.prob_over_calibrada, p.prob_over)
                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                2
            )
        ) AS brier
    FROM predicciones_futbol p
    JOIN partidos_futbol pf ON pf.id = p.partido_id
    JOIN competiciones_futbol c ON c.id = pf.competicion_id
    WHERE p.outcome_binario IS NOT NULL
      AND COALESCE(p.prob_over_calibrada, p.prob_over) IS NOT NULL
      AND pf.fecha_partido >= NOW() - INTERVAL '14 days'
      AND pf.fecha_partido < NOW() - INTERVAL '7 days'
    GROUP BY pf.competicion_id, c.codigo, c.nombre
"""

with pool.connection() as conn:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query_actual)
        actual = cur.fetchall()
        cur.execute(query_previa)
        previa = cur.fetchall()

res = _clasificar_estabilidad_b3(actual, previa)

now = datetime.now(timezone.utc)
stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
out = Path("docs/reportes") / f"B3_ESTABILIDAD_{stamp}.md"

estado_gate = "APROBADO" if res["gate_aprobado"] else "NO_APROBADO"

lineas = []
lineas.append(f"# B3 Estabilidad semanal — {stamp}")
lineas.append("")
lineas.append(f"- Estado gate B3: **{estado_gate}**")
lineas.append(f"- Ligas evaluadas: **{res['ligas_evaluadas']}**")
lineas.append(f"- Ligas con muestra suficiente: **{res['ligas_con_muestra']}**")
lineas.append(f"- Ligas críticas: **{res['ligas_criticas']}**")
lineas.append(f"- Umbral degradación Brier (abs): **{UMBRAL_DEGRADACION_BRIER_ABS}**")
lineas.append(f"- Umbral degradación Brier (rel): **{UMBRAL_DEGRADACION_BRIER_REL*100:.0f}%**")
lineas.append(f"- Muestra mínima por ventana: **{MIN_MUESTRA_SEMANAL_B3}**")
lineas.append("")
lineas.append("## Detalle por liga")
lineas.append("")
lineas.append("| Liga | Estado | n actual | n previo | Brier actual | Brier previo | Δ abs | Δ rel % |")
lineas.append("|---|---:|---:|---:|---:|---:|---:|---:|")

for l in res["ligas"]:
    lineas.append(
        f"| {l.get('competicion_nombre') or l.get('competicion_codigo') or l.get('competicion_id')} | "
        f"{l['estado']} | {l['n_actual']} | {l['n_previo']} | "
        f"{l['brier_actual']} | {l['brier_previo'] if l['brier_previo'] is not None else '-'} | "
        f"{l['delta_abs'] if l['delta_abs'] is not None else '-'} | "
        f"{l['delta_rel_pct'] if l['delta_rel_pct'] is not None else '-'} |"
    )

lineas.append("")
lineas.append("## Criterio operativo B3 (2 ciclos)")
lineas.append("")
lineas.append("B3 avanza a cierre cuando se cumpla en **2 ciclos semanales consecutivos**:")
lineas.append("1. `gate_aprobado=true`")
lineas.append("2. `ligas_criticas=0`")
lineas.append("3. Al menos 1 liga con muestra suficiente (`ligas_con_muestra > 0`)")

out.write_text("\n".join(lineas), encoding="utf-8")
print(str(out))
PY

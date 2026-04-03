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
from motor_futbol.readiness_gate import cargar_politica_readiness, evaluar_readiness_corners

TARGET = ["CORNERS_1T", "CORNERS_LOCAL_1T"]


def _metricas_actuales(cur, mercado: str) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT
          COUNT(*) AS emitidos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos_binarios,
          COUNT(*) FILTER (WHERE resuelto = false OR resuelto IS NULL) AS pendientes,
          COUNT(DISTINCT linea) AS lineas_cubiertas
        FROM predicciones_futbol
        WHERE mercado::text = %s
        """,
        [mercado],
    )
    r = cur.fetchone()
    return {
        "emitidos": int(r["emitidos"] or 0),
        "resueltos_binarios": int(r["resueltos_binarios"] or 0),
        "pendientes": int(r["pendientes"] or 0),
        "lineas_cubiertas": int(r["lineas_cubiertas"] or 0),
    }


def main() -> None:
    politica = cargar_politica_readiness()

    pool = obtener_pool()
    readiness: List[Dict[str, Any]] = []

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for mercado in TARGET:
                metricas = _metricas_actuales(cur, mercado)
                evaluacion = evaluar_readiness_corners(metricas, politica, ventanas_estables=0)
                readiness.append({
                    "mercado": mercado,
                    "masa_binaria_actual": evaluacion["resueltos_binarios"],
                    "masa_requerida": {
                        "reevaluacion_seria": politica["umbrales"]["min_resueltas_reevaluacion_seria"],
                        "salir_bloqueado": politica["umbrales"]["min_resueltas_salida_bloqueado"],
                        "candidatura_validacion": politica["umbrales"]["min_resueltas_candidatura_validacion"],
                    },
                    "gap_restante": {
                        "reevaluacion_seria": evaluacion["gaps"]["resueltas_para_reevaluacion"],
                        "salir_bloqueado": evaluacion["gaps"]["resueltas_para_salir_bloqueado"],
                        "candidatura_validacion": evaluacion["gaps"]["resueltas_para_candidatura_validacion"],
                    },
                    "coverage_actual": evaluacion["lineas_cubiertas"],
                    "coverage_requerido": {
                        "reevaluacion_seria": politica["umbrales"]["min_lineas_cobertura_reevaluacion"],
                        "salir_bloqueado": politica["umbrales"]["min_lineas_cobertura_salida_bloqueado"],
                        "candidatura_validacion": politica["umbrales"]["min_lineas_cobertura_candidatura_validacion"],
                    },
                    "pendientes_actuales": evaluacion["pendientes"],
                    "pendientes_rate_actual": evaluacion["pendientes_rate"],
                    "pendientes_tolerables_max_rate": {
                        "reevaluacion_seria": politica["umbrales"]["max_pendientes_rate_reevaluacion"],
                        "salir_bloqueado": politica["umbrales"]["max_pendientes_rate_salida_bloqueado"],
                        "candidatura_validacion": politica["umbrales"]["max_pendientes_rate_candidatura_validacion"],
                    },
                    "readiness_status": evaluacion["status"],
                    "descripcion": evaluacion["descripcion"],
                    "faltantes": evaluacion["faltantes"],
                    "gate_reevaluacion_seria_habilitado": evaluacion["gates"]["reevaluacion"],
                })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bloque": 18,
        "mercados_foco": TARGET,
        "politica": politica,
        "readiness": readiness,
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_18_READINESS_GATE_CORNERS.json"
    out_md = reports / "BLOQUE_18_READINESS_GATE_CORNERS.md"

    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 18 — Umbral duro de masa resolutiva y gate de reevaluación",
        "",
        "## Política aplicada",
        f"- Archivo: `backend/config/futbol_readiness_gate_corners_b18.json`",
        f"- Regla: {politica['regla_central']}",
        "",
        "## Readiness por mercado foco",
        "| Mercado | Masa actual | Req. reevaluación | Req. salir BLOQUEADO | Req. candidatura VALIDACIÓN | Coverage actual | Pendientes rate | Readiness | Gate reevaluación |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for r in readiness:
        lines.append(
            f"| {r['mercado']} | {r['masa_binaria_actual']} | {r['masa_requerida']['reevaluacion_seria']} | "
            f"{r['masa_requerida']['salir_bloqueado']} | {r['masa_requerida']['candidatura_validacion']} | "
            f"{r['coverage_actual']} | {r['pendientes_rate_actual']:.4f} | {r['readiness_status']} | "
            f"{'HABILITADO' if r['gate_reevaluacion_seria_habilitado'] else 'BLOQUEADO'} |"
        )

    lines += [
        "",
        "## Conclusión",
        "- Mientras el gate de readiness esté BLOQUEADO, cualquier re-scorecard debe tratarse como no concluyente para promoción.",
        "- Primero se acumula masa resolutiva y estabilidad temporal; luego se reabre reevaluación seria.",
    ]

    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from motor.resolucion_predicciones_futbol import resolver_predicciones_futbol

TARGET = ["CORNERS_1T", "CORNERS_LOCAL_1T"]
WINDOWS = [7, 14, 30]
NO_DISPUTABLES = ["CANCELADO", "POSPUESTO", "SUSPENDIDO"]


def clasificar_cuello(stats: Dict[str, int]) -> str:
    if stats["pendientes_finalizado_con_datos"] > 0:
        return "pipeline_roto_resolubles_sin_convertir"
    if stats["partidos_finalizados"] == 0 and stats["pendientes_programado"] > 0:
        return "calendario_real_sin_partidos_finalizados"
    if stats["partidos_finalizados"] > 0 and stats["finalizados_con_datos"] == 0:
        return "faltan_datos_reales_post_partido"
    if stats["partidos_finalizados"] > 0 and stats["finalizados_con_datos"] > 0 and stats["outcomes_nuevos"] == 0:
        return "posible_fallo_job_o_persistencia"
    return "mixto_o_sin_bloqueo"


def _resolver_col_fecha(cur) -> str:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='predicciones_futbol'")
    cols = {r["column_name"] for r in cur.fetchall()}
    if "timestamp_generacion" in cols:
        return "timestamp_generacion"
    if "creado_en" in cols:
        return "creado_en"
    raise RuntimeError("predicciones_futbol sin timestamp_generacion/creado_en")


def _stats_window(cur, mercado: str, fecha_col: str, days: int, now: datetime) -> Dict[str, Any]:
    start = now - timedelta(days=days)
    cur.execute(
        f"""
        SELECT
          COUNT(*)::int AS emitidos_nuevos,
          COUNT(*) FILTER (WHERE pfu.outcome_binario IS NOT NULL)::int AS outcomes_nuevos,
          COUNT(*) FILTER (WHERE pfu.resuelto = true)::int AS cerrados_operativos_nuevos,
          COUNT(*) FILTER (WHERE pfu.resuelto = false OR pfu.resuelto IS NULL)::int AS pendientes_nuevos,
          COUNT(*) FILTER (WHERE pf.estado = 'FINALIZADO')::int AS partidos_finalizados,
          COUNT(*) FILTER (WHERE pf.estado = 'FINALIZADO' AND pf.local_corners_1t IS NOT NULL AND pf.visitante_corners_1t IS NOT NULL)::int AS finalizados_con_datos,
          COUNT(*) FILTER (
            WHERE (pfu.resuelto = false OR pfu.resuelto IS NULL)
              AND pf.estado = 'FINALIZADO'
              AND pf.local_corners_1t IS NOT NULL AND pf.visitante_corners_1t IS NOT NULL
          )::int AS pendientes_finalizado_con_datos,
          COUNT(*) FILTER (
            WHERE (pfu.resuelto = false OR pfu.resuelto IS NULL)
              AND pf.estado = 'FINALIZADO'
              AND (pf.local_corners_1t IS NULL OR pf.visitante_corners_1t IS NULL)
          )::int AS pendientes_finalizado_sin_datos,
          COUNT(*) FILTER (WHERE (pfu.resuelto = false OR pfu.resuelto IS NULL) AND pf.estado = 'PROGRAMADO')::int AS pendientes_programado,
          COUNT(*) FILTER (WHERE (pfu.resuelto = false OR pfu.resuelto IS NULL) AND pf.estado = ANY(%s))::int AS pendientes_no_disputables
        FROM predicciones_futbol pfu
        JOIN partidos_futbol pf ON pf.id = pfu.partido_id
        WHERE pfu.mercado::text = %s
          AND pfu.{fecha_col} >= %s
        """,
        [NO_DISPUTABLES, mercado, start],
    )
    stats = dict(cur.fetchone())
    stats["days"] = days
    stats["cuello_detectado"] = clasificar_cuello(stats)
    return stats


def _totales(cur, mercado: str) -> Dict[str, int]:
    cur.execute(
        """
        SELECT
          COUNT(*)::int AS emitidos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL)::int AS outcomes,
          COUNT(*) FILTER (WHERE resuelto = true)::int AS cerrados,
          COUNT(*) FILTER (WHERE resuelto = false OR resuelto IS NULL)::int AS pendientes
        FROM predicciones_futbol
        WHERE mercado::text = %s
        """,
        [mercado],
    )
    return dict(cur.fetchone())


def main() -> None:
    ap = argparse.ArgumentParser(description="B19.5 auditoría E2E resolución corners prioritarios")
    ap.add_argument("--apply-backfill", action="store_true", help="ejecuta resolvedor focalizado si detecta resolubles")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    pool = obtener_pool()

    reporte: Dict[str, Any] = {
        "generated_at": now.isoformat(),
        "bloque": "19.5",
        "mercados_foco": TARGET,
        "windows_days": WINDOWS,
        "auditoria": [],
    }

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            fecha_col = _resolver_col_fecha(cur)

            for mercado in TARGET:
                before = _totales(cur, mercado)
                ventanas = [_stats_window(cur, mercado, fecha_col, d, now) for d in WINDOWS]

                pendientes_resolubles = sum(v["pendientes_finalizado_con_datos"] for v in ventanas)

                backfill = None
                if args.apply_backfill and pendientes_resolubles > 0:
                    resumen = resolver_predicciones_futbol(
                        limite=5000,
                        mercado=mercado,
                        solo_hasta_fecha=date.today(),
                        force=False,
                        pool=pool,
                    )
                    backfill = resumen.to_dict()

                after = _totales(cur, mercado)

                reporte["auditoria"].append(
                    {
                        "mercado": mercado,
                        "antes": before,
                        "ventanas": ventanas,
                        "pendientes_resolubles_detectados": pendientes_resolubles,
                        "backfill": backfill,
                        "despues": after,
                        "delta_outcomes": after["outcomes"] - before["outcomes"],
                        "diagnostico_final": clasificar_cuello(ventanas[0]),
                    }
                )

    diag = [a["diagnostico_final"] for a in reporte["auditoria"]]
    if all(d == "calendario_real_sin_partidos_finalizados" for d in diag):
        conclusion = "cuello_principal_calendario_real"
    elif any(d == "pipeline_roto_resolubles_sin_convertir" for d in diag):
        conclusion = "cuello_principal_pipeline"
    else:
        conclusion = "cuello_mixto"

    reporte["conclusion"] = {
        "tipo": conclusion,
        "gate_b20": "bloqueado" if conclusion != "cuello_principal_pipeline" else "bloqueado_hasta_correccion",
        "nota": "No correr B20 mientras gate readiness siga NO_LISTO y sin ritmo resolutivo > 0.",
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_19_5_AUDITORIA_RESOLUCION_CORNERS.json"
    out_md = reports / "BLOQUE_19_5_AUDITORIA_RESOLUCION_CORNERS.md"

    out_json.write_text(json.dumps(reporte, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 19.5 — Auditoría E2E resolución post-partido corners prioritarios",
        "",
        "## Conclusión",
        f"- {reporte['conclusion']['tipo']}",
        f"- Gate B20: {reporte['conclusion']['gate_b20']}",
        "",
        "## Matriz por mercado (ventana 7d)",
        "| Mercado | Emitidos nuevos | Finalizados | Finalizados con datos 1T | Pendientes resolubles | Outcomes nuevos | Diagnóstico |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for a in reporte["auditoria"]:
        v7 = next(v for v in a["ventanas"] if v["days"] == 7)
        lines.append(
            f"| {a['mercado']} | {v7['emitidos_nuevos']} | {v7['partidos_finalizados']} | {v7['finalizados_con_datos']} | "
            f"{v7['pendientes_finalizado_con_datos']} | {v7['outcomes_nuevos']} | {v7['cuello_detectado']} |"
        )

    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

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
from motor_futbol.readiness_gate import cargar_politica_readiness, evaluar_readiness_corners
from motor_futbol.freshness_programado import cargar_politica_sla, clasificar_programado_por_sla

TARGET = ["GOLES_FT", "GOLES_1T", "GOLES_2T", "GOLES_LOCAL_FT", "GOLES_VISITANTE_FT"]


def _score_rescatabilidad(m: Dict[str, Any]) -> int:
    score = 0
    if m["emitidos"] >= 20:
        score += 2
    if m["lineas_cubiertas"] >= 3:
        score += 2
    if m["fallback_rate"] <= 0.05:
        score += 1
    if m["partidos_finalizados_30d"] > 0:
        score += 2
    else:
        score -= 3
    if m["resueltos_binarios"] >= 10:
        score += 2
    elif m["resueltos_binarios"] == 0:
        score -= 2
    if m["pendientes_finalizado_con_datos"] > 0:
        score += 2
    return score


def _nivel(score: int) -> str:
    if score >= 6:
        return "ALTA"
    if score >= 3:
        return "MEDIA"
    return "BAJA"


def _bench_corners(cur, inicio_30: datetime) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT
          COUNT(*) FILTER (WHERE mercado::text LIKE 'CORNERS%%')::int AS emitidos,
          COUNT(*) FILTER (WHERE mercado::text LIKE 'CORNERS%%' AND outcome_binario IS NOT NULL)::int AS resueltos,
          COUNT(*) FILTER (WHERE mercado::text LIKE 'CORNERS%%' AND pf.estado='FINALIZADO' AND pfu.timestamp_generacion >= %s)::int AS finalizados_30d
        FROM predicciones_futbol pfu
        JOIN partidos_futbol pf ON pf.id=pfu.partido_id
        """,
        [inicio_30],
    )
    r = dict(cur.fetchone())
    return r


def main() -> None:
    now = datetime.now(timezone.utc)
    inicio_30 = now - timedelta(days=30)

    pol_readiness = cargar_politica_readiness()
    pol_sla = cargar_politica_sla()

    pool = obtener_pool()
    mercados: List[Dict[str, Any]] = []

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='predicciones_futbol'")
            cols = {r["column_name"] for r in cur.fetchall()}
            fecha_col = "timestamp_generacion" if "timestamp_generacion" in cols else ("creado_en" if "creado_en" in cols else "fecha_partido")

            for m in TARGET:
                cur.execute(
                    f"""
                    SELECT
                      COUNT(*)::int AS emitidos,
                      COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL)::int AS resueltos_binarios,
                      COUNT(*) FILTER (WHERE resuelto=true)::int AS cerrados_operativos,
                      COUNT(*) FILTER (WHERE resuelto=false OR resuelto IS NULL)::int AS pendientes,
                      COUNT(*) FILTER (WHERE prob_over_calibrada IS NULL OR prob_under_calibrada IS NULL)::int AS fallback_rows,
                      COUNT(DISTINCT linea)::int AS lineas_cubiertas,
                      AVG(POWER(COALESCE(prob_over_calibrada, prob_over) - COALESCE(outcome_binario::int,0),2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier,
                      AVG(CASE
                        WHEN outcome_binario IS NULL THEN NULL
                        ELSE -(
                          outcome_binario::int * LN(GREATEST(COALESCE(prob_over_calibrada, prob_over), 1e-9))
                          + (1 - outcome_binario::int) * LN(GREATEST(1 - COALESCE(prob_over_calibrada, prob_over), 1e-9))
                        )
                      END) AS log_loss,
                      COUNT(*) FILTER (WHERE pf.estado='FINALIZADO' AND pfu.{fecha_col} >= %s)::int AS partidos_finalizados_30d,
                      COUNT(*) FILTER (WHERE pf.estado='FINALIZADO' AND (pfu.resuelto=false OR pfu.resuelto IS NULL))::int AS pendientes_finalizado,
                      COUNT(*) FILTER (
                        WHERE pf.estado='FINALIZADO' AND (pfu.resuelto=false OR pfu.resuelto IS NULL)
                          AND (
                            (pfu.mercado::text IN ('GOLES_FT','GOLES_LOCAL_FT','GOLES_VISITANTE_FT') AND pf.local_goles_total IS NOT NULL AND pf.visitante_goles_total IS NOT NULL)
                            OR
                            (pfu.mercado::text IN ('GOLES_1T') AND pf.local_goles_1t IS NOT NULL AND pf.visitante_goles_1t IS NOT NULL)
                            OR
                            (pfu.mercado::text IN ('GOLES_2T') AND pf.local_goles_2t IS NOT NULL AND pf.visitante_goles_2t IS NOT NULL)
                          )
                      )::int AS pendientes_finalizado_con_datos
                    FROM predicciones_futbol pfu
                    JOIN partidos_futbol pf ON pf.id=pfu.partido_id
                    WHERE pfu.mercado::text=%s
                    """,
                    [inicio_30, m],
                )
                r = dict(cur.fetchone())
                emitidos = int(r["emitidos"] or 0)
                resueltos = int(r["resueltos_binarios"] or 0)
                fallback_rows = int(r["fallback_rows"] or 0)

                cur.execute(
                    """
                    SELECT pf.fecha_partido
                    FROM predicciones_futbol pfu
                    JOIN partidos_futbol pf ON pf.id=pfu.partido_id
                    WHERE pfu.mercado::text=%s AND (pfu.resuelto=false OR pfu.resuelto IS NULL) AND pf.estado='PROGRAMADO'
                    """,
                    [m],
                )
                slas = {"SANO": 0, "AMARILLO": 0, "VENCIDO": 0}
                for rr in cur.fetchall():
                    fp = rr["fecha_partido"]
                    if fp is None:
                        slas["AMARILLO"] += 1
                    else:
                        slas[clasificar_programado_por_sla(fp, pol_sla, now)] += 1

                readiness = evaluar_readiness_corners(
                    {
                        "emitidos": emitidos,
                        "resueltos_binarios": resueltos,
                        "pendientes": int(r["pendientes"] or 0),
                        "lineas_cubiertas": int(r["lineas_cubiertas"] or 0),
                    },
                    pol_readiness,
                    ventanas_estables=0,
                )

                row = {
                    "mercado": m,
                    "emitidos": emitidos,
                    "resueltos_binarios": resueltos,
                    "cerrados_operativos": int(r["cerrados_operativos"] or 0),
                    "pendientes": int(r["pendientes"] or 0),
                    "coverage_lineas": int(r["lineas_cubiertas"] or 0),
                    "fallback_rate": round((fallback_rows / emitidos), 4) if emitidos else 0.0,
                    "brier": float(r["brier"]) if r["brier"] is not None else None,
                    "log_loss": float(r["log_loss"]) if r["log_loss"] is not None else None,
                    "partidos_finalizados_30d": int(r["partidos_finalizados_30d"] or 0),
                    "pendientes_finalizado": int(r["pendientes_finalizado"] or 0),
                    "pendientes_finalizado_con_datos": int(r["pendientes_finalizado_con_datos"] or 0),
                    "freshness": slas,
                    "readiness_status": readiness["status"],
                    "readiness_gate": readiness["gates"],
                }
                row["score_rescatabilidad"] = _score_rescatabilidad({
                    "emitidos": row["emitidos"],
                    "lineas_cubiertas": row["coverage_lineas"],
                    "fallback_rate": row["fallback_rate"],
                    "partidos_finalizados_30d": row["partidos_finalizados_30d"],
                    "resueltos_binarios": row["resueltos_binarios"],
                    "pendientes_finalizado_con_datos": row["pendientes_finalizado_con_datos"],
                })
                row["nivel_rescatabilidad"] = _nivel(row["score_rescatabilidad"])
                mercados.append(row)

            corners = _bench_corners(cur, inicio_30)

    ranking = sorted(
        [{
            "mercado": m["mercado"],
            "score": m["score_rescatabilidad"],
            "nivel": m["nivel_rescatabilidad"],
            "readiness_status": m["readiness_status"],
            "pendientes_finalizado_con_datos": m["pendientes_finalizado_con_datos"],
        } for m in mercados],
        key=lambda x: (x["score"], x["pendientes_finalizado_con_datos"]),
        reverse=True,
    )

    top = ranking[:2]
    recomendacion: Dict[str, Any]
    if top and top[0]["nivel"] in {"ALTA", "MEDIA"}:
        recomendacion = {
            "candidato_1": top[0]["mercado"],
            "candidato_2": top[1]["mercado"] if len(top) > 1 else None,
            "accion": "preparar_rescate_condicional",
        }
    else:
        recomendacion = {
            "candidato_1": None,
            "candidato_2": None,
            "accion": "no_abrir_rescate_goles_todavia",
        }

    goles_emit = sum(m["emitidos"] for m in mercados)
    goles_res = sum(m["resueltos_binarios"] for m in mercados)
    goles_fin_30 = sum(m["partidos_finalizados_30d"] for m in mercados)

    if goles_fin_30 > corners.get("finalizados_30d", 0):
        comp = "goles_tiene_mejor_traccion_que_corners"
    elif goles_fin_30 < corners.get("finalizados_30d", 0):
        comp = "counters_mejor_que_goles"
    else:
        comp = "empate_en_cuello_calendario_masa"

    out = {
        "generated_at": now.isoformat(),
        "bloque": "20B",
        "mercados_objetivo": TARGET,
        "auditoria_goles": mercados,
        "ranking_rescatabilidad": ranking,
        "recomendacion": recomendacion,
        "comparacion_estrategica_goles_vs_corners": {
            "goles": {
                "emitidos": goles_emit,
                "resueltos_binarios": goles_res,
                "finalizados_30d": goles_fin_30,
            },
            "corners_benchmark": corners,
            "veredicto": comp,
        },
        "nota": "No se abre B20 ni promoción automática en este bloque.",
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_20B_AUDITORIA_GOLES_FAMILIA.json"
    out_md = reports / "BLOQUE_20B_AUDITORIA_GOLES_FAMILIA.md"

    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 20B — Auditoría y priorización familia GOLES",
        "",
        "## Ranking",
        "| Mercado | Score | Nivel | Emitidos | Resueltos | Pendientes | Readiness | Vencidos |",
        "|---|---:|---|---:|---:|---:|---|---:|",
    ]
    for r in ranking:
        m = next(x for x in mercados if x["mercado"] == r["mercado"])
        lines.append(
            f"| {r['mercado']} | {r['score']} | {r['nivel']} | {m['emitidos']} | {m['resueltos_binarios']} | {m['pendientes']} | {m['readiness_status']} | {m['freshness']['VENCIDO']} |"
        )

    lines += [
        "",
        "## Recomendación",
        f"- Acción: {recomendacion['accion']}",
        f"- Candidato 1: {recomendacion['candidato_1']}",
        f"- Candidato 2: {recomendacion['candidato_2']}",
        "",
        "## Comparación estratégica GOLES vs CORNERS",
        f"- Veredicto: {out['comparacion_estrategica_goles_vs_corners']['veredicto']}",
    ]

    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

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
from motor.resolucion_predicciones_futbol import resolver_predicciones_futbol
from motor_futbol.readiness_gate import cargar_politica_readiness, evaluar_readiness_corners
from motor_futbol.freshness_programado import cargar_politica_sla, clasificar_programado_por_sla

TARGET_CORE = ["CORNERS_FT", "CORNERS_2T", "CORNERS_VISITANTE_2T"]
TARGET_OPTIONAL = ["CORNERS_VISITANTE_1T", "CORNERS_LOCAL_FT"]
TARGET_ALL = TARGET_CORE + TARGET_OPTIONAL


def puntuar_rescatabilidad(m: Dict[str, Any]) -> int:
    score = 0
    if m["emitidos"] >= 20:
        score += 2
    if m["lineas_cubiertas"] >= 3:
        score += 2
    if m["fallback_rate"] <= 0.05:
        score += 2
    if m["pendientes_finalizado_con_datos"] > 0:
        score += 2
    else:
        score -= 1
    if m["partidos_finalizados_30d"] > 0:
        score += 1
    else:
        score -= 3
    if m["resueltos_binarios"] == 0:
        score -= 2
    return score


def nivel_rescatabilidad(score: int) -> str:
    if score >= 6:
        return "ALTA"
    if score >= 3:
        return "MEDIA"
    return "BAJA"


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

            # baseline
            baseline: Dict[str, Dict[str, int]] = {}
            for m in TARGET_ALL:
                cur.execute(
                    f"""
                    SELECT
                      COUNT(*)::int AS emitidos,
                      COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL)::int AS resueltos_binarios,
                      COUNT(*) FILTER (WHERE resuelto=true)::int AS cerrados_operativos,
                      COUNT(*) FILTER (WHERE resuelto=false OR resuelto IS NULL)::int AS pendientes,
                      COUNT(*) FILTER (WHERE prob_over_calibrada IS NULL OR prob_under_calibrada IS NULL)::int AS fallback_rows,
                      COUNT(DISTINCT linea)::int AS lineas_cubiertas,
                      COUNT(*) FILTER (WHERE pf.estado='FINALIZADO' AND (resuelto=false OR resuelto IS NULL))::int AS pendientes_finalizado,
                      COUNT(*) FILTER (WHERE pf.estado='FINALIZADO' AND (resuelto=false OR resuelto IS NULL)
                        AND ((pf.local_corners_2t IS NOT NULL AND pf.visitante_corners_2t IS NOT NULL) OR (pf.local_corners_total IS NOT NULL AND pf.visitante_corners_total IS NOT NULL)))::int AS pendientes_finalizado_con_datos,
                      COUNT(*) FILTER (WHERE pf.estado='FINALIZADO' AND {fecha_col} >= %s)::int AS partidos_finalizados_30d,
                      COUNT(*) FILTER (WHERE pf.estado='PROGRAMADO')::int AS programado_total
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

                # freshness programado
                cur.execute(
                    """
                    SELECT pf.fecha_partido
                    FROM predicciones_futbol pfu
                    JOIN partidos_futbol pf ON pf.id=pfu.partido_id
                    WHERE pfu.mercado::text=%s
                      AND (pfu.resuelto=false OR pfu.resuelto IS NULL)
                      AND pf.estado='PROGRAMADO'
                    """,
                    [m],
                )
                slas = {"SANO": 0, "AMARILLO": 0, "VENCIDO": 0}
                for row in cur.fetchall():
                    fp = row["fecha_partido"]
                    if fp is None:
                        slas["AMARILLO"] += 1
                    else:
                        c = clasificar_programado_por_sla(fp, pol_sla, now)
                        slas[c] += 1

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
                    "scope": "core" if m in TARGET_CORE else "optional",
                    "emitidos": emitidos,
                    "resueltos_binarios": resueltos,
                    "cerrados_operativos": int(r["cerrados_operativos"] or 0),
                    "pendientes": int(r["pendientes"] or 0),
                    "lineas_cubiertas": int(r["lineas_cubiertas"] or 0),
                    "fallback_rate": round((fallback_rows / emitidos), 4) if emitidos else 0.0,
                    "partidos_finalizados_30d": int(r["partidos_finalizados_30d"] or 0),
                    "pendientes_finalizado": int(r["pendientes_finalizado"] or 0),
                    "pendientes_finalizado_con_datos": int(r["pendientes_finalizado_con_datos"] or 0),
                    "freshness_programado": slas,
                    "readiness_status": readiness["status"],
                    "readiness_gate": readiness["gates"],
                }
                s = puntuar_rescatabilidad(row)
                row["score_rescatabilidad"] = s
                row["nivel_rescatabilidad"] = nivel_rescatabilidad(s)
                mercados.append(row)
                baseline[m] = {"resueltos_binarios": resueltos, "cerrados_operativos": int(r["cerrados_operativos"] or 0)}

            # rescate focalizado solo si hay señal ALTA/MEDIA con casos resolubles
            candidatos = [m["mercado"] for m in mercados if m["pendientes_finalizado_con_datos"] > 0 and m["nivel_rescatabilidad"] in {"ALTA", "MEDIA"}]

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
                [TARGET_ALL],
            )
            backfill_calibradas = cur.rowcount
            conn.commit()

    rescate: Dict[str, Any] = {}
    for m in candidatos:
        rescate[m] = resolver_predicciones_futbol(limite=10000, mercado=m).to_dict()

    # post
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for m in mercados:
                cur.execute(
                    """
                    SELECT
                      COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL)::int AS resueltos_binarios,
                      COUNT(*) FILTER (WHERE resuelto=true)::int AS cerrados_operativos
                    FROM predicciones_futbol
                    WHERE mercado::text=%s
                    """,
                    [m["mercado"]],
                )
                r = dict(cur.fetchone())
                m["delta_resueltos_binarios"] = int(r["resueltos_binarios"] or 0) - baseline[m["mercado"]]["resueltos_binarios"]
                m["delta_cerrados_operativos"] = int(r["cerrados_operativos"] or 0) - baseline[m["mercado"]]["cerrados_operativos"]

    ranking = sorted(
        [{
            "mercado": m["mercado"],
            "score": m["score_rescatabilidad"],
            "nivel": m["nivel_rescatabilidad"],
            "pendientes_finalizado_con_datos": m["pendientes_finalizado_con_datos"],
            "readiness_status": m["readiness_status"],
        } for m in mercados],
        key=lambda x: (x["score"], x["pendientes_finalizado_con_datos"]),
        reverse=True,
    )

    out = {
        "generated_at": now.isoformat(),
        "bloque": "20A",
        "mercados_objetivo": TARGET_CORE,
        "mercados_opcionales_evaluados": TARGET_OPTIONAL,
        "auditoria": mercados,
        "ranking_rescatabilidad": ranking,
        "rescate_aplicado": {
            "candidatos": candidatos,
            "backfill_calibradas_desde_raw": backfill_calibradas,
            "resultado_resolver": rescate,
        },
        "nota": "No se toca promoción/B20; solo expansión de marco y rescate técnico donde aplica.",
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_20A_EXPANSION_CORNERS_FAMILIA.json"
    out_md = reports / "BLOQUE_20A_EXPANSION_CORNERS_FAMILIA.md"

    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 20A — Expansión del marco de madurez a familia corners",
        "",
        "## Ranking de rescatabilidad",
        "| Mercado | Score | Nivel | Resueltos | Pendientes finalizado con datos | Readiness |",
        "|---|---:|---|---:|---:|---|",
    ]
    for r in ranking:
        m = next(x for x in mercados if x["mercado"] == r["mercado"])
        lines.append(f"| {r['mercado']} | {r['score']} | {r['nivel']} | {m['resueltos_binarios']} | {r['pendientes_finalizado_con_datos']} | {r['readiness_status']} |")

    lines += [
        "",
        "## Rescate técnico aplicado",
        f"- Candidatos: {', '.join(candidatos) if candidatos else 'ninguno'}",
        f"- Backfill calibradas: {backfill_calibradas}",
        "",
        "## Regla",
        "- Este bloque no ejecuta B20 ni promoción automática.",
    ]
    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

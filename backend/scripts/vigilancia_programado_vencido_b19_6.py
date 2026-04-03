#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import obtener_pool
from motor_futbol.freshness_programado import cargar_politica_sla, clasificar_programado_por_sla, horas_desfase

TARGET = ["CORNERS_1T", "CORNERS_LOCAL_1T"]


def _row_to_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return None


def main() -> None:
    now = datetime.now(timezone.utc)
    politica = cargar_politica_sla()

    pool = obtener_pool()
    mercados: List[Dict[str, Any]] = []

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='partidos_futbol'")
            cols_pf = {r['column_name'] for r in cur.fetchall()}
            proveedor_sql = "pf.proveedor" if "proveedor" in cols_pf else "NULL::text AS proveedor"

            cur.execute(
                f"""
                SELECT
                  pfu.id AS prediccion_id,
                  pfu.mercado::text AS mercado,
                  pfu.partido_id,
                  pfu.fecha_partido AS fecha_prediccion,
                  pf.fecha_partido AS fecha_partido,
                  pf.estado::text AS estado_partido,
                  pf.competicion_id,
                  {proveedor_sql}
                FROM predicciones_futbol pfu
                JOIN partidos_futbol pf ON pf.id = pfu.partido_id
                WHERE pfu.mercado::text = ANY(%s)
                  AND (pfu.resuelto = false OR pfu.resuelto IS NULL)
                  AND pf.estado = 'PROGRAMADO'
                ORDER BY pf.fecha_partido ASC NULLS LAST, pfu.fecha_partido ASC
                """,
                [TARGET],
            )
            rows = cur.fetchall()

    por_mercado = defaultdict(list)
    for r in rows:
        mercado = r["mercado"]
        fecha_ref = _row_to_dt(r["fecha_partido"]) or _row_to_dt(r["fecha_prediccion"])
        if fecha_ref is None:
            clase = "AMARILLO"
            atraso_horas = None
        else:
            clase = clasificar_programado_por_sla(fecha_ref, politica, now)
            atraso_horas = round(horas_desfase(fecha_ref, now), 2)

        por_mercado[mercado].append(
            {
                "prediccion_id": str(r["prediccion_id"]),
                "partido_id": str(r["partido_id"]),
                "fecha_partido": str(r["fecha_partido"]) if r["fecha_partido"] else None,
                "fecha_prediccion": str(r["fecha_prediccion"]) if r["fecha_prediccion"] else None,
                "estado_partido": r["estado_partido"],
                "competicion_id": str(r["competicion_id"]) if r["competicion_id"] is not None else None,
                "proveedor": r["proveedor"],
                "atraso_horas": atraso_horas,
                "clase_sla": clase,
            }
        )

    for m in TARGET:
        casos = por_mercado.get(m, [])
        c = Counter(x["clase_sla"] for x in casos)
        por_comp = Counter((x["competicion_id"] or "sin_competicion") for x in casos if x["clase_sla"] == "VENCIDO")
        por_prov = Counter((x["proveedor"] or "sin_proveedor") for x in casos if x["clase_sla"] == "VENCIDO")

        mercados.append(
            {
                "mercado": m,
                "programado_total": len(casos),
                "programado_sano": c.get("SANO", 0),
                "programado_amarillo": c.get("AMARILLO", 0),
                "programado_vencido": c.get("VENCIDO", 0),
                "impacto_masa_resolutiva": {
                    "bloquea_outcomes_nuevos": len(casos) > 0,
                    "potencial_stale_data": c.get("VENCIDO", 0) > 0,
                },
                "patron_vencidos": {
                    "por_competicion": dict(por_comp),
                    "por_proveedor": dict(por_prov),
                },
                "muestra_casos": casos[:20],
            }
        )

    total_vencidos = sum(m["programado_vencido"] for m in mercados)
    if total_vencidos > 0:
        senal = {
            "tipo": "stale_data_detectado",
            "abrir_bloque_ingestion_resultados": True,
            "mensaje": "Se detectaron PROGRAMADO vencidos; abrir bloque de corrección de ingestión/freshness.",
        }
    else:
        senal = {
            "tipo": "calendario_real_sin_vencidos",
            "abrir_bloque_ingestion_resultados": False,
            "mensaje": "No hay PROGRAMADO vencidos; el bloqueo actual sigue siendo calendario real.",
        }

    out = {
        "generated_at": now.isoformat(),
        "bloque": "19.6",
        "mercados_foco": TARGET,
        "politica_sla": politica,
        "resumen_mercados": mercados,
        "senal_operativa": senal,
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_19_6_VIGILANCIA_PROGRAMADO_VENCIDO.json"
    out_md = reports / "BLOQUE_19_6_VIGILANCIA_PROGRAMADO_VENCIDO.md"

    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 19.6 — Vigilancia automática de PROGRAMADO vencido",
        "",
        "## SLA",
        f"- normal <= {politica['sla_horas']['normal_hasta']}h",
        f"- alerta >= {politica['sla_horas']['alerta_desde']}h y < {politica['sla_horas']['vencido_desde']}h",
        f"- vencido >= {politica['sla_horas']['vencido_desde']}h",
        "",
        "## Resumen por mercado",
        "| Mercado | PROGRAMADO total | SANO | AMARILLO | VENCIDO |",
        "|---|---:|---:|---:|---:|",
    ]

    for m in mercados:
        lines.append(
            f"| {m['mercado']} | {m['programado_total']} | {m['programado_sano']} | {m['programado_amarillo']} | {m['programado_vencido']} |"
        )

    lines += [
        "",
        "## Señal operativa",
        f"- Tipo: {senal['tipo']}",
        f"- Abrir bloque ingestión/resultados: {'SÍ' if senal['abrir_bloque_ingestion_resultados'] else 'NO'}",
        f"- Mensaje: {senal['mensaje']}",
    ]

    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

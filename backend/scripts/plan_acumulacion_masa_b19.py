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
from motor_futbol.readiness_tracking import (
    calcular_delta_readiness,
    proyectar_horizonte_semanas,
    evaluar_disparo_b20,
)

TARGET = ["CORNERS_1T", "CORNERS_LOCAL_1T"]
VENTANAS = [7, 14, 30]


def _resolver_columna_fecha(cur) -> str:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='predicciones_futbol'
        """
    )
    cols = {r["column_name"] for r in cur.fetchall()}
    if "timestamp_generacion" in cols:
        return "timestamp_generacion"
    if "creado_en" in cols:
        return "creado_en"
    raise RuntimeError("No existe timestamp_generacion/creado_en en predicciones_futbol")


def _metricas_actuales(cur, mercado: str) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT
          COUNT(*) AS emitidos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos_binarios,
          COUNT(*) FILTER (WHERE resuelto = true) AS cerrados_operativos,
          COUNT(*) FILTER (WHERE resuelto = false OR resuelto IS NULL) AS pendientes,
          COUNT(DISTINCT linea) AS lineas_cubiertas
        FROM predicciones_futbol
        WHERE mercado::text = %s
        """,
        [mercado],
    )
    r = cur.fetchone()
    emitidos = int(r["emitidos"] or 0)
    resueltos = int(r["resueltos_binarios"] or 0)
    return {
        "emitidos": emitidos,
        "resueltos_binarios": resueltos,
        "cerrados_operativos": int(r["cerrados_operativos"] or 0),
        "pendientes": int(r["pendientes"] or 0),
        "lineas_cubiertas": int(r["lineas_cubiertas"] or 0),
        "tasa_resolucion": round((resueltos / emitidos), 4) if emitidos else 0.0,
    }


def _metricas_ventana(cur, mercado: str, fecha_col: str, days: int, now: datetime) -> Dict[str, Any]:
    start = now - timedelta(days=days)
    cur.execute(
        f"""
        SELECT
          COUNT(*) AS emitidos_nuevos,
          COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos_binarios_nuevos,
          COUNT(*) FILTER (WHERE resuelto = true) AS cerrados_operativos_nuevos
        FROM predicciones_futbol
        WHERE mercado::text = %s
          AND {fecha_col} >= %s
        """,
        [mercado, start],
    )
    r = cur.fetchone()
    emitidos_nuevos = int(r["emitidos_nuevos"] or 0)
    resueltos_nuevos = int(r["resueltos_binarios_nuevos"] or 0)
    cerrados_nuevos = int(r["cerrados_operativos_nuevos"] or 0)
    pendientes_calendario = max(0, emitidos_nuevos - cerrados_nuevos)
    pendientes_calendario_rate = (pendientes_calendario / emitidos_nuevos) if emitidos_nuevos else 0.0
    return {
        "days": days,
        "emitidos_nuevos": emitidos_nuevos,
        "resueltos_binarios_nuevos": resueltos_nuevos,
        "cerrados_operativos_nuevos": cerrados_nuevos,
        "pendientes_calendario_estimados": pendientes_calendario,
        "pendientes_calendario_rate": round(pendientes_calendario_rate, 4),
        "tasa_resolucion_ventana": round((resueltos_nuevos / emitidos_nuevos), 4) if emitidos_nuevos else 0.0,
    }


def _calcular_ventanas_estables(ventanas: List[Dict[str, Any]]) -> int:
    # estabilidad mínima: avance resolutivo positivo en ventanas cortas consecutivas
    consecutivas = 0
    for w in ventanas:
        if w["resueltos_binarios_nuevos"] > 0:
            consecutivas += 1
        else:
            break
    return consecutivas


def main() -> None:
    now = datetime.now(timezone.utc)

    b18_path = Path("docs/reportes/BLOQUE_18_READINESS_GATE_CORNERS.json")
    if not b18_path.exists():
        raise RuntimeError("No existe baseline B18. Ejecuta primero gate_readiness_corners_b18.py")
    b18 = json.loads(b18_path.read_text())
    base_by_market = {r["mercado"]: r for r in b18.get("readiness", [])}

    politica = cargar_politica_readiness()
    plan: List[Dict[str, Any]] = []

    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            fecha_col = _resolver_columna_fecha(cur)

            for mercado in TARGET:
                actual = _metricas_actuales(cur, mercado)
                ventanas = [_metricas_ventana(cur, mercado, fecha_col, d, now) for d in VENTANAS]
                ventanas_estables = _calcular_ventanas_estables(ventanas)
                readiness = evaluar_readiness_corners(actual, politica, ventanas_estables=ventanas_estables)

                base = base_by_market.get(mercado, {})
                gap_base = (base.get("gap_restante") or {})

                delta_gap_reeval = calcular_delta_readiness(int(gap_base.get("reevaluacion_seria", readiness["gaps"]["resueltas_para_reevaluacion"])), readiness["gaps"]["resueltas_para_reevaluacion"])
                delta_gap_bloq = calcular_delta_readiness(int(gap_base.get("salir_bloqueado", readiness["gaps"]["resueltas_para_salir_bloqueado"])), readiness["gaps"]["resueltas_para_salir_bloqueado"])
                delta_gap_val = calcular_delta_readiness(int(gap_base.get("candidatura_validacion", readiness["gaps"]["resueltas_para_candidatura_validacion"])), readiness["gaps"]["resueltas_para_candidatura_validacion"])

                ritmo_semanal = float(ventanas[0]["resueltos_binarios_nuevos"])
                horizontes = {
                    "semanas_hasta_reevaluacion_seria": proyectar_horizonte_semanas(readiness["gaps"]["resueltas_para_reevaluacion"], ritmo_semanal),
                    "semanas_hasta_salir_bloqueado": proyectar_horizonte_semanas(readiness["gaps"]["resueltas_para_salir_bloqueado"], ritmo_semanal),
                    "semanas_hasta_candidatura_validacion": proyectar_horizonte_semanas(readiness["gaps"]["resueltas_para_candidatura_validacion"], ritmo_semanal),
                }

                plan.append({
                    "mercado": mercado,
                    "masa_actual": actual["resueltos_binarios"],
                    "metas_siguiente_ventana": {
                        "semanal_resueltos_nuevos_min": 4,
                        "quincenal_resueltos_nuevos_min": 8,
                        "mensual_resueltos_nuevos_min": 16,
                    },
                    "gaps_actuales": {
                        "reevaluacion_seria": readiness["gaps"]["resueltas_para_reevaluacion"],
                        "salir_bloqueado": readiness["gaps"]["resueltas_para_salir_bloqueado"],
                        "candidatura_validacion": readiness["gaps"]["resueltas_para_candidatura_validacion"],
                    },
                    "delta_gap_desde_b18": {
                        "reevaluacion_seria": delta_gap_reeval,
                        "salir_bloqueado": delta_gap_bloq,
                        "candidatura_validacion": delta_gap_val,
                    },
                    "horizonte_estimado": horizontes,
                    "tracking_ventanas": ventanas,
                    "readiness_actual": readiness,
                    "avance_suficiente": {
                        "semanal": ventanas[0]["resueltos_binarios_nuevos"] >= 4,
                        "quincenal": ventanas[1]["resueltos_binarios_nuevos"] >= 8,
                        "mensual": ventanas[2]["resueltos_binarios_nuevos"] >= 16,
                    },
                    "puede_disparar_nueva_reevaluacion_seria": readiness["gates"]["reevaluacion"],
                })

    readiness_map = {
        p["mercado"]: {
            "gate_reevaluacion_seria_habilitado": p["puede_disparar_nueva_reevaluacion_seria"],
            "status": p["readiness_actual"]["status"],
        }
        for p in plan
    }
    gate_b20 = evaluar_disparo_b20(readiness_map)

    payload = {
        "generated_at": now.isoformat(),
        "bloque": 19,
        "mercados_foco": TARGET,
        "regla": "No correr re-scorecard seria hasta que gate readiness esté habilitado para ambos mercados foco.",
        "plan_operativo": plan,
        "gate_disparo_b20": {
            "habilitado": gate_b20["habilitado"],
            "motivo": gate_b20["motivo"],
            "mercados_pendientes": gate_b20["mercados_pendientes"],
            "condicion_formal": "B20 se habilita solo cuando CORNERS_1T y CORNERS_LOCAL_1T tengan gate_reevaluacion_seria_habilitado=true en la misma corrida.",
        },
    }

    reports = Path("docs/reportes")
    reports.mkdir(parents=True, exist_ok=True)
    out_json = reports / "BLOQUE_19_PLAN_ACUMULACION_MASA_CORNERS.json"
    out_md = reports / "BLOQUE_19_PLAN_ACUMULACION_MASA_CORNERS.md"

    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    lines = [
        "# BLOQUE 19 — Plan operativo de acumulación de masa resolutiva",
        "",
        "## Regla",
        "- No tocar promoción/validación final. Solo acumulación, tracking y gate de disparo a B20.",
        "",
        "## Tracker de progreso por mercado",
        "| Mercado | Masa actual | Gap reeval | Gap salir bloqueado | Gap validación | Ritmo semanal (resueltos nuevos) | Horizon reeval (semanas) | Readiness | ¿Dispara reevaluación seria? |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for p in plan:
        w7 = p["tracking_ventanas"][0]
        h = p["horizonte_estimado"]["semanas_hasta_reevaluacion_seria"]
        lines.append(
            f"| {p['mercado']} | {p['masa_actual']} | {p['gaps_actuales']['reevaluacion_seria']} | "
            f"{p['gaps_actuales']['salir_bloqueado']} | {p['gaps_actuales']['candidatura_validacion']} | "
            f"{w7['resueltos_binarios_nuevos']} | {h if h is not None else 'N/D'} | {p['readiness_actual']['status']} | "
            f"{'SÍ' if p['puede_disparar_nueva_reevaluacion_seria'] else 'NO'} |"
        )

    lines += [
        "",
        "## Gate de disparo a B20",
        f"- Habilitado: {'SÍ' if payload['gate_disparo_b20']['habilitado'] else 'NO'}",
        f"- Motivo: {payload['gate_disparo_b20']['motivo']}",
        f"- Mercados pendientes: {', '.join(payload['gate_disparo_b20']['mercados_pendientes']) if payload['gate_disparo_b20']['mercados_pendientes'] else 'ninguno'}",
        f"- Condición formal: {payload['gate_disparo_b20']['condicion_formal']}",
    ]

    out_md.write_text("\n".join(lines))
    print(f"Generados: {out_json.name}, {out_md.name}")


if __name__ == "__main__":
    main()

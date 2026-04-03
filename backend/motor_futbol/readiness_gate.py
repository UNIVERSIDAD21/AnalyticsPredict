from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "futbol_readiness_gate_corners_b18.json"


def cargar_politica_readiness(path: Path = POLICY_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text())


def evaluar_readiness_corners(metricas: Dict[str, Any], politica: Dict[str, Any], ventanas_estables: int = 0) -> Dict[str, Any]:
    u = politica["umbrales"]

    emitidos = int(metricas.get("emitidos") or 0)
    resueltos = int(metricas.get("resueltos_binarios") or 0)
    lineas = int(metricas.get("lineas_cubiertas") or 0)
    pendientes = int(metricas.get("pendientes") or 0)
    pendientes_rate = (pendientes / emitidos) if emitidos else 1.0

    checks = {
        "reevaluacion": {
            "resueltas": resueltos >= int(u["min_resueltas_reevaluacion_seria"]),
            "pendientes": pendientes_rate <= float(u["max_pendientes_rate_reevaluacion"]),
            "lineas": lineas >= int(u["min_lineas_cobertura_reevaluacion"]),
            "ventanas": ventanas_estables >= int(u["min_ventanas_estables_reevaluacion"]),
        },
        "salir_bloqueado": {
            "resueltas": resueltos >= int(u["min_resueltas_salida_bloqueado"]),
            "pendientes": pendientes_rate <= float(u["max_pendientes_rate_salida_bloqueado"]),
            "lineas": lineas >= int(u["min_lineas_cobertura_salida_bloqueado"]),
            "ventanas": ventanas_estables >= int(u["min_ventanas_estables_salida_bloqueado"]),
        },
        "candidatura_validacion": {
            "resueltas": resueltos >= int(u["min_resueltas_candidatura_validacion"]),
            "pendientes": pendientes_rate <= float(u["max_pendientes_rate_candidatura_validacion"]),
            "lineas": lineas >= int(u["min_lineas_cobertura_candidatura_validacion"]),
            "ventanas": ventanas_estables >= int(u["min_ventanas_estables_candidatura_validacion"]),
        },
    }

    gates = {k: all(v.values()) for k, v in checks.items()}

    if gates["candidatura_validacion"]:
        status = "LISTO_CANDIDATO_VALIDACION"
    elif gates["salir_bloqueado"]:
        status = "LISTO_SALIR_BLOQUEADO"
    elif gates["reevaluacion"]:
        status = "LISTO_REEVALUACION"
    else:
        status = "NO_LISTO"

    faltantes: List[str] = []
    if not checks["reevaluacion"]["resueltas"]:
        faltantes.append("masa_binaria_insuficiente_para_reevaluacion")
    if not checks["reevaluacion"]["pendientes"]:
        faltantes.append("pendientes_excesivos_para_reevaluacion")
    if not checks["reevaluacion"]["lineas"]:
        faltantes.append("coverage_lineas_insuficiente_para_reevaluacion")
    if not checks["reevaluacion"]["ventanas"]:
        faltantes.append("estabilidad_temporal_insuficiente_para_reevaluacion")

    return {
        "status": status,
        "descripcion": politica["interpretacion"][status],
        "emitidos": emitidos,
        "resueltos_binarios": resueltos,
        "pendientes": pendientes,
        "pendientes_rate": round(pendientes_rate, 4),
        "lineas_cubiertas": lineas,
        "ventanas_estables": ventanas_estables,
        "checks": checks,
        "gates": gates,
        "faltantes": faltantes,
        "gaps": {
            "resueltas_para_reevaluacion": max(0, int(u["min_resueltas_reevaluacion_seria"]) - resueltos),
            "resueltas_para_salir_bloqueado": max(0, int(u["min_resueltas_salida_bloqueado"]) - resueltos),
            "resueltas_para_candidatura_validacion": max(0, int(u["min_resueltas_candidatura_validacion"]) - resueltos),
            "lineas_para_reevaluacion": max(0, int(u["min_lineas_cobertura_reevaluacion"]) - lineas),
            "lineas_para_salir_bloqueado": max(0, int(u["min_lineas_cobertura_salida_bloqueado"]) - lineas),
            "lineas_para_candidatura_validacion": max(0, int(u["min_lineas_cobertura_candidatura_validacion"]) - lineas),
        },
    }

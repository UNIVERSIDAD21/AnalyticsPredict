from __future__ import annotations

import math
from typing import Dict, Any


def calcular_delta_readiness(gap_base: int, gap_actual: int) -> int:
    return int(gap_base) - int(gap_actual)


def proyectar_horizonte_semanas(gap_restante: int, ritmo_resolucion_semanal: float) -> int | None:
    if ritmo_resolucion_semanal <= 0:
        return None
    return int(math.ceil(float(gap_restante) / float(ritmo_resolucion_semanal)))


def evaluar_disparo_b20(readiness_por_mercado: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not readiness_por_mercado:
        return {
            "habilitado": False,
            "motivo": "sin_datos_readiness",
            "mercados_pendientes": [],
        }

    pendientes = [
        mercado
        for mercado, datos in readiness_por_mercado.items()
        if not bool(datos.get("gate_reevaluacion_seria_habilitado"))
    ]

    return {
        "habilitado": len(pendientes) == 0,
        "motivo": "habilitado" if len(pendientes) == 0 else "mercados_no_listos",
        "mercados_pendientes": pendientes,
    }

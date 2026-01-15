# -*- coding: utf-8 -*-
"""
distribucion.py — Métricas de calidad para predicciones de distribución.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional


def calcular_metricas_distribucion(
    predicciones: Iterable[
        tuple[
            Optional[float],
            Optional[float],
            Optional[float],
            Optional[float],
        ]
    ],
) -> dict[str, float | int | None]:
    """
    Calcula métricas basadas en la distribución predicha.

    Cada predicción es una tupla:
    (media_predicha, valor_real, intervalo_inferior, intervalo_superior)

    Reglas:
    - Excluye filas sin valor_real o media_predicha.
    - Cobertura solo se calcula sobre filas con intervalo completo.
    - Si no hay intervalos, cobertura = None.
    - Nunca retorna NaN ni Infinity.
    """
    errores = []
    n_con_intervalo = 0
    cobertura_aciertos = 0
    n = 0

    for media_predicha, valor_real, intervalo_inferior, intervalo_superior in predicciones:
        if media_predicha is None or valor_real is None:
            continue
        if not _es_finito(media_predicha) or not _es_finito(valor_real):
            continue
        n += 1
        error = float(valor_real) - float(media_predicha)
        errores.append(error)

        if (
            intervalo_inferior is not None
            and intervalo_superior is not None
            and _es_finito(intervalo_inferior)
            and _es_finito(intervalo_superior)
        ):
            n_con_intervalo += 1
            if float(intervalo_inferior) <= float(valor_real) <= float(intervalo_superior):
                cobertura_aciertos += 1

    n_sin_intervalo = n - n_con_intervalo

    if n == 0:
        return {
            "n": 0,
            "mae_media": None,
            "rmse_media": None,
            "sesgo_media": None,
            "cobertura_intervalo": None,
            "n_con_intervalo": 0,
            "n_sin_intervalo": 0,
        }

    mae_media = sum(abs(error) for error in errores) / n
    rmse_media = math.sqrt(sum(error * error for error in errores) / n)
    sesgo_media = sum(errores) / n

    cobertura_intervalo = None
    if n_con_intervalo > 0:
        cobertura_intervalo = cobertura_aciertos / n_con_intervalo

    return {
        "n": n,
        "mae_media": _normalizar_numero(mae_media),
        "rmse_media": _normalizar_numero(rmse_media),
        "sesgo_media": _normalizar_numero(sesgo_media),
        "cobertura_intervalo": _normalizar_numero(cobertura_intervalo),
        "n_con_intervalo": n_con_intervalo,
        "n_sin_intervalo": n_sin_intervalo,
    }


def _es_finito(valor: float) -> bool:
    return math.isfinite(float(valor))


def _normalizar_numero(valor: Optional[float]) -> Optional[float]:
    if valor is None:
        return None
    if not math.isfinite(valor):
        return None
    return float(valor)

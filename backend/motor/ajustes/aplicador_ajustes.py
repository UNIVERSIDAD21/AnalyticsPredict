# -*- coding: utf-8 -*-
"""aplicador_ajustes.py — Aplica ajustes a la predicción base."""

from __future__ import annotations

from typing import Optional

from .tipos_ajustes import ResultadoAjustes
from ..calculadora_probabilidad import calcular_probabilidad_over

PESOS_B2B_CUARTOS = {
    "Q1": 0.2,
    "Q2": 0.2,
    "Q3": 0.3,
    "Q4": 0.3,
}


def _escala_cuarto(ajuste_total: float, resultado: ResultadoAjustes, mercado: str) -> float:
    if mercado == "COMPLETO":
        return ajuste_total

    if mercado not in PESOS_B2B_CUARTOS:
        return ajuste_total / 4.0

    if resultado.ajuste_total == 0:
        ratio = 0.0
    else:
        ratio = resultado.ajuste_total_capped / resultado.ajuste_total

    ajuste_cuarto = 0.0
    for ajuste in resultado.ajustes:
        valor = ajuste.valor * ratio
        if ajuste.factor == "back_to_back":
            ajuste_cuarto += valor * PESOS_B2B_CUARTOS[mercado]
        else:
            ajuste_cuarto += valor * 0.25
    return ajuste_cuarto


def aplicar_ajustes(
    media_base: float,
    desviacion_base: float,
    linea: Optional[float],
    ajustes: ResultadoAjustes,
    mercado: str,
) -> tuple[float, float, float]:
    """Aplica ajustes y recalcula probabilidades."""
    ajuste_aplicado = _escala_cuarto(ajustes.ajuste_total_capped, ajustes, mercado)
    media_ajustada = media_base + ajuste_aplicado

    prob_over = 0.0
    if linea is not None:
        prob_over = calcular_probabilidad_over(media_ajustada, desviacion_base, linea)
    prob_under = 1.0 - prob_over if linea is not None else 0.0

    return media_ajustada, prob_over, prob_under

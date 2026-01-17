# -*- coding: utf-8 -*-
"""motor_ajustes.py — Orquestador principal de ajustes."""

from __future__ import annotations

from typing import Optional

from .aplicador_ajustes import aplicar_ajustes
from .reglas_ajuste import calcular_ajustes
from .tipos_ajustes import PrediccionAjustada
from .validador_ajustes import aplicar_caps
from ..contexto.tipos_contexto import ContextoCompleto
from ..tipos import NivelConfianza


def _nivel_a_puntaje(nivel: NivelConfianza) -> float:
    if nivel == NivelConfianza.ALTA:
        return 2.0
    if nivel == NivelConfianza.MEDIA:
        return 1.0
    return 0.0


def _puntaje_a_nivel(puntaje: float) -> NivelConfianza:
    if puntaje >= 1.5:
        return NivelConfianza.ALTA
    if puntaje >= 0.75:
        return NivelConfianza.MEDIA
    return NivelConfianza.BAJA


def aplicar_ajustes_contextuales(
    contexto: ContextoCompleto,
    media_base: float,
    desviacion_base: float,
    probabilidad_over_base: float,
    probabilidad_under_base: float,
    linea: Optional[float],
    mercado: str,
    confianza_base: NivelConfianza,
) -> PrediccionAjustada:
    """Calcula y aplica ajustes contextuales sobre la predicción base."""
    resultado_ajustes = calcular_ajustes(contexto, media_base)
    resultado_ajustes = aplicar_caps(resultado_ajustes)

    advertencias = list(resultado_ajustes.advertencias)

    delta_confianza = 0.0
    if contexto.h2h and contexto.h2h.total_partidos >= 5:
        delta_confianza += 0.2
    if contexto.descanso_equipo.es_back_to_back or contexto.descanso_rival.es_back_to_back:
        delta_confianza -= 0.5
    if abs(contexto.descanso_equipo.dias_descanso - contexto.descanso_rival.dias_descanso) >= 3:
        delta_confianza -= 0.3
    if contexto.h2h and abs(contexto.h2h.promedio_total - media_base) > 8:
        delta_confianza -= 0.2
        advertencias.append("⚠️ Predicción alejada del histórico H2H.")
    if abs(resultado_ajustes.ajuste_total_capped) > 6:
        delta_confianza -= 0.3

    resultado_ajustes.confianza_delta = delta_confianza
    resultado_ajustes.advertencias = list(dict.fromkeys(advertencias))

    media_ajustada, prob_over_ajustada, prob_under_ajustada = aplicar_ajustes(
        media_base=media_base,
        desviacion_base=desviacion_base,
        linea=linea,
        ajustes=resultado_ajustes,
        mercado=mercado,
    )

    puntaje_base = _nivel_a_puntaje(confianza_base)
    puntaje_final = max(min(puntaje_base + delta_confianza, 2.0), 0.0)
    nivel_final = _puntaje_a_nivel(puntaje_final)

    return PrediccionAjustada(
        media_base=media_base,
        desviacion_base=desviacion_base,
        probabilidad_over_base=probabilidad_over_base,
        probabilidad_under_base=probabilidad_under_base,
        media_ajustada=media_ajustada,
        probabilidad_over_ajustada=prob_over_ajustada,
        probabilidad_under_ajustada=prob_under_ajustada,
        ajustes_aplicados=resultado_ajustes,
        confianza_base=confianza_base.value,
        confianza_ajustada=nivel_final.value,
    )

# -*- coding: utf-8 -*-
"""Utilidades B3: estabilización fútbol cross-liga y confianza por muestra."""

from __future__ import annotations

from typing import Optional

PESO_CONTEXTO_POR_COMPETICION = {
    "PREMIER_LEAGUE": 0.78,
    "LALIGA": 0.76,
    "SERIE_A": 0.74,
    "BUNDESLIGA": 0.73,
    "LIGUE_1": 0.72,
    "BRASILEIRAO": 0.69,
    "PRIMERA_A": 0.68,
}


def peso_contexto_por_competicion(codigo_competicion: Optional[str]) -> float:
    codigo = (codigo_competicion or "").upper().strip()
    return float(PESO_CONTEXTO_POR_COMPETICION.get(codigo, 0.70))


def combinar_valor_cross_liga(
    *,
    valor_ctx: Optional[float],
    n_ctx: int,
    valor_global: Optional[float],
    n_global: int,
    valor_liga: Optional[float],
    codigo_competicion: Optional[str],
) -> float:
    """Combina contexto relevante + global + liga con ponderación por competición y muestra."""
    piezas: list[tuple[float, float]] = []

    peso_ctx_obj = peso_contexto_por_competicion(codigo_competicion)
    if valor_ctx is not None and n_ctx > 0:
        ajuste_muestra = min(1.0, n_ctx / 30.0)
        piezas.append((float(valor_ctx), peso_ctx_obj * ajuste_muestra))

    if valor_global is not None and n_global > 0:
        peso_global = 0.22 + min(0.12, n_global / 300.0)
        piezas.append((float(valor_global), peso_global))

    if valor_liga is not None:
        # Fallback estructural: mientras menor muestra contextual, más pesa la liga.
        falta_contexto = 1.0 if n_ctx <= 0 else max(0.0, 1.0 - min(1.0, n_ctx / 25.0))
        peso_liga = 0.12 + (0.22 * falta_contexto)
        piezas.append((float(valor_liga), peso_liga))

    if not piezas:
        return 0.0

    total_peso = sum(p for _, p in piezas)
    if total_peso <= 0:
        return float(piezas[0][0])

    return float(sum(v * p for v, p in piezas) / total_peso)


def ajustar_probabilidad_por_muestras(prob: float, n_total: int, n_relevante: int) -> float:
    """Contrae probabilidad hacia 0.5 cuando la muestra relevante es baja."""
    prob_clamp = max(0.02, min(0.98, float(prob)))
    edge = prob_clamp - 0.5

    factor_total = min(1.0, max(0.0, n_total / 80.0))
    factor_relevante = min(1.0, max(0.0, n_relevante / 25.0))
    factor = 0.25 + (0.75 * min(factor_total, factor_relevante))

    ajustada = 0.5 + (edge * factor)
    return float(max(0.02, min(0.98, ajustada)))


def nivel_confianza_b3(prob: float, n_total: int, n_relevante: int) -> str:
    """Confianza considerando probabilidad y cobertura total/relevante."""
    p = float(prob)
    extrema = p >= 0.75 or p <= 0.25

    if n_total >= 80 and n_relevante >= 25 and extrema:
        return "ALTA"
    if n_total >= 40 and n_relevante >= 12:
        return "MEDIA"
    if extrema and n_relevante >= 8:
        return "MEDIA"
    return "BAJA"

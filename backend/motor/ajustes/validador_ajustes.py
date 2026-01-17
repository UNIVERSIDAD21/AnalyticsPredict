# -*- coding: utf-8 -*-
"""validador_ajustes.py — Caps y validaciones de ajustes."""

from __future__ import annotations

from typing import List

from .reglas_ajuste import CONFIG_AJUSTES
from .tipos_ajustes import ResultadoAjustes, AjusteIndividual


def _cap_individual(ajuste: AjusteIndividual, max_abs: float) -> AjusteIndividual:
    if abs(ajuste.valor) <= max_abs:
        return ajuste
    ajuste.valor = max(min(ajuste.valor, max_abs), -max_abs)
    ajuste.descripcion += " (cap aplicado)"
    return ajuste


def aplicar_caps(resultado: ResultadoAjustes) -> ResultadoAjustes:
    advertencias: List[str] = list(resultado.advertencias)
    max_individual = CONFIG_AJUSTES["ajuste_max_individual"]

    ajustes_capeados: List[AjusteIndividual] = []
    for ajuste in resultado.ajustes:
        original = ajuste.valor
        ajuste = _cap_individual(ajuste, max_individual)
        if ajuste.valor != original:
            advertencias.append("Ajuste individual capped por límite máximo.")
        ajustes_capeados.append(ajuste)

    ajuste_total = sum(ajuste.valor for ajuste in ajustes_capeados)
    max_total = CONFIG_AJUSTES["ajuste_max_total"]

    fue_capped = False
    ajuste_total_capped = ajuste_total
    if abs(ajuste_total) > max_total and ajuste_total != 0:
        factor = max_total / abs(ajuste_total)
        for ajuste in ajustes_capeados:
            ajuste.valor *= factor
        ajuste_total_capped = sum(ajuste.valor for ajuste in ajustes_capeados)
        fue_capped = True
        advertencias.append("Ajuste total capped por límite global.")

    if abs(ajuste_total_capped) > 6:
        advertencias.append("⚠️ Múltiples ajustes significativos (>6 pts).")

    resultado.ajustes = ajustes_capeados
    resultado.ajuste_total = ajuste_total
    resultado.ajuste_total_capped = ajuste_total_capped
    resultado.fue_capped = fue_capped
    resultado.advertencias = advertencias
    return resultado

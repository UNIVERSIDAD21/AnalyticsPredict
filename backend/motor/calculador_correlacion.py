# -*- coding: utf-8 -*-
"""
calculador_correlacion.py — Motor para calcular correlaciones en combinadas.

Aplica reglas de negocio para detectar selecciones del mismo partido y
ajustar la probabilidad combinada mediante un factor de correlación.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Iterable


MERCADOS_CUARTOS = {"Q1", "Q2", "Q3", "Q4"}


@dataclass
class DetalleCorrelacion:
    """Detalle del análisis de correlación por grupo de partido."""

    partido_id: str
    mercados: List[str]
    lados: List[str]
    factor: float
    etiqueta: str
    advertencias: List[str] = field(default_factory=list)


@dataclass
class ResultadoCorrelacion:
    """Resultado global del cálculo de correlación."""

    factor_correlacion: float
    tiene_mismo_partido: bool
    n_partidos_unicos: int
    advertencias: List[str]
    detalles: List[DetalleCorrelacion]
    grupos: Dict[str, int]
    factores_grupo: Dict[str, float]


def _clasificar_grupo(mercados: Iterable[str], lados: Iterable[str]) -> tuple[float, str, List[str]]:
    mercados_set = set(mercados)
    lados_set = set(lados)
    tiene_completo = "COMPLETO" in mercados_set
    tiene_cuartos = any(mercado in MERCADOS_CUARTOS for mercado in mercados_set)
    mismo_lado = len(lados_set) == 1

    if tiene_completo and tiene_cuartos and mismo_lado:
        return 0.80, "COMPLETO + CUARTOS (MISMO LADO)", [
            "⚠️ CORRELACIÓN ALTA: selecciones del mismo partido con completo + cuartos en el mismo lado.",
        ]

    if tiene_completo and tiene_cuartos and not mismo_lado:
        return 0.93, "COMPLETO + CUARTOS (LADOS MIXTOS)", [
            "⚠️ CORRELACIÓN MEDIA: selecciones del mismo partido con completo + cuartos en lados mixtos.",
        ]

    if not tiene_completo and tiene_cuartos and mismo_lado:
        return 0.84, "SOLO CUARTOS (MISMO LADO)", [
            "⚠️ CORRELACIÓN ALTA: múltiples cuartos del mismo partido con el mismo lado.",
        ]

    if not tiene_completo and tiene_cuartos and not mismo_lado:
        return 0.96, "SOLO CUARTOS (LADOS MIXTOS)", [
            "⚠️ CORRELACIÓN BAJA: cuartos del mismo partido con lados mixtos.",
        ]

    return 1.0, "SIN CORRELACIÓN", []


def calcular_correlacion_combinada(selecciones: List[dict]) -> ResultadoCorrelacion:
    """
    Calcula el factor de correlación global para una combinada.

    Agrupa selecciones por partido_id y aplica reglas de negocio.
    """
    grupos_por_partido: Dict[str, List[dict]] = {}
    for seleccion in selecciones:
        partido_id = str(seleccion.get("partido_id") or "sin-partido")
        grupos_por_partido.setdefault(partido_id, []).append(seleccion)

    detalles: List[DetalleCorrelacion] = []
    advertencias: List[str] = []
    factor_global = 1.0
    grupos_indices: Dict[str, int] = {}
    factores_grupo: Dict[str, float] = {}

    for indice, (partido_id, grupo) in enumerate(grupos_por_partido.items(), start=1):
        mercados = [str(item.get("mercado")) for item in grupo]
        lados = [str(item.get("lado")) for item in grupo]

        if len(grupo) > 1:
            factor, etiqueta, advertencias_grupo = _clasificar_grupo(mercados, lados)
            detalles.append(
                DetalleCorrelacion(
                    partido_id=partido_id,
                    mercados=mercados,
                    lados=lados,
                    factor=factor,
                    etiqueta=etiqueta,
                    advertencias=advertencias_grupo,
                )
            )
            advertencias.extend(advertencias_grupo)
            factor_global *= factor
        else:
            factor = 1.0

        grupos_indices[partido_id] = indice
        factores_grupo[partido_id] = factor

    tiene_mismo_partido = any(len(grupo) > 1 for grupo in grupos_por_partido.values())
    n_partidos_unicos = len(grupos_por_partido)

    if tiene_mismo_partido:
        advertencias.append(
            f"Se detectaron selecciones correlacionadas. Factor global aplicado: {factor_global:.2f}."
        )

    return ResultadoCorrelacion(
        factor_correlacion=factor_global,
        tiene_mismo_partido=tiene_mismo_partido,
        n_partidos_unicos=n_partidos_unicos,
        advertencias=advertencias,
        detalles=detalles,
        grupos=grupos_indices,
        factores_grupo=factores_grupo,
    )

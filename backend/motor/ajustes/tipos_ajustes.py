# -*- coding: utf-8 -*-
"""tipos_ajustes.py — Dataclasses para ajustes contextuales."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AjusteIndividual:
    """Un ajuste individual con su justificación."""

    factor: str
    valor: float
    direccion: str
    confianza_ajuste: float
    descripcion: str
    datos_soporte: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoAjustes:
    """Resultado consolidado de todos los ajustes."""

    ajustes: List[AjusteIndividual] = field(default_factory=list)
    ajuste_total: float = 0.0
    ajuste_total_capped: float = 0.0
    fue_capped: bool = False
    advertencias: List[str] = field(default_factory=list)
    confianza_delta: float = 0.0


@dataclass
class PrediccionAjustada:
    """Predicción final con ajustes aplicados."""

    media_base: float
    desviacion_base: float
    probabilidad_over_base: float
    probabilidad_under_base: float
    media_ajustada: float
    probabilidad_over_ajustada: float
    probabilidad_under_ajustada: float
    ajustes_aplicados: ResultadoAjustes
    confianza_base: str
    confianza_ajustada: str

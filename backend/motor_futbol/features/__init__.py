# -*- coding: utf-8 -*-
"""
features — Módulo de generación de características para predicción.

Este módulo contiene el sistema de generación de features para partidos de fútbol.
"""

from .generador import GeneradorFeaturesFutbol
from .calculadores import (
    calcular_estadisticas_temporada,
    calcular_estadisticas_ubicacion,
    calcular_forma_reciente,
    calcular_tendencia,
)
from .cache import CacheFeatures

__all__ = [
    "GeneradorFeaturesFutbol",
    "calcular_estadisticas_temporada",
    "calcular_estadisticas_ubicacion",
    "calcular_forma_reciente",
    "calcular_tendencia",
    "CacheFeatures",
]

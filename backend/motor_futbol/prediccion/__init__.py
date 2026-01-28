# -*- coding: utf-8 -*-
"""
prediccion — Módulo de predicción y cálculos probabilísticos.

Este módulo contiene el predictor principal y la calculadora de probabilidades.
"""

from .calculadora_probabilidad import CalculadoraProbabilidad
from .predictor import PredictorFutbol

__all__ = [
    "CalculadoraProbabilidad",
    "PredictorFutbol",
]

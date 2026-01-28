# -*- coding: utf-8 -*-
"""
evaluacion — Módulo de evaluación y backtesting.

Este módulo contiene el sistema de métricas y backtesting.
"""

from .metricas import CalculadorMetricas
from .backtesting import BacktesterFutbol

__all__ = [
    "CalculadorMetricas",
    "BacktesterFutbol",
]

# -*- coding: utf-8 -*-
"""
modelos — Módulo de modelos de predicción Ridge.

Este módulo contiene los modelos de Machine Learning para predicción.
"""

from .base import ModeloPrediccionBase
from .corners import ModeloCorners
from .goles import ModeloGoles
from .disparos import ModeloDisparos

__all__ = [
    "ModeloPrediccionBase",
    "ModeloCorners",
    "ModeloGoles",
    "ModeloDisparos",
]

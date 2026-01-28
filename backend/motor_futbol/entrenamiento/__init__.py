# -*- coding: utf-8 -*-
"""
entrenamiento — Módulo de entrenamiento de modelos.

Este módulo contiene el sistema de entrenamiento y validación.
"""

from .entrenador import EntrenadorFutbol
from .validacion import ValidacionCruzadaTemporal
from .gestor_versiones import GestorVersiones

__all__ = [
    "EntrenadorFutbol",
    "ValidacionCruzadaTemporal",
    "GestorVersiones",
]

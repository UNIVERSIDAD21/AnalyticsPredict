# -*- coding: utf-8 -*-
"""
calculadora_probabilidad.py — Funciones matemáticas para el motor.
"""

from __future__ import annotations

import math
from typing import Tuple


def cdf_normal(z: float) -> float:
    """Función de distribución acumulativa de la normal estándar."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calcular_probabilidad_over(media: float, desviacion: float, linea: float) -> float:
    """Calcula la probabilidad de que el total supere la línea."""
    desviacion = max(float(desviacion), 1e-9)
    z = (linea - media) / desviacion
    return 1.0 - cdf_normal(z)


def calcular_probabilidad_victoria(
    media_equipo: float,
    desviacion_equipo: float,
    media_rival: float,
    desviacion_rival: float,
) -> float:
    """Calcula la probabilidad de victoria del equipo en el cuarto."""
    diferencia_media = float(media_equipo) - float(media_rival)
    desviacion_diferencia = math.sqrt(float(desviacion_equipo) ** 2 + float(desviacion_rival) ** 2)
    desviacion_diferencia = max(desviacion_diferencia, 1e-9)
    return cdf_normal(diferencia_media / desviacion_diferencia)


def calcular_intervalo_confianza(
    media: float,
    desviacion: float,
    z: float = 1.0
) -> Tuple[float, float]:
    """Calcula un intervalo de confianza simétrico."""
    margen = z * desviacion
    return media - margen, media + margen

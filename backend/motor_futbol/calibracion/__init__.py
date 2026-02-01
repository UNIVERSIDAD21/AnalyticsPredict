# -*- coding: utf-8 -*-
"""
calibracion — Módulo de calibración de probabilidades para fútbol.

Este módulo implementa un sistema de calibración de probabilidades
que transforma las probabilidades "raw" del modelo en probabilidades
calibradas que reflejan la frecuencia real de los eventos.

Componentes principales:
- CalibradorBase: Clase base abstracta para calibradores
- CalibradorPlatt: Calibrador usando Platt Scaling
- CalibradorIsotonic: Calibrador usando Isotonic Regression
- GestorCalibradores: Gestión de calibradores activos y persistencia
- Métricas: Funciones para evaluar calidad de calibración

Uso básico:
    from motor_futbol.calibracion import (
        CalibradorPlatt,
        GestorCalibradores,
        calcular_brier_score,
    )

    # Entrenar un calibrador
    calibrador = CalibradorPlatt(TipoMercadoFutbol.CORNERS_FT)
    resultado = calibrador.entrenar(prob_raw, outcomes)

    # Calibrar una probabilidad
    prob_calibrada = calibrador.calibrar(0.65)

    # Usar el gestor para persistencia
    gestor = GestorCalibradores(pool)
    gestor.guardar_calibrador(calibrador, resultado)
    gestor.activar_calibrador(calibrador_id)
"""

from .calibrador_base import CalibradorBase
from .platt_scaling import CalibradorPlatt
from .isotonic import CalibradorIsotonic
from .gestor_calibradores import GestorCalibradores, CALIBRADORES_DISPONIBLES
from .metricas_calibracion import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
    calcular_mce,
    generar_reliability_diagram,
    calcular_metricas_completas,
    comparar_calibracion,
)


__all__ = [
    # Clases de calibradores
    "CalibradorBase",
    "CalibradorPlatt",
    "CalibradorIsotonic",
    # Gestor
    "GestorCalibradores",
    "CALIBRADORES_DISPONIBLES",
    # Métricas
    "calcular_brier_score",
    "calcular_log_loss",
    "calcular_ece",
    "calcular_mce",
    "generar_reliability_diagram",
    "calcular_metricas_completas",
    "comparar_calibracion",
]

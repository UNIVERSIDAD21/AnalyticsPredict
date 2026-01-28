# -*- coding: utf-8 -*-
"""
motor_futbol — Motor de predicción de fútbol con Machine Learning.

Este módulo implementa un sistema de predicción para partidos de fútbol,
enfocado en mercados de corners, goles y disparos para apuestas deportivas.

Arquitectura basada en el módulo motor de NBA existente, adaptada al dominio del fútbol.

Uso:
    from motor_futbol import PredictorFutbol, EntrenadorFutbol

    # Entrenar modelos
    entrenador = EntrenadorFutbol(pool)
    resultado = entrenador.entrenar_completo()

    # Generar predicciones
    predictor = PredictorFutbol(pool)
    prediccion = predictor.predecir_partido(partido_id)
"""

from .tipos import (
    # Enums
    TipoMercadoFutbol,
    NivelConfianza,
    TipoModelo,
    LadoApuesta,
    ResultadoApuesta,

    # Dataclasses principales
    FeaturesPartidoFutbol,
    PrediccionMercado,
    PrediccionPartido,
    ResultadoEntrenamiento,
    ConfiguracionEntrenamiento,
    ModeloRidgeFutbol,
)

from .constantes import (
    ALPHA_RIDGE_DEFAULT,
    N_PARTIDOS_FORMA,
    MIN_PARTIDOS_ESTADISTICAS,
    LINEAS_CORNERS,
    LINEAS_GOLES,
    LINEAS_DISPAROS,
)

from .excepciones import (
    MotorFutbolError,
    PartidoNoEncontrado,
    DatosInsuficientes,
    EquipoNoEncontrado,
    ModeloNoEntrenado,
)

__version__ = "1.0.0"
__all__ = [
    # Enums
    "TipoMercadoFutbol",
    "NivelConfianza",
    "TipoModelo",
    "LadoApuesta",
    "ResultadoApuesta",
    # Dataclasses
    "FeaturesPartidoFutbol",
    "PrediccionMercado",
    "PrediccionPartido",
    "ResultadoEntrenamiento",
    "ConfiguracionEntrenamiento",
    "ModeloRidgeFutbol",
    # Constantes
    "ALPHA_RIDGE_DEFAULT",
    "N_PARTIDOS_FORMA",
    "MIN_PARTIDOS_ESTADISTICAS",
    "LINEAS_CORNERS",
    "LINEAS_GOLES",
    "LINEAS_DISPAROS",
    # Excepciones
    "MotorFutbolError",
    "PartidoNoEncontrado",
    "DatosInsuficientes",
    "EquipoNoEncontrado",
    "ModeloNoEntrenado",
]

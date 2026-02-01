# -*- coding: utf-8 -*-
"""
calibrador_base.py — Clase base abstracta para calibradores de probabilidad.

Este módulo define la interfaz común que deben implementar todos los
calibradores de probabilidad (Platt Scaling, Isotonic Regression, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Union, Optional

import numpy as np

from ..tipos import TipoMercadoFutbol, ResultadoCalibracion
from .metricas_calibracion import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
)


class CalibradorBase(ABC):
    """
    Clase base abstracta para calibradores de probabilidad.

    Los calibradores transforman probabilidades "raw" del modelo
    en probabilidades calibradas que reflejan la frecuencia real
    de los eventos.

    Atributos:
        mercado: Tipo de mercado para el que se calibra
        entrenado: Indica si el calibrador ha sido entrenado
        fecha_entrenamiento: Fecha del último entrenamiento
        parametros: Parámetros del calibrador (para serialización)
    """

    # Nombre del método de calibración (sobrescribir en subclases)
    NOMBRE_METODO: str = "base"

    def __init__(self, mercado: TipoMercadoFutbol):
        """
        Inicializa el calibrador.

        Args:
            mercado: Tipo de mercado de fútbol para el que se calibrará
        """
        self.mercado = mercado
        self.entrenado = False
        self.fecha_entrenamiento: Optional[datetime] = None
        self.parametros: Dict[str, Any] = {}

    @abstractmethod
    def entrenar(
        self,
        prob_raw: np.ndarray,
        outcomes: np.ndarray,
    ) -> ResultadoCalibracion:
        """
        Entrena el calibrador con datos históricos.

        Args:
            prob_raw: Array de probabilidades sin calibrar (0 a 1)
            outcomes: Array de resultados reales (0 o 1)

        Returns:
            ResultadoCalibracion con métricas antes y después

        Raises:
            ValueError: Si los datos son inválidos
        """
        pass

    @abstractmethod
    def calibrar(
        self,
        prob_raw: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calibra una o más probabilidades.

        Args:
            prob_raw: Probabilidad(es) sin calibrar (0 a 1)

        Returns:
            Probabilidad(es) calibrada(s)

        Raises:
            RuntimeError: Si el calibrador no ha sido entrenado
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el calibrador a diccionario.

        Returns:
            Diccionario con toda la información del calibrador
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibradorBase":
        """
        Reconstruye un calibrador desde diccionario.

        Args:
            data: Diccionario con información del calibrador

        Returns:
            Instancia del calibrador reconstruida
        """
        pass

    def validar_entrada(self, prob: np.ndarray) -> None:
        """
        Valida que las probabilidades estén en rango [0, 1].

        Args:
            prob: Array de probabilidades a validar

        Raises:
            ValueError: Si hay valores fuera de rango
        """
        if np.any(prob < 0) or np.any(prob > 1):
            invalidos = prob[(prob < 0) | (prob > 1)]
            raise ValueError(
                f"Las probabilidades deben estar entre 0 y 1. "
                f"Valores inválidos encontrados: {invalidos[:5]}..."
            )

    def validar_entrenamiento(self) -> None:
        """
        Valida que el calibrador haya sido entrenado.

        Raises:
            RuntimeError: Si el calibrador no ha sido entrenado
        """
        if not self.entrenado:
            raise RuntimeError(
                f"El calibrador para {self.mercado.value} no ha sido entrenado. "
                "Llama a entrenar() primero."
            )

    def calcular_metricas(
        self,
        prob_raw: np.ndarray,
        prob_calibrada: np.ndarray,
        outcomes: np.ndarray,
        n_bins: int = 10,
    ) -> Dict[str, float]:
        """
        Calcula métricas de calibración antes y después.

        Args:
            prob_raw: Probabilidades sin calibrar
            prob_calibrada: Probabilidades calibradas
            outcomes: Resultados reales
            n_bins: Número de bins para ECE

        Returns:
            Diccionario con métricas antes/después y mejoras
        """
        return {
            "brier_antes": calcular_brier_score(prob_raw, outcomes),
            "brier_despues": calcular_brier_score(prob_calibrada, outcomes),
            "log_loss_antes": calcular_log_loss(prob_raw, outcomes),
            "log_loss_despues": calcular_log_loss(prob_calibrada, outcomes),
            "ece_antes": calcular_ece(prob_raw, outcomes, n_bins),
            "ece_despues": calcular_ece(prob_calibrada, outcomes, n_bins),
        }

    def _base_to_dict(self) -> Dict[str, Any]:
        """
        Genera el diccionario base para serialización.

        Returns:
            Diccionario con campos comunes
        """
        return {
            "mercado": self.mercado.value,
            "metodo": self.NOMBRE_METODO,
            "entrenado": self.entrenado,
            "fecha_entrenamiento": (
                self.fecha_entrenamiento.isoformat()
                if self.fecha_entrenamiento
                else None
            ),
            "parametros": self.parametros,
        }

    def __repr__(self) -> str:
        """Representación legible del calibrador."""
        estado = "entrenado" if self.entrenado else "no entrenado"
        return (
            f"{self.__class__.__name__}("
            f"mercado={self.mercado.value}, "
            f"metodo={self.NOMBRE_METODO}, "
            f"estado={estado})"
        )

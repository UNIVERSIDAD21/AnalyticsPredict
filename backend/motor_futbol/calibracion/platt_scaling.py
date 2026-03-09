# -*- coding: utf-8 -*-
"""
platt_scaling.py — Calibrador usando Platt Scaling.

Platt Scaling ajusta una regresión logística sobre las probabilidades
raw para producir probabilidades calibradas. Es el método más simple
y funciona bien cuando la descalibración es monotónica.

Fórmula:
    prob_calibrada = 1 / (1 + exp(a * logit(prob_raw) + b))

donde logit(p) = log(p / (1-p))
"""

from __future__ import annotations

import math
import logging
from datetime import datetime
from typing import Dict, Any, Union, Optional

import numpy as np
from sklearn.linear_model import LogisticRegression

from ..tipos import TipoMercadoFutbol, ResultadoCalibracion
from .calibrador_base import CalibradorBase
from .metricas_calibracion import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
)

logger = logging.getLogger(__name__)


def _logit(p: np.ndarray, epsilon: float = 1e-9) -> np.ndarray:
    """
    Calcula el logit (log-odds) de probabilidades.

    logit(p) = log(p / (1-p))

    Args:
        p: Array de probabilidades
        epsilon: Valor para evitar log(0)

    Returns:
        Array de log-odds
    """
    p_clipped = np.clip(p, epsilon, 1 - epsilon)
    return np.log(p_clipped / (1 - p_clipped))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """
    Función sigmoide estable numéricamente.

    sigmoid(x) = 1 / (1 + exp(-x))

    Args:
        x: Array de valores

    Returns:
        Array de probabilidades
    """
    # Implementación estable para evitar overflow
    positive = x >= 0
    result = np.empty_like(x, dtype=float)

    # Para x >= 0
    result[positive] = 1 / (1 + np.exp(-x[positive]))

    # Para x < 0
    exp_x = np.exp(x[~positive])
    result[~positive] = exp_x / (1 + exp_x)

    return result


class CalibradorPlatt(CalibradorBase):
    """
    Calibrador usando Platt Scaling.

    Platt Scaling ajusta los parámetros a y b de una transformación
    sigmoide para calibrar las probabilidades:

        prob_calibrada = sigmoid(a * logit(prob_raw) + b)

    Este método es simple, rápido, y funciona bien cuando:
    - La descalibración es monotónica
    - Hay pocas muestras (< 500)
    - Se necesita un modelo con pocos parámetros

    Atributos adicionales:
        a: Parámetro de escala
        b: Parámetro de sesgo (bias)
    """

    NOMBRE_METODO = "platt"

    def __init__(self, mercado: TipoMercadoFutbol):
        """
        Inicializa el calibrador Platt.

        Args:
            mercado: Tipo de mercado de fútbol
        """
        super().__init__(mercado)
        self.a: float = 1.0  # Escala
        self.b: float = 0.0  # Sesgo
        self._modelo: Optional[LogisticRegression] = None
        self._es_fallback: bool = False
        self._fallback_prob: float = 0.5

    def entrenar(
        self,
        prob_raw: np.ndarray,
        outcomes: np.ndarray,
        regularization_c: float = 1.0,
    ) -> ResultadoCalibracion:
        """
        Entrena el calibrador con datos históricos.

        El entrenamiento ajusta una regresión logística con:
        - Features: logit de las probabilidades raw
        - Target: outcomes binarios

        Args:
            prob_raw: Array de probabilidades sin calibrar (0 a 1)
            outcomes: Array de resultados reales (0 o 1)
            regularization_c: Parámetro de regularización (mayor = menos regularización)

        Returns:
            ResultadoCalibracion con métricas antes y después

        Raises:
            ValueError: Si hay menos de 10 muestras o datos inválidos
        """
        prob = np.asarray(prob_raw, dtype=float).ravel()
        out = np.asarray(outcomes, dtype=float).ravel()

        # Validaciones
        if len(prob) != len(out):
            raise ValueError(
                f"Los arrays deben tener la misma longitud: "
                f"prob_raw={len(prob)}, outcomes={len(out)}"
            )

        if len(prob) < 10:
            raise ValueError(
                f"Se requieren al menos 10 muestras para entrenar. "
                f"Recibidas: {len(prob)}"
            )

        self.validar_entrada(prob)

        # Calcular métricas antes de calibración
        brier_antes = calcular_brier_score(prob, out)
        log_loss_antes = calcular_log_loss(prob, out)
        ece_antes = calcular_ece(prob, out)

        # Transformar a logit para el modelo
        X = _logit(prob).reshape(-1, 1)

        clases_unicas = np.unique(out)
        if len(clases_unicas) < 2:
            # FALLBACK: dataset de clase única → probabilidad constante.
            # No es un calibrador útil; se activa solo en edge cases de test
            # o mercados con 0 pérdidas/ganancias en ventana de entrenamiento.
            self._fallback_prob = float(np.mean(out))
            self._es_fallback = True
            self.entrenado = True
            self.fecha_entrenamiento = datetime.now()
            self.parametros = {
                "a": self.a,
                "b": self.b,
                "regularization_c": regularization_c,
                "fallback_clase_unica": True,
                "fallback_prob": self._fallback_prob,
            }
            logger.warning(
                "CalibradorPlatt activó fallback por clase única",
                extra={
                    "mercado": self.mercado.value,
                    "n_muestras": len(out),
                    "clases": [float(c) for c in clases_unicas],
                },
            )
            prob_calibrada = np.full(len(prob), self._fallback_prob, dtype=float)
            brier_despues = calcular_brier_score(prob_calibrada, out)
            log_loss_despues = calcular_log_loss(prob_calibrada, out)
            ece_despues = calcular_ece(prob_calibrada, out)

            return ResultadoCalibracion(
                mercado=self.mercado,
                metodo=self.NOMBRE_METODO,
                brier_antes=brier_antes,
                log_loss_antes=log_loss_antes,
                ece_antes=ece_antes,
                brier_despues=brier_despues,
                log_loss_despues=log_loss_despues,
                ece_despues=ece_despues,
                n_muestras=len(prob),
                fecha_entrenamiento=self.fecha_entrenamiento,
                parametros=self.parametros,
            )

        self._es_fallback = False

        # Ajustar regresión logística
        self._modelo = LogisticRegression(
            C=regularization_c,
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        )
        self._modelo.fit(X, out)

        # Extraer parámetros
        # La regresión logística da: P(y=1) = sigmoid(coef * X + intercept)
        # Queremos: sigmoid(a * logit(prob) + b)
        self.a = float(self._modelo.coef_[0, 0])
        self.b = float(self._modelo.intercept_[0])

        # Guardar parámetros para serialización
        self.parametros = {
            "a": self.a,
            "b": self.b,
            "regularization_c": regularization_c,
        }

        # Marcar como entrenado
        self.entrenado = True
        self.fecha_entrenamiento = datetime.now()

        # Calcular probabilidades calibradas
        prob_calibrada = self.calibrar(prob)

        # Calcular métricas después de calibración
        brier_despues = calcular_brier_score(prob_calibrada, out)
        log_loss_despues = calcular_log_loss(prob_calibrada, out)
        ece_despues = calcular_ece(prob_calibrada, out)

        return ResultadoCalibracion(
            mercado=self.mercado,
            metodo=self.NOMBRE_METODO,
            brier_antes=brier_antes,
            log_loss_antes=log_loss_antes,
            ece_antes=ece_antes,
            brier_despues=brier_despues,
            log_loss_despues=log_loss_despues,
            ece_despues=ece_despues,
            n_muestras=len(prob),
            fecha_entrenamiento=self.fecha_entrenamiento,
            parametros=self.parametros,
        )

    def calibrar(
        self,
        prob_raw: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calibra una o más probabilidades.

        Aplica la transformación: sigmoid(a * logit(prob) + b)

        Args:
            prob_raw: Probabilidad(es) sin calibrar (0 a 1)

        Returns:
            Probabilidad(es) calibrada(s)

        Raises:
            RuntimeError: Si el calibrador no ha sido entrenado
        """
        self.validar_entrenamiento()

        # Manejar entrada escalar
        es_escalar = np.isscalar(prob_raw)
        prob = np.atleast_1d(np.asarray(prob_raw, dtype=float))

        # Validar entrada
        self.validar_entrada(prob)

        if self._es_fallback:
            prob_calibrada = np.full(len(prob), self._fallback_prob, dtype=float)
        else:
            # Transformar: sigmoid(a * logit(prob) + b)
            logit_prob = _logit(prob)
            prob_calibrada = _sigmoid(self.a * logit_prob + self.b)

        # Asegurar que está en [0, 1]
        prob_calibrada = np.clip(prob_calibrada, 0.0, 1.0)

        if es_escalar:
            return float(prob_calibrada[0])

        return prob_calibrada

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el calibrador a diccionario.

        Returns:
            Diccionario con toda la información del calibrador
        """
        data = self._base_to_dict()
        data.update({
            "a": self.a,
            "b": self.b,
            "es_fallback": self._es_fallback,
            "fallback_prob": self._fallback_prob,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibradorPlatt":
        """
        Reconstruye un calibrador desde diccionario.

        Args:
            data: Diccionario con información del calibrador

        Returns:
            Instancia del calibrador reconstruida
        """
        mercado = TipoMercadoFutbol(data["mercado"])
        calibrador = cls(mercado)

        calibrador.a = data.get("a", 1.0)
        calibrador.b = data.get("b", 0.0)
        calibrador.entrenado = data.get("entrenado", True)
        calibrador.parametros = data.get("parametros", {"a": calibrador.a, "b": calibrador.b})
        calibrador._es_fallback = bool(data.get("es_fallback", False))
        calibrador._fallback_prob = float(data.get("fallback_prob", 0.5))

        if data.get("fecha_entrenamiento"):
            calibrador.fecha_entrenamiento = datetime.fromisoformat(
                data["fecha_entrenamiento"]
            )

        return calibrador

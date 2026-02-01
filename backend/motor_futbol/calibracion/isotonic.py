# -*- coding: utf-8 -*-
"""
isotonic.py — Calibrador usando Isotonic Regression.

Isotonic Regression es un método no paramétrico que ajusta una función
monotónica creciente para calibrar las probabilidades. No asume ninguna
forma funcional específica, lo que lo hace más flexible que Platt Scaling.

Ventajas:
- No asume forma funcional
- Captura patrones complejos de descalibración

Desventajas:
- Puede sobreajustar con pocas muestras
- Más parámetros para almacenar
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Union, Optional, List

import numpy as np
from sklearn.isotonic import IsotonicRegression

from ..tipos import TipoMercadoFutbol, ResultadoCalibracion
from .calibrador_base import CalibradorBase
from .metricas_calibracion import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
)


class CalibradorIsotonic(CalibradorBase):
    """
    Calibrador usando Isotonic Regression.

    Isotonic Regression ajusta una función escalonada monotónica creciente
    que mapea probabilidades raw a probabilidades calibradas.

    Este método es más flexible que Platt Scaling y funciona mejor cuando:
    - Hay muchas muestras (> 1000)
    - La descalibración tiene patrones complejos no monotónicos
    - Se requiere máxima flexibilidad en el ajuste

    Atributos adicionales:
        x_thresholds: Puntos X de la función escalonada
        y_thresholds: Puntos Y de la función escalonada
    """

    NOMBRE_METODO = "isotonic"

    def __init__(self, mercado: TipoMercadoFutbol):
        """
        Inicializa el calibrador Isotonic.

        Args:
            mercado: Tipo de mercado de fútbol
        """
        super().__init__(mercado)
        self.x_thresholds: Optional[np.ndarray] = None
        self.y_thresholds: Optional[np.ndarray] = None
        self._modelo: Optional[IsotonicRegression] = None

    def entrenar(
        self,
        prob_raw: np.ndarray,
        outcomes: np.ndarray,
    ) -> ResultadoCalibracion:
        """
        Entrena el calibrador con datos históricos.

        Ajusta una regresión isotónica monotónica creciente que mapea
        probabilidades raw a la frecuencia real de outcomes positivos.

        Args:
            prob_raw: Array de probabilidades sin calibrar (0 a 1)
            outcomes: Array de resultados reales (0 o 1)

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

        # Ajustar regresión isotónica
        self._modelo = IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            out_of_bounds="clip",
            increasing=True,
        )
        self._modelo.fit(prob, out)

        # Extraer puntos de la función escalonada
        # La regresión isotónica almacena los puntos únicos
        if hasattr(self._modelo, "X_thresholds_") and self._modelo.X_thresholds_ is not None:
            self.x_thresholds = self._modelo.X_thresholds_.copy()
            self.y_thresholds = self._modelo.y_thresholds_.copy()
        else:
            # Fallback: usar puntos únicos ordenados
            unique_probs = np.unique(prob)
            self.x_thresholds = unique_probs
            self.y_thresholds = self._modelo.predict(unique_probs)

        # Guardar parámetros para serialización
        self.parametros = {
            "n_thresholds": len(self.x_thresholds),
            "x_min": float(self.x_thresholds.min()),
            "x_max": float(self.x_thresholds.max()),
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

        Usa interpolación lineal entre los puntos de la función escalonada.

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

        # Usar el modelo si está disponible
        if self._modelo is not None:
            prob_calibrada = self._modelo.predict(prob)
        else:
            # Reconstruir desde thresholds usando interpolación lineal
            prob_calibrada = np.interp(
                prob,
                self.x_thresholds,
                self.y_thresholds,
            )

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
            "x_thresholds": (
                self.x_thresholds.tolist()
                if self.x_thresholds is not None
                else []
            ),
            "y_thresholds": (
                self.y_thresholds.tolist()
                if self.y_thresholds is not None
                else []
            ),
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibradorIsotonic":
        """
        Reconstruye un calibrador desde diccionario.

        Args:
            data: Diccionario con información del calibrador

        Returns:
            Instancia del calibrador reconstruida
        """
        mercado = TipoMercadoFutbol(data["mercado"])
        calibrador = cls(mercado)

        x_thresh = data.get("x_thresholds", [])
        y_thresh = data.get("y_thresholds", [])

        if x_thresh and y_thresh:
            calibrador.x_thresholds = np.array(x_thresh)
            calibrador.y_thresholds = np.array(y_thresh)
            calibrador.entrenado = True

            # Reconstruir modelo desde thresholds
            calibrador._modelo = IsotonicRegression(
                y_min=0.0,
                y_max=1.0,
                out_of_bounds="clip",
                increasing=True,
            )
            # Ajustar con los puntos guardados
            calibrador._modelo.fit(
                calibrador.x_thresholds,
                calibrador.y_thresholds,
            )

        calibrador.parametros = data.get("parametros", {})

        if data.get("fecha_entrenamiento"):
            calibrador.fecha_entrenamiento = datetime.fromisoformat(
                data["fecha_entrenamiento"]
            )

        return calibrador

    def preserva_orden(self, prob_raw: np.ndarray) -> bool:
        """
        Verifica que la calibración preserva el orden de las probabilidades.

        La regresión isotónica garantiza monotonía, pero este método
        permite verificarlo explícitamente.

        Args:
            prob_raw: Array de probabilidades sin calibrar

        Returns:
            True si el orden se preserva
        """
        if not self.entrenado:
            return True

        prob_calibrada = self.calibrar(prob_raw)

        # Ordenar ambos arrays por prob_raw
        indices = np.argsort(prob_raw)
        prob_cal_ordenada = prob_calibrada[indices]

        # Verificar que es monotónica creciente
        return np.all(np.diff(prob_cal_ordenada) >= -1e-9)

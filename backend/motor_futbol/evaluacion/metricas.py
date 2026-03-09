# -*- coding: utf-8 -*-
"""
metricas.py — Cálculo de métricas de evaluación para modelos de fútbol.

Este módulo contiene funciones para calcular métricas de regresión
y calibración de probabilidades.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CalculadorMetricas:
    """
    Calculadora de métricas de evaluación.

    Métricas de regresión:
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - R² (Coeficiente de determinación)

    Métricas de calibración:
    - Brier Score
    - ECE (Expected Calibration Error)
    - MCE (Maximum Calibration Error)

    Métricas de rentabilidad:
    - ROI
    - Win Rate
    - Yield
    """

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTRICAS DE REGRESIÓN
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def mae(y_real: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calcula Mean Absolute Error.

        Args:
            y_real: Valores reales
            y_pred: Valores predichos

        Returns:
            MAE
        """
        return float(np.mean(np.abs(y_real - y_pred)))

    @staticmethod
    def rmse(y_real: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calcula Root Mean Squared Error.

        Args:
            y_real: Valores reales
            y_pred: Valores predichos

        Returns:
            RMSE
        """
        return float(np.sqrt(np.mean((y_real - y_pred) ** 2)))

    @staticmethod
    def r2(y_real: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calcula coeficiente de determinación R².

        Args:
            y_real: Valores reales
            y_pred: Valores predichos

        Returns:
            R² (puede ser negativo si el modelo es peor que la media)
        """
        ss_res = np.sum((y_real - y_pred) ** 2)
        ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)

        if ss_tot == 0:
            return 0.0

        return float(1 - (ss_res / ss_tot))

    @staticmethod
    def mape(y_real: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calcula Mean Absolute Percentage Error.

        Args:
            y_real: Valores reales
            y_pred: Valores predichos

        Returns:
            MAPE como porcentaje
        """
        # Evitar división por cero
        mask = y_real != 0
        if not np.any(mask):
            return 0.0

        return float(np.mean(np.abs((y_real[mask] - y_pred[mask]) / y_real[mask])) * 100)

    @staticmethod
    def metricas_regresion(
        y_real: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calcula todas las métricas de regresión.

        Returns:
            Dict con mae, rmse, r2, mape
        """
        return {
            "mae": CalculadorMetricas.mae(y_real, y_pred),
            "rmse": CalculadorMetricas.rmse(y_real, y_pred),
            "r2": CalculadorMetricas.r2(y_real, y_pred),
            "mape": CalculadorMetricas.mape(y_real, y_pred),
        }

    @staticmethod
    def calcular_metricas_regresion(
        y_real: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        """Calcula MAE/RMSE/R²/MAPE para predicciones continuas (unidades originales)."""
        return CalculadorMetricas.metricas_regresion(y_real, y_pred)

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTRICAS DE CALIBRACIÓN
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def brier_score(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
    ) -> float:
        """
        Calcula Brier Score.

        BS = (1/N) × Σ(prob_predicha - resultado)²

        Args:
            probabilidades: Probabilidades predichas (0 a 1)
            resultados: Resultados reales (0 o 1)

        Returns:
            Brier Score (menor es mejor, 0 es perfecto)
        """
        return float(np.mean((probabilidades - resultados) ** 2))

    @staticmethod
    def log_loss(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
        eps: float = 1e-15,
    ) -> float:
        """
        Calcula Log Loss (Binary Cross-Entropy).

        Args:
            probabilidades: Probabilidades predichas
            resultados: Resultados reales
            eps: Epsilon para evitar log(0)

        Returns:
            Log Loss
        """
        probs = np.clip(probabilidades, eps, 1 - eps)
        return float(-np.mean(resultados * np.log(probs) + (1 - resultados) * np.log(1 - probs)))

    @staticmethod
    def ece(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        Calcula Expected Calibration Error.

        ECE = Σᵢ (nᵢ/N) × |acc(i) - conf(i)|

        Args:
            probabilidades: Probabilidades predichas
            resultados: Resultados reales
            n_bins: Número de bins

        Returns:
            ECE (menor es mejor)
        """
        bins = np.linspace(0, 1, n_bins + 1)
        ece_value = 0.0
        n_total = len(probabilidades)

        for i in range(n_bins):
            mask = (probabilidades >= bins[i]) & (probabilidades < bins[i + 1])
            n_bin = np.sum(mask)

            if n_bin == 0:
                continue

            acc_bin = np.mean(resultados[mask])
            conf_bin = np.mean(probabilidades[mask])

            ece_value += (n_bin / n_total) * np.abs(acc_bin - conf_bin)

        return float(ece_value)

    @staticmethod
    def mce(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        Calcula Maximum Calibration Error.

        MCE = max_i |acc(i) - conf(i)|

        Args:
            probabilidades: Probabilidades predichas
            resultados: Resultados reales
            n_bins: Número de bins

        Returns:
            MCE (menor es mejor)
        """
        bins = np.linspace(0, 1, n_bins + 1)
        max_error = 0.0

        for i in range(n_bins):
            mask = (probabilidades >= bins[i]) & (probabilidades < bins[i + 1])
            n_bin = np.sum(mask)

            if n_bin == 0:
                continue

            acc_bin = np.mean(resultados[mask])
            conf_bin = np.mean(probabilidades[mask])

            error = np.abs(acc_bin - conf_bin)
            max_error = max(max_error, error)

        return float(max_error)

    @staticmethod
    def diagrama_calibracion(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
        n_bins: int = 10,
    ) -> Dict[str, List[float]]:
        """
        Genera datos para diagrama de calibración (reliability diagram).

        Returns:
            Dict con listas de bins, confianza media, y frecuencia real
        """
        bins = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        confianza = []
        frecuencia = []
        conteo = []

        for i in range(n_bins):
            mask = (probabilidades >= bins[i]) & (probabilidades < bins[i + 1])
            n_bin = np.sum(mask)

            if n_bin == 0:
                confianza.append(bin_centers[i])
                frecuencia.append(0.0)
                conteo.append(0)
            else:
                confianza.append(float(np.mean(probabilidades[mask])))
                frecuencia.append(float(np.mean(resultados[mask])))
                conteo.append(int(n_bin))

        return {
            "bins": bin_centers.tolist(),
            "confianza_media": confianza,
            "frecuencia_real": frecuencia,
            "conteo": conteo,
        }

    @staticmethod
    def metricas_calibracion(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calcula todas las métricas de calibración.

        Returns:
            Dict con brier, log_loss, ece, mce
        """
        return {
            "brier_score": CalculadorMetricas.brier_score(probabilidades, resultados),
            "log_loss": CalculadorMetricas.log_loss(probabilidades, resultados),
            "ece": CalculadorMetricas.ece(probabilidades, resultados),
            "mce": CalculadorMetricas.mce(probabilidades, resultados),
        }

    @staticmethod
    def calcular_metricas_calibracion(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
    ) -> Dict[str, float]:
        """Calcula Brier/LogLoss/ECE/MCE para probabilidades (unidad [0,1])."""
        return CalculadorMetricas.metricas_calibracion(probabilidades, resultados)

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTRICAS DE RENTABILIDAD
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def roi(
        ganancias: float,
        total_apostado: float,
    ) -> float:
        """
        Calcula Return on Investment.

        ROI = ganancias_netas / total_apostado

        Args:
            ganancias: Suma de ganancias netas (puede ser negativo)
            total_apostado: Total de dinero apostado

        Returns:
            ROI en decimal (0.0 a 1.0+), no porcentaje.
        """
        if total_apostado == 0:
            return 0.0
        # ROI en decimal (0.0 a 1.0+), no porcentaje
        return float(ganancias / total_apostado)

    @staticmethod
    def win_rate(
        apuestas_ganadas: int,
        total_apuestas: int,
    ) -> float:
        """
        Calcula Win Rate.

        Args:
            apuestas_ganadas: Número de apuestas ganadas
            total_apuestas: Total de apuestas

        Returns:
            Win Rate en decimal (0.0 a 1.0).
        """
        if total_apuestas == 0:
            return 0.0
        return float(apuestas_ganadas / total_apuestas)

    @staticmethod
    def yield_apuestas(
        ganancias: float,
        total_apostado: float,
    ) -> float:
        """
        Calcula Yield de apuestas.

        Args:
            ganancias: Ganancias netas totales
            total_apostado: Stake total apostado

        Returns:
            Yield en decimal (0.0 a 1.0+).
        """
        if total_apostado == 0:
            return 0.0
        return float(ganancias / total_apostado)

    @staticmethod
    def calcular_metricas_rentabilidad(
        beneficio: float,
        total_apostado: float,
        ganadas: int,
        total_apuestas: int,
    ) -> Dict[str, float]:
        """Calcula ROI/WinRate/Yield en DECIMAL y agrega profit/total_apostado."""
        return {
            "roi": CalculadorMetricas.roi(beneficio, total_apostado),
            "win_rate": CalculadorMetricas.win_rate(ganadas, total_apuestas),
            "yield": CalculadorMetricas.yield_apuestas(beneficio, total_apostado),
            "profit": float(beneficio),
            "total_apostado": float(total_apostado),
        }

    @staticmethod
    def simular_apuestas(
        probabilidades: np.ndarray,
        resultados: np.ndarray,
        cuotas: np.ndarray,
        umbral_edge: float = 0.05,
        stake_fijo: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Simula apuestas y calcula métricas de rentabilidad.

        Args:
            probabilidades: Probabilidades del modelo
            resultados: Resultados reales (0 o 1)
            cuotas: Cuotas ofrecidas
            umbral_edge: Edge mínimo para apostar
            stake_fijo: Monto de cada apuesta

        Returns:
            Dict con métricas de rentabilidad
        """
        # Calcular probabilidades implícitas
        prob_implicita = 1.0 / cuotas

        # Calcular edge
        edges = probabilidades - prob_implicita

        # Seleccionar apuestas con edge positivo
        mask_apuesta = edges > umbral_edge

        if not np.any(mask_apuesta):
            return {
                "n_apuestas": 0,
                "roi": 0.0,
                "win_rate": 0.0,
                "yield": 0.0,
                "ganancias_netas": 0.0,
                "total_apostado": 0.0,
            }

        # Simular resultados
        apuestas = mask_apuesta.sum()
        resultados_filtrados = resultados[mask_apuesta]
        cuotas_filtradas = cuotas[mask_apuesta]

        # Calcular ganancias
        ganancias = np.sum(resultados_filtrados * (cuotas_filtradas - 1) * stake_fijo)
        perdidas = np.sum((1 - resultados_filtrados) * stake_fijo)
        ganancias_netas = ganancias - perdidas

        total_apostado = apuestas * stake_fijo
        ganadas = np.sum(resultados_filtrados)

        return {
            "n_apuestas": int(apuestas),
            "ganadas": int(ganadas),
            "perdidas": int(apuestas - ganadas),
            "roi": CalculadorMetricas.roi(ganancias_netas, total_apostado),
            "win_rate": CalculadorMetricas.win_rate(int(ganadas), int(apuestas)),
            "yield": CalculadorMetricas.yield_apuestas(ganancias_netas, total_apostado),
            "ganancias_netas": float(ganancias_netas),
            "total_apostado": float(total_apostado),
            "edge_promedio": float(np.mean(edges[mask_apuesta])),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # MÉTRICAS BASELINE
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def mae_baseline(y_real: np.ndarray) -> float:
        """
        Calcula MAE del baseline (predecir siempre la media).

        Args:
            y_real: Valores reales

        Returns:
            MAE baseline
        """
        media = np.mean(y_real)
        return float(np.mean(np.abs(y_real - media)))

    @staticmethod
    def mejora_vs_baseline(
        y_real: np.ndarray,
        y_pred: np.ndarray,
    ) -> float:
        """
        Calcula mejora porcentual vs baseline.

        Args:
            y_real: Valores reales
            y_pred: Predicciones del modelo

        Returns:
            Mejora como porcentaje (positivo = mejor que baseline)
        """
        mae_modelo = CalculadorMetricas.mae(y_real, y_pred)
        mae_base = CalculadorMetricas.mae_baseline(y_real)

        if mae_base == 0:
            return 0.0

        return ((mae_base - mae_modelo) / mae_base) * 100

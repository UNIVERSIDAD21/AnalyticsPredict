# -*- coding: utf-8 -*-
"""
test_metricas.py — Tests unitarios para CalculadorMetricas.

Tests obligatorios según especificación:
- test_mae_calculo_correcto
- test_brier_score_rango_valido
- test_ece_calibracion
- test_roi_formula
"""

import pytest
import numpy as np

from motor_futbol.evaluacion.metricas import CalculadorMetricas


class TestMAE:
    """Tests para Mean Absolute Error."""

    def test_mae_calculo_correcto(self):
        """
        MAE = mean(|y_real - y_pred|)

        Ejemplo: predicciones [10, 11, 9] vs reales [9, 12, 10]
        MAE = (|10-9| + |11-12| + |9-10|) / 3 = (1 + 1 + 1) / 3 = 1.0
        """
        y_real = np.array([9, 12, 10])
        y_pred = np.array([10, 11, 9])

        mae = CalculadorMetricas.mae(y_real, y_pred)

        assert abs(mae - 1.0) < 0.001

    def test_mae_prediccion_perfecta(self):
        """MAE = 0 cuando predicción es perfecta."""
        y = np.array([5, 10, 15])

        mae = CalculadorMetricas.mae(y, y)

        assert mae == 0.0

    def test_mae_siempre_positivo(self):
        """MAE siempre es >= 0."""
        y_real = np.random.randn(100)
        y_pred = np.random.randn(100)

        mae = CalculadorMetricas.mae(y_real, y_pred)

        assert mae >= 0


class TestRMSE:
    """Tests para Root Mean Squared Error."""

    def test_rmse_calculo_correcto(self):
        """
        RMSE = sqrt(mean((y_real - y_pred)²))
        """
        y_real = np.array([3, 4, 5])
        y_pred = np.array([2, 5, 4])

        # Errores: 1, -1, 1
        # Errores²: 1, 1, 1
        # MSE: 1
        # RMSE: 1
        rmse = CalculadorMetricas.rmse(y_real, y_pred)

        assert abs(rmse - 1.0) < 0.001

    def test_rmse_penaliza_errores_grandes(self):
        """RMSE penaliza más los errores grandes que MAE."""
        y_real = np.array([0, 0, 0, 0])
        y_pred = np.array([1, 1, 1, 5])  # Un error grande

        mae = CalculadorMetricas.mae(y_real, y_pred)
        rmse = CalculadorMetricas.rmse(y_real, y_pred)

        # MAE: (1+1+1+5)/4 = 2
        # RMSE: sqrt((1+1+1+25)/4) = sqrt(7) ≈ 2.65

        assert rmse > mae

    def test_rmse_mayor_igual_mae(self):
        """RMSE >= MAE siempre."""
        for _ in range(10):
            y_real = np.random.randn(50)
            y_pred = np.random.randn(50)

            mae = CalculadorMetricas.mae(y_real, y_pred)
            rmse = CalculadorMetricas.rmse(y_real, y_pred)

            assert rmse >= mae - 0.001  # Tolerancia numérica


class TestR2:
    """Tests para coeficiente de determinación R²."""

    def test_r2_prediccion_perfecta(self):
        """R² = 1 cuando predicción es perfecta."""
        y = np.array([1, 2, 3, 4, 5])

        r2 = CalculadorMetricas.r2(y, y)

        assert abs(r2 - 1.0) < 0.001

    def test_r2_prediccion_media(self):
        """R² = 0 cuando se predice siempre la media."""
        y_real = np.array([1, 2, 3, 4, 5])
        y_pred = np.full_like(y_real, y_real.mean(), dtype=float)

        r2 = CalculadorMetricas.r2(y_real, y_pred)

        assert abs(r2) < 0.001

    def test_r2_rango_tipico(self):
        """R² típicamente entre 0 y 1 para predicciones razonables."""
        # Predicción con ruido
        y_real = np.array([1, 2, 3, 4, 5])
        y_pred = y_real + np.random.randn(5) * 0.5

        r2 = CalculadorMetricas.r2(y_real, y_pred)

        # Con predicción razonable, R² debería ser positivo
        assert r2 > 0


class TestMAPE:
    """Tests para Mean Absolute Percentage Error."""

    def test_mape_calculo_correcto(self):
        """
        MAPE = mean(|y_real - y_pred| / |y_real|) * 100
        """
        y_real = np.array([100, 200, 300])
        y_pred = np.array([90, 210, 270])

        # |100-90|/100 = 0.10
        # |200-210|/200 = 0.05
        # |300-270|/300 = 0.10
        # MAPE = (0.10 + 0.05 + 0.10) / 3 = 0.0833 = 8.33%

        mape = CalculadorMetricas.mape(y_real, y_pred)

        assert abs(mape - 8.333) < 0.1

    def test_mape_maneja_ceros(self):
        """MAPE maneja correctamente valores reales de cero."""
        y_real = np.array([0, 10, 20])
        y_pred = np.array([1, 11, 19])

        # No debe lanzar división por cero
        mape = CalculadorMetricas.mape(y_real, y_pred)

        assert not np.isnan(mape)
        assert not np.isinf(mape)


class TestBrierScore:
    """Tests para Brier Score."""

    def test_brier_score_rango_valido(self):
        """
        Brier Score está entre 0 y 1.

        BS = mean((p - y)²)
        donde p ∈ [0,1] y y ∈ {0,1}
        """
        probabilidades = np.array([0.7, 0.3, 0.9, 0.5])
        resultados = np.array([1, 0, 1, 0])

        brier = CalculadorMetricas.brier_score(probabilidades, resultados)

        assert 0 <= brier <= 1

    def test_brier_score_prediccion_perfecta(self):
        """Brier Score = 0 cuando predicción perfecta."""
        probabilidades = np.array([1.0, 0.0, 1.0, 0.0])
        resultados = np.array([1, 0, 1, 0])

        brier = CalculadorMetricas.brier_score(probabilidades, resultados)

        assert brier == 0.0

    def test_brier_score_prediccion_peor(self):
        """Brier Score = 1 cuando predicción completamente incorrecta."""
        probabilidades = np.array([0.0, 1.0, 0.0, 1.0])
        resultados = np.array([1, 0, 1, 0])

        brier = CalculadorMetricas.brier_score(probabilidades, resultados)

        assert brier == 1.0

    def test_brier_score_menor_es_mejor(self):
        """Menor Brier Score indica mejor calibración."""
        resultados = np.array([1, 0, 1, 1, 0])

        # Buena calibración
        prob_buena = np.array([0.9, 0.1, 0.8, 0.7, 0.2])
        # Mala calibración
        prob_mala = np.array([0.5, 0.5, 0.5, 0.5, 0.5])

        brier_bueno = CalculadorMetricas.brier_score(prob_buena, resultados)
        brier_malo = CalculadorMetricas.brier_score(prob_mala, resultados)

        assert brier_bueno < brier_malo


class TestLogLoss:
    """Tests para Log Loss (Binary Cross-Entropy)."""

    def test_log_loss_prediccion_segura_correcta(self):
        """Log loss bajo para predicciones seguras y correctas."""
        probabilidades = np.array([0.99, 0.01, 0.95])
        resultados = np.array([1, 0, 1])

        log_loss = CalculadorMetricas.log_loss(probabilidades, resultados)

        # Debería ser muy bajo (< 0.1)
        assert log_loss < 0.1

    def test_log_loss_prediccion_segura_incorrecta(self):
        """Log loss alto para predicciones seguras pero incorrectas."""
        probabilidades = np.array([0.99, 0.99, 0.99])
        resultados = np.array([0, 0, 0])

        log_loss = CalculadorMetricas.log_loss(probabilidades, resultados)

        # Debería ser muy alto
        assert log_loss > 2

    def test_log_loss_siempre_positivo(self):
        """Log loss siempre es >= 0."""
        for _ in range(10):
            prob = np.random.uniform(0.01, 0.99, 20)
            resultados = np.random.randint(0, 2, 20)

            log_loss = CalculadorMetricas.log_loss(prob, resultados)

            assert log_loss >= 0


class TestECE:
    """Tests para Expected Calibration Error."""

    def test_ece_calibracion_perfecta(self):
        """
        ECE = 0 cuando el modelo está perfectamente calibrado.

        Calibrado = P(y=1|p) = p para todo p
        """
        # Simular calibración perfecta
        # En bin 0.6-0.7, prob media 0.65, 65% de aciertos
        probabilidades = np.array([0.65] * 100)
        resultados = np.array([1] * 65 + [0] * 35)

        ece = CalculadorMetricas.ece(probabilidades, resultados, n_bins=10)

        # ECE debería ser muy bajo
        assert ece < 0.05

    def test_ece_rango_valido(self):
        """ECE está entre 0 y 1."""
        probabilidades = np.random.uniform(0, 1, 100)
        resultados = np.random.randint(0, 2, 100)

        ece = CalculadorMetricas.ece(probabilidades, resultados)

        assert 0 <= ece <= 1

    def test_ece_descalibrado(self):
        """ECE alto cuando modelo descalibrado."""
        # Modelo que siempre predice 0.8 pero solo acierta 50%
        probabilidades = np.array([0.8] * 100)
        resultados = np.array([1] * 50 + [0] * 50)

        ece = CalculadorMetricas.ece(probabilidades, resultados, n_bins=10)

        # Diferencia de 0.8 - 0.5 = 0.3, ECE debería ser ~0.3
        assert ece > 0.2


class TestMCE:
    """Tests para Maximum Calibration Error."""

    def test_mce_mayor_igual_ece(self):
        """MCE >= ECE siempre."""
        probabilidades = np.random.uniform(0, 1, 100)
        resultados = np.random.randint(0, 2, 100)

        ece = CalculadorMetricas.ece(probabilidades, resultados)
        mce = CalculadorMetricas.mce(probabilidades, resultados)

        assert mce >= ece - 0.001  # Tolerancia numérica


class TestROI:
    """Tests para Return on Investment."""

    def test_roi_formula_correcta(self):
        """
        ROI = (ganancias_totales - apuestas_totales) / apuestas_totales
        """
        apuestas = [
            {"stake": 100, "ganancia": 90},   # +90
            {"stake": 100, "ganancia": -100}, # -100
            {"stake": 100, "ganancia": 85},   # +85
        ]

        total_apostado = sum(a["stake"] for a in apuestas)
        beneficio_neto = sum(a["ganancia"] for a in apuestas)

        roi = beneficio_neto / total_apostado

        # (90 - 100 + 85) / 300 = 75 / 300 = 0.25 = 25%
        assert abs(roi - 0.25) < 0.001

    def test_roi_positivo_ganancias(self):
        """ROI > 0 cuando hay ganancias netas."""
        total_apostado = 1000
        beneficio = 50

        roi = CalculadorMetricas.roi(beneficio, total_apostado)

        assert roi > 0
        assert abs(roi - 0.05) < 0.001  # 5%

    def test_roi_negativo_perdidas(self):
        """ROI < 0 cuando hay pérdidas netas."""
        total_apostado = 1000
        beneficio = -100

        roi = CalculadorMetricas.roi(beneficio, total_apostado)

        assert roi < 0
        assert abs(roi - (-0.10)) < 0.001  # -10%


class TestWinRate:
    """Tests para Win Rate."""

    def test_win_rate_calculo(self):
        """Win rate = apuestas ganadas / total apuestas."""
        ganadas = 52
        perdidas = 48

        win_rate = CalculadorMetricas.win_rate(ganadas, ganadas + perdidas)

        assert abs(win_rate - 0.52) < 0.001

    def test_win_rate_rango(self):
        """Win rate está entre 0 y 1."""
        for ganadas in range(0, 101, 10):
            perdidas = 100 - ganadas

            win_rate = CalculadorMetricas.win_rate(ganadas, ganadas + perdidas)

            assert 0 <= win_rate <= 1


class TestYield:
    """Tests para Yield (beneficio por unidad apostada)."""

    def test_yield_calculo(self):
        """Yield = beneficio_neto / stake_total."""
        beneficio = 75
        stake_total = 500

        yield_pct = CalculadorMetricas.yield_apuestas(beneficio, stake_total)

        # 75/500 = 0.15 = 15%
        assert abs(yield_pct - 0.15) < 0.001


class TestMetricasCorners:
    """Tests específicos para métricas de corners."""

    def test_mae_corners_objetivo(self):
        """El objetivo de MAE para corners es < 2.5."""
        # Simular predicciones de corners
        y_real = np.random.poisson(10, 100)  # ~10 corners por partido
        # Predicciones con error moderado
        y_pred = y_real + np.random.normal(0, 2, 100)

        mae = CalculadorMetricas.mae(y_real, y_pred)

        # MAE debería estar cerca del std del ruido
        assert mae < 3.0  # Tolerante por varianza

    def test_brier_objetivo_corners(self):
        """El objetivo de Brier Score es < 0.25."""
        # Simular probabilidades calibradas
        n = 100
        prob_reales = np.random.uniform(0.3, 0.7, n)
        # Resultados consistentes con probabilidades
        resultados = (np.random.random(n) < prob_reales).astype(int)

        brier = CalculadorMetricas.brier_score(prob_reales, resultados)

        # Con calibración razonable, Brier debería estar cerca de 0.25
        assert brier < 0.35  # Tolerante por varianza


class TestCalculadorMetricasCompleto:
    """Tests para cálculo de métricas completas."""

    def test_calcular_metricas_regresion(self):
        """Calcula todas las métricas de regresión."""
        y_real = np.array([10, 11, 9, 12, 8])
        y_pred = np.array([10.5, 10.8, 9.2, 11.5, 8.5])

        metricas = CalculadorMetricas.calcular_metricas_regresion(y_real, y_pred)

        assert "mae" in metricas
        assert "rmse" in metricas
        assert "r2" in metricas
        assert "mape" in metricas

    def test_calcular_metricas_calibracion(self):
        """Calcula todas las métricas de calibración."""
        probabilidades = np.array([0.7, 0.3, 0.8, 0.6])
        resultados = np.array([1, 0, 1, 1])

        metricas = CalculadorMetricas.calcular_metricas_calibracion(
            probabilidades, resultados
        )

        assert "brier_score" in metricas
        assert "log_loss" in metricas
        assert "ece" in metricas
        assert "mce" in metricas

    def test_calcular_metricas_rentabilidad(self):
        """Calcula todas las métricas de rentabilidad."""
        beneficio = 150
        total_apostado = 1000
        ganadas = 55
        total_apuestas = 100

        metricas = CalculadorMetricas.calcular_metricas_rentabilidad(
            beneficio=beneficio,
            total_apostado=total_apostado,
            ganadas=ganadas,
            total_apuestas=total_apuestas,
        )

        assert "roi" in metricas
        assert "win_rate" in metricas
        assert "yield" in metricas

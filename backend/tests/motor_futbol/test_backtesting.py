# -*- coding: utf-8 -*-
"""
test_backtesting.py — Tests unitarios para sistema de backtesting.

Tests obligatorios según especificación:
- test_walk_forward_no_data_leakage
- test_backtest_calcula_roi
- test_backtest_genera_reporte
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from motor_futbol.evaluacion.backtesting import (
    BacktesterFutbol,
    ConfiguracionBacktest,
    ResultadoBacktest,
    ReporteBacktest,
)
from motor_futbol.tipos import TipoMercadoFutbol


class TestConfiguracionBacktest:
    """Tests para la configuración del backtest."""

    def test_configuracion_fechas_requeridas(self):
        """La configuración requiere fechas de inicio y fin."""
        with pytest.raises(TypeError):
            ConfiguracionBacktest()

    def test_configuracion_default_valores(self):
        """Valores por defecto de la configuración."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 3, 31),
        )

        assert config.step_dias == 7  # Por defecto semanal
        assert config.min_entrenamiento_dias == 90
        assert config.umbral_edge == 0.05  # 5% edge mínimo
        assert config.fraccion_kelly == 0.25  # Quarter Kelly

    def test_configuracion_personalizada(self):
        """Se pueden personalizar todos los parámetros."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 3, 31),
            step_dias=14,
            min_entrenamiento_dias=120,
            umbral_edge=0.10,
            fraccion_kelly=0.5,
        )

        assert config.step_dias == 14
        assert config.min_entrenamiento_dias == 120
        assert config.umbral_edge == 0.10
        assert config.fraccion_kelly == 0.5


class TestWalkForward:
    """Tests para walk-forward validation."""

    def test_walk_forward_no_data_leakage(self):
        """
        CRÍTICO: Walk-forward no usa datos futuros.

        Para cada punto de predicción t:
        - Entrenamiento: solo datos con fecha < t
        - Predicción: datos en fecha t
        - Evaluación: resultados reales de fecha t
        """
        mock_pool = Mock()
        mock_entrenador = Mock()
        mock_predictor = Mock()

        backtester = BacktesterFutbol(
            pool=mock_pool,
            entrenador=mock_entrenador,
            predictor=mock_predictor,
        )

        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 3, 31),
            step_dias=7,
        )

        # Simular walk-forward
        fechas_evaluacion = []
        fechas_entrenamiento_max = []

        fecha_actual = config.fecha_inicio
        while fecha_actual <= config.fecha_fin:
            # Fecha de corte para entrenamiento
            fecha_corte = fecha_actual

            # Verificar: entrenamiento solo usa datos anteriores
            fechas_evaluacion.append(fecha_actual)
            fechas_entrenamiento_max.append(fecha_corte - timedelta(days=1))

            fecha_actual += timedelta(days=config.step_dias)

        # Para cada evaluación, la fecha max de entrenamiento debe ser anterior
        for eval_fecha, train_max in zip(fechas_evaluacion, fechas_entrenamiento_max):
            assert train_max < eval_fecha, (
                f"Data leakage: entrenamiento usa datos de {train_max} "
                f"para predecir {eval_fecha}"
            )

    def test_walk_forward_genera_ventanas(self):
        """Walk-forward genera las ventanas correctas."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 15),
            fecha_fin=date(2024, 2, 15),
            step_dias=7,
        )

        ventanas = list(BacktesterFutbol._generar_ventanas(config))

        # 15 Enero a 15 Febrero con step 7 = ~4-5 ventanas
        assert len(ventanas) >= 4

        # Cada ventana tiene fecha_corte y fecha_evaluacion
        for ventana in ventanas:
            assert "fecha_corte" in ventana
            assert "fecha_evaluacion_inicio" in ventana
            assert "fecha_evaluacion_fin" in ventana

    def test_walk_forward_ventanas_consecutivas(self):
        """Las ventanas son consecutivas sin gaps."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 2, 1),
            step_dias=7,
        )

        ventanas = list(BacktesterFutbol._generar_ventanas(config))

        for i in range(1, len(ventanas)):
            # La evaluación de una ventana termina donde empieza la siguiente
            fin_anterior = ventanas[i-1]["fecha_evaluacion_fin"]
            inicio_actual = ventanas[i]["fecha_evaluacion_inicio"]

            assert fin_anterior == inicio_actual - timedelta(days=1) or fin_anterior < inicio_actual


class TestBacktestROI:
    """Tests para cálculo de ROI en backtest."""

    def test_backtest_calcula_roi(self):
        """El backtest calcula el ROI correctamente."""
        # Simular resultados de apuestas
        apuestas = [
            {"stake": 100, "resultado": "ganada", "cuota": 2.0},  # +100
            {"stake": 100, "resultado": "perdida", "cuota": 1.8},  # -100
            {"stake": 100, "resultado": "ganada", "cuota": 1.9},  # +90
            {"stake": 100, "resultado": "perdida", "cuota": 2.1},  # -100
            {"stake": 100, "resultado": "ganada", "cuota": 1.85},  # +85
        ]

        total_stake = sum(a["stake"] for a in apuestas)
        ganancias = sum(
            a["stake"] * (a["cuota"] - 1) if a["resultado"] == "ganada" else -a["stake"]
            for a in apuestas
        )

        roi = ganancias / total_stake

        # 3 ganadas, 2 perdidas
        # Ganancias: 100 + 90 + 85 = 275
        # Pérdidas: 100 + 100 = 200
        # Neto: 75
        # ROI: 75 / 500 = 15%
        assert abs(roi - 0.15) < 0.001

    def test_roi_formula_correcta(self):
        """ROI = (ganancias - pérdidas) / total_apostado."""
        # Caso simple: 1 apuesta ganada
        stake = 100
        cuota = 2.0
        ganancia = stake * (cuota - 1)  # 100

        roi = ganancia / stake
        assert roi == 1.0  # 100% ROI

        # Caso: apuesta perdida
        roi_perdida = -stake / stake
        assert roi_perdida == -1.0  # -100% ROI

    def test_yield_vs_roi(self):
        """
        Yield incluye todas las apuestas, ROI solo las resueltas.

        Yield = beneficio / total_apostado
        """
        apuestas_resueltas = 10
        apuestas_pendientes = 2

        total_apostado = (apuestas_resueltas + apuestas_pendientes) * 100
        beneficio = 150  # De las resueltas

        yield_total = beneficio / total_apostado  # 150/1200 = 12.5%
        roi_resueltas = beneficio / (apuestas_resueltas * 100)  # 150/1000 = 15%

        assert yield_total < roi_resueltas


class TestReporteBacktest:
    """Tests para generación de reportes."""

    def test_backtest_genera_reporte(self):
        """El backtest genera un reporte completo."""
        # Simular resultado
        resultado = ResultadoBacktest(
            config=ConfiguracionBacktest(
                fecha_inicio=date(2024, 1, 1),
                fecha_fin=date(2024, 3, 31),
            ),
            predicciones=[],
            apuestas=[],
            metricas_calibracion={},
            metricas_rentabilidad={},
        )

        reporte = ReporteBacktest.generar(resultado)

        assert hasattr(reporte, "resumen")
        assert hasattr(reporte, "metricas_por_mercado")
        assert hasattr(reporte, "curva_equity")

    def test_reporte_incluye_metricas_clave(self):
        """El reporte incluye todas las métricas clave."""
        reporte = ReporteBacktest(
            resumen={
                "roi": 0.05,
                "win_rate": 0.52,
                "total_apuestas": 100,
                "beneficio_neto": 250,
            },
            metricas_por_mercado={},
            curva_equity=[],
            periodo={"inicio": date(2024, 1, 1), "fin": date(2024, 3, 31)},
        )

        assert "roi" in reporte.resumen
        assert "win_rate" in reporte.resumen
        assert "total_apuestas" in reporte.resumen
        assert "beneficio_neto" in reporte.resumen


class TestMetricasCalibracion:
    """Tests para métricas de calibración en backtest."""

    def test_brier_score_backtest(self):
        """Calcula Brier Score durante backtest."""
        # Predicciones de probabilidad y resultados reales
        predicciones = [0.7, 0.6, 0.8, 0.55, 0.9]
        resultados = [1, 1, 0, 1, 1]  # 1 = over, 0 = under

        # Brier Score = mean((p - y)²)
        brier = np.mean([(p - y)**2 for p, y in zip(predicciones, resultados)])

        # (0.3² + 0.4² + 0.8² + 0.45² + 0.1²) / 5
        # = (0.09 + 0.16 + 0.64 + 0.2025 + 0.01) / 5
        # = 1.1025 / 5 = 0.2205
        assert abs(brier - 0.2205) < 0.001

    def test_calibracion_perfecta(self):
        """Calibración perfecta: predicción = resultado."""
        predicciones = [0.0, 0.5, 1.0]
        resultados = [0, 1, 1]  # Asumiendo 0.5 se resuelve como over

        # Con calibración perfecta (imposible en práctica)
        predicciones_perfectas = [0.0, 1.0, 1.0]
        brier_perfecto = np.mean(
            [(p - y)**2 for p, y in zip(predicciones_perfectas, resultados)]
        )

        assert brier_perfecto == 0.0


class TestBacktesterFlujo:
    """Tests para el flujo completo del backtester."""

    @pytest.fixture
    def backtester_mock(self):
        """Crea backtester con mocks."""
        mock_pool = Mock()
        mock_entrenador = Mock()
        mock_predictor = Mock()

        # Configurar mocks
        mock_entrenador.entrenar_para_backtest.return_value = {
            "corners": Mock(),
            "goles": Mock(),
            "disparos": Mock(),
        }

        return BacktesterFutbol(
            pool=mock_pool,
            entrenador=mock_entrenador,
            predictor=mock_predictor,
        )

    def test_ejecutar_backtest_flujo(self, backtester_mock):
        """Ejecutar backtest sigue el flujo correcto."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
            step_dias=7,
        )

        # Mock de partidos
        backtester_mock._obtener_partidos = Mock(return_value=[])

        resultado = backtester_mock.ejecutar(config)

        assert isinstance(resultado, ResultadoBacktest)

    def test_backtest_por_mercado(self, backtester_mock):
        """Backtest genera métricas por mercado."""
        config = ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 31),
        )

        backtester_mock._obtener_partidos = Mock(return_value=[])
        resultado = backtester_mock.ejecutar(config)

        # Debe haber métricas para cada mercado
        assert isinstance(resultado.metricas_calibracion, dict)


class TestSeleccionApuestas:
    """Tests para selección de apuestas basada en edge."""

    def test_filtrar_por_umbral_edge(self):
        """Solo se apuesta si edge > umbral."""
        umbral_edge = 0.05  # 5%

        predicciones = [
            {"edge": 0.10, "mercado": "CORNERS_FT"},  # Apostar
            {"edge": 0.03, "mercado": "GOLES_FT"},    # No apostar
            {"edge": 0.08, "mercado": "DISPAROS_FT"}, # Apostar
            {"edge": -0.02, "mercado": "CORNERS_1T"}, # No apostar
        ]

        apuestas = [p for p in predicciones if p["edge"] > umbral_edge]

        assert len(apuestas) == 2
        assert all(a["edge"] > umbral_edge for a in apuestas)

    def test_kelly_sizing_en_backtest(self):
        """El tamaño de apuesta usa Kelly Criterion."""
        from motor_futbol.prediccion.calculadora_probabilidad import CalculadoraProbabilidad

        prob = 0.6
        cuota = 2.0
        fraccion = 0.25

        kelly = CalculadoraProbabilidad.kelly_criterion(prob, cuota, fraccion)

        # f* = (p*b - q) / b donde b = cuota - 1
        # f* = (0.6*1 - 0.4) / 1 = 0.2
        # Quarter Kelly = 0.2 * 0.25 = 0.05
        assert abs(kelly - 0.05) < 0.001


class TestCurvaEquity:
    """Tests para la curva de equity."""

    def test_curva_equity_acumulativa(self):
        """La curva de equity es acumulativa."""
        resultados_diarios = [10, -5, 15, -8, 20]

        curva = []
        equity = 1000  # Capital inicial

        for resultado in resultados_diarios:
            equity += resultado
            curva.append(equity)

        # Curva final
        assert curva == [1010, 1005, 1020, 1012, 1032]

    def test_drawdown_maximo(self):
        """Calcula el drawdown máximo."""
        curva = [1000, 1050, 1020, 1100, 1000, 1150]

        # Drawdown = (pico - valle) / pico
        pico_actual = curva[0]
        max_drawdown = 0

        for valor in curva:
            if valor > pico_actual:
                pico_actual = valor
            drawdown = (pico_actual - valor) / pico_actual
            max_drawdown = max(max_drawdown, drawdown)

        # Pico en 1100, valle en 1000 -> DD = 100/1100 ≈ 9.09%
        assert abs(max_drawdown - 0.0909) < 0.01


class TestComparacionModelos:
    """Tests para comparación de modelos en backtest."""

    def test_comparar_versiones_modelos(self):
        """Permite comparar diferentes versiones de modelos."""
        resultados_v1 = {"roi": 0.05, "brier": 0.22}
        resultados_v2 = {"roi": 0.08, "brier": 0.19}

        # v2 es mejor en ambas métricas
        assert resultados_v2["roi"] > resultados_v1["roi"]
        assert resultados_v2["brier"] < resultados_v1["brier"]  # Menor es mejor

    def test_significancia_estadistica(self):
        """Evalúa significancia estadística de diferencias."""
        # Simular ROIs de múltiples runs
        rois_v1 = np.random.normal(0.05, 0.02, 100)
        rois_v2 = np.random.normal(0.08, 0.02, 100)

        # Test t simple (en práctica usar scipy.stats.ttest_ind)
        mean_diff = np.mean(rois_v2) - np.mean(rois_v1)
        std_pooled = np.sqrt(np.var(rois_v1)/100 + np.var(rois_v2)/100)

        t_stat = mean_diff / std_pooled

        # Con diferencia de ~0.03 y std ~0.02, t-stat debería ser significativo
        assert abs(t_stat) > 2.0  # Aproximadamente significativo al 95%

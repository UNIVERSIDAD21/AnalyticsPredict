# -*- coding: utf-8 -*-
"""
test_metricas_calibracion.py — Tests para las métricas de calibración.

Cubre:
- Brier Score: Casos conocidos y límites
- Log Loss: Casos conocidos y estabilidad numérica
- ECE/MCE: Calibración perfecta y bins vacíos
- Reliability Diagram: Estructura y contenido
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np

from motor_futbol.calibracion import (
    calcular_brier_score,
    calcular_log_loss,
    calcular_ece,
    calcular_mce,
    generar_reliability_diagram,
    calcular_metricas_completas,
    comparar_calibracion,
)
from motor_futbol.tipos import DatosReliabilityDiagram


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: BRIER SCORE
# ══════════════════════════════════════════════════════════════════════════════

class TestBrierScore:
    """Tests para el cálculo del Brier Score."""

    def test_prediccion_perfecta_brier_cero(self):
        """Predicciones perfectas deberían dar Brier Score = 0."""
        # Predicciones perfectas: prob = outcome
        prob = np.array([0.0, 1.0, 0.0, 1.0, 1.0])
        outcomes = np.array([0, 1, 0, 1, 1])

        brier = calcular_brier_score(prob, outcomes)

        assert brier == 0.0

    def test_prediccion_peor_brier_uno(self):
        """Predicciones completamente equivocadas deberían dar Brier Score = 1."""
        # Predicciones invertidas
        prob = np.array([1.0, 0.0, 1.0, 0.0])
        outcomes = np.array([0, 1, 0, 1])

        brier = calcular_brier_score(prob, outcomes)

        assert brier == 1.0

    def test_brier_valores_conocidos(self):
        """Verifica con valores calculados manualmente."""
        # Ejemplo: prob = [0.7, 0.3], outcomes = [1, 0]
        # Brier = ((0.7-1)^2 + (0.3-0)^2) / 2 = (0.09 + 0.09) / 2 = 0.09
        prob = np.array([0.7, 0.3])
        outcomes = np.array([1, 0])

        brier = calcular_brier_score(prob, outcomes)

        assert abs(brier - 0.09) < 1e-9

    def test_brier_probabilidad_50_siempre_025(self):
        """Probabilidad 0.5 siempre da Brier = 0.25."""
        prob = np.array([0.5, 0.5, 0.5, 0.5])
        outcomes = np.array([0, 1, 0, 1])

        brier = calcular_brier_score(prob, outcomes)

        assert abs(brier - 0.25) < 1e-9

    def test_error_longitudes_diferentes(self):
        """Verifica que lanza error con arrays de diferente longitud."""
        prob = np.array([0.5, 0.6])
        outcomes = np.array([0, 1, 0])

        with pytest.raises(ValueError, match="misma longitud"):
            calcular_brier_score(prob, outcomes)

    def test_error_probabilidades_fuera_rango(self):
        """Verifica que lanza error con probabilidades inválidas."""
        prob = np.array([0.5, 1.5])
        outcomes = np.array([0, 1])

        with pytest.raises(ValueError, match="entre 0 y 1"):
            calcular_brier_score(prob, outcomes)

    def test_array_vacio_retorna_cero(self):
        """Array vacío debería retornar 0."""
        prob = np.array([])
        outcomes = np.array([])

        brier = calcular_brier_score(prob, outcomes)

        assert brier == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: LOG LOSS
# ══════════════════════════════════════════════════════════════════════════════

class TestLogLoss:
    """Tests para el cálculo del Log Loss."""

    def test_prediccion_perfecta_log_loss_cercano_cero(self):
        """Predicciones perfectas deberían dar Log Loss cercano a 0."""
        # Usar valores cercanos a 0 y 1 para evitar log(0)
        prob = np.array([0.001, 0.999, 0.001, 0.999])
        outcomes = np.array([0, 1, 0, 1])

        log_loss = calcular_log_loss(prob, outcomes)

        assert log_loss < 0.01  # Muy pequeño

    def test_prediccion_equivocada_log_loss_alto(self):
        """Predicciones muy equivocadas deberían dar Log Loss alto."""
        prob = np.array([0.999, 0.001])
        outcomes = np.array([0, 1])

        log_loss = calcular_log_loss(prob, outcomes)

        assert log_loss > 5  # Muy alto

    def test_log_loss_probabilidad_50(self):
        """Log Loss con prob=0.5 es log(2) = 0.693..."""
        prob = np.array([0.5, 0.5])
        outcomes = np.array([0, 1])

        log_loss = calcular_log_loss(prob, outcomes)

        assert abs(log_loss - np.log(2)) < 1e-6

    def test_log_loss_estable_con_extremos(self):
        """Verifica estabilidad numérica con valores extremos."""
        # Valores muy cercanos a 0 y 1
        prob = np.array([1e-15, 1 - 1e-15, 0.5])
        outcomes = np.array([0, 1, 1])

        log_loss = calcular_log_loss(prob, outcomes)

        # No debe ser infinito o NaN
        assert np.isfinite(log_loss)

    def test_array_vacio_retorna_cero(self):
        """Array vacío debería retornar 0."""
        prob = np.array([])
        outcomes = np.array([])

        log_loss = calcular_log_loss(prob, outcomes)

        assert log_loss == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: ECE (Expected Calibration Error)
# ══════════════════════════════════════════════════════════════════════════════

class TestECE:
    """Tests para el cálculo del ECE."""

    def test_calibracion_perfecta_ece_cero(self):
        """Calibración perfecta debería dar ECE = 0."""
        # Crear datos perfectamente calibrados
        # En cada bin, la frecuencia real = promedio de probabilidades
        np.random.seed(42)
        n = 1000

        # Generar probabilidades uniformes
        prob = np.random.uniform(0, 1, n)

        # Generar outcomes que coincidan con las probabilidades
        outcomes = (np.random.random(n) < prob).astype(int)

        ece = calcular_ece(prob, outcomes, n_bins=10)

        # ECE debería ser pequeño (no exactamente 0 por varianza muestral)
        assert ece < 0.05

    def test_ece_con_bins_vacios(self):
        """Verifica que ECE funciona con bins vacíos."""
        # Todas las probabilidades en un rango estrecho
        prob = np.array([0.45, 0.48, 0.50, 0.52, 0.55])
        outcomes = np.array([0, 1, 1, 0, 1])

        # Con 10 bins, la mayoría estarán vacíos
        ece = calcular_ece(prob, outcomes, n_bins=10)

        assert np.isfinite(ece)
        assert ece >= 0

    def test_ece_valores_conocidos(self):
        """Verifica ECE con ejemplo calculado manualmente."""
        # Ejemplo simple con 2 bins
        # Bin 1 (0-0.5): prob=[0.3], outcomes=[0] -> gap = |0.3 - 0| = 0.3
        # Bin 2 (0.5-1): prob=[0.8], outcomes=[1] -> gap = |0.8 - 1| = 0.2
        # ECE = (1/2 * 0.3) + (1/2 * 0.2) = 0.25

        prob = np.array([0.3, 0.8])
        outcomes = np.array([0, 1])

        ece = calcular_ece(prob, outcomes, n_bins=2)

        assert abs(ece - 0.25) < 1e-6

    def test_ece_sobreconfianza(self):
        """ECE alto cuando hay sobreconfianza."""
        # Modelo que siempre predice 0.9, pero solo acierta 50%
        prob = np.full(100, 0.9)
        outcomes = np.random.binomial(1, 0.5, 100)

        ece = calcular_ece(prob, outcomes)

        # Gap debería ser ~0.4 (0.9 - 0.5)
        assert ece > 0.3


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: MCE (Maximum Calibration Error)
# ══════════════════════════════════════════════════════════════════════════════

class TestMCE:
    """Tests para el cálculo del MCE."""

    def test_mce_mayor_o_igual_ece(self):
        """MCE siempre debería ser >= ECE."""
        np.random.seed(42)
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        ece = calcular_ece(prob, outcomes)
        mce = calcular_mce(prob, outcomes)

        assert mce >= ece

    def test_mce_calibracion_perfecta(self):
        """MCE debería ser pequeño con calibración perfecta."""
        np.random.seed(42)
        n = 1000
        prob = np.random.uniform(0, 1, n)
        outcomes = (np.random.random(n) < prob).astype(int)

        mce = calcular_mce(prob, outcomes)

        assert mce < 0.1

    def test_mce_descalibracion_extrema(self):
        """MCE alto con descalibración extrema en un bin."""
        # La mayoría bien calibrados, pero un grupo muy mal
        prob = np.concatenate([
            np.full(50, 0.9),  # Muy mal calibrados
            np.random.uniform(0.4, 0.6, 50)  # Bien calibrados
        ])
        outcomes = np.concatenate([
            np.zeros(50),  # 0.9 predicho, 0.0 real -> gap = 0.9
            np.random.binomial(1, 0.5, 50)
        ])

        mce = calcular_mce(prob, outcomes)

        assert mce >= 0.8  # Gap máximo debería ser ~0.9


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: RELIABILITY DIAGRAM
# ══════════════════════════════════════════════════════════════════════════════

class TestReliabilityDiagram:
    """Tests para la generación de reliability diagrams."""

    def test_genera_estructura_correcta(self):
        """Verifica que genera la estructura correcta."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        resultado = generar_reliability_diagram(prob, outcomes, n_bins=10)

        assert isinstance(resultado, DatosReliabilityDiagram)
        assert len(resultado.bins) == 10
        assert len(resultado.frecuencia_predicha) == 10
        assert len(resultado.frecuencia_real) == 10
        assert len(resultado.conteo) == 10

    def test_bins_cubren_todo_rango(self):
        """Verifica que los bins cubren [0, 1]."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        resultado = generar_reliability_diagram(prob, outcomes, n_bins=10)

        # Primer bin empieza en 0
        assert resultado.bins[0][0] == 0.0
        # Último bin termina en 1
        assert resultado.bins[-1][1] == 1.0

        # Bins son contiguos
        for i in range(len(resultado.bins) - 1):
            assert resultado.bins[i][1] == resultado.bins[i + 1][0]

    def test_conteo_suma_total(self):
        """Verifica que el conteo total suma al número de muestras."""
        n = 100
        prob = np.random.uniform(0, 1, n)
        outcomes = np.random.binomial(1, 0.5, n)

        resultado = generar_reliability_diagram(prob, outcomes)

        assert sum(resultado.conteo) == n

    def test_frecuencias_en_rango(self):
        """Verifica que las frecuencias están en [0, 1]."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        resultado = generar_reliability_diagram(prob, outcomes)

        for pred, real in zip(resultado.frecuencia_predicha, resultado.frecuencia_real):
            assert 0 <= pred <= 1
            assert 0 <= real <= 1

    def test_to_dict(self):
        """Verifica serialización a diccionario."""
        prob = np.random.uniform(0, 1, 50)
        outcomes = np.random.binomial(1, 0.5, 50)

        resultado = generar_reliability_diagram(prob, outcomes, n_bins=5)
        data = resultado.to_dict()

        assert "bins" in data
        assert "frecuencia_predicha" in data
        assert "frecuencia_real" in data
        assert "conteo" in data


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

class TestFuncionesAuxiliares:
    """Tests para funciones auxiliares de métricas."""

    def test_calcular_metricas_completas(self):
        """Verifica que calcular_metricas_completas retorna todas las métricas."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        metricas = calcular_metricas_completas(prob, outcomes)

        assert "brier_score" in metricas
        assert "log_loss" in metricas
        assert "ece" in metricas
        assert "mce" in metricas
        assert "n_muestras" in metricas
        assert metricas["n_muestras"] == 100

    def test_comparar_calibracion(self):
        """Verifica comparación antes/después de calibración."""
        np.random.seed(42)
        prob_antes = np.random.uniform(0, 1, 100)
        # Simular calibración que mejora ligeramente
        prob_despues = 0.5 + 0.8 * (prob_antes - 0.5)
        outcomes = (np.random.random(100) < prob_despues).astype(int)

        comparacion = comparar_calibracion(prob_antes, prob_despues, outcomes)

        assert "antes" in comparacion
        assert "despues" in comparacion
        assert "mejora_porcentual" in comparacion

        # Verificar estructura de métricas
        assert "brier_score" in comparacion["antes"]
        assert "brier_score" in comparacion["despues"]
        assert "brier_score" in comparacion["mejora_porcentual"]


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests para casos límite en métricas."""

    def test_una_sola_muestra(self):
        """Verifica comportamiento con una sola muestra."""
        prob = np.array([0.7])
        outcomes = np.array([1])

        brier = calcular_brier_score(prob, outcomes)
        log_loss = calcular_log_loss(prob, outcomes)
        ece = calcular_ece(prob, outcomes)

        assert np.isfinite(brier)
        assert np.isfinite(log_loss)
        assert np.isfinite(ece)

    def test_probabilidades_extremas(self):
        """Verifica estabilidad con probabilidades muy extremas."""
        prob = np.array([0.0001, 0.9999])
        outcomes = np.array([0, 1])

        brier = calcular_brier_score(prob, outcomes)
        log_loss = calcular_log_loss(prob, outcomes)

        assert np.isfinite(brier)
        assert np.isfinite(log_loss)
        assert brier < 0.001  # Casi perfecto

    def test_todos_outcomes_iguales(self):
        """Verifica comportamiento cuando todos los outcomes son iguales."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.ones(100)

        ece = calcular_ece(prob, outcomes)
        mce = calcular_mce(prob, outcomes)

        assert np.isfinite(ece)
        assert np.isfinite(mce)

    def test_diferentes_numeros_de_bins(self):
        """Verifica que funciona con diferentes números de bins."""
        prob = np.random.uniform(0, 1, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        for n_bins in [2, 5, 10, 20, 50]:
            ece = calcular_ece(prob, outcomes, n_bins=n_bins)
            mce = calcular_mce(prob, outcomes, n_bins=n_bins)
            rd = generar_reliability_diagram(prob, outcomes, n_bins=n_bins)

            assert np.isfinite(ece)
            assert np.isfinite(mce)
            assert len(rd.bins) == n_bins

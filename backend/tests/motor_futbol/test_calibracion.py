# -*- coding: utf-8 -*-
"""
test_calibracion.py — Tests para el módulo de calibración de probabilidades.

Cubre:
- CalibradorPlatt: Entrenamiento, calibración, serialización
- CalibradorIsotonic: Entrenamiento, calibración, serialización
- GestorCalibradores: Operaciones de gestión (mock)
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch

from motor_futbol.tipos import TipoMercadoFutbol, ResultadoCalibracion
from motor_futbol.calibracion import (
    CalibradorPlatt,
    CalibradorIsotonic,
    GestorCalibradores,
)


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def datos_sinteticos():
    """Genera datos sintéticos para pruebas."""
    np.random.seed(42)
    n = 500

    # Generar probabilidades "raw" con sobreconfianza
    prob_raw = np.random.beta(2, 2, n)

    # Simular descalibración: comprimir hacia 0.5
    prob_real = 0.5 + 0.7 * (prob_raw - 0.5)
    prob_real = np.clip(prob_real, 0.01, 0.99)

    # Generar outcomes según probabilidad real
    outcomes = (np.random.random(n) < prob_real).astype(int)

    return prob_raw, outcomes


@pytest.fixture
def datos_pequenos():
    """Datos pequeños para pruebas rápidas."""
    np.random.seed(123)
    n = 50
    prob_raw = np.random.uniform(0.2, 0.8, n)
    outcomes = (np.random.random(n) < prob_raw).astype(int)
    return prob_raw, outcomes


@pytest.fixture
def mercado():
    """Mercado de prueba."""
    return TipoMercadoFutbol.CORNERS_FT


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CALIBRADOR PLATT
# ══════════════════════════════════════════════════════════════════════════════

class TestCalibradorPlatt:
    """Tests para el calibrador Platt Scaling."""

    def test_entrenar_con_datos_sinteticos(self, datos_sinteticos, mercado):
        """Verifica que el entrenamiento funciona con datos sintéticos."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        resultado = calibrador.entrenar(prob_raw, outcomes)

        # Verificar que está entrenado
        assert calibrador.entrenado
        assert calibrador.fecha_entrenamiento is not None

        # Verificar parámetros
        assert calibrador.a != 1.0 or calibrador.b != 0.0  # Algo cambió

        # Verificar resultado
        assert isinstance(resultado, ResultadoCalibracion)
        assert resultado.n_muestras == len(prob_raw)
        assert resultado.metodo == "platt"

    def test_calibrar_probabilidad_unica(self, datos_sinteticos, mercado):
        """Verifica calibración de una única probabilidad."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Calibrar valor escalar
        prob = 0.65
        prob_calibrada = calibrador.calibrar(prob)

        assert isinstance(prob_calibrada, float)
        assert 0 <= prob_calibrada <= 1

    def test_calibrar_array_probabilidades(self, datos_sinteticos, mercado):
        """Verifica calibración de un array de probabilidades."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Calibrar array
        probs = np.array([0.2, 0.5, 0.8])
        probs_calibradas = calibrador.calibrar(probs)

        assert isinstance(probs_calibradas, np.ndarray)
        assert len(probs_calibradas) == 3
        assert np.all(probs_calibradas >= 0)
        assert np.all(probs_calibradas <= 1)

    def test_serializacion_to_dict_from_dict(self, datos_sinteticos, mercado):
        """Verifica serialización y deserialización."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Serializar
        data = calibrador.to_dict()
        assert "mercado" in data
        assert "a" in data
        assert "b" in data
        assert data["metodo"] == "platt"

        # Deserializar
        calibrador2 = CalibradorPlatt.from_dict(data)

        assert calibrador2.mercado == calibrador.mercado
        assert calibrador2.a == calibrador.a
        assert calibrador2.b == calibrador.b
        assert calibrador2.entrenado

        # Verificar que produce mismos resultados
        prob = 0.6
        assert abs(calibrador.calibrar(prob) - calibrador2.calibrar(prob)) < 1e-9

    def test_probabilidades_calibradas_en_rango_0_1(self, datos_sinteticos, mercado):
        """Verifica que las probabilidades calibradas siempre están en [0, 1]."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Probar con valores extremos
        probs_extremas = np.array([0.001, 0.01, 0.5, 0.99, 0.999])
        probs_calibradas = calibrador.calibrar(probs_extremas)

        assert np.all(probs_calibradas >= 0)
        assert np.all(probs_calibradas <= 1)

    def test_error_sin_entrenar(self, mercado):
        """Verifica que lanza error si no está entrenado."""
        calibrador = CalibradorPlatt(mercado)

        with pytest.raises(RuntimeError, match="no ha sido entrenado"):
            calibrador.calibrar(0.5)

    def test_error_pocas_muestras(self, mercado):
        """Verifica que lanza error con muy pocas muestras."""
        calibrador = CalibradorPlatt(mercado)

        prob = np.array([0.5, 0.6, 0.7])  # Solo 3 muestras
        outcomes = np.array([1, 0, 1])

        with pytest.raises(ValueError, match="al menos 10 muestras"):
            calibrador.entrenar(prob, outcomes)

    def test_error_probabilidades_fuera_rango(self, datos_sinteticos, mercado):
        """Verifica que lanza error con probabilidades inválidas."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        with pytest.raises(ValueError, match="entre 0 y 1"):
            calibrador.calibrar(np.array([0.5, 1.5, -0.1]))


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CALIBRADOR ISOTONIC
# ══════════════════════════════════════════════════════════════════════════════

class TestCalibradorIsotonic:
    """Tests para el calibrador Isotonic Regression."""

    def test_entrenar_con_datos_sinteticos(self, datos_sinteticos, mercado):
        """Verifica que el entrenamiento funciona con datos sintéticos."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorIsotonic(mercado)
        resultado = calibrador.entrenar(prob_raw, outcomes)

        # Verificar que está entrenado
        assert calibrador.entrenado
        assert calibrador.fecha_entrenamiento is not None
        assert calibrador.x_thresholds is not None
        assert calibrador.y_thresholds is not None

        # Verificar resultado
        assert isinstance(resultado, ResultadoCalibracion)
        assert resultado.metodo == "isotonic"

    def test_calibrar_preserva_orden(self, datos_sinteticos, mercado):
        """Verifica que Isotonic preserva el orden de probabilidades."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorIsotonic(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Usar método de verificación
        assert calibrador.preserva_orden(prob_raw)

        # Verificación manual
        probs_ordenadas = np.linspace(0.1, 0.9, 50)
        probs_calibradas = calibrador.calibrar(probs_ordenadas)

        # Las calibradas deben ser monotónicas crecientes (o iguales)
        diffs = np.diff(probs_calibradas)
        assert np.all(diffs >= -1e-9)  # Tolerancia numérica

    def test_serializacion_to_dict_from_dict(self, datos_sinteticos, mercado):
        """Verifica serialización y deserialización."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorIsotonic(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Serializar
        data = calibrador.to_dict()
        assert "x_thresholds" in data
        assert "y_thresholds" in data
        assert data["metodo"] == "isotonic"

        # Deserializar
        calibrador2 = CalibradorIsotonic.from_dict(data)

        assert calibrador2.mercado == calibrador.mercado
        assert calibrador2.entrenado

        # Verificar que produce mismos resultados
        probs = np.array([0.3, 0.5, 0.7])
        np.testing.assert_array_almost_equal(
            calibrador.calibrar(probs),
            calibrador2.calibrar(probs),
            decimal=6
        )

    def test_out_of_bounds_clipping(self, datos_sinteticos, mercado):
        """Verifica que valores fuera de rango se clipean correctamente."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorIsotonic(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        # Calibrar valores extremos (dentro de [0,1] pero cerca de los límites)
        probs_extremas = np.array([0.001, 0.999])
        probs_calibradas = calibrador.calibrar(probs_extremas)

        assert np.all(probs_calibradas >= 0)
        assert np.all(probs_calibradas <= 1)

    def test_calibrar_probabilidad_unica(self, datos_sinteticos, mercado):
        """Verifica calibración de una única probabilidad."""
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorIsotonic(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        prob = 0.65
        prob_calibrada = calibrador.calibrar(prob)

        assert isinstance(prob_calibrada, float)
        assert 0 <= prob_calibrada <= 1


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: GESTOR DE CALIBRADORES
# ══════════════════════════════════════════════════════════════════════════════

class TestGestorCalibradores:
    """Tests para el gestor de calibradores (con mocks)."""

    @pytest.fixture
    def mock_pool(self):
        """Crea un mock del pool de conexiones."""
        pool = MagicMock()
        conn = MagicMock()
        cur = MagicMock()

        pool.connection.return_value.__enter__ = MagicMock(return_value=conn)
        pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        return pool, conn, cur

    def test_calibrar_sin_calibrador_activo_retorna_raw(self, mock_pool, mercado):
        """Verifica que sin calibrador activo retorna probabilidad raw."""
        pool, conn, cur = mock_pool
        cur.fetchone.return_value = None  # No hay calibrador activo

        gestor = GestorCalibradores(pool)
        prob = 0.65

        resultado = gestor.calibrar_probabilidad(mercado, prob)

        assert resultado == prob

    def test_cache_funciona_correctamente(self, mock_pool, mercado, datos_sinteticos):
        """Verifica que el cache evita consultas repetidas."""
        pool, conn, cur = mock_pool
        prob_raw, outcomes = datos_sinteticos

        # Crear y entrenar calibrador
        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        gestor = GestorCalibradores(pool)

        # Agregar al cache manualmente
        gestor.calibradores_cache[mercado] = calibrador

        # Cargar debería usar cache
        cargado = gestor.cargar_calibrador_activo(mercado, usar_cache=True)

        assert cargado is calibrador
        # No debería haber llamado a la BD
        assert cur.execute.call_count == 0

    def test_limpiar_cache(self, mock_pool, mercado, datos_sinteticos):
        """Verifica que limpiar cache funciona."""
        pool, conn, cur = mock_pool
        prob_raw, outcomes = datos_sinteticos

        calibrador = CalibradorPlatt(mercado)
        calibrador.entrenar(prob_raw, outcomes)

        gestor = GestorCalibradores(pool)
        gestor.calibradores_cache[mercado] = calibrador

        assert len(gestor.calibradores_cache) == 1

        gestor.limpiar_cache()

        assert len(gestor.calibradores_cache) == 0


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: COMPARACIÓN PLATT VS ISOTONIC
# ══════════════════════════════════════════════════════════════════════════════

class TestComparacionCalibradores:
    """Tests comparativos entre métodos de calibración."""

    def test_ambos_mejoran_brier_score(self, datos_sinteticos, mercado):
        """Verifica que ambos métodos mejoran el Brier Score."""
        prob_raw, outcomes = datos_sinteticos

        from motor_futbol.calibracion import calcular_brier_score

        brier_raw = calcular_brier_score(prob_raw, outcomes)

        # Platt
        cal_platt = CalibradorPlatt(mercado)
        res_platt = cal_platt.entrenar(prob_raw, outcomes)
        prob_platt = cal_platt.calibrar(prob_raw)
        brier_platt = calcular_brier_score(prob_platt, outcomes)

        # Isotonic
        cal_isotonic = CalibradorIsotonic(mercado)
        res_isotonic = cal_isotonic.entrenar(prob_raw, outcomes)
        prob_isotonic = cal_isotonic.calibrar(prob_raw)
        brier_isotonic = calcular_brier_score(prob_isotonic, outcomes)

        # Ambos deberían mejorar (o al menos no empeorar significativamente)
        # En training set, siempre deberían mejorar
        assert brier_platt <= brier_raw + 0.01
        assert brier_isotonic <= brier_raw + 0.01

    def test_isotonic_no_peor_que_platt_con_muchos_datos(self, mercado):
        """Con muchos datos, Isotonic debería ser al menos tan bueno como Platt."""
        np.random.seed(42)
        n = 2000

        prob_raw = np.random.beta(2, 2, n)
        prob_real = 0.5 + 0.6 * (prob_raw - 0.5)
        outcomes = (np.random.random(n) < prob_real).astype(int)

        from motor_futbol.calibracion import calcular_brier_score

        cal_platt = CalibradorPlatt(mercado)
        cal_platt.entrenar(prob_raw, outcomes)
        brier_platt = calcular_brier_score(cal_platt.calibrar(prob_raw), outcomes)

        cal_isotonic = CalibradorIsotonic(mercado)
        cal_isotonic.entrenar(prob_raw, outcomes)
        brier_isotonic = calcular_brier_score(cal_isotonic.calibrar(prob_raw), outcomes)

        # Isotonic debería ser igual o mejor (en training set)
        assert brier_isotonic <= brier_platt + 0.01


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests para casos límite."""

    def test_probabilidades_todas_iguales(self, mercado):
        """Verifica comportamiento con probabilidades idénticas."""
        prob_raw = np.full(100, 0.5)
        outcomes = np.random.binomial(1, 0.5, 100)

        calibrador = CalibradorPlatt(mercado)
        resultado = calibrador.entrenar(prob_raw, outcomes)

        # Debería funcionar sin errores
        assert calibrador.entrenado

    def test_outcomes_todos_cero(self, mercado):
        """Verifica comportamiento cuando todos los outcomes son 0."""
        np.random.seed(42)
        prob_raw = np.random.uniform(0.2, 0.8, 100)
        outcomes = np.zeros(100)

        calibrador = CalibradorPlatt(mercado)
        resultado = calibrador.entrenar(prob_raw, outcomes)

        # Las probabilidades calibradas deberían ser bajas
        prob_calibrada = calibrador.calibrar(np.array([0.5]))
        assert prob_calibrada[0] < 0.5

    def test_outcomes_todos_uno(self, mercado):
        """Verifica comportamiento cuando todos los outcomes son 1."""
        np.random.seed(42)
        prob_raw = np.random.uniform(0.2, 0.8, 100)
        outcomes = np.ones(100)

        calibrador = CalibradorPlatt(mercado)
        resultado = calibrador.entrenar(prob_raw, outcomes)

        # Las probabilidades calibradas deberían ser altas
        prob_calibrada = calibrador.calibrar(np.array([0.5]))
        assert prob_calibrada[0] > 0.5

    def test_mercados_diferentes(self):
        """Verifica que calibradores de diferentes mercados son independientes."""
        np.random.seed(42)
        prob_raw = np.random.uniform(0.3, 0.7, 100)
        outcomes = np.random.binomial(1, 0.5, 100)

        cal_corners = CalibradorPlatt(TipoMercadoFutbol.CORNERS_FT)
        cal_goles = CalibradorPlatt(TipoMercadoFutbol.GOLES_FT)

        cal_corners.entrenar(prob_raw, outcomes)
        cal_goles.entrenar(prob_raw, outcomes)

        assert cal_corners.mercado != cal_goles.mercado
        assert cal_corners.mercado.value == "CORNERS_FT"
        assert cal_goles.mercado.value == "GOLES_FT"

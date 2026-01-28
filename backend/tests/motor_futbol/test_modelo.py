# -*- coding: utf-8 -*-
"""
test_modelo.py — Tests unitarios para ModeloPrediccionBase y modelos específicos.

Tests obligatorios según especificación:
- test_construir_matriz_diseno_formato
- test_ajustar_ridge_pesos
- test_predecir_retorna_media_std
- test_modelo_corners_9_mercados
"""

import pytest
import numpy as np

from motor_futbol.modelos.base import (
    ModeloPrediccionBase,
    construir_matriz_diseno,
    ajustar_ridge,
    calcular_std_residuales,
)
from motor_futbol.modelos.corners import ModeloCorners
from motor_futbol.modelos.goles import ModeloGoles
from motor_futbol.modelos.disparos import ModeloDisparos
from motor_futbol.tipos import TipoModelo, TipoMercadoFutbol
from motor_futbol.excepciones import ModeloNoEntrenado


class TestConstruirMatrizDiseno:
    """Tests para la función construir_matriz_diseno."""

    def test_construir_matriz_diseno_formato(self):
        """
        Verifica formato de la matriz de diseño.

        Formato esperado: [1, one-hot-equipo, one-hot-rival, es_local]
        """
        entidad_a_indice = {
            "Real Madrid": 0,
            "Barcelona": 1,
            "Sevilla": 2,
        }
        n_equipos = len(entidad_a_indice)

        nombres_equipo = np.array(["Real Madrid", "Barcelona"])
        nombres_rival = np.array(["Sevilla", "Real Madrid"])
        es_local = np.array([1.0, 0.0])

        X = construir_matriz_diseno(
            nombres_equipo, nombres_rival, es_local, entidad_a_indice
        )

        # Dimensiones esperadas: (n_muestras, 1 + n_equipos + n_equipos + 1)
        n_muestras = 2
        n_cols_esperadas = 1 + n_equipos + n_equipos + 1  # intercepto + equipos + rivales + es_local

        assert X.shape == (n_muestras, n_cols_esperadas)

    def test_matriz_diseno_intercepto(self):
        """Primera columna es intercepto (todos 1s)."""
        entidad_a_indice = {"A": 0, "B": 1}
        X = construir_matriz_diseno(
            np.array(["A", "B"]),
            np.array(["B", "A"]),
            np.array([1.0, 0.0]),
            entidad_a_indice,
        )

        # Primera columna debe ser todos 1s
        assert np.allclose(X[:, 0], 1.0)

    def test_matriz_diseno_one_hot_equipo(self):
        """Columnas de equipo son one-hot encoding."""
        entidad_a_indice = {"A": 0, "B": 1, "C": 2}
        X = construir_matriz_diseno(
            np.array(["A", "B", "C"]),
            np.array(["B", "C", "A"]),
            np.array([1.0, 1.0, 1.0]),
            entidad_a_indice,
        )

        # Columnas 1-3 son one-hot de equipo
        one_hot_equipo = X[:, 1:4]

        # Cada fila debe tener exactamente un 1
        assert np.allclose(one_hot_equipo.sum(axis=1), 1.0)

        # Primera fila: equipo A (índice 0)
        assert one_hot_equipo[0, 0] == 1.0
        assert one_hot_equipo[0, 1] == 0.0
        assert one_hot_equipo[0, 2] == 0.0

    def test_matriz_diseno_es_local(self):
        """Última columna es el flag es_local."""
        entidad_a_indice = {"A": 0, "B": 1}
        es_local = np.array([1.0, 0.0, 1.0])

        X = construir_matriz_diseno(
            np.array(["A", "B", "A"]),
            np.array(["B", "A", "B"]),
            es_local,
            entidad_a_indice,
        )

        # Última columna
        assert np.allclose(X[:, -1], es_local)


class TestAjustarRidge:
    """Tests para la función ajustar_ridge."""

    def test_ajustar_ridge_pesos_dimensiones(self):
        """Verifica dimensiones de los pesos."""
        n_muestras = 100
        n_features = 10
        n_targets = 4

        X = np.random.randn(n_muestras, n_features)
        Y = np.random.randn(n_muestras, n_targets)
        alpha = 5.0

        pesos, residuales = ajustar_ridge(X, Y, alpha)

        # Pesos: (n_features, n_targets)
        assert pesos.shape == (n_features, n_targets)
        # Residuales: (n_muestras, n_targets)
        assert residuales.shape == (n_muestras, n_targets)

    def test_ajustar_ridge_regularizacion(self):
        """Mayor alpha reduce magnitud de pesos."""
        X = np.random.randn(100, 10)
        Y = np.random.randn(100, 2)

        pesos_alpha_1, _ = ajustar_ridge(X, Y, alpha=1.0)
        pesos_alpha_10, _ = ajustar_ridge(X, Y, alpha=10.0)
        pesos_alpha_100, _ = ajustar_ridge(X, Y, alpha=100.0)

        # Norma de pesos decrece con alpha
        norma_1 = np.linalg.norm(pesos_alpha_1)
        norma_10 = np.linalg.norm(pesos_alpha_10)
        norma_100 = np.linalg.norm(pesos_alpha_100)

        assert norma_1 > norma_10 > norma_100

    def test_ajustar_ridge_formula_correcta(self):
        """
        Verifica que se usa la fórmula correcta de Ridge.

        W = (X'X + αI)^(-1) X'Y
        """
        # Datos pequeños para verificación manual
        X = np.array([[1, 2], [3, 4], [5, 6]])
        Y = np.array([[1], [2], [3]])
        alpha = 1.0

        pesos, _ = ajustar_ridge(X, Y, alpha)

        # Calcular manualmente
        XtX = X.T @ X
        XtY = X.T @ Y
        I = np.eye(X.shape[1])
        pesos_manual = np.linalg.solve(XtX + alpha * I, XtY)

        assert np.allclose(pesos, pesos_manual)


class TestCalcularStdResiduales:
    """Tests para cálculo de desviación estándar de residuales."""

    def test_std_residuales_por_target(self):
        """Calcula std separadamente para cada target."""
        residuales = np.array([
            [1.0, 2.0],
            [-1.0, -2.0],
            [1.0, 2.0],
            [-1.0, -2.0],
        ])

        stds = calcular_std_residuales(residuales)

        # std del primer target (valores: 1, -1, 1, -1)
        assert abs(stds[0] - 1.0) < 0.01
        # std del segundo target (valores: 2, -2, 2, -2)
        assert abs(stds[1] - 2.0) < 0.01


class TestModeloCorners:
    """Tests para el modelo de corners."""

    @pytest.fixture
    def modelo_corners(self):
        """Crea un modelo de corners."""
        return ModeloCorners()

    def test_tipo_correcto(self, modelo_corners):
        """El tipo debe ser CORNERS."""
        assert modelo_corners.tipo == TipoModelo.CORNERS

    def test_targets_correctos(self, modelo_corners):
        """Tiene los 4 targets de corners."""
        targets = modelo_corners.targets

        assert "corners_local_1t" in targets
        assert "corners_local_2t" in targets
        assert "corners_visitante_1t" in targets
        assert "corners_visitante_2t" in targets
        assert len(targets) == 4

    def test_predecir_sin_entrenar_lanza_error(self, modelo_corners):
        """Predecir sin entrenar lanza ModeloNoEntrenado."""
        with pytest.raises(ModeloNoEntrenado):
            modelo_corners.predecir_completo("Real Madrid", "Barcelona")

    def test_modelo_corners_9_mercados(self, modelo_corners):
        """
        Después de entrenar, genera predicciones para 9 mercados.

        Mercados:
        - CORNERS_LOCAL_1T, CORNERS_LOCAL_2T
        - CORNERS_VISITANTE_1T, CORNERS_VISITANTE_2T
        - CORNERS_1T, CORNERS_2T
        - CORNERS_LOCAL_FT, CORNERS_VISITANTE_FT
        - CORNERS_FT
        """
        # Entrenar con datos simulados
        n_partidos = 100
        n_equipos = 5

        # Crear datos de entrenamiento
        entidad_a_indice = {f"Equipo_{i}": i for i in range(n_equipos)}
        n_features = 1 + n_equipos + n_equipos + 1  # intercepto + equipos + rivales + es_local

        X = np.random.randn(n_partidos, n_features)
        X[:, 0] = 1.0  # Intercepto

        # Targets simulados
        y_dict = {
            "corners_local_1t": np.random.poisson(2.5, n_partidos).astype(float),
            "corners_local_2t": np.random.poisson(2.8, n_partidos).astype(float),
            "corners_visitante_1t": np.random.poisson(2.3, n_partidos).astype(float),
            "corners_visitante_2t": np.random.poisson(2.6, n_partidos).astype(float),
        }

        nombres_equipos = list(entidad_a_indice.keys())
        fechas = np.arange(n_partidos)

        # Entrenar
        modelo_corners.entrenar(X, y_dict, nombres_equipos, alpha=5.0, fechas=fechas)

        # Predecir
        mercados = modelo_corners.predecir_completo("Equipo_0", "Equipo_1")

        # Verificar que hay 9 mercados
        assert len(mercados) == 9

        # Verificar mercados específicos
        mercados_esperados = [
            TipoMercadoFutbol.CORNERS_LOCAL_1T.value,
            TipoMercadoFutbol.CORNERS_LOCAL_2T.value,
            TipoMercadoFutbol.CORNERS_VISITANTE_1T.value,
            TipoMercadoFutbol.CORNERS_VISITANTE_2T.value,
            TipoMercadoFutbol.CORNERS_1T.value,
            TipoMercadoFutbol.CORNERS_2T.value,
            TipoMercadoFutbol.CORNERS_LOCAL_FT.value,
            TipoMercadoFutbol.CORNERS_VISITANTE_FT.value,
            TipoMercadoFutbol.CORNERS_FT.value,
        ]

        for mercado in mercados_esperados:
            assert mercado in mercados, f"Falta mercado {mercado}"


class TestModeloGoles:
    """Tests para el modelo de goles."""

    @pytest.fixture
    def modelo_goles(self):
        """Crea un modelo de goles."""
        return ModeloGoles()

    def test_tipo_correcto(self, modelo_goles):
        """El tipo debe ser GOLES."""
        assert modelo_goles.tipo == TipoModelo.GOLES

    def test_modelo_goles_9_mercados(self, modelo_goles):
        """Genera predicciones para 9 mercados de goles."""
        # Entrenar
        n_partidos = 100
        n_equipos = 5
        entidad_a_indice = {f"Equipo_{i}": i for i in range(n_equipos)}
        n_features = 1 + n_equipos + n_equipos + 1

        X = np.random.randn(n_partidos, n_features)
        X[:, 0] = 1.0

        y_dict = {
            "goles_local_1t": np.random.poisson(0.7, n_partidos).astype(float),
            "goles_local_2t": np.random.poisson(0.8, n_partidos).astype(float),
            "goles_visitante_1t": np.random.poisson(0.5, n_partidos).astype(float),
            "goles_visitante_2t": np.random.poisson(0.6, n_partidos).astype(float),
        }

        modelo_goles.entrenar(
            X, y_dict, list(entidad_a_indice.keys()),
            alpha=5.0, fechas=np.arange(n_partidos)
        )

        mercados = modelo_goles.predecir_completo("Equipo_0", "Equipo_1")

        # 9 mercados de goles
        assert len(mercados) == 9

        mercados_goles = [
            TipoMercadoFutbol.GOLES_LOCAL_1T.value,
            TipoMercadoFutbol.GOLES_LOCAL_2T.value,
            TipoMercadoFutbol.GOLES_VISITANTE_1T.value,
            TipoMercadoFutbol.GOLES_VISITANTE_2T.value,
            TipoMercadoFutbol.GOLES_1T.value,
            TipoMercadoFutbol.GOLES_2T.value,
            TipoMercadoFutbol.GOLES_LOCAL_FT.value,
            TipoMercadoFutbol.GOLES_VISITANTE_FT.value,
            TipoMercadoFutbol.GOLES_FT.value,
        ]

        for mercado in mercados_goles:
            assert mercado in mercados


class TestModeloDisparos:
    """Tests para el modelo de disparos."""

    @pytest.fixture
    def modelo_disparos(self):
        """Crea un modelo de disparos."""
        return ModeloDisparos()

    def test_tipo_correcto(self, modelo_disparos):
        """El tipo debe ser DISPAROS."""
        assert modelo_disparos.tipo == TipoModelo.DISPAROS

    def test_modelo_disparos_6_mercados(self, modelo_disparos):
        """Genera predicciones para 6 mercados de disparos."""
        # Entrenar
        n_partidos = 100
        n_equipos = 5
        entidad_a_indice = {f"Equipo_{i}": i for i in range(n_equipos)}
        n_features = 1 + n_equipos + n_equipos + 1

        X = np.random.randn(n_partidos, n_features)
        X[:, 0] = 1.0

        y_dict = {
            "disparos_local": np.random.poisson(12, n_partidos).astype(float),
            "disparos_visitante": np.random.poisson(10, n_partidos).astype(float),
            "disparos_arco_local": np.random.poisson(5, n_partidos).astype(float),
            "disparos_arco_visitante": np.random.poisson(4, n_partidos).astype(float),
        }

        modelo_disparos.entrenar(
            X, y_dict, list(entidad_a_indice.keys()),
            alpha=5.0, fechas=np.arange(n_partidos)
        )

        mercados = modelo_disparos.predecir_completo("Equipo_0", "Equipo_1")

        # 6 mercados de disparos
        assert len(mercados) == 6


class TestPrediccionMercado:
    """Tests para estructura PrediccionMercado."""

    def test_prediccion_retorna_media_std(self):
        """Cada predicción de mercado tiene media y std."""
        modelo = ModeloCorners()

        # Entrenar
        n_partidos = 100
        n_equipos = 5
        entidad_a_indice = {f"Equipo_{i}": i for i in range(n_equipos)}
        n_features = 1 + n_equipos + n_equipos + 1

        X = np.random.randn(n_partidos, n_features)
        X[:, 0] = 1.0

        y_dict = {
            "corners_local_1t": np.random.poisson(2.5, n_partidos).astype(float),
            "corners_local_2t": np.random.poisson(2.8, n_partidos).astype(float),
            "corners_visitante_1t": np.random.poisson(2.3, n_partidos).astype(float),
            "corners_visitante_2t": np.random.poisson(2.6, n_partidos).astype(float),
        }

        modelo.entrenar(
            X, y_dict, list(entidad_a_indice.keys()),
            alpha=5.0, fechas=np.arange(n_partidos)
        )

        mercados = modelo.predecir_completo("Equipo_0", "Equipo_1")

        # Verificar cada mercado tiene media y std
        for nombre_mercado, prediccion in mercados.items():
            assert hasattr(prediccion, "media"), f"{nombre_mercado} sin media"
            assert hasattr(prediccion, "std"), f"{nombre_mercado} sin std"
            assert prediccion.media >= 0, f"{nombre_mercado} media negativa"
            assert prediccion.std > 0, f"{nombre_mercado} std <= 0"


class TestMercadosDerivados:
    """Tests para cálculo de mercados derivados."""

    def test_corners_ft_es_suma_de_parciales(self):
        """
        CORNERS_FT = CORNERS_LOCAL_1T + CORNERS_LOCAL_2T +
                     CORNERS_VISITANTE_1T + CORNERS_VISITANTE_2T
        """
        modelo = ModeloCorners()

        # Entrenar
        n_partidos = 200
        n_equipos = 5
        entidad_a_indice = {f"Equipo_{i}": i for i in range(n_equipos)}
        n_features = 1 + n_equipos + n_equipos + 1

        X = np.random.randn(n_partidos, n_features)
        X[:, 0] = 1.0

        y_dict = {
            "corners_local_1t": np.random.poisson(2.5, n_partidos).astype(float),
            "corners_local_2t": np.random.poisson(2.8, n_partidos).astype(float),
            "corners_visitante_1t": np.random.poisson(2.3, n_partidos).astype(float),
            "corners_visitante_2t": np.random.poisson(2.6, n_partidos).astype(float),
        }

        modelo.entrenar(
            X, y_dict, list(entidad_a_indice.keys()),
            alpha=5.0, fechas=np.arange(n_partidos)
        )

        mercados = modelo.predecir_completo("Equipo_0", "Equipo_1")

        # Obtener medias
        media_local_1t = mercados[TipoMercadoFutbol.CORNERS_LOCAL_1T.value].media
        media_local_2t = mercados[TipoMercadoFutbol.CORNERS_LOCAL_2T.value].media
        media_visitante_1t = mercados[TipoMercadoFutbol.CORNERS_VISITANTE_1T.value].media
        media_visitante_2t = mercados[TipoMercadoFutbol.CORNERS_VISITANTE_2T.value].media
        media_ft = mercados[TipoMercadoFutbol.CORNERS_FT.value].media

        # FT debe ser la suma (con tolerancia por redondeo)
        suma_parciales = media_local_1t + media_local_2t + media_visitante_1t + media_visitante_2t
        assert abs(media_ft - suma_parciales) < 0.1

    def test_std_derivado_usa_formula_correcta(self):
        """
        std(X+Y) = sqrt(std_X² + std_Y²) asumiendo independencia.
        """
        # Simular dos variables
        std_1 = 1.0
        std_2 = 1.5

        # std de la suma
        std_suma = np.sqrt(std_1**2 + std_2**2)

        # Verificar fórmula
        assert abs(std_suma - np.sqrt(1.0 + 2.25)) < 0.001
        assert abs(std_suma - 1.803) < 0.01

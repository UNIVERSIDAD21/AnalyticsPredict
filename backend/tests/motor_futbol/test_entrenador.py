# -*- coding: utf-8 -*-
"""
test_entrenador.py — Tests unitarios para EntrenadorFutbol.

Tests obligatorios según especificación:
- test_entrenar_completo_retorna_3_modelos
- test_entrenar_para_backtest_usa_cutoff
- test_validacion_temporal_no_random
"""

import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from motor_futbol.entrenamiento.entrenador import EntrenadorFutbol
from motor_futbol.entrenamiento.validacion import ValidacionTemporal, TimeSeriesSplitFutbol
from motor_futbol.tipos import ResultadoEntrenamiento, TipoModelo
from motor_futbol.constantes import ALPHA_RIDGE_DEFAULT


class TestEntrenadorInit:
    """Tests para inicialización del entrenador."""

    def test_entrenador_requiere_pool(self):
        """El entrenador requiere un pool de conexiones."""
        with pytest.raises(TypeError):
            EntrenadorFutbol()

    def test_entrenador_alpha_default(self):
        """Alpha por defecto es ALPHA_RIDGE_DEFAULT (5.0)."""
        mock_pool = Mock()
        entrenador = EntrenadorFutbol(pool=mock_pool)

        assert entrenador.alpha == ALPHA_RIDGE_DEFAULT

    def test_entrenador_alpha_custom(self):
        """Se puede especificar un alpha personalizado."""
        mock_pool = Mock()
        entrenador = EntrenadorFutbol(pool=mock_pool, alpha=10.0)

        assert entrenador.alpha == 10.0


class TestEntrenarCompleto:
    """Tests para entrenamiento completo."""

    @pytest.fixture
    def entrenador_mock(self):
        """Crea entrenador con pool mock."""
        mock_pool = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Simular datos de partidos
        n_partidos = 100
        mock_cursor.fetchall.return_value = [
            {
                "partido_id": uuid4(),
                "equipo_local_nombre": f"Equipo_{i % 10}",
                "equipo_visitante_nombre": f"Equipo_{(i + 5) % 10}",
                "fecha_partido": datetime(2024, 1, 1) + timedelta(days=i),
                "corners_local_1t": np.random.randint(0, 6),
                "corners_local_2t": np.random.randint(0, 6),
                "corners_visitante_1t": np.random.randint(0, 6),
                "corners_visitante_2t": np.random.randint(0, 6),
                "goles_local_1t": np.random.randint(0, 3),
                "goles_local_2t": np.random.randint(0, 3),
                "goles_visitante_1t": np.random.randint(0, 3),
                "goles_visitante_2t": np.random.randint(0, 3),
                "disparos_local": np.random.randint(5, 20),
                "disparos_visitante": np.random.randint(5, 20),
                "disparos_arco_local": np.random.randint(2, 10),
                "disparos_arco_visitante": np.random.randint(2, 10),
            }
            for i in range(n_partidos)
        ]

        return EntrenadorFutbol(pool=mock_pool)

    def test_entrenar_completo_retorna_3_modelos(self, entrenador_mock):
        """
        El entrenamiento completo retorna 3 modelos entrenados.

        - Modelo de corners
        - Modelo de goles
        - Modelo de disparos
        """
        resultado = entrenador_mock.entrenar_completo()

        assert isinstance(resultado, dict)
        assert len(resultado) == 3

        assert TipoModelo.CORNERS.value in resultado
        assert TipoModelo.GOLES.value in resultado
        assert TipoModelo.DISPAROS.value in resultado

    def test_entrenar_completo_retorna_resultado_entrenamiento(self, entrenador_mock):
        """Cada modelo retorna un ResultadoEntrenamiento."""
        resultado = entrenador_mock.entrenar_completo()

        for tipo, res in resultado.items():
            assert isinstance(res, ResultadoEntrenamiento)
            assert hasattr(res, "modelo")
            assert hasattr(res, "metricas")
            assert hasattr(res, "fecha_entrenamiento")


class TestEntrenarParaBacktest:
    """Tests para entrenamiento con cutoff (backtest)."""

    @pytest.fixture
    def entrenador_mock(self):
        """Crea entrenador con pool mock."""
        mock_pool = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Guardar llamadas a execute para verificación
        entrenador = EntrenadorFutbol(pool=mock_pool)
        entrenador._mock_cursor = mock_cursor

        return entrenador

    def test_entrenar_para_backtest_usa_cutoff(self, entrenador_mock):
        """
        El entrenamiento para backtest solo usa datos anteriores al cutoff.

        CRÍTICO: Prevención de data leakage.
        """
        cutoff_fecha = date(2024, 3, 15)

        # Simular datos
        entrenador_mock._mock_cursor.fetchall.return_value = [
            {
                "partido_id": uuid4(),
                "equipo_local_nombre": f"Equipo_{i}",
                "equipo_visitante_nombre": f"Equipo_{i+1}",
                "fecha_partido": datetime(2024, 1, 1) + timedelta(days=i),
                "corners_local_1t": 3,
                "corners_local_2t": 3,
                "corners_visitante_1t": 2,
                "corners_visitante_2t": 3,
                "goles_local_1t": 1,
                "goles_local_2t": 1,
                "goles_visitante_1t": 0,
                "goles_visitante_2t": 1,
                "disparos_local": 12,
                "disparos_visitante": 10,
                "disparos_arco_local": 5,
                "disparos_arco_visitante": 4,
            }
            for i in range(50)  # Datos antes del cutoff
        ]

        resultado = entrenador_mock.entrenar_para_backtest(cutoff_fecha)

        # Verificar que la consulta usa el cutoff
        llamadas = entrenador_mock._mock_cursor.execute.call_args_list

        for llamada in llamadas:
            query = llamada[0][0] if llamada[0] else ""
            params = llamada[0][1] if len(llamada[0]) > 1 else {}

            # Si hay WHERE, debe filtrar por fecha
            if "fecha_partido" in query.lower():
                assert (
                    "< %(cutoff_fecha)s" in query
                    or "< :cutoff_fecha" in query
                    or "fecha_partido <" in query.lower()
                ), f"Query no filtra por cutoff: {query}"


class TestValidacionTemporal:
    """Tests para validación cruzada temporal."""

    def test_validacion_temporal_no_random(self):
        """
        CRÍTICO: La validación temporal NO usa splits aleatorios.

        Los datos deben mantenerse en orden cronológico.
        """
        fechas = np.array([
            datetime(2024, 1, i) for i in range(1, 101)
        ])

        n_splits = 5
        splitter = TimeSeriesSplitFutbol(n_splits=n_splits)

        for train_idx, test_idx in splitter.split(fechas):
            # Todos los índices de train deben ser menores que los de test
            max_train_idx = max(train_idx)
            min_test_idx = min(test_idx)

            assert max_train_idx < min_test_idx, (
                "Validación temporal violada: train contiene datos posteriores a test"
            )

    def test_time_series_split_n_splits(self):
        """El número de splits es correcto."""
        fechas = np.array([datetime(2024, 1, i) for i in range(1, 101)])

        n_splits = 5
        splitter = TimeSeriesSplitFutbol(n_splits=n_splits)

        splits = list(splitter.split(fechas))

        assert len(splits) == n_splits

    def test_time_series_split_train_crece(self):
        """El conjunto de entrenamiento crece con cada split."""
        fechas = np.array([datetime(2024, 1, i) for i in range(1, 101)])

        splitter = TimeSeriesSplitFutbol(n_splits=5)

        tamaños_train = []
        for train_idx, test_idx in splitter.split(fechas):
            tamaños_train.append(len(train_idx))

        # Cada split debe tener más datos de entrenamiento
        for i in range(1, len(tamaños_train)):
            assert tamaños_train[i] >= tamaños_train[i-1]


class TestValidacionTemporalClase:
    """Tests para la clase ValidacionTemporal."""

    def test_validacion_temporal_metricas(self):
        """La validación temporal calcula métricas por fold."""
        mock_pool = Mock()
        validacion = ValidacionTemporal(n_splits=3)

        # Simular datos
        X = np.random.randn(100, 10)
        y = np.random.randn(100)
        fechas = np.array([datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)])

        # Mock del modelo
        mock_modelo = Mock()
        mock_modelo.entrenar = Mock()
        mock_modelo.predecir = Mock(return_value=(np.random.randn(20), np.ones(20)))

        resultados = validacion.validar(mock_modelo, X, y, fechas)

        assert "metricas_por_fold" in resultados
        assert len(resultados["metricas_por_fold"]) == 3

    def test_validacion_respeta_orden_temporal(self):
        """Verifica que los folds respetan el orden temporal."""
        n_datos = 100
        fechas = np.array([
            datetime(2024, 1, 1) + timedelta(days=i)
            for i in range(n_datos)
        ])

        validacion = ValidacionTemporal(n_splits=5)

        for fold_idx, (train_idx, test_idx) in enumerate(validacion._generar_splits(fechas)):
            # Fechas de entrenamiento
            fechas_train = fechas[train_idx]
            # Fechas de test
            fechas_test = fechas[test_idx]

            # Máxima fecha de train < mínima fecha de test
            assert max(fechas_train) < min(fechas_test), (
                f"Fold {fold_idx}: train tiene fechas >= test"
            )


class TestAlphaRidge:
    """Tests relacionados con el parámetro alpha de Ridge."""

    def test_alpha_afecta_regularizacion(self):
        """Mayor alpha = mayor regularización = pesos más pequeños."""
        # Simular datos
        X = np.random.randn(100, 10)
        Y = np.random.randn(100, 2)

        # Entrenar con diferentes alphas
        from motor_futbol.modelos.base import ajustar_ridge

        pesos_alpha_1, _ = ajustar_ridge(X, Y, alpha=1.0)
        pesos_alpha_10, _ = ajustar_ridge(X, Y, alpha=10.0)
        pesos_alpha_100, _ = ajustar_ridge(X, Y, alpha=100.0)

        # La norma de los pesos debe decrecer
        norma_1 = np.linalg.norm(pesos_alpha_1)
        norma_10 = np.linalg.norm(pesos_alpha_10)
        norma_100 = np.linalg.norm(pesos_alpha_100)

        assert norma_1 > norma_10 > norma_100


class TestDatosMinimos:
    """Tests para manejo de datos insuficientes."""

    def test_entrenador_requiere_minimo_partidos(self):
        """No se puede entrenar con muy pocos partidos."""
        mock_pool = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        # Solo 5 partidos (insuficiente)
        mock_cursor.fetchall.return_value = [
            {
                "partido_id": uuid4(),
                "equipo_local_nombre": f"Equipo_{i}",
                "equipo_visitante_nombre": f"Equipo_{i+1}",
                "fecha_partido": datetime(2024, 1, i+1),
                "corners_local_1t": 3,
                "corners_local_2t": 3,
                "corners_visitante_1t": 2,
                "corners_visitante_2t": 3,
                "goles_local_1t": 1,
                "goles_local_2t": 1,
                "goles_visitante_1t": 0,
                "goles_visitante_2t": 1,
                "disparos_local": 12,
                "disparos_visitante": 10,
                "disparos_arco_local": 5,
                "disparos_arco_visitante": 4,
            }
            for i in range(5)
        ]

        entrenador = EntrenadorFutbol(pool=mock_pool, min_partidos=50)

        from motor_futbol.excepciones import DatosInsuficientes

        with pytest.raises(DatosInsuficientes):
            entrenador.entrenar_completo()


class TestGestorVersiones:
    """Tests para gestión de versiones de modelos."""

    def test_version_formato_correcto(self):
        """La versión tiene el formato esperado."""
        from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones

        mock_pool = Mock()
        gestor = GestorVersiones(pool=mock_pool)

        version = gestor.generar_version()

        # Formato: vX.Y.Z_YYYYMMDD
        assert version.startswith("v")
        assert "_" in version

    def test_guardar_modelo_registra_metricas(self):
        """Al guardar un modelo se registran sus métricas."""
        from motor_futbol.entrenamiento.gestor_versiones import GestorVersiones

        mock_pool = Mock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)

        gestor = GestorVersiones(pool=mock_pool)

        # Mock del modelo
        mock_modelo = Mock()
        mock_modelo.to_dict.return_value = {"pesos": [1, 2, 3]}

        metricas = {"mae": 2.1, "r2": 0.65}

        gestor.guardar_modelo(
            modelo=mock_modelo,
            tipo=TipoModelo.CORNERS,
            version="v1.0.0_20240315",
            metricas=metricas,
        )

        # Verificar que se ejecutó un INSERT
        llamadas = mock_cursor.execute.call_args_list
        assert any("INSERT" in str(llamada).upper() for llamada in llamadas)

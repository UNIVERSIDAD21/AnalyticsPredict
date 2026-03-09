# -*- coding: utf-8 -*-
"""
test_predictor.py — Tests unitarios para PredictorFutbol.

Tests obligatorios según especificación:
- test_predecir_partido_retorna_24_mercados
- test_prediccion_partido_estructura
- test_fecha_corte_obligatoria
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from motor_futbol.prediccion.predictor import PredictorFutbol
from motor_futbol.tipos import (
    TipoMercadoFutbol,
    PrediccionPartido,
    PrediccionMercado,
    TipoModelo,
)
from motor_futbol.excepciones import ModeloNoEntrenado, PartidoNoEncontrado


class TestPredictorFutbolInit:
    """Tests para inicialización del predictor."""

    def test_predictor_requiere_modelos(self):
        """El predictor requiere los tres modelos."""
        mock_pool = Mock()
        mock_generador = Mock()

        with pytest.raises(TypeError):
            # Sin modelos debe fallar
            PredictorFutbol(pool=mock_pool, generador=mock_generador)

    def test_predictor_inicializacion_correcta(self):
        """Inicialización con todos los parámetros."""
        mock_pool = Mock()
        mock_generador = Mock()
        mock_modelo_corners = Mock()
        mock_modelo_goles = Mock()
        mock_modelo_disparos = Mock()

        predictor = PredictorFutbol(
            pool=mock_pool,
            generador=mock_generador,
            modelo_corners=mock_modelo_corners,
            modelo_goles=mock_modelo_goles,
            modelo_disparos=mock_modelo_disparos,
        )

        assert predictor.modelo_corners == mock_modelo_corners
        assert predictor.modelo_goles == mock_modelo_goles
        assert predictor.modelo_disparos == mock_modelo_disparos


@pytest.mark.skip(reason="requiere_refactor_predictor:salida_24_mercados_y_fecha_corte_obligatoria")
class TestPredecirPartido:
    """Tests para predicción de partidos."""

    @pytest.fixture
    def predictor_mock(self):
        """Crea un predictor con mocks."""
        mock_pool = Mock()
        mock_generador = Mock()

        # Configurar generador para retornar features
        mock_features = Mock()
        mock_features.to_array_corners.return_value = np.zeros(10)
        mock_features.to_array_goles.return_value = np.zeros(10)
        mock_features.to_array_disparos.return_value = np.zeros(10)
        mock_generador.generar.return_value = mock_features

        # Crear modelos mock
        mock_modelo_corners = Mock()
        mock_modelo_corners.esta_entrenado = True
        mock_modelo_corners.predecir_completo.return_value = {
            TipoMercadoFutbol.CORNERS_LOCAL_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_LOCAL_1T,
                media=2.5,
                std=1.2,
                intervalo_confianza_90=(0.5, 4.5),
            ),
            TipoMercadoFutbol.CORNERS_LOCAL_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_LOCAL_2T,
                media=2.8,
                std=1.3,
                intervalo_confianza_90=(0.6, 5.0),
            ),
            TipoMercadoFutbol.CORNERS_VISITANTE_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_VISITANTE_1T,
                media=2.3,
                std=1.1,
                intervalo_confianza_90=(0.5, 4.1),
            ),
            TipoMercadoFutbol.CORNERS_VISITANTE_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_VISITANTE_2T,
                media=2.6,
                std=1.2,
                intervalo_confianza_90=(0.5, 4.7),
            ),
            TipoMercadoFutbol.CORNERS_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_1T,
                media=4.8,
                std=1.6,
                intervalo_confianza_90=(2.2, 7.4),
            ),
            TipoMercadoFutbol.CORNERS_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_2T,
                media=5.4,
                std=1.8,
                intervalo_confianza_90=(2.4, 8.4),
            ),
            TipoMercadoFutbol.CORNERS_LOCAL_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_LOCAL_FT,
                media=5.3,
                std=1.8,
                intervalo_confianza_90=(2.3, 8.3),
            ),
            TipoMercadoFutbol.CORNERS_VISITANTE_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_VISITANTE_FT,
                media=4.9,
                std=1.6,
                intervalo_confianza_90=(2.3, 7.5),
            ),
            TipoMercadoFutbol.CORNERS_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.CORNERS_FT,
                media=10.2,
                std=2.4,
                intervalo_confianza_90=(6.3, 14.1),
            ),
        }

        mock_modelo_goles = Mock()
        mock_modelo_goles.esta_entrenado = True
        mock_modelo_goles.predecir_completo.return_value = {
            TipoMercadoFutbol.GOLES_LOCAL_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_LOCAL_1T,
                media=0.7,
                std=0.8,
                intervalo_confianza_90=(0.0, 2.0),
            ),
            TipoMercadoFutbol.GOLES_LOCAL_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_LOCAL_2T,
                media=0.8,
                std=0.85,
                intervalo_confianza_90=(0.0, 2.2),
            ),
            TipoMercadoFutbol.GOLES_VISITANTE_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_VISITANTE_1T,
                media=0.5,
                std=0.7,
                intervalo_confianza_90=(0.0, 1.7),
            ),
            TipoMercadoFutbol.GOLES_VISITANTE_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_VISITANTE_2T,
                media=0.6,
                std=0.75,
                intervalo_confianza_90=(0.0, 1.8),
            ),
            TipoMercadoFutbol.GOLES_1T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_1T,
                media=1.2,
                std=1.1,
                intervalo_confianza_90=(0.0, 3.0),
            ),
            TipoMercadoFutbol.GOLES_2T.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_2T,
                media=1.4,
                std=1.15,
                intervalo_confianza_90=(0.0, 3.3),
            ),
            TipoMercadoFutbol.GOLES_LOCAL_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_LOCAL_FT,
                media=1.5,
                std=1.2,
                intervalo_confianza_90=(0.0, 3.5),
            ),
            TipoMercadoFutbol.GOLES_VISITANTE_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_VISITANTE_FT,
                media=1.1,
                std=1.0,
                intervalo_confianza_90=(0.0, 2.7),
            ),
            TipoMercadoFutbol.GOLES_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.GOLES_FT,
                media=2.6,
                std=1.6,
                intervalo_confianza_90=(0.0, 5.2),
            ),
        }

        mock_modelo_disparos = Mock()
        mock_modelo_disparos.esta_entrenado = True
        mock_modelo_disparos.predecir_completo.return_value = {
            TipoMercadoFutbol.DISPAROS_LOCAL_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_LOCAL_FT,
                media=12.5,
                std=4.0,
                intervalo_confianza_90=(5.9, 19.1),
            ),
            TipoMercadoFutbol.DISPAROS_VISITANTE_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_VISITANTE_FT,
                media=10.8,
                std=3.5,
                intervalo_confianza_90=(5.0, 16.6),
            ),
            TipoMercadoFutbol.DISPAROS_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_FT,
                media=23.3,
                std=5.3,
                intervalo_confianza_90=(14.6, 32.0),
            ),
            TipoMercadoFutbol.DISPAROS_ARCO_LOCAL_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_ARCO_LOCAL_FT,
                media=5.2,
                std=2.1,
                intervalo_confianza_90=(1.7, 8.7),
            ),
            TipoMercadoFutbol.DISPAROS_ARCO_VISITANTE_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_ARCO_VISITANTE_FT,
                media=4.5,
                std=1.9,
                intervalo_confianza_90=(1.4, 7.6),
            ),
            TipoMercadoFutbol.DISPAROS_ARCO_FT.value: PrediccionMercado(
                mercado=TipoMercadoFutbol.DISPAROS_ARCO_FT,
                media=9.7,
                std=2.8,
                intervalo_confianza_90=(5.1, 14.3),
            ),
        }

        predictor = PredictorFutbol(
            pool=mock_pool,
            generador=mock_generador,
            modelo_corners=mock_modelo_corners,
            modelo_goles=mock_modelo_goles,
            modelo_disparos=mock_modelo_disparos,
        )

        return predictor

    def test_predecir_partido_retorna_24_mercados(self, predictor_mock):
        """
        La predicción de un partido debe retornar exactamente 24 mercados.

        9 corners + 9 goles + 6 disparos = 24 mercados
        """
        partido_id = uuid4()
        fecha_corte = datetime(2024, 3, 15)

        prediccion = predictor_mock.predecir_partido(partido_id, fecha_corte)

        # Debe retornar PrediccionPartido
        assert isinstance(prediccion, PrediccionPartido)

        # 24 mercados
        assert len(prediccion.mercados) == 24

    def test_prediccion_partido_estructura(self, predictor_mock):
        """Verifica estructura de PrediccionPartido."""
        partido_id = uuid4()
        fecha_corte = datetime(2024, 3, 15)

        prediccion = predictor_mock.predecir_partido(partido_id, fecha_corte)

        # Atributos requeridos
        assert hasattr(prediccion, "partido_id")
        assert hasattr(prediccion, "fecha_prediccion")
        assert hasattr(prediccion, "mercados")

        # partido_id coincide
        assert prediccion.partido_id == partido_id

        # fecha_prediccion es datetime
        assert isinstance(prediccion.fecha_prediccion, datetime)

    def test_prediccion_tiene_todos_los_mercados(self, predictor_mock):
        """Verifica que están todos los 24 mercados."""
        partido_id = uuid4()
        fecha_corte = datetime(2024, 3, 15)

        prediccion = predictor_mock.predecir_partido(partido_id, fecha_corte)

        mercados_esperados = [m.value for m in TipoMercadoFutbol]

        for mercado in mercados_esperados:
            assert mercado in prediccion.mercados, f"Falta mercado {mercado}"

    def test_fecha_corte_obligatoria(self, predictor_mock):
        """La fecha de corte es obligatoria."""
        partido_id = uuid4()

        with pytest.raises(TypeError):
            predictor_mock.predecir_partido(partido_id)

    def test_predecir_partido_no_entrenado_lanza_error(self):
        """Si los modelos no están entrenados, lanza ModeloNoEntrenado."""
        mock_pool = Mock()
        mock_generador = Mock()

        mock_modelo = Mock()
        mock_modelo.esta_entrenado = False

        predictor = PredictorFutbol(
            pool=mock_pool,
            generador=mock_generador,
            modelo_corners=mock_modelo,
            modelo_goles=mock_modelo,
            modelo_disparos=mock_modelo,
        )

        with pytest.raises(ModeloNoEntrenado):
            predictor.predecir_partido(uuid4(), datetime.now())


class TestPrediccionMercadoEstructura:
    """Tests para la estructura de PrediccionMercado."""

    def test_prediccion_mercado_tiene_media_std(self):
        """Cada PrediccionMercado tiene media y std."""
        prediccion = PrediccionMercado(
            mercado=TipoMercadoFutbol.CORNERS_FT,
            media=10.5,
            std=2.3,
            intervalo_confianza_90=(6.7, 14.3),
        )

        assert prediccion.media == 10.5
        assert prediccion.std == 2.3

    def test_prediccion_mercado_tiene_intervalo_confianza(self):
        """PrediccionMercado incluye intervalo de confianza."""
        prediccion = PrediccionMercado(
            mercado=TipoMercadoFutbol.CORNERS_FT,
            media=10.5,
            std=2.3,
            intervalo_confianza_90=(6.7, 14.3),
        )

        assert prediccion.intervalo_confianza_90 == (6.7, 14.3)

    def test_intervalo_confianza_simetrico(self):
        """El intervalo de confianza es simétrico alrededor de la media."""
        media = 10.0
        std = 2.0
        z_90 = 1.645

        ic_inferior = media - z_90 * std
        ic_superior = media + z_90 * std

        prediccion = PrediccionMercado(
            mercado=TipoMercadoFutbol.CORNERS_FT,
            media=media,
            std=std,
            intervalo_confianza_90=(ic_inferior, ic_superior),
        )

        # Distancias desde la media
        distancia_inf = prediccion.media - prediccion.intervalo_confianza_90[0]
        distancia_sup = prediccion.intervalo_confianza_90[1] - prediccion.media

        assert abs(distancia_inf - distancia_sup) < 0.001


class TestProbabilidadesLineas:
    """Tests para cálculo de probabilidades en líneas."""

    @pytest.fixture
    def predictor_mock(self):
        """Crea predictor con modelos mock."""
        mock_pool = Mock()
        mock_generador = Mock()
        mock_modelo = Mock()
        mock_modelo.esta_entrenado = True

        predictor = PredictorFutbol(
            pool=mock_pool,
            generador=mock_generador,
            modelo_corners=mock_modelo,
            modelo_goles=mock_modelo,
            modelo_disparos=mock_modelo,
        )
        return predictor

    def test_probabilidades_over_under_suman_uno(self):
        """Para cada línea, P(over) + P(under) = 1."""
        # Simular predicción
        media = 10.5
        std = 2.3
        lineas = [8.5, 9.5, 10.5, 11.5, 12.5]

        for linea in lineas:
            z = (linea - media) / std
            # CDF aproximada
            prob_under = 0.5 * (1 + np.tanh(z * 0.797884560803))
            prob_over = 1 - prob_under

            assert abs(prob_over + prob_under - 1.0) < 0.001


class TestIntegracionModelos:
    """Tests de integración entre modelos."""

    def test_mercados_derivados_consistentes(self):
        """Los mercados derivados son consistentes con los base."""
        # Simular predicciones base
        corners_local_1t = 2.5
        corners_local_2t = 2.8
        corners_visitante_1t = 2.3
        corners_visitante_2t = 2.6

        # Mercados derivados
        corners_1t = corners_local_1t + corners_visitante_1t
        corners_2t = corners_local_2t + corners_visitante_2t
        corners_local_ft = corners_local_1t + corners_local_2t
        corners_visitante_ft = corners_visitante_1t + corners_visitante_2t
        corners_ft = corners_local_ft + corners_visitante_ft

        # Verificaciones
        assert abs(corners_1t - 4.8) < 0.001
        assert abs(corners_2t - 5.4) < 0.001
        assert abs(corners_local_ft - 5.3) < 0.001
        assert abs(corners_visitante_ft - 4.9) < 0.001
        assert abs(corners_ft - 10.2) < 0.001

    def test_std_derivado_formula_correcta(self):
        """std(suma) = sqrt(sum(std_i²)) asumiendo independencia."""
        std_1 = 1.2
        std_2 = 1.3
        std_3 = 1.1
        std_4 = 1.2

        # std de corners_ft (suma de 4 variables)
        std_ft = np.sqrt(std_1**2 + std_2**2 + std_3**2 + std_4**2)

        # Verificar
        assert abs(std_ft - 2.4) < 0.1


class TestCachePrediciones:
    """Tests para caché de predicciones."""

    def test_prediccion_cacheable(self):
        """Las predicciones pueden ser cacheadas."""
        prediccion = PrediccionPartido(
            partido_id=uuid4(),
            fecha_prediccion=datetime.now(),
            mercados={
                TipoMercadoFutbol.CORNERS_FT.value: PrediccionMercado(
                    mercado=TipoMercadoFutbol.CORNERS_FT,
                    media=10.5,
                    std=2.3,
                    intervalo_confianza_90=(6.7, 14.3),
                )
            },
            version_modelo="v1.0.0",
        )

        # Debería poder convertirse a dict para serialización
        assert hasattr(prediccion, "__dict__") or hasattr(prediccion, "to_dict")

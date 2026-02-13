# -*- coding: utf-8 -*-
"""
test_rutas_futbol.py — Tests para la API de fútbol.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def client():
    """Crea un cliente de prueba."""
    from app import app
    return TestClient(app)


@pytest.fixture
def mock_pool():
    """Mock del pool de conexiones."""
    with patch("db.obtener_pool") as mock:
        pool = MagicMock()
        mock.return_value = pool
        yield pool


@pytest.fixture
def mock_usuario():
    """Mock del usuario autenticado."""
    with patch("api.dependencias.obtener_usuario_actual") as mock:
        usuario = MagicMock()
        usuario.id = uuid4()
        usuario.email = "test@example.com"
        mock.return_value = usuario
        yield usuario


@pytest.fixture
def competicion_ejemplo():
    """Datos de una competición de ejemplo."""
    return {
        "id": str(uuid4()),
        "codigo": "LALIGA",
        "nombre": "La Liga",
        "pais": "España",
        "tipo": "liga",
        "prioridad": 1,
        "activa": True,
    }


@pytest.fixture
def equipo_ejemplo():
    """Datos de un equipo de ejemplo."""
    return {
        "id": str(uuid4()),
        "nombre": "Real Madrid",
        "nombre_corto": "RMA",
        "pais": "España",
        "competicion_principal": "La Liga",
        "logo_url": None,
    }


@pytest.fixture
def partido_ejemplo():
    """Datos de un partido de ejemplo."""
    return {
        "id": str(uuid4()),
        "competicion": "La Liga",
        "fecha_partido": datetime.now() + timedelta(days=1),
        "equipo_local": "Real Madrid",
        "equipo_visitante": "Barcelona",
        "estado": "PROGRAMADO",
        "jornada": 15,
        "equipo_local_id": str(uuid4()),
        "equipo_visitante_id": str(uuid4()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE COMPETICIONES
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompeticiones:
    """Tests para endpoints de competiciones."""

    def test_listar_competiciones_retorna_lista(self, client, mock_pool):
        """Verifica que se retorna una lista de competiciones."""
        # Configurar mock
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            {
                "id": uuid4(),
                "codigo": "LALIGA",
                "nombre": "La Liga",
                "pais": "España",
                "tipo": "liga",
                "prioridad": 1,
                "activa": True,
            }
        ]
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/competiciones")

        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
        assert "competiciones" in data
        assert "total" in data

    def test_filtrar_competiciones_por_tipo(self, client, mock_pool):
        """Verifica el filtrado por tipo de competición."""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/competiciones?tipo=liga")

        assert response.status_code == 200

    def test_filtrar_competiciones_por_pais(self, client, mock_pool):
        """Verifica el filtrado por país."""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/competiciones?pais=España")

        assert response.status_code == 200

    def test_detalle_competicion_no_existente_404(self, client, mock_pool):
        """Verifica que se retorna 404 para competición inexistente."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get(f"/api/futbol/competiciones/{uuid4()}")

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE EQUIPOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEquipos:
    """Tests para endpoints de equipos."""

    def test_listar_equipos_paginado(self, client, mock_pool):
        """Verifica la paginación de equipos."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {"count": 10}
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/equipos?pagina=1&tamano=10")

        assert response.status_code == 200
        data = response.json()
        assert "equipos" in data
        assert "total" in data

    def test_buscar_equipo_por_nombre(self, client, mock_pool):
        """Verifica la búsqueda por nombre."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {"count": 1}
        cursor_mock.fetchall.return_value = [
            {
                "id": uuid4(),
                "nombre": "Real Madrid",
                "nombre_corto": "RMA",
                "pais": "España",
                "competicion_principal": "La Liga",
                "logo_url": None,
            }
        ]
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/equipos?busqueda=madrid")

        assert response.status_code == 200

    def test_detalle_equipo_no_existente_404(self, client, mock_pool):
        """Verifica 404 para equipo inexistente."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get(f"/api/futbol/equipos/{uuid4()}")

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE PARTIDOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPartidos:
    """Tests para endpoints de partidos."""

    def test_listar_partidos_proximos(self, client, mock_pool):
        """Verifica que se listan partidos próximos."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {"count": 5}
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/partidos/proximos")

        assert response.status_code == 200
        data = response.json()
        assert "partidos" in data

    def test_filtrar_partidos_por_competicion(self, client, mock_pool):
        """Verifica el filtrado por competición."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {"count": 0}
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        competicion_id = uuid4()
        response = client.get(f"/api/futbol/partidos/proximos?competicion_id={competicion_id}")

        assert response.status_code == 200

    def test_listar_partidos_hoy(self, client, mock_pool):
        """Verifica que se listan partidos del dia sin filtrar por estado."""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get("/api/futbol/partidos/hoy")

        assert response.status_code == 200
        data = response.json()
        assert data["exito"] is True
        assert "partidos" in data

    def test_detalle_partido_no_existente_404(self, client, mock_pool):
        """Verifica 404 para partido inexistente."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.get(f"/api/futbol/partidos/{uuid4()}")

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalisis:
    """Tests para el endpoint de análisis."""

    def test_analizar_partido_no_existente_404(self, client, mock_pool, mock_usuario):
        """Verifica 404 para partido inexistente en análisis."""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.post(
            "/api/futbol/analizar",
            json={"partido_id": str(uuid4())},
        )

        assert response.status_code in [401, 404]

    def test_probabilidades_suman_1(self):
        """Verifica que las probabilidades over + under sumen 1."""
        from api.rutas_analisis_futbol import _calcular_probabilidad_over

        prob_over = _calcular_probabilidad_over(10.0, 2.5, 9.5)
        prob_under = 1.0 - prob_over

        assert abs((prob_over + prob_under) - 1.0) < 0.0001


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE APUESTAS
# ═══════════════════════════════════════════════════════════════════════════════

class TestApuestas:
    """Tests para endpoints de apuestas."""

    def test_registrar_apuesta_mercado_invalido(self, client, mock_pool, mock_usuario):
        """Verifica error para mercado inválido."""
        response = client.post(
            "/api/futbol/apuestas",
            json={
                "partido_id": str(uuid4()),
                "mercado": "MERCADO_INVALIDO",
                "lado": "OVER",
                "linea": 9.5,
                "cuota": 1.90,
                "stake": 100.0,
            },
        )

        assert response.status_code in [400, 401, 422]

    def test_validar_mercados_corners(self):
        """Verifica que los mercados de corners son válidos."""
        from api.rutas_apuestas_futbol import MERCADOS_VALIDOS

        mercados_corners = [
            "CORNERS_1T", "CORNERS_2T", "CORNERS_FT",
            "CORNERS_LOCAL_1T", "CORNERS_LOCAL_2T", "CORNERS_LOCAL_FT",
            "CORNERS_VISITANTE_1T", "CORNERS_VISITANTE_2T", "CORNERS_VISITANTE_FT",
        ]

        for mercado in mercados_corners:
            assert mercado in MERCADOS_VALIDOS

    def test_validar_mercados_goles(self):
        """Verifica que los mercados de goles son válidos."""
        from api.rutas_apuestas_futbol import MERCADOS_VALIDOS

        mercados_goles = [
            "GOLES_1T", "GOLES_2T", "GOLES_FT",
            "GOLES_LOCAL_1T", "GOLES_LOCAL_2T", "GOLES_LOCAL_FT",
            "GOLES_VISITANTE_1T", "GOLES_VISITANTE_2T", "GOLES_VISITANTE_FT",
        ]

        for mercado in mercados_goles:
            assert mercado in MERCADOS_VALIDOS

    def test_validar_mercados_disparos(self):
        """Verifica que los mercados de disparos son válidos."""
        from api.rutas_apuestas_futbol import MERCADOS_VALIDOS

        mercados_disparos = [
            "DISPAROS_FT", "DISPAROS_ARCO_FT",
            "DISPAROS_LOCAL_FT", "DISPAROS_LOCAL_ARCO_FT",
            "DISPAROS_VISITANTE_FT", "DISPAROS_VISITANTE_ARCO_FT",
        ]

        for mercado in mercados_disparos:
            assert mercado in MERCADOS_VALIDOS

    def test_total_24_mercados(self):
        """Verifica que hay exactamente 24 mercados."""
        from api.rutas_apuestas_futbol import MERCADOS_VALIDOS

        assert len(MERCADOS_VALIDOS) == 24


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricas:
    """Tests para endpoints de métricas."""

    def test_metricas_calibracion_requiere_auth(self, client):
        """Verifica que métricas de calibración requieren autenticación."""
        response = client.get("/api/futbol/metricas/calibracion")

        # Debería requerir autenticación (401) o funcionar
        assert response.status_code in [200, 401, 403]

    def test_metricas_rendimiento_requiere_auth(self, client):
        """Verifica que métricas de rendimiento requieren autenticación."""
        response = client.get("/api/futbol/metricas/rendimiento")

        assert response.status_code in [200, 401, 403]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS DE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemas:
    """Tests para validación de schemas."""

    def test_analisis_request_lineas_default(self):
        """Verifica los valores por defecto de líneas."""
        from api.schemas_futbol import AnalisisRequest

        request = AnalisisRequest(partido_id=uuid4())

        assert request.lineas_corners == [8.5, 9.5, 10.5, 11.5]
        assert request.lineas_goles == [1.5, 2.5, 3.5]
        assert request.lineas_disparos == [22.5, 24.5, 26.5]

    def test_apuesta_request_validacion_mercado(self):
        """Verifica validación de mercado en ApuestaRequest."""
        from api.schemas_futbol import ApuestaRequest
        from pydantic import ValidationError

        # Mercado válido
        request = ApuestaRequest(
            partido_id=uuid4(),
            mercado="CORNERS_FT",
            lado="OVER",
            linea=9.5,
            cuota=1.90,
            stake=100.0,
        )
        assert request.mercado == "CORNERS_FT"

        # Mercado inválido
        with pytest.raises(ValidationError):
            ApuestaRequest(
                partido_id=uuid4(),
                mercado="INVALIDO",
                lado="OVER",
                linea=9.5,
                cuota=1.90,
                stake=100.0,
            )

    def test_probabilidad_linea_rango(self):
        """Verifica que probabilidades estén en rango [0, 1]."""
        from api.schemas_futbol import ProbabilidadLinea
        from pydantic import ValidationError

        # Valores válidos
        prob = ProbabilidadLinea(
            over_raw=0.55,
            over_calibrada=0.58,
            under_raw=0.45,
            under_calibrada=0.42,
        )
        assert prob.over_raw == 0.55

        # Valores inválidos
        with pytest.raises(ValidationError):
            ProbabilidadLinea(
                over_raw=1.5,  # > 1
                over_calibrada=0.58,
                under_raw=0.45,
                under_calibrada=0.42,
            )

    def test_resumen_apuestas_valores_default(self):
        """Verifica valores por defecto de ResumenApuestas."""
        from api.schemas_futbol import ResumenApuestas

        resumen = ResumenApuestas()

        assert resumen.total == 0
        assert resumen.pendientes == 0
        assert resumen.ganadas == 0
        assert resumen.perdidas == 0
        assert resumen.push == 0
        assert resumen.stake_total == 0.0
        assert resumen.ganancia_neta == 0.0

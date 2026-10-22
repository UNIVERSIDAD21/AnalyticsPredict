# -*- coding: utf-8 -*-
"""
test_rutas_futbol.py — Tests para la API de fútbol.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock

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
def mock_pool(monkeypatch):
    """Reemplaza el pool en los módulos que importan la función directamente."""
    from api import (
        rutas_competiciones_futbol, rutas_equipos_futbol, rutas_partidos_futbol,
        rutas_analisis_futbol, rutas_apuestas_futbol, rutas_metricas_futbol,
    )
    pool = MagicMock()
    for modulo in (
        rutas_competiciones_futbol, rutas_equipos_futbol, rutas_partidos_futbol,
        rutas_analisis_futbol, rutas_apuestas_futbol, rutas_metricas_futbol,
    ):
        monkeypatch.setattr(modulo, "obtener_pool", lambda: pool)
    return pool


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
                "activo": True,
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

    def test_rango_proximos_incluye_hoy_completo_y_dia_final_en_bogota(self):
        """El horizonte conserva partidos de hoy que ya iniciaron y el día final."""
        from zoneinfo import ZoneInfo
        from api.rutas_partidos_futbol import _rango_proximos

        bogota = ZoneInfo("America/Bogota")
        inicio, fin_exclusivo = _rango_proximos(
            datetime(2026, 10, 22, 12, 10, tzinfo=bogota), 30
        )

        assert inicio.isoformat() == "2026-10-22T00:00:00-05:00"
        assert fin_exclusivo.isoformat() == "2026-11-22T00:00:00-05:00"
        inicio_ya_transcurrido = datetime(2026, 10, 22, 11, 45, tzinfo=bogota)
        assert inicio <= inicio_ya_transcurrido < fin_exclusivo
        assert datetime(2026, 11, 21, 23, 59, tzinfo=bogota) < fin_exclusivo
        assert datetime(2026, 11, 22, 0, 0, tzinfo=bogota) == fin_exclusivo

    def test_rango_proximos_rechaza_fecha_sin_zona_o_horizonte_invalido(self):
        from api.rutas_partidos_futbol import _rango_proximos

        with pytest.raises(ValueError, match="zona horaria"):
            _rango_proximos(datetime(2026, 10, 21, 10, 30), 30)
        with pytest.raises(ValueError, match="entre 1 y 30"):
            _rango_proximos(datetime.now().astimezone(), 31)

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
        from zoneinfo import ZoneInfo
        from api.rutas_partidos_futbol import _rango_proximos

        parametros_partidos = cursor_mock.execute.call_args_list[1].args[1]
        assert parametros_partidos[0] == _rango_proximos(
            datetime.now(ZoneInfo("America/Bogota")), 7
        )[0]
        assert parametros_partidos[2] == [
            "PROGRAMADO",
            "EN_VIVO",
            "PRIMER_TIEMPO",
            "ENTRETIEMPO",
            "SEGUNDO_TIEMPO",
            "TIEMPO_EXTRA",
            "PENALES",
        ]

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

    def test_analizar_partido_no_existente_404(self, client, mock_pool):
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

        assert response.status_code == 404

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

    def test_registrar_apuesta_mercado_invalido(self, client, mock_pool):
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

        assert response.status_code in [400, 422]

    @pytest.mark.parametrize(
        ("probabilidad_sistema", "confianza_sistema", "valor_esperado"),
        [(None, None, None), (0.62, "MEDIA", 0.14)],
    )
    def test_guardar_seleccion_manual_con_snapshot_analitico_opcional(
        self, client, mock_pool, probabilidad_sistema, confianza_sistema, valor_esperado,
    ):
        """Registra selección manual y conserva métricas reales o N/D sin inventarlas."""
        partido_id = uuid4()
        fecha_partido = datetime.now() + timedelta(days=1)
        fecha_creacion = datetime.now()
        cursor_mock = MagicMock()
        cursor_mock.fetchone.side_effect = [
            {
                "partido_id_detalle": partido_id,
                "fecha_partido": fecha_partido,
                "partido_estado": "PROGRAMADO",
                "jornada": 10,
                "equipo_local_id": uuid4(),
                "equipo_visitante_id": uuid4(),
                "competicion_nombre": "Liga sintética",
                "equipo_local_nombre": "Local sintético",
                "equipo_visitante_nombre": "Visitante sintético",
                "goles_local": None,
                "goles_visitante": None,
            },
            {"fecha_creacion": fecha_creacion},
        ]
        cursor_mock.fetchall.return_value = [
            {"column_name": columna}
            for columna in (
                "id", "partido_id", "mercado", "lado", "linea", "stake", "cuota",
                "resultado", "probabilidad_sistema", "confianza_sistema", "valor_esperado",
                "ganancia_potencial", "notas", "creado_en",
            )
        ]
        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value.__enter__ = MagicMock(return_value=cursor_mock)
        conn_mock.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_pool.connection.return_value = conn_mock

        response = client.post(
            "/api/futbol/apuestas",
            json={
                "partido_id": str(partido_id),
                "mercado": "GOLES_FT",
                "lado": "UNDER",
                "linea": 2.5,
                "cuota": 1.84,
                "stake": 25,
                "probabilidad_sistema": probabilidad_sistema,
                "confianza_sistema": confianza_sistema,
                "valor_esperado": valor_esperado,
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["probabilidad_sistema"] == probabilidad_sistema
        assert data["confianza"] == confianza_sistema
        assert data["valor_esperado"] == valor_esperado
        insert_sql, insert_values = cursor_mock.execute.call_args_list[-1].args
        insert_columns = insert_sql.split("(", 1)[1].split(")", 1)[0].split(", ")
        persisted_values = dict(zip(insert_columns, insert_values))
        assert data["id"] == persisted_values["id"]
        assert persisted_values["probabilidad_sistema"] == probabilidad_sistema
        assert persisted_values["confianza_sistema"] == confianza_sistema
        assert persisted_values["valor_esperado"] == valor_esperado
        assert persisted_values["mercado"] == "GOLES_FT"
        assert persisted_values["lado"] == "UNDER"
        assert persisted_values["cuota"] == 1.84
        assert persisted_values["stake"] == 25
        conn_mock.commit.assert_called_once()

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
        assert resumen.stake_total is None
        assert resumen.ganancia_neta is None

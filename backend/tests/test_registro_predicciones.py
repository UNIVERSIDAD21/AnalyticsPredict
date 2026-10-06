# -*- coding: utf-8 -*-
"""
Tests para registro_predicciones.py

Incluye tests unitarios con mocks y tests de integración marcados
para ejecutar con Postgres real.
"""

from datetime import date
from uuid import UUID, uuid4
from unittest.mock import patch

from motor.registro_predicciones import registrar_prediccion


class FakeCursor:
    """Cursor simulado para tests unitarios."""

    def __init__(self, store, fail=False, modelo_version_valido=True):
        self._store = store
        self._row = None
        self._fail = fail
        self._modelo_version_valido = modelo_version_valido

    def execute(self, query, params):
        if self._fail:
            raise RuntimeError("DB down")

        # Simular resolución de competicion por partido
        if "FROM partidos_baloncesto" in query:
            self._row = (UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),)
            return

        # Simular verificación de modelo_version_id
        if "modelo_versiones" in query and "SELECT 1" in query:
            if self._modelo_version_valido:
                self._row = (1,)
            else:
                self._row = None
            return

        # Simular INSERT con ON CONFLICT
        key = (
            params[0],  # partido_id
            params[7],  # mercado
            params[8],  # lado
            params[9],  # linea
            params[11],  # origen
            params[12],  # modelo_version_id
            params[13],  # calibrador_id
        )
        if key in self._store:
            self._row = None
        else:
            nuevo_id = uuid4()
            self._store[key] = nuevo_id
            self._row = (nuevo_id,)

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    """Conexión simulada para tests unitarios."""

    def __init__(self, store, fail=False, modelo_version_valido=True):
        self._store = store
        self._fail = fail
        self._modelo_version_valido = modelo_version_valido

    def cursor(self):
        return FakeCursor(
            self._store,
            fail=self._fail,
            modelo_version_valido=self._modelo_version_valido,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    """Pool simulado para tests unitarios."""

    def __init__(self, store, fail=False, modelo_version_valido=True):
        self._store = store
        self._fail = fail
        self._modelo_version_valido = modelo_version_valido

    def connection(self):
        return FakeConnection(
            self._store,
            fail=self._fail,
            modelo_version_valido=self._modelo_version_valido,
        )


def _base_kwargs():
    return {
        "partido_id": UUID("11111111-1111-1111-1111-111111111111"),
        "temporada_id": UUID("22222222-2222-2222-2222-222222222222"),
        "equipo_local_id": UUID("33333333-3333-3333-3333-333333333333"),
        "equipo_visitante_id": UUID("44444444-4444-4444-4444-444444444444"),
        "fecha_partido": date(2024, 1, 1),
        "tipo_partido": "REG",
        "mercado": "Q1",
        "lado": "OVER",
        "linea": 210.5,
        "linea_es_sintetica": False,
        "origen": "API_USUARIO",
        "modelo_version_id": 1,
        "calibrador_id": None,
        "media_predicha": 110.2,
        "desviacion_predicha": 8.1,
        "p_raw": 0.62,
        "cuota": 1.9,
        "cuota_over": 1.9,
        "cuota_under": 1.9,
    }


def test_registro_idempotente_por_llave_natural():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(pool=pool, **kwargs)

    assert primero is not None
    assert segundo is None


def test_registro_con_modelo_version_distinta_inserta():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(pool=pool, **{**kwargs, "modelo_version_id": 2})

    assert primero is not None
    assert segundo is not None
    assert primero != segundo


def test_registro_con_calibrador_distinto_inserta():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    primero = registrar_prediccion(pool=pool, **kwargs)
    segundo = registrar_prediccion(
        pool=pool,
        **{**kwargs, "calibrador_id": UUID("55555555-5555-5555-5555-555555555555")},
    )

    assert primero is not None
    assert segundo is not None
    assert primero != segundo


def test_registro_falla_sin_romper_flujo():
    store = {}
    pool = FakePool(store, fail=True)
    kwargs = _base_kwargs()

    resultado = registrar_prediccion(pool=pool, **kwargs)

    assert resultado is None


def test_registro_falla_si_faltan_campos_obligatorios():
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    resultado = registrar_prediccion(pool=pool, **{**kwargs, "partido_id": None})

    assert resultado is None


def test_registro_falla_si_modelo_version_no_existe():
    """Verifica que falla si modelo_version_id no existe en modelo_versiones."""
    store = {}
    pool = FakePool(store, modelo_version_valido=False)
    kwargs = _base_kwargs()

    resultado = registrar_prediccion(pool=pool, **kwargs)

    assert resultado is None


def test_registro_falla_si_modelo_version_id_no_es_entero():
    """Verifica que falla si modelo_version_id no es un entero."""
    store = {}
    pool = FakePool(store)
    kwargs = _base_kwargs()

    resultado = registrar_prediccion(pool=pool, **{**kwargs, "modelo_version_id": "1"})

    assert resultado is None


# =============================================================================
# TESTS DE INTEGRACIÓN EN POSTGRESQL SINTÉTICO DESECHABLE
# =============================================================================

import os
import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import ConnectionPool


@pytest.fixture(scope="module")
def pool_real():
    """Nunca permitir que estas pruebas escriban en una BD persistente/Neon."""
    database_url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(database_url).get("dbname", "") if database_url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Integración solo en PostgreSQL sintético desechable del runner")
    pool = ConnectionPool(database_url, min_size=1, max_size=2, open=True)
    try:
        yield pool
    finally:
        pool.close()


@pytest.fixture
def datos_prueba_integracion(pool_real):
    """Crea partido/modelo propios; no depende de temporadas o datos reales."""
    partido_id = uuid4()
    competicion_id = uuid4()
    datos = {
        "partido_id": partido_id,
        "temporada_id": uuid4(),
        "competicion_id": competicion_id,
        "equipo_local_id": uuid4(),
        "equipo_visitante_id": uuid4(),
        "fecha_partido": date(2024, 1, 1),
        "tipo_partido": "REG",
    }
    with pool_real.connection() as conn:
        modelo_id = conn.execute(
            "INSERT INTO modelo_versiones (version, partidos_entrenamiento) "
            "VALUES (%s, %s) RETURNING id", ("test-registro", 100),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO partidos_baloncesto "
            "(id, fecha_partido, temporada_id, competicion_id, equipo_local_id, equipo_visitante_id, tipo_partido) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            tuple(datos[k] for k in (
                "partido_id", "fecha_partido", "temporada_id", "competicion_id",
                "equipo_local_id", "equipo_visitante_id", "tipo_partido",
            )),
        )
    try:
        yield {**datos, "modelo_version_id": modelo_id}
    finally:
        with pool_real.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE partido_id = %s", (partido_id,))
            conn.execute("DELETE FROM partidos_baloncesto WHERE id = %s", (partido_id,))
            conn.execute("DELETE FROM modelo_versiones WHERE id = %s", (modelo_id,))


@pytest.mark.integracion
def test_integracion_idempotencia_real(pool_real, datos_prueba_integracion):
    """El constraint natural impide duplicados en SQL real, sin datos productivos."""
    kwargs = {
        **datos_prueba_integracion,
        "mercado": "Q1",
        "lado": "OVER",
        "linea": 55.5,
        "linea_es_sintetica": False,
        "origen": "TEST_H9",
        "calibrador_id": None,
        "media_predicha": 28.5,
        "desviacion_predicha": 4.2,
        "p_raw": 0.58,
        "cuota": 1.85,
        "cuota_over": 1.85,
        "cuota_under": 2.0,
    }
    primero = registrar_prediccion(pool=pool_real, **kwargs)
    segundo = registrar_prediccion(pool=pool_real, **kwargs)
    assert primero is not None
    assert segundo is None
    with pool_real.connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM predicciones_registradas WHERE partido_id = %s AND mercado = %s",
            (kwargs["partido_id"], kwargs["mercado"]),
        ).fetchone()[0]
    assert count == 1


@pytest.mark.integracion
def test_integracion_modelo_version_valida(pool_real, datos_prueba_integracion):
    """Un modelo existente registra; uno inexistente no deja fila huérfana."""
    kwargs = {
        **datos_prueba_integracion,
        "mercado": "Q2",
        "lado": "UNDER",
        "linea": 52.0,
        "linea_es_sintetica": False,
        "origen": "TEST_H9",
        "calibrador_id": None,
        "media_predicha": 25.0,
        "desviacion_predicha": 3.8,
        "p_raw": 0.45,
    }
    assert registrar_prediccion(pool=pool_real, **kwargs) is not None
    assert registrar_prediccion(
        pool=pool_real, **{**kwargs, "modelo_version_id": 999999999, "linea": 53.0}
    ) is None
    with pool_real.connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM predicciones_registradas WHERE partido_id = %s AND mercado = 'Q2'",
            (kwargs["partido_id"],),
        ).fetchone()[0]
    assert count == 1

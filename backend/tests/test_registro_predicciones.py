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
            params[6],  # mercado
            params[7],  # lado
            params[8],  # linea
            params[10],  # origen
            params[11],  # modelo_version_id
            params[12],  # calibrador_id
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
# TESTS DE INTEGRACIÓN (requieren Postgres real)
# =============================================================================
# Para ejecutar: pytest -m integracion backend/tests/test_registro_predicciones.py
#
# Requieren:
# 1. Variable de entorno DATABASE_URL configurada
# 2. Ejecutar migración: scripts/migracion_idempotencia_predicciones.sql
# 3. Tener datos de prueba (equipos, temporadas, partidos, modelo_versiones)

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

if HAS_PYTEST:
    import os

    @pytest.fixture(scope="module")
    def pool_real():
        """Pool de conexiones real para tests de integración."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL no configurada")

        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(database_url, min_size=1, max_size=2)
        yield pool
        pool.close()

    @pytest.fixture
    def datos_prueba_integracion(pool_real):
        """Crea datos de prueba y los limpia después."""
        with pool_real.connection() as conn:
            with conn.cursor() as cur:
                # Verificar que hay equipos
                cur.execute("SELECT id FROM equipos LIMIT 2")
                equipos = cur.fetchall()
                if len(equipos) < 2:
                    pytest.skip("No hay suficientes equipos en BD")

                # Verificar que hay temporadas
                cur.execute("SELECT id FROM temporadas LIMIT 1")
                temporada = cur.fetchone()
                if not temporada:
                    pytest.skip("No hay temporadas en BD")

                # Verificar que hay partidos
                cur.execute(
                    """
                    SELECT p.id, p.temporada_id, p.equipo_local_id,
                           p.equipo_visitante_id, p.fecha_partido, p.tipo_partido
                    FROM partidos p
                    LIMIT 1
                    """
                )
                partido = cur.fetchone()
                if not partido:
                    pytest.skip("No hay partidos en BD")

                # Crear modelo_version de prueba
                cur.execute(
                    """
                    INSERT INTO modelo_versiones (version, partidos_entrenamiento, equipos,
                        mae_q1, mae_q2, mae_q3, mae_q4, duracion_segundos, hash_datos)
                    VALUES (99999, 100, 30, 2.5, 2.6, 2.7, 2.8, 1.5, 'test_hash')
                    RETURNING id
                    """
                )
                modelo_version_id = cur.fetchone()[0]
                conn.commit()

                yield {
                    "partido_id": partido[0],
                    "temporada_id": partido[1],
                    "equipo_local_id": partido[2],
                    "equipo_visitante_id": partido[3],
                    "fecha_partido": partido[4],
                    "tipo_partido": partido[5],
                    "modelo_version_id": modelo_version_id,
                }

                # Limpieza
                cur.execute(
                    "DELETE FROM predicciones_registradas WHERE modelo_version_id = %s",
                    [modelo_version_id],
                )
                cur.execute(
                    "DELETE FROM modelo_versiones WHERE id = %s", [modelo_version_id]
                )
                conn.commit()

    @pytest.mark.integracion
    def test_integracion_idempotencia_real(pool_real, datos_prueba_integracion):
        """
        TEST DE INTEGRACIÓN: Verifica idempotencia real con Postgres.

        Este test DEBE ejecutarse contra una BD real con:
        1. El constraint uq_prediccion_llave_natural creado
        2. Datos reales de partidos, equipos, temporadas
        """
        kwargs = {
            **datos_prueba_integracion,
            "mercado": "Q1",
            "lado": "OVER",
            "linea": 55.5,
            "linea_es_sintetica": False,
            "origen": "API_USUARIO",
            "calibrador_id": None,
            "media_predicha": 28.5,
            "desviacion_predicha": 4.2,
            "p_raw": 0.58,
            "cuota": 1.85,
            "cuota_over": 1.85,
            "cuota_under": 2.0,
        }

        # Primera inserción debe retornar ID
        primero = registrar_prediccion(pool=pool_real, **kwargs)
        assert primero is not None, "Primera inserción debe retornar ID"

        # Segunda inserción debe retornar None (duplicado)
        segundo = registrar_prediccion(pool=pool_real, **kwargs)
        assert segundo is None, "Segunda inserción debe ser None (duplicado)"

        # Verificar que solo hay un registro
        with pool_real.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM predicciones_registradas
                    WHERE partido_id = %s AND mercado = %s AND lado = %s
                      AND linea = %s AND origen = %s
                      AND modelo_version_id = %s
                    """,
                    [
                        str(kwargs["partido_id"]),
                        kwargs["mercado"],
                        kwargs["lado"],
                        kwargs["linea"],
                        kwargs["origen"],
                        kwargs["modelo_version_id"],
                    ],
                )
                count = cur.fetchone()[0]
                assert count == 1, f"Debe haber exactamente 1 registro, hay {count}"

    @pytest.mark.integracion
    def test_integracion_modelo_version_fk_valida(pool_real, datos_prueba_integracion):
        """
        TEST DE INTEGRACIÓN: Verifica que modelo_version_id debe ser FK válida.
        """
        kwargs = {
            **datos_prueba_integracion,
            "mercado": "Q2",
            "lado": "UNDER",
            "linea": 52.0,
            "linea_es_sintetica": False,
            "origen": "API_USUARIO",
            "calibrador_id": None,
            "media_predicha": 25.0,
            "desviacion_predicha": 3.8,
            "p_raw": 0.45,
        }

        # Con modelo_version_id válido debe funcionar
        resultado_valido = registrar_prediccion(pool=pool_real, **kwargs)
        assert resultado_valido is not None

        # Con modelo_version_id inválido (no existe en BD) debe fallar
        kwargs_invalido = {**kwargs, "modelo_version_id": 999999999, "linea": 53.0}
        resultado_invalido = registrar_prediccion(pool=pool_real, **kwargs_invalido)
        assert resultado_invalido is None

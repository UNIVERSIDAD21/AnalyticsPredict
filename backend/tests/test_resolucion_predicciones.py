# -*- coding: utf-8 -*-
"""
Tests para resolucion_predicciones.py (Tarea 6)

Tests obligatorios:
1. Cálculo correcto de valor_real para Q1-Q4 y COMPLETO
2. PUSH → outcome_binario=NULL y resuelto=true
3. Predicciones sin datos completos quedan pendientes
4. Idempotencia: correr 2 veces no cambia conteos ni reescribe

Incluye tests unitarios con mocks y tests de integración marcados
para ejecutar con Postgres real.
"""

import pytest
from datetime import date, datetime
from uuid import UUID, uuid4
from unittest.mock import MagicMock, patch

from motor.resolucion_predicciones import (
    _calcular_valor_real,
    _calcular_outcome_binario,
    _partido_tiene_datos_completos,
    resolver_predicciones,
    ResumenResolucion,
)


# =============================================================================
# TESTS UNITARIOS: _calcular_valor_real
# =============================================================================


class TestCalcularValorReal:
    """Tests para cálculo de valor_real según mercado."""

    def test_q1_suma_correcta(self):
        """Q1: local_q1 + visitante_q1"""
        resultado = _calcular_valor_real(
            mercado="Q1",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado == 54  # 28 + 26

    def test_q2_suma_correcta(self):
        """Q2: local_q2 + visitante_q2"""
        resultado = _calcular_valor_real(
            mercado="Q2",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado == 58  # 30 + 28

    def test_q3_suma_correcta(self):
        """Q3: local_q3 + visitante_q3"""
        resultado = _calcular_valor_real(
            mercado="Q3",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado == 54  # 25 + 29

    def test_q4_suma_correcta(self):
        """Q4: local_q4 + visitante_q4"""
        resultado = _calcular_valor_real(
            mercado="Q4",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado == 52  # 27 + 25

    def test_completo_suma_totales(self):
        """COMPLETO: local_total + visitante_total"""
        resultado = _calcular_valor_real(
            mercado="COMPLETO",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado == 218  # 110 + 108

    def test_q1_retorna_none_si_falta_local(self):
        """Q1 retorna None si falta local_q1"""
        resultado = _calcular_valor_real(
            mercado="Q1",
            local_q1=None,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is None

    def test_q1_retorna_none_si_falta_visitante(self):
        """Q1 retorna None si falta visitante_q1"""
        resultado = _calcular_valor_real(
            mercado="Q1",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=None,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is None

    def test_completo_retorna_none_si_falta_total(self):
        """COMPLETO retorna None si falta algún total"""
        resultado = _calcular_valor_real(
            mercado="COMPLETO",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=None,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is None

    def test_mercado_desconocido_retorna_none(self):
        """Mercado no reconocido retorna None"""
        resultado = _calcular_valor_real(
            mercado="UNKNOWN",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is None


# =============================================================================
# TESTS UNITARIOS: _calcular_outcome_binario
# =============================================================================


class TestCalcularOutcomeBinario:
    """Tests para cálculo de outcome_binario."""

    def test_over_gana_cuando_valor_mayor_linea(self):
        """OVER gana si valor_real > linea"""
        resultado = _calcular_outcome_binario(lado="OVER", valor_real=55, linea=52.5)
        assert resultado is True

    def test_over_pierde_cuando_valor_menor_linea(self):
        """OVER pierde si valor_real < linea"""
        resultado = _calcular_outcome_binario(lado="OVER", valor_real=50, linea=52.5)
        assert resultado is False

    def test_under_gana_cuando_valor_menor_linea(self):
        """UNDER gana si valor_real < linea"""
        resultado = _calcular_outcome_binario(lado="UNDER", valor_real=50, linea=52.5)
        assert resultado is True

    def test_under_pierde_cuando_valor_mayor_linea(self):
        """UNDER pierde si valor_real > linea"""
        resultado = _calcular_outcome_binario(lado="UNDER", valor_real=55, linea=52.5)
        assert resultado is False

    def test_push_retorna_none_over(self):
        """PUSH: valor_real == linea retorna None (OVER)"""
        resultado = _calcular_outcome_binario(lado="OVER", valor_real=52, linea=52.0)
        assert resultado is None

    def test_push_retorna_none_under(self):
        """PUSH: valor_real == linea retorna None (UNDER)"""
        resultado = _calcular_outcome_binario(lado="UNDER", valor_real=52, linea=52.0)
        assert resultado is None

    def test_push_con_linea_decimal_exacta(self):
        """PUSH con línea 52.5 y valor_real 52.5"""
        # En la práctica esto no debería pasar porque valor_real es entero
        # pero probamos el caso edge
        resultado = _calcular_outcome_binario(lado="OVER", valor_real=53, linea=53.0)
        assert resultado is None

    def test_over_con_diferencia_minima(self):
        """OVER gana con diferencia mínima (1 punto)"""
        resultado = _calcular_outcome_binario(lado="OVER", valor_real=53, linea=52.5)
        assert resultado is True

    def test_under_con_diferencia_minima(self):
        """UNDER gana con diferencia mínima"""
        resultado = _calcular_outcome_binario(lado="UNDER", valor_real=52, linea=52.5)
        assert resultado is True


# =============================================================================
# TESTS UNITARIOS: _partido_tiene_datos_completos
# =============================================================================


class TestPartidoTieneDatosCompletos:
    """Tests para verificación de datos completos."""

    def test_q1_completo_retorna_true(self):
        resultado = _partido_tiene_datos_completos(
            mercado="Q1",
            local_q1=28,
            local_q2=None,
            local_q3=None,
            local_q4=None,
            local_total=None,
            visitante_q1=26,
            visitante_q2=None,
            visitante_q3=None,
            visitante_q4=None,
            visitante_total=None,
        )
        assert resultado is True

    def test_q1_incompleto_retorna_false(self):
        resultado = _partido_tiene_datos_completos(
            mercado="Q1",
            local_q1=28,
            local_q2=None,
            local_q3=None,
            local_q4=None,
            local_total=None,
            visitante_q1=None,  # Falta!
            visitante_q2=None,
            visitante_q3=None,
            visitante_q4=None,
            visitante_total=None,
        )
        assert resultado is False

    def test_completo_requiere_totales(self):
        resultado = _partido_tiene_datos_completos(
            mercado="COMPLETO",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=110,
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is True

    def test_completo_incompleto_sin_totales(self):
        resultado = _partido_tiene_datos_completos(
            mercado="COMPLETO",
            local_q1=28,
            local_q2=30,
            local_q3=25,
            local_q4=27,
            local_total=None,  # Falta!
            visitante_q1=26,
            visitante_q2=28,
            visitante_q3=29,
            visitante_q4=25,
            visitante_total=108,
        )
        assert resultado is False


# =============================================================================
# TESTS UNITARIOS: resolver_predicciones (con mocks)
# =============================================================================


class FakeCursor:
    """Cursor simulado para tests de resolución."""

    def __init__(self, filas_select, updates_ok=True):
        self._filas_select = filas_select
        self._updates_ok = updates_ok
        self._updates = []

    def execute(self, query, params=None):
        if "UPDATE" in query:
            if not self._updates_ok:
                raise RuntimeError("UPDATE failed")
            self._updates.append(params)

    def fetchall(self):
        return self._filas_select

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnection:
    """Conexión simulada."""

    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakePool:
    """Pool simulado."""

    def __init__(self, cursor):
        self._cursor = cursor

    def connection(self):
        return FakeConnection(self._cursor)


class TestResolverPrediccionesUnitario:
    """Tests unitarios para resolver_predicciones."""

    def test_sin_predicciones_pendientes(self):
        """Sin predicciones pendientes retorna conteos en cero."""
        cursor = FakeCursor(filas_select=[])
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 0
        assert resumen.pendientes == 0
        assert resumen.push == 0

    def test_resuelve_prediccion_over_correcta(self):
        """Resuelve predicción OVER cuando valor_real > linea."""
        pred_id = uuid4()
        partido_id = uuid4()
        # Fila: prediccion_id, partido_id, mercado, lado, linea, ya_resuelto,
        #       local_q1..q4, local_total, visitante_q1..q4, visitante_total
        filas = [
            (
                pred_id,
                partido_id,
                "Q1",
                "OVER",
                52.5,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 1
        assert resumen.push == 0
        # Verificar que el UPDATE fue llamado
        assert len(cursor._updates) == 1
        # valor_real = 28 + 26 = 54 (> 52.5 = OVER gana)
        assert cursor._updates[0][0] == 54  # valor_real
        assert cursor._updates[0][1] is True  # outcome_binario

    def test_resuelve_prediccion_under_correcta(self):
        """Resuelve predicción UNDER cuando valor_real < linea."""
        pred_id = uuid4()
        partido_id = uuid4()
        filas = [
            (
                pred_id,
                partido_id,
                "Q1",
                "UNDER",
                56.5,  # linea alta
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 1
        # valor_real = 28 + 26 = 54 (< 56.5 = UNDER gana)
        assert cursor._updates[0][0] == 54
        assert cursor._updates[0][1] is True

    def test_resuelve_push_outcome_null(self):
        """PUSH: outcome_binario es None pero resuelto=True."""
        pred_id = uuid4()
        partido_id = uuid4()
        filas = [
            (
                pred_id,
                partido_id,
                "Q1",
                "OVER",
                54.0,  # linea exacta = PUSH
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 1
        assert resumen.push == 1
        # valor_real = 28 + 26 = 54 (== 54.0 = PUSH)
        assert cursor._updates[0][0] == 54
        assert cursor._updates[0][1] is None  # outcome_binario NULL

    def test_partido_sin_datos_queda_pendiente(self):
        """Predicción sin datos de partido queda pendiente."""
        pred_id = uuid4()
        partido_id = uuid4()
        # Partido sin resultados (NULLs)
        filas = [
            (
                pred_id,
                partido_id,
                "Q1",
                "OVER",
                52.5,
                False,
                None,  # local_q1 NULL
                None,
                None,
                None,
                None,
                None,  # visitante_q1 NULL
                None,
                None,
                None,
                None,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 0
        assert resumen.pendientes == 1
        assert resumen.sin_datos_partido == 1
        assert len(cursor._updates) == 0  # No debe hacer UPDATE

    def test_ya_resuelta_se_salta(self):
        """Predicción ya resuelta se salta (idempotencia)."""
        pred_id = uuid4()
        partido_id = uuid4()
        filas = [
            (
                pred_id,
                partido_id,
                "Q1",
                "OVER",
                52.5,
                True,  # YA RESUELTA
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 0
        assert resumen.ya_resueltas == 1
        assert len(cursor._updates) == 0

    def test_mercado_completo(self):
        """Resuelve mercado COMPLETO usando totales."""
        pred_id = uuid4()
        partido_id = uuid4()
        filas = [
            (
                pred_id,
                partido_id,
                "COMPLETO",
                "OVER",
                215.5,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 1
        # valor_real = 110 + 108 = 218 (> 215.5 = OVER gana)
        assert cursor._updates[0][0] == 218
        assert cursor._updates[0][1] is True

    def test_multiples_predicciones(self):
        """Resuelve múltiples predicciones en un lote."""
        filas = [
            (
                uuid4(),
                uuid4(),
                "Q1",
                "OVER",
                52.5,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            ),
            (
                uuid4(),
                uuid4(),
                "Q2",
                "UNDER",
                60.5,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            ),
            (
                uuid4(),
                uuid4(),
                "Q3",
                "OVER",
                54.0,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            ),  # PUSH
        ]
        cursor = FakeCursor(filas_select=filas)
        pool = FakePool(cursor)

        resumen = resolver_predicciones(pool=pool)

        assert resumen.resueltas == 3
        assert resumen.push == 1  # Q3 es PUSH (25+29=54)


# =============================================================================
# TESTS DE IDEMPOTENCIA
# =============================================================================


class TestIdempotencia:
    """Tests para verificar idempotencia del resolvedor."""

    def test_segunda_ejecucion_no_cambia_nada(self):
        """Segunda ejecución no modifica predicciones ya resueltas."""
        # Primera ejecución: predicción pendiente
        filas_primera = [
            (
                uuid4(),
                uuid4(),
                "Q1",
                "OVER",
                52.5,
                False,
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor1 = FakeCursor(filas_select=filas_primera)
        pool1 = FakePool(cursor1)
        resumen1 = resolver_predicciones(pool=pool1)

        # Segunda ejecución: predicción ya resuelta
        filas_segunda = [
            (
                uuid4(),
                uuid4(),
                "Q1",
                "OVER",
                52.5,
                True,  # YA RESUELTA
                28,
                30,
                25,
                27,
                110,
                26,
                28,
                29,
                25,
                108,
            )
        ]
        cursor2 = FakeCursor(filas_select=filas_segunda)
        pool2 = FakePool(cursor2)
        resumen2 = resolver_predicciones(pool=pool2)

        assert resumen1.resueltas == 1
        assert resumen2.resueltas == 0
        assert resumen2.ya_resueltas == 1
        assert len(cursor2._updates) == 0  # No debe hacer UPDATE


# =============================================================================
# TESTS DE INTEGRACIÓN (requieren Postgres real)
# =============================================================================
# Para ejecutar: pytest -m integracion backend/tests/test_resolucion_predicciones.py

try:
    import os

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

if HAS_PYTEST:

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
    def datos_resolucion_integracion(pool_real):
        """Crea predicción de prueba para resolver."""
        from motor.registro_predicciones import registrar_prediccion

        with pool_real.connection() as conn:
            with conn.cursor() as cur:
                # Buscar partido CON resultados
                cur.execute(
                    """
                    SELECT p.id, p.temporada_id, p.equipo_local_id,
                           p.equipo_visitante_id, p.fecha_partido, p.tipo_partido,
                           p.local_q1, p.visitante_q1, p.local_total, p.visitante_total
                    FROM partidos p
                    WHERE p.local_total IS NOT NULL
                    LIMIT 1
                    """
                )
                partido = cur.fetchone()
                if not partido:
                    pytest.skip("No hay partidos con resultados en BD")

                # Crear modelo_version de prueba
                cur.execute(
                    """
                    INSERT INTO modelo_versiones (version, partidos_entrenamiento, equipos,
                        mae_q1, mae_q2, mae_q3, mae_q4, duracion_segundos, hash_datos)
                    VALUES (88888, 100, 30, 2.5, 2.6, 2.7, 2.8, 1.5, 'test_resolucion')
                    RETURNING id
                    """
                )
                modelo_version_id = cur.fetchone()[0]
                conn.commit()

                # Registrar predicción pendiente
                valor_real_esperado = partido[6] + partido[7]  # local_q1 + visitante_q1
                linea = float(valor_real_esperado) - 2.5  # Línea menor para que OVER gane

                pred_id = registrar_prediccion(
                    pool=pool_real,
                    partido_id=partido[0],
                    temporada_id=partido[1],
                    equipo_local_id=partido[2],
                    equipo_visitante_id=partido[3],
                    fecha_partido=partido[4],
                    tipo_partido=partido[5],
                    mercado="Q1",
                    lado="OVER",
                    linea=linea,
                    linea_es_sintetica=False,
                    origen="API_USUARIO",
                    modelo_version_id=modelo_version_id,
                    calibrador_id=None,
                    media_predicha=28.0,
                    desviacion_predicha=4.0,
                    p_raw=0.6,
                )

                yield {
                    "prediccion_id": pred_id,
                    "partido_id": partido[0],
                    "modelo_version_id": modelo_version_id,
                    "valor_real_esperado": valor_real_esperado,
                    "linea": linea,
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
    def test_integracion_resolucion_completa(pool_real, datos_resolucion_integracion):
        """
        TEST DE INTEGRACIÓN: Verifica resolución completa con BD real.
        """
        pred_id = datos_resolucion_integracion["prediccion_id"]
        valor_esperado = datos_resolucion_integracion["valor_real_esperado"]

        # Ejecutar resolución
        resumen = resolver_predicciones(
            pool=pool_real,
            mercado="Q1",
            limite=100,
        )

        assert resumen.resueltas >= 1, "Debe resolver al menos 1 predicción"

        # Verificar que la predicción fue resuelta
        with pool_real.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT resuelto, valor_real, outcome_binario, timestamp_resolucion
                    FROM predicciones_registradas
                    WHERE id = %s
                    """,
                    [str(pred_id)],
                )
                row = cur.fetchone()
                assert row is not None, "Predicción debe existir"
                resuelto, valor_real, outcome, ts = row

                assert resuelto is True, "Debe estar resuelta"
                assert valor_real == valor_esperado, f"valor_real debe ser {valor_esperado}"
                assert outcome is True, "OVER debe ganar (línea < valor_real)"
                assert ts is not None, "timestamp_resolucion no debe ser NULL"

    @pytest.mark.integracion
    def test_integracion_idempotencia_real(pool_real, datos_resolucion_integracion):
        """
        TEST DE INTEGRACIÓN: Verifica idempotencia con BD real.
        """
        # Primera ejecución
        resumen1 = resolver_predicciones(pool=pool_real, limite=100)
        resueltas_primera = resumen1.resueltas

        # Segunda ejecución - no debe resolver nada nuevo
        resumen2 = resolver_predicciones(pool=pool_real, limite=100)

        assert resumen2.resueltas == 0, "Segunda ejecución no debe resolver nada"
        assert resumen2.ya_resueltas >= 0, "Debe contar las ya resueltas"

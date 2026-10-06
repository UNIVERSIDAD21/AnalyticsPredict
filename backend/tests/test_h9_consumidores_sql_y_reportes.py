"""Superficies H9 no convierten ausencia de calibración en 0 o aptitud."""

import os
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from api.rutas_backtest import _generar_recomendaciones
from api.rutas_explicabilidad import _fetch_prediccion
from api.rutas_metricas_futbol import _estado_mercados_futbol
from db import obtener_pool
from metricas_probabilisticas import expresiones_sql_probabilidad_futbol
from motor_futbol.evaluacion.backtesting import BacktesterFutbol, ResultadoBacktest


def test_backtest_sin_pares_probabilisticos_muestra_nd():
    resultado = ResultadoBacktest()
    assert resultado.brier_global is None
    assert resultado.ece_global is None
    assert "Brier Score: N/D" in resultado.resumen()
    assert "ECE: N/D" in resultado.resumen()

    reporte = BacktesterFutbol(pool=None).generar_reporte(resultado)
    assert "| Brier Score | N/D |" in reporte
    assert "| ECE | N/D |" in reporte


def test_recomendaciones_no_aprueban_produccion_por_ece_ausente_o_bajo():
    sin_muestra = _generar_recomendaciones([], [])
    assert any("ECE N/D" in mensaje for mensaje in sin_muestra)
    assert not any("apto para uso en producción" in mensaje for mensaje in sin_muestra)

    con_ece = _generar_recomendaciones([{"ece": 0.02}], [])
    assert any("no certifica calibración prospectiva" in mensaje for mensaje in con_ece)
    assert any("validación prospectiva" in mensaje for mensaje in con_ece)
    assert not any("apto para uso en producción" in mensaje for mensaje in con_ece)


def test_explicabilidad_usa_raw_si_falta_procedencia_en_postgres_efimero():
    cfg = conninfo_to_dict(os.environ.get("DATABASE_URL") or "")
    if not str(cfg.get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo se ejecuta en la base sintética del runner global")

    local_id, visita_id, partido_id, nba_id, fut_id, calibrador_id = (uuid4() for _ in range(6))
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            conn.execute("INSERT INTO equipos (id, nombre) VALUES (%s, 'Local'), (%s, 'Visita')", (local_id, visita_id))
            conn.execute(
                "INSERT INTO partidos_baloncesto (id, equipo_local_id, equipo_visitante_id) VALUES (%s, %s, %s)",
                (partido_id, local_id, visita_id),
            )
            conn.execute(
                "INSERT INTO predicciones_registradas (id, partido_id, p_raw, p_calibrada) VALUES (%s, %s, 0.2, 0.9)",
                (nba_id, partido_id),
            )
            conn.execute(
                "INSERT INTO predicciones_futbol (id, prob_over, prob_over_calibrada) VALUES (%s, 0.2, 0.9)",
                (fut_id,),
            )

        def obtener_ambas():
            with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                return _fetch_prediccion(cur, str(nba_id)), _fetch_prediccion(cur, str(fut_id))

        for fila in obtener_ambas():
            assert fila["calibration_source"] == "p_raw"
            assert float(fila["confidence_numeric"]) == pytest.approx(20.0)

        with pool.connection() as conn:
            conn.execute("UPDATE predicciones_registradas SET calibrador_id = %s WHERE id = %s", (calibrador_id, nba_id))
            conn.execute("UPDATE predicciones_futbol SET calibrador_id = %s WHERE id = %s", (calibrador_id, fut_id))
        for fila in obtener_ambas():
            assert fila["calibration_source"] == "p_calibrada"
            assert float(fila["confidence_numeric"]) == pytest.approx(90.0)
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE id = %s", (nba_id,))
            conn.execute("DELETE FROM predicciones_futbol WHERE id = %s", (fut_id,))
            conn.execute("DELETE FROM partidos_baloncesto WHERE id = %s", (partido_id,))
            conn.execute("DELETE FROM equipos WHERE id IN (%s, %s)", (local_id, visita_id))


def test_gate_madurez_futbol_no_usa_calibrada_sin_id_en_postgres_efimero():
    cfg = conninfo_to_dict(os.environ.get("DATABASE_URL") or "")
    if not str(cfg.get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo se ejecuta en la base sintética del runner global")

    prediccion_id, calibrador_id = uuid4(), uuid4()
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO predicciones_futbol "
                "(id, mercado, prob_over_raw, prob_over_calibrada, outcome_binario) "
                "VALUES (%s, 'GOLES_FT', 0.2, 0.9, false)",
                (prediccion_id,),
            )

        def estado():
            with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                return _estado_mercados_futbol(cur, min_muestras=1)

        assert estado()["GOLES_FT"] == "verde"
        with pool.connection() as conn:
            conn.execute("UPDATE predicciones_futbol SET calibrador_id = %s WHERE id = %s", (calibrador_id, prediccion_id))
        assert estado()["GOLES_FT"] == "rojo"
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_futbol WHERE id = %s", (prediccion_id,))


def test_expresion_reportes_futbol_se_ejecuta_en_postgres_efimero():
    cfg = conninfo_to_dict(os.environ.get("DATABASE_URL") or "")
    if not str(cfg.get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo se ejecuta en la base sintética del runner global")

    efectiva, fallback = expresiones_sql_probabilidad_futbol(
        {"prob_over_raw", "prob_over_calibrada", "calibrador_id"}
    )
    pool = obtener_pool()
    with pool.connection() as conn:
        filas = conn.execute(
            f"SELECT {efectiva} AS p, {fallback} AS fallback "
            "FROM (VALUES (0.2::numeric, 0.9::numeric, NULL::uuid), "
            "(0.2::numeric, 0.9::numeric, %s::uuid)) "
            "AS predicciones(prob_over_raw, prob_over_calibrada, calibrador_id)",
            (uuid4(),),
        ).fetchall()
    assert [(float(p), flag) for p, flag in filas] == [(0.2, 1), (0.9, 0)]

"""Un 0–0 histórico conserva la fila, pero no aporta pares a la calibración."""

import os
from datetime import date
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict

from api.rutas_metricas import _obtener_predicciones_para_curva, _contar_outcomes_nba_cero_cero
from api.rutas_backtest import (_calcular_resumen_global, _obtener_predicciones_backtest,
                                _obtener_predicciones_para_curva as _curva_backtest)
from backtesting.metricas.calculador import _obtener_predicciones
from db import obtener_pool
from motor.recalibracion import _cargar_datos_entrenamiento
from motor.resolucion_predicciones import obtener_estadisticas_predicciones


def test_vista_calculador_y_curva_en_postgres_sintetico():
    url = os.environ.get("DATABASE_URL") or ""
    if not conninfo_to_dict(url).get("dbname", "").startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable")

    partido_dudoso, partido_valido = uuid4(), uuid4()
    pool = obtener_pool()
    estadisticas_antes = obtener_estadisticas_predicciones(pool)
    try:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO partidos_baloncesto (id, local_total, visitante_total) "
                "VALUES (%s, 0, 0), (%s, 101, 99)",
                (partido_dudoso, partido_valido),
            )
            conn.execute(
                "INSERT INTO predicciones_registradas "
                "(partido_id, mercado, origen, fecha_partido, p_raw, outcome_binario, "
                "resuelto, valor_real) VALUES "
                "(%s, 'COMPLETO', 'CERO_CERO_TEST', '2026-01-01', 0.8, true, true, 0), "
                "(%s, 'COMPLETO', 'CERO_CERO_TEST', '2026-01-02', 0.2, false, true, 200)",
                (partido_dudoso, partido_valido),
            )

        filas = _obtener_predicciones(
            pool, mercado="COMPLETO", origen="CERO_CERO_TEST",
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 1, 2),
            modelo_version_id=None,
        )
        assert [fila[2] for fila in filas] == [None, False]
        assert [fila[4] for fila in filas] == [None, 200]

        curva = _obtener_predicciones_para_curva(
            mercado="COMPLETO", origen="CERO_CERO_TEST",
            desde=date(2026, 1, 1), hasta=date(2026, 1, 2),
        )
        assert [fila["outcome_binario"] for fila in curva] == [None, False]
        assert _contar_outcomes_nba_cero_cero(
            "COMPLETO", "CERO_CERO_TEST", date(2026, 1, 1), date(2026, 1, 2),
            modelo_version_id=None,
        ) == 1

        probabilidades, outcomes = _cargar_datos_entrenamiento(
            pool, mercado="COMPLETO", origen="CERO_CERO_TEST",
            cutoff_datos=date(2026, 1, 3), modelo_version_id=None,
        )
        assert probabilidades == [0.2] and outcomes == [False]

        parametros = {"fecha_inicio_eval": date(2026, 1, 1),
                      "fecha_fin_eval": date(2026, 1, 2)}
        resumen = _calcular_resumen_global(parametros, ["COMPLETO"], ["CERO_CERO_TEST"])
        assert resumen["total_predicciones"] == 2
        assert resumen["total_resueltas"] == 1
        assert resumen["n_excluidos_outcome_dudoso"] == 1
        predicciones = _obtener_predicciones_backtest(
            parametros, ["COMPLETO"], ["CERO_CERO_TEST"])
        assert [(p["outcome_no_evaluable"], p["outcome_binario"])
                for p in predicciones] == [(True, None), (False, False)]
        assert _curva_backtest(mercado="COMPLETO", origen="CERO_CERO_TEST",
                              desde=date(2026, 1, 1), hasta=date(2026, 1, 2)) == [(0.2, False)]
        estadisticas = obtener_estadisticas_predicciones(pool)
        assert estadisticas["no_evaluables"] == estadisticas_antes["no_evaluables"] + 1
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE origen = 'CERO_CERO_TEST'")
            conn.execute("DELETE FROM partidos_baloncesto WHERE id IN (%s, %s)",
                         (partido_dudoso, partido_valido))

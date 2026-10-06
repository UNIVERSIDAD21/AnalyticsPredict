"""Los gates de calidad NBA no usan outcomes de partidos 0–0."""

import os
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict

from api.rutas_analisis import _obtener_mercados_bloqueados_nba
from db import obtener_pool


def test_gate_calidad_ignora_outcome_cero_cero_en_postgres_sintetico():
    url = os.environ.get("DATABASE_URL") or ""
    if not str(conninfo_to_dict(url).get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable")

    dudoso, valido = uuid4(), uuid4()
    mercado = "GATE_CERO_TEST"
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO partidos_baloncesto(id, local_total, visitante_total) "
                "VALUES (%s, 0, 0), (%s, 110, 105)", (dudoso, valido),
            )
            conn.execute(
                """INSERT INTO predicciones_registradas
                   (partido_id, mercado, origen, p_raw, outcome_binario, resuelto)
                   VALUES (%s, %s, 'GATE_CERO_TEST', 0.9, false, true),
                          (%s, %s, 'GATE_CERO_TEST', 0.9, false, true)""",
                (dudoso, mercado, valido, mercado),
            )

        assert mercado not in _obtener_mercados_bloqueados_nba(
            min_muestras=2, umbral_brier=0.1,
        )

        with pool.connection() as conn:
            conn.execute(
                """INSERT INTO predicciones_registradas
                   (partido_id, mercado, origen, p_raw, outcome_binario, resuelto)
                   VALUES (%s, %s, 'GATE_CERO_TEST', 0.9, false, true)""",
                (valido, mercado),
            )
        assert mercado in _obtener_mercados_bloqueados_nba(
            min_muestras=2, umbral_brier=0.1,
        )
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE origen = 'GATE_CERO_TEST'")
            conn.execute("DELETE FROM partidos_baloncesto WHERE id IN (%s, %s)", (dudoso, valido))

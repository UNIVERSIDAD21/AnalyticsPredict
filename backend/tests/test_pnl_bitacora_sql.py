"""La misma regla SQL usada por la API clasifica fixtures en PostgreSQL real."""

import os

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from api.rutas_bitacora import _PNL_NBA_NO_EVALUABLE_SQL


def test_regla_sql_pnl_no_evaluable_sin_escrituras():
    url = os.environ.get("DATABASE_URL") or ""
    if not conninfo_to_dict(url).get("dbname", "").startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable")
    consulta = f"""
        SELECT caso, {_PNL_NBA_NO_EVALUABLE_SQL} AS no_evaluable
        FROM (VALUES
            ('ganada_valida', 'GANADA', 1000::numeric, 1.80::numeric, 800::numeric,
             'UNDER', NULL::numeric, 1.80::numeric),
            ('mitad_stake', 'GANADA', 1000::numeric, 1.80::numeric, 400::numeric,
             'UNDER', NULL::numeric, 1.80::numeric),
            ('cuota_lado', 'GANADA', 1000::numeric, 1.80::numeric, 800::numeric,
             'UNDER', NULL::numeric, 2.10::numeric),
            ('perdida_valida', 'PERDIDA', 1000::numeric, 1.80::numeric, -1000::numeric,
             'OVER', 1.80::numeric, NULL::numeric),
            ('anulada_sin_cuota', 'ANULADA', 1000::numeric, NULL::numeric, 0::numeric,
             'UNDER', NULL::numeric, 1.80::numeric),
            ('sin_stake', 'GANADA', NULL::numeric, 1.80::numeric, 800::numeric,
             'OVER', 1.80::numeric, NULL::numeric)
        ) AS apuestas(caso, resultado, stake, cuota, ganancia, lado, cuota_over, cuota_under)
    """
    with psycopg.connect(url) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        estados = dict(conn.execute(consulta).fetchall())
    assert estados == {"ganada_valida": False, "mitad_stake": True,
                       "cuota_lado": True, "perdida_valida": False,
                       "anulada_sin_cuota": False,
                       "sin_stake": True}

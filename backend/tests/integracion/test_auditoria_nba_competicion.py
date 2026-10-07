"""El corte NBA no mezcla partidos de Euroliga en la tabla compartida."""

import os

import psycopg
from psycopg.conninfo import conninfo_to_dict
import pytest

from scripts.auditar_corte_analitico import resumen_partidos_nba


@pytest.mark.integracion
def test_resumen_nba_excluye_euroliga_en_postgres_sintetico():
    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    with psycopg.connect(url) as conn:
        conn.execute("""CREATE TEMP TABLE competiciones_baloncesto (
            id integer PRIMARY KEY, codigo text NOT NULL) ON COMMIT DROP""")
        conn.execute("""CREATE TEMP TABLE partidos_baloncesto (
            competicion_id integer, fecha_partido date, source text, source_game_id text,
            local_total integer, visitante_total integer,
            local_q1 integer, visitante_q1 integer, local_q4 integer, visitante_q4 integer
        ) ON COMMIT DROP""")
        conn.execute("INSERT INTO competiciones_baloncesto VALUES (1,'nba'),(2,'euroleague')")
        conn.execute("""INSERT INTO partidos_baloncesto VALUES
            (1,current_date,NULL,NULL,0,0,0,0,0,0),
            (1,current_date,'ESPN','nba-1',120,110,30,27,28,29),
            (2,current_date,'SOFASCORE','euro-1',0,0,0,0,0,0),
            (2,current_date,'SOFASCORE','euro-1',0,0,0,0,0,0)""")
        with conn.cursor() as cur:
            resultado = resumen_partidos_nba(cur)
        assert resultado["partidos"] == 2
        assert resultado["cero_cero"] == 1
        assert resultado["sin_source"] == 1
        assert resultado["partidos_ultimos_30_dias"] == 2
        assert resultado["duplicados_source_id"] == 0
        conn.rollback()

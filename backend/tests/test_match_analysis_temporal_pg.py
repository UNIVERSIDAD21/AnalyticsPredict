"""El análisis interno no mezcla fases ni ve partidos del día/futuros."""
import os
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from scripts import generar_analisis_partido_nba as analisis
from scripts.run_suite_global_testdb import validar_admin_local


def test_selector_interno_fase_corte_e_invalidacion_en_postgres(monkeypatch):
    url=os.getenv('TEST_PG_ADMIN_URL')
    if not url: pytest.skip('Requiere PostgreSQL local sintético')
    validar_admin_local(url)
    schema='ap_match_'+uuid4().hex
    with psycopg.connect(url,autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        try:
            c.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
            c.execute('''CREATE TABLE competiciones_baloncesto(id int,codigo text);
              CREATE TABLE equipos(id uuid,nombre text,abreviatura text);
              CREATE TABLE partidos_baloncesto(id uuid,competicion_id int,equipo_local_id uuid,equipo_visitante_id uuid,
                fecha_partido date,tipo_partido text,valido boolean,local_q1 int,local_q2 int,local_q3 int,local_q4 int,
                local_ot int,local_total int,visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,
                visitante_ot int,visitante_total int,hubo_overtime boolean,source text,source_game_id text);
              INSERT INTO competiciones_baloncesto VALUES(1,'nba'),(2,'euroleague');''')
            local,visitante=uuid4(),uuid4()
            c.execute("INSERT INTO equipos VALUES(%s,'Local','AAA'),(%s,'Visitante','BBB')",[local,visitante])
            for fecha,fase,valido,competicion in [('2026-10-10','REG',True,1),('2026-10-09','PRE',True,1),
                ('2026-10-12','REG',True,1),('2026-10-13','REG',True,1),('2026-10-11','REG',False,1),('2026-10-10','REG',True,2)]:
                c.execute("INSERT INTO partidos_baloncesto VALUES(%s,%s,%s,%s,%s,%s,%s,25,25,25,25,0,100,25,25,25,25,0,100,false,'SINTETICO','test')",[uuid4(),competicion,local,visitante,fecha,fase,valido])
            monkeypatch.setattr(analisis,'db_url',lambda:make_conninfo(url,options=f'-c search_path={schema}'))
            r=analisis.fetch_team_rows_from_db('AAA',fecha_corte='2026-10-12',fase='REG')
            assert r['candidate_count']==2 and r['used_count']==1
            assert [x['fecha_partido'] for x in r['valid']]==['2026-10-10']
            assert r['excluded'][0]['categoria_exclusion']=='INVALIDATED'
            assert all(x['tipo_partido']=='REG' for x in r['valid'])
            assert c.execute('SELECT count(*) FROM partidos_baloncesto').fetchone()[0]==6
        finally:
            c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_fallback_no_utiliza_otra_fase_ni_el_dia_del_analisis():
    base={'puntos_total':100,'recibidos_total':100,**{k:25 for k in ['puntos_q1','puntos_q2','puntos_q3','puntos_q4','recibidos_q1','recibidos_q2','recibidos_q3','recibidos_q4']}}
    filas=[dict(base,fecha_partido=fecha,tipo_partido=fase) for fecha,fase in [('2026-10-10','PRE'),('2026-10-10','REG'),('2026-10-11','PRE')]]
    filas.extend(dict(base, fecha_partido=fecha, tipo_partido='PRE') for fecha in [None, '', '2026-02-30', 'fecha-desconocida'])
    r=analisis.extract_rows({'ultimos_30_partidos':filas},fecha_corte='2026-10-11',fase='PRE')
    assert len(r)==1 and r[0]['fecha_partido']=='2026-10-10' and r[0]['tipo_partido']=='PRE'

"""Cohortes y aritmética cross-sport en SQL real, sin tocar tablas del servicio real."""
import os
from uuid import uuid4

from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from app import app
from db import obtener_pool, PoolAplicacion
from servicios.politica_pnl import no_concilia_sql, publicar_pnl


@pytest.fixture
def datos_pnl(monkeypatch):
    url = os.environ.get('DATABASE_URL') or ''
    if not conninfo_to_dict(url).get('dbname','').startswith('ap_suite_test_'):
        pytest.skip('Solo PostgreSQL sintético desechable')
    import app as modulo_app
    monkeypatch.setattr(modulo_app,'cerrar_pool',lambda:None)
    admin = PoolAplicacion(url, min_size=1, max_size=1, open=True, kwargs={"prepare_threshold": None})
    schema = 'ap_pnl_' + uuid4().hex
    with admin.connection() as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        c.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        c.execute('''
            CREATE TABLE partidos_baloncesto(id uuid, valido boolean,
              local_total int,visitante_total int,local_q1 int,visitante_q1 int,
              local_q2 int,visitante_q2 int,local_q3 int,visitante_q3 int,local_q4 int,visitante_q4 int);
            CREATE TABLE apuestas(id uuid, mercado text,resultado text,stake numeric,cuota numeric,
              ganancia numeric,partido_id uuid,lado text,linea numeric,cuota_over numeric,cuota_under numeric,
              fecha_partido date,edge_real numeric,probabilidad_sistema numeric,confianza_sistema text);
            CREATE TYPE resultado_apuesta_futbol AS ENUM ('GANADA','PERDIDA','PUSH','PENDIENTE');
            CREATE TABLE apuestas_futbol(id uuid, mercado text,resultado resultado_apuesta_futbol,stake numeric,cuota numeric,
              ganancia numeric,fecha_creacion timestamptz,partido_id uuid,lado text,linea numeric);
            CREATE TABLE apuestas_combinadas(id uuid,resultado text,stake numeric,cuota_total numeric,ganancia numeric);
            CREATE TABLE selecciones_combinada(id uuid, combinada_id uuid);
            CREATE TABLE partidos_futbol(id uuid,competicion_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,
              fecha_partido timestamptz, estado text,jornada int,local_goles_total int,visitante_goles_total int);
            CREATE TABLE competiciones_futbol(id uuid,nombre text);
            CREATE TABLE equipos_futbol(id uuid,nombre text);
            CREATE TABLE predicciones_futbol(mercado text,prob_over numeric,outcome_binario boolean);
        ''')
        c.execute("INSERT INTO apuestas VALUES (%s,'Q1','GANADA',10,2,10,NULL,'OVER',50,2,NULL,CURRENT_DATE,.1,.7,'ALTA')",[uuid4()])
        for mercado,resultado,ganancia in [('GOLES_FT','GANADA',10),('GOLES_FT','PERDIDA',-5),('CORNERS_FT','PUSH',0),('GOLES_FT','PENDIENTE',900)]:
            c.execute('INSERT INTO apuestas_futbol VALUES (%s,%s,%s,10,2,%s,NOW(),gen_random_uuid(),\'OVER\',2.5)',[uuid4(),mercado,resultado,ganancia])
        comb = uuid4()
        c.execute("INSERT INTO apuestas_combinadas VALUES (%s,'GANADA',10,3,20)",[comb])
        for _ in range(3):
            c.execute('INSERT INTO selecciones_combinada VALUES (%s,%s)',[uuid4(),comb])
    pool = PoolAplicacion(make_conninfo(url, options=f'-c search_path={schema}'),min_size=1,max_size=2,open=True)
    pool.wait()
    import db
    from api import rutas_bitacora, rutas_apuestas_futbol, rutas_metricas_futbol
    for mod in (db,rutas_bitacora,rutas_apuestas_futbol,rutas_metricas_futbol):
        monkeypatch.setattr(mod,'obtener_pool',lambda:pool)
    try:
        yield pool
    finally:
        pool.close()
        with admin.connection() as c:
            c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        admin.close()


def test_unificado_cuenta_apuestas_no_selecciones_y_no_certifica(datos_pnl):
    with TestClient(app,raise_server_exceptions=False) as client:
        r = client.get('/api/bitacora/resumen')
        assert r.status_code == 200, r.text
        s = r.json()['resumen']
        assert s['total_apuestas'] == 6  # 1 NBA + 4 fútbol + 1 combinada; no 3 selecciones
        assert s['pendientes'] == 1
        assert s['calidad_pnl']['n_resueltas'] == 5
        assert s['calidad_pnl']['n_no_conciliables'] == 1  # pérdida incorrecta, no la pendiente
        assert s['n_pnl_no_evaluable_nba'] == 1  # diagnóstico deportivo NBA sigue visible
        for bloque in [s,*s['por_deporte'],*s['por_mercado']]:
            assert bloque['roi'] is bloque['ganancia_total'] is bloque['stake_total'] is None
            assert bloque['calidad_pnl']['n_evaluables'] == 0
        futbol = next(x for x in s['por_deporte'] if x['deporte']=='futbol')
        assert futbol['ganadas'] == 1 and futbol['perdidas'] == 1 and futbol['winrate'] == 50
        # Cambiar un dato se refleja de inmediato, sin TTL ni precálculo.
        with datos_pnl.connection() as c:
            c.execute("UPDATE apuestas_futbol SET resultado='GANADA',ganancia=10 WHERE resultado='PENDIENTE'")
        assert client.get('/api/bitacora/resumen').json()['resumen']['calidad_pnl']['n_resueltas'] == 6


def test_listado_futbol_resumen_filtrado_independiente_de_pagina(datos_pnl):
    with TestClient(app,raise_server_exceptions=False) as client:
        r = client.get('/api/futbol/apuestas',params={'mercado':'GOLES_FT','estado':'GANADA','limite':1,'offset':0})
        assert r.status_code == 200,r.text
        s = r.json()
        assert s['total'] == s['resumen']['total'] == len(s['apuestas']) == 1
        assert s['apuestas'][0]['estado'] == 'GANADA'  # canónica resultado, no falso pendiente
        assert s['apuestas'][0]['ganancia_real'] == 10  # individual preservado
        assert s['resumen']['roi'] is s['resumen']['stake_total'] is None
        assert s['resumen']['calidad_pnl']['n_excluidas'] == 1
        r = client.get('/api/futbol/apuestas',params={'mercado':'GOLES_FT','limite':1,'offset':1})
        assert r.status_code == 200,r.text
        assert r.json()['resumen']['total'] == 3 and len(r.json()['apuestas'])==1
        assert r.json()['resumen']['calidad_pnl']['n_excluidas']==2
        vacio=client.get('/api/futbol/apuestas',params={'mercado':'DISPAROS_FT'}).json()['resumen']
        assert vacio['total']==0 and vacio['roi'] is None and vacio['calidad_pnl']['n_resueltas']==0


def test_rendimiento_y_serie_cuentan_misma_cohorte_sin_importes(datos_pnl):
    with TestClient(app,raise_server_exceptions=False) as client:
        r = client.get('/api/futbol/metricas/rendimiento', params={'mercado':'GOLES_FT'})
        assert r.status_code==200,r.text
        m=r.json()['metricas'][0]
        assert m['n_apuestas']==2 and m['calidad_pnl']['n_no_conciliables']==1
        assert m['roi'] is m['ganancia_neta'] is m['stake_total'] is None
        r=client.get('/api/futbol/metricas/roi-temporal',params={'dias':7})
        assert r.status_code==200,r.text
        serie=r.json()['serie']
        assert len(serie)==7 and serie[-1]['calidad_pnl']['n_resueltas']==3
        assert serie[-1]['calidad_pnl']['n_no_conciliables']==1
        assert all(x['roi'] is x['stake_acumulado'] is x['ganancia_acumulada'] is None for x in serie)
        r=client.get('/api/bitacora/metricas')
        assert r.status_code==200,r.text
        m=r.json()
        for s in [m['resumen_global'],*m['por_mercado'],*m['por_confianza'],*m['por_mes']]:
            assert s['roi'] is None and s['n_pnl_no_evaluable']==1 and s['calidad_pnl']['n_evaluables']==0


def test_publicacion_no_modifica_input_ni_inventa_cero():
    entrada={'ganadas':1,'perdidas':0,'ganancia_total':10,'stake_total':10,'roi':100}
    salida=publicar_pnl(entrada)
    assert entrada['roi']==100
    assert salida['roi'] is salida['ganancia_total'] is salida['stake_total'] is None
    assert salida['calidad_pnl']['unidad'] is None
    assert publicar_pnl({'roi':0})['calidad_pnl']['estado']=='NO_EVALUABLE'
    assert publicar_pnl({'roi':None},n_resueltas=3)['calidad_pnl']['n_binarias_registradas'] is None


def test_madurez_raw_funciona_sin_columna_legacy(datos_pnl):
    from api.rutas_metricas_futbol import _estado_mercados_futbol
    from psycopg.rows import dict_row
    with datos_pnl.connection() as c:
        c.execute("INSERT INTO predicciones_futbol SELECT 'GOLES_FT',.8,true FROM generate_series(1,100)")
        with c.cursor(row_factory=dict_row) as cur:
            assert _estado_mercados_futbol(cur) == {'GOLES_FT':'verde'}

"""Agenda conjunta y reconstrucción sin fugas temporales ni persistencia."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from servicios import agenda_baloncesto as agenda
from servicios import reconstruccion_nba as nba
from api.modelos_peticion import PeticionAnalisis
from lecturas_http import solo_lectura_http
from test_ingesta_futbol_americas_pg import db_local  # noqa: F401


def fila(**kw):
    return {'id':uuid4(),'equipo_local_id':uuid4(),'equipo_visitante_id':uuid4(),'temporada_id':uuid4(),
            'codigo':'nba','fecha_local':date(2020,3,10),'inicio_utc':None,'local':'Club A','visitante':'Club B',
            'temporada':'2020','fase':'REG','estado':'PROGRAMADO','local_total':0,'visitante_total':0,**kw}


def test_fecha_sin_hora_no_inventa_inicio_y_hoy_es_consulta():
    p=agenda.resumir(fila(),datetime(2020,3,10,0,tzinfo=agenda.BOGOTA))
    assert p['inicio_utc'] is None and p['precision_fecha']=='DIA'
    assert p['reconstruccion'] and p['analizable']
    assert p['local_total'] is None and p['visitante_total'] is None


def test_wnba_dia_colombia_y_conservacion_estado():
    p=agenda.resumir(fila(codigo='wnba',inicio_utc=datetime(2020,3,11,2,tzinfo=timezone.utc),estado='FINALIZADO',local_total=99,visitante_total=90),datetime(2020,3,11,tzinfo=agenda.BOGOTA))
    assert p['fecha_partido']=='2020-03-10' and p['local_total']==99 and p['analizable']
    p=agenda.resumir(fila(fecha_local=date(2099,1,1),estado='CANCELADO'),agenda.ahora())
    assert not p['analizable']


@pytest.fixture
def agenda_sql(db_local,monkeypatch):
    c=db_local
    c.execute('CREATE TABLE competiciones_baloncesto(id uuid PRIMARY KEY,codigo text)')
    c.execute('CREATE TABLE equipos(id uuid PRIMARY KEY,nombre text)')
    c.execute('CREATE TABLE temporadas_baloncesto(id uuid PRIMARY KEY,nombre text)')
    c.execute('''CREATE TABLE partidos_baloncesto(id uuid PRIMARY KEY,competicion_id uuid,temporada_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,fecha_partido date,tipo_partido text,valido bool,local_total int,visitante_total int,actualizado_en timestamptz,espn_game_id text)''')
    c.execute('''CREATE TABLE partidos_fuente_wnba(partido_id uuid,competicion_id uuid,inicio_utc timestamptz,estado text)''')
    c.execute('''CREATE TABLE fixtures_wnba(id uuid,competicion_id uuid,temporada_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,fecha_local date,inicio_utc timestamptz,estado text,fase text,resultado_id uuid,registro jsonb,actualizado_en timestamptz)''')
    ids={}
    for codigo in ('nba','euroleague','wnba'):
        cid,tid,h,a,pid=[uuid4() for _ in range(5)];ids[codigo]=pid
        c.execute('INSERT INTO competiciones_baloncesto VALUES(%s,%s)',(cid,codigo))
        c.execute('INSERT INTO equipos VALUES(%s,%s),(%s,%s)',(h,codigo+' local',a,codigo+' visitante'))
        c.execute('INSERT INTO temporadas_baloncesto VALUES(%s,%s)',(tid,'2020'))
        c.execute("INSERT INTO partidos_baloncesto VALUES(%s,%s,%s,%s,%s,'2020-03-10','REG',true,100,90,now(),'123')",(pid,cid,tid,h,a))
        if codigo=='wnba':
            c.execute("INSERT INTO partidos_fuente_wnba VALUES(%s,%s,'2020-03-11 02:00Z','FINALIZADO')",(pid,cid))
            c.execute("INSERT INTO fixtures_wnba VALUES(%s,%s,%s,%s,%s,'2020-03-10','2020-03-11 02:00Z','FINALIZADO','REG',%s,'{}',now())",(uuid4(),cid,tid,h,a,pid))
    @contextmanager
    def lectura():yield c
    monkeypatch.setattr(agenda,'conexion_lectura',lectura)
    monkeypatch.setattr(agenda,'ahora',lambda:datetime(2020,3,12,tzinfo=agenda.BOGOTA))
    return ids


def test_sql_mezcla_ligas_pagina_busca_y_no_duplica_final_wnba(agenda_sql):
    r=agenda.consultar(date(2020,3,10))
    assert r['total']==3 and r['competiciones']==['Euroliga','NBA','WNBA']
    assert len({p['id'] for p in r['partidos']})==3
    assert r['partidos'][0]['liga']=='wnba'
    assert agenda.consultar(date(2020,3,10),liga='nba')['total']==1
    assert agenda.consultar(date(2020,3,10),buscar='%')['total']==0
    assert agenda.consultar(date(2020,3,10),buscar='euroleague')['total']==1
    assert agenda.consultar(date(2020,3,10),estado='pendientes')['total']==0
    assert agenda.consultar(date(2020,3,10),pagina=2,tamano=2)['partidos']==r['partidos'][2:]
    assert agenda.consultar(date(2020,3,11))['total']==0


def test_reconstruccion_nba_no_usa_el_evento_ni_datos_posteriores(monkeypatch):
    corte=date(2020,3,10)
    filas=[{'id':str(i),'fecha_partido':corte-timedelta(days=i+1),'equipo_local':'Club A','equipo_visitante':'Club B',
        **{f'{l}_q{q}':22+(i+q)%5 for l in ('local','visitante') for q in range(1,5)}} for i in range(110)]
    filas.extend([{**filas[0],'id':'excluir','fecha_partido':corte,**{f'{l}_q{q}':500 for l in ('local','visitante') for q in range(1,5)}}])
    def leer(self,**kw):
        assert kw['cutoff_fecha']==corte and solo_lectura_http.get()
        return filas
    monkeypatch.setattr(nba.EntrenadorBD,'_obtener_partidos',leer)
    monkeypatch.setattr(nba,'obtener_pool',lambda:None)
    from motor import nba_predictor_cuartos as motor
    def prohibido(*a,**kw):raise AssertionError('No se permite consultar calibradores o contexto actual')
    monkeypatch.setattr(motor,'obtener_calibrador_activo',prohibido)
    monkeypatch.setattr(motor,'recolectar_contexto',prohibido)
    p=PeticionAnalisis(equipo_local='Club A',equipo_visitante='Club B',mercado='Q1',linea=48.5)
    r=nba.reconstruir(p,{'id':uuid4(),'fecha_partido':corte,'local':'Club A','visitante':'Club B'})
    assert not solo_lectura_http.get()
    assert r['metadata']['partidos_entrenamiento']==110
    assert r['metadata']['ultimo_dato_utilizado']<corte.isoformat()
    assert r['metadata']['modelo_version'] is None and r['metadata']['solo_consulta']
    assert not r['candidatos'] and r['mejor_apuesta'] is None
    assert r['predicciones']['Q1']['media_total']<100


def test_contrato_agenda_valida_filtros_y_orden_de_rutas(monkeypatch):
    from api import rutas_partidos as rutas
    monkeypatch.setattr(agenda,'consultar',lambda *a: {'total':0,'partidos':[]})
    app=FastAPI();app.include_router(rutas.router);client=TestClient(app)
    assert client.get('/api/partidos/agenda?fecha=2020-03-10').status_code==200
    for q in ('fecha=invalida','liga=mls','pagina=0','tamano=101','estado=inventado'):
        assert client.get('/api/partidos/agenda?'+q).status_code==422


def test_endpoint_pasado_ignora_modelo_actual_y_no_registra(monkeypatch):
    from api import rutas_analisis as rutas
    fixture={'id':uuid4(),'fecha_partido':date(2020,3,10),'local':'Club A','visitante':'Club B'}
    monkeypatch.setattr(rutas,'_resolver_fixture_nba',lambda p:fixture)
    def prohibido(*a,**kw):raise AssertionError('No se permite modelo actual ni persistencia')
    for nombre in ('obtener_modelo','registrar_prediccion','_registrar_bitacora_analisis_nba'):
        monkeypatch.setattr(rutas,nombre,prohibido)
    monkeypatch.setattr(nba,'reconstruir',lambda *a:{'metadata':{'modo_analisis':'HISTORICO_RECONSTRUIDO'}})
    p=PeticionAnalisis(equipo_local='Club A',equipo_visitante='Club B',partido_id=fixture['id'],fecha_partido=date(2099,1,1),mercado='Q1',linea=48.5)
    r=rutas.ejecutar_analisis(p)
    assert r.exito and r.datos['metadata']['modo_analisis']=='HISTORICO_RECONSTRUIDO'


def test_post_conexion_lectura_activa_proteccion_antes_de_adquirir_pool(db_local):
    from db import PoolAplicacion
    from servicios.predictor_euroliga import conexion_lectura
    from lecturas_http import en_peticion_http
    import psycopg
    token=en_peticion_http.set(True)
    try:
        with PoolAplicacion(conninfo=db_local.info.dsn,min_size=1,max_size=1) as pool:
            with conexion_lectura(pool) as c:
                assert c.read_only
                assert c.execute('SHOW transaction_read_only').fetchone()[0]=='on'
            assert not solo_lectura_http.get()
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                with conexion_lectura(pool) as c:
                    c.execute('CREATE TABLE no_debe_existir(id int)')
            with pool.connection() as c:
                assert not c.read_only
    finally:
        en_peticion_http.reset(token)


def test_euroliga_manual_sin_fixture_no_usa_historico_sin_inicializar(monkeypatch):
    from api import rutas_euroliga as rutas
    from fastapi import HTTPException
    monkeypatch.setattr(rutas, 'modelo_actual', lambda: {'fecha_max': '2020-01-01'})
    monkeypatch.setattr(rutas, 'leer_datos', lambda: [])
    def abstencion(*a, **kw):
        raise ValueError('Muestra sintética insuficiente')
    monkeypatch.setattr(rutas, 'predecir', abstencion)
    p = rutas.PeticionEuroliga(equipo_local='Club A', equipo_visitante='Club B', linea=150.5)
    with pytest.raises(HTTPException) as error:
        rutas.analizar(p)
    assert error.value.status_code == 422
    assert error.value.detail == 'Muestra sintética insuficiente'

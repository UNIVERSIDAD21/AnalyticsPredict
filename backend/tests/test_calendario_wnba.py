"""Ventana completa, estados de fuente, idempotencia, migración y enlace FT WNBA."""
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from servicios import calendario_wnba as cal
from ingesta_wnba import importar, leer_lote, uid, MIGRACION as INGESTA
from scripts.run_suite_global_testdb import validar_admin_local
from test_ingesta_wnba import escribir_lote, registro


def evento(eid='700',inicio='2026-10-27T00:00:00Z',estado='STATUS_SCHEDULED'):
    return {'id':eid,'date':inicio,'season':{'year':2026,'type':3},'status':{'type':{'name':estado}},
            'competitions':[{'timeValid':True,'competitors':[
                {'homeAway':'home','team':{'id':'1','displayName':'Participante W A'}},
                {'homeAway':'away','team':{'id':'2','displayName':'Participante W B'}}]}]}


def reporte():
    return {'desde':'2026-10-25','hasta':'2027-01-25','comprobado_utc':'2026-10-25T20:00:00Z',
            'fuentes':[{'url':cal.ESPN,'estado':'CONSULTADA'}], 'estado':'PARTIDOS_PUBLICADOS',
            'partidos':[cal.normalizar_evento(evento(),date(2026,10,25),date(2027,1,25))]}


@pytest.mark.parametrize('inicio,fin',[
    ('2026-10-25','2027-01-25'),('2026-11-30','2027-02-28'),('2027-11-30','2028-02-29'),('2026-12-31','2027-03-31')])
def test_tres_meses_calendario_no_treinta_dias(inicio,fin):
    assert str(cal.ventana(date.fromisoformat(inicio))[1])==fin


@pytest.mark.parametrize('estado,esperado',[
    ('STATUS_SCHEDULED','PROGRAMADO'),('STATUS_POSTPONED','POSPUESTO'),('STATUS_CANCELED','CANCELADO'),
    ('STATUS_IN_PROGRESS','EN_VIVO'),('STATUS_FINAL','FINALIZADO')])
def test_no_finales_sin_puntos_y_sin_hora_ficticia(estado,esperado):
    e=evento(estado=estado);e['competitions'][0]['timeValid']=False
    r=cal.normalizar_evento(e,date(2026,10,25),date(2027,1,25))
    assert r['estado']==esperado and r['inicio_utc'] is None and r['precision_fecha']=='DIA'
    assert 'local_total' not in r and 'visitante_total' not in r


def test_93_dias_con_ultima_fecha_incluida_y_fallo_oficial_no_es_vacio(monkeypatch):
    urls=[]
    def obtener(url,s,fuentes):
        urls.append(url);fuentes.append({'url':url,'http':200})
        if url==cal.OFICIAL:raise ValueError('incompleto')
        return {'events':[evento(inicio='2027-01-26T00:00:00Z')|{'season':{'year':2027,'type':2}}] if '20270125' in url else []}
    monkeypatch.setattr(cal,'obtener_json',obtener)
    r=cal.consultar(date(2026,10,25),pausa=0)
    assert r['dias_consultados']==r['dias_requeridos']==93
    assert len(r['partidos'])==1 and not r['oficial_completa']
    assert r['estado']=='PARTIDOS_PUBLICADOS'
    assert any('20270125' in x for x in urls)


def test_no_publicado_no_se_infiere_de_lista_vacia(monkeypatch):
    def obtener(url,s,fuentes):
        fuentes.append({'url':url,'http':200})
        return {'leagueSchedule':{'leagueId':'10','seasonYear':'2026','gameDates':[]}} if url==cal.OFICIAL else {'events':[]}
    monkeypatch.setattr(cal,'obtener_json',obtener)
    r=cal.consultar(date(2026,10,25),pausa=0)
    assert r['estado']=='CONSULTA_PARCIAL' and r['dias_consultados']==93


@pytest.fixture
def base(tmp_path):
    admin=os.environ.get('TEST_PG_ADMIN_URL')
    if not admin:pytest.skip('PostgreSQL sintético requerido')
    validar_admin_local(admin);nombre='ap_wnba_cal_'+uuid4().hex
    with psycopg.connect(admin,autocommit=True) as c:
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
    url=make_conninfo(admin,dbname=nombre)
    with psycopg.connect(url) as c:
        c.execute((Path(__file__).parent/'integracion/wnba_legacy_fixture.sql').read_text())
        c.execute('CREATE TABLE apuestas(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),partido_id uuid,competicion_id uuid,razones jsonb)')
        c.execute(INGESTA.read_text())
        importar(c,leer_lote(escribir_lote(tmp_path/'inicial')))
    yield url
    with psycopg.connect(admin,autocommit=True) as c:
        c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))


@pytest.mark.integracion
def test_migracion_rollback_fixture_reprogramacion_cancelacion_y_final(base,tmp_path):
    with psycopg.connect(base,autocommit=True) as c:
        with c.transaction(force_rollback=True):
            c.execute(cal.MIGRACION.read_text());cal.aplicar(c,reporte())
        assert c.execute("SELECT to_regclass('fixtures_wnba')").fetchone()[0] is None
        with c.transaction():
            c.execute(cal.MIGRACION.read_text());c.execute(cal.MIGRACION.read_text())
            assert cal.aplicar(c,reporte())['altas']==1
            assert cal.aplicar(c,reporte())=={'altas':0,'revisados':0,'sin_cambios':1}
            assert c.execute('SELECT count(*) FROM partidos_baloncesto').fetchone()[0]==1
            fid=c.execute('SELECT id FROM fixtures_wnba').fetchone()[0]
            r=deepcopy(reporte());r['partidos'][0]['inicio_utc']='2026-10-28T00:00:00+00:00';r['partidos'][0]['fecha_local']='2026-10-27'
            assert cal.aplicar(c,r)['revisados']==1
            r['partidos'][0]['estado']='POSPUESTO';assert cal.aplicar(c,r)['revisados']==1
            r['partidos'][0]['estado']='CANCELADO';assert cal.aplicar(c,r)['revisados']==1
            r['partidos'][0]['estado']='PROGRAMADO';assert cal.aplicar(c,r)['revisados']==1
            assert c.execute('SELECT count(*) FROM fixtures_wnba').fetchone()[0]==1
            assert c.execute('SELECT count(*) FROM revisiones_fixtures_wnba').fetchone()[0]==4
            cid=c.execute("SELECT id FROM competiciones_baloncesto WHERE codigo='wnba'").fetchone()[0]
            c.execute('INSERT INTO apuestas(fixture_wnba_id,competicion_id) VALUES(%s,%s)',(fid,cid))
            final=registro('700',True,'POST');final.update(temporada=2026,inicio_utc='2026-10-28T00:00:00+00:00',inicio_colombia='2026-10-27T19:00:00-05:00')
            final['evidencia'][0]['observado_utc']='2026-11-01T00:00:00Z'
            lote=deepcopy(leer_lote(escribir_lote(tmp_path/'final')));lote['registros']=[final];lote['sha256']='b'*64;importar(c,lote)
            f=c.execute('SELECT id,estado,resultado_id FROM fixtures_wnba').fetchone()
            assert f[0]==fid and f[1]=='FINALIZADO' and str(f[2])==uid('partido','700')
            assert c.execute('SELECT partido_id FROM apuestas').fetchone()[0]==f[2]
            assert not cal.vincular_final(c,final,f[2])
            # Una consulta posterior del mismo final no pisa su evidencia canónica.
            r['partidos'][0]['estado']='FINALIZADO'
            assert cal.aplicar(c,r)=={'altas':0,'revisados':0,'sin_cambios':1}
            with pytest.raises(ValueError,match='temporada/fase distintas'):
                cal.vincular_final(c,{**final,'fase':'REG'},f[2])
            with pytest.raises(ValueError,match='Final válido protegido'):
                r['partidos'][0]['estado']='PROGRAMADO';cal.aplicar(c,r)


def test_fecha_pendiente_no_inventa_dia_ni_medianoche():
    e=evento();e.pop('date');r=cal.normalizar_evento(e,date(2026,10,25),date(2027,1,25))
    assert r['precision_fecha']=='PENDIENTE' and r['fecha_local'] is None and r['inicio_utc'] is None
    e=evento();e['competitions'][0]['timeValid']=False
    r=cal.normalizar_evento(e,date(2026,10,25),date(2027,1,25))
    assert r['fecha_local']=='2026-10-27' and r['precision_fecha']=='DIA'


@pytest.mark.integracion
def test_guardado_api_wnba_fixture_sin_resultado_y_revision_obsoleta(base,tmp_path,monkeypatch):
    """Escritura financiera EXCLUSIVAMENTE en PostgreSQL sintético descartable."""
    import asyncio
    from psycopg_pool import ConnectionPool
    from api import rutas_bitacora
    from api.modelos_peticion import PeticionCrearApuesta
    from servicios import predictor_wnba as svc
    rep=reporte();e=evento(inicio='2099-10-27T00:00:00Z');e['season']['year']=2099
    rep['partidos']=[cal.normalizar_evento(e,date(2099,10,25),date(2100,1,25))]
    with psycopg.connect(base) as c:
        c.execute(cal.MIGRACION.read_text());cal.aplicar(c,rep)
        c.execute('''ALTER TABLE apuestas
          ADD COLUMN competicion_nombre text,ADD COLUMN equipo_local text,ADD COLUMN equipo_visitante text,
          ADD COLUMN fecha_partido date,ADD COLUMN mercado text,ADD COLUMN lado text,ADD COLUMN linea numeric,
          ADD COLUMN cuota numeric,ADD COLUMN cuota_over numeric,ADD COLUMN cuota_under numeric,ADD COLUMN stake numeric,
          ADD COLUMN probabilidad_sistema numeric,ADD COLUMN confianza_sistema text,ADD COLUMN valor_esperado numeric,
          ADD COLUMN devig_metodo text,ADD COLUMN modo_devig text,ADD COLUMN devig_overround numeric,
          ADD COLUMN devig_p_mkt_raw numeric,ADD COLUMN devig_p_mkt_fair numeric,ADD COLUMN devig_advertencias text[],
          ADD COLUMN edge_real numeric,ADD COLUMN score_total numeric,ADD COLUMN score_componentes jsonb,
          ADD COLUMN score_explicacion text,ADD COLUMN score_penalizaciones text[],ADD COLUMN kelly_full numeric,
          ADD COLUMN kelly_fraccional numeric,ADD COLUMN fraccion_kelly numeric,ADD COLUMN stake_porcentaje numeric,
          ADD COLUMN bankroll_momento numeric,ADD COLUMN perfil_riesgo_usado text,ADD COLUMN sizing_advertencias text[],
          ADD COLUMN sizing_penalizaciones jsonb,ADD COLUMN prediccion_media numeric,ADD COLUMN prediccion_desviacion numeric,
          ADD COLUMN resultado text DEFAULT 'PENDIENTE',ADD COLUMN ganancia numeric DEFAULT 0''')
        fid,digest=c.execute('SELECT id,revision_sha256 FROM fixtures_wnba').fetchone()
    monkeypatch.setenv('ANALYTICSPREDICT_MODELO_WNBA_ACTIVO',str(tmp_path/'activo.json'))
    r=svc.registrar({'dominio':'wnba','modo':'PREPARTIDO','es_prueba':False,'guardar_bitacora_habilitado':True,
          'fecha_partido':'2099-10-27T00:00:00+00:00','partido_id':str(fid),'equipo_local':'Participante W A',
          'equipo_visitante':'Participante W B','mercado':'COMPLETO','linea':150.5,'incluye_ot':True,
          'fixture_revision_sha256':digest,'probabilidades':{'over':.61,'under':.39,'push':0}})
    pet=PeticionCrearApuesta(competicion_codigo='wnba',partido_id=str(fid),equipo_local=r['equipo_local'],
          equipo_visitante=r['equipo_visitante'],fecha_partido='2099-10-26',mercado='COMPLETO',lado='OVER',linea=150.5,
          cuota=1.91,stake=1,probabilidad_sistema=.61,confianza_sistema=None,
          razones=[{'tipo':'trazabilidad_wnba','analisis_id':r['analisis_id'],'partido_id':str(fid),
                    'incluye_ot':True,'fixture_revision_sha256':digest}])
    with ConnectionPool(base,min_size=1,max_size=2,open=True) as pool:
        pool.wait();monkeypatch.setattr(rutas_bitacora,'obtener_pool',lambda:pool)
        out=asyncio.run(rutas_bitacora.guardar_apuesta(pet))
        assert out.apuesta.competicion_nombre=='WNBA' and out.apuesta.confianza_sistema is None
        with pool.connection() as c:
            assert c.execute('SELECT partido_id,fixture_wnba_id,probabilidad_sistema FROM apuestas').fetchone()==(None,fid,__import__('decimal').Decimal('.61'))
            assert c.execute('SELECT count(*) FROM partidos_baloncesto').fetchone()[0]==1
            c.execute("UPDATE fixtures_wnba SET revision_sha256='cambio' WHERE id=%s",(fid,))
        from fastapi import HTTPException
        with pytest.raises(HTTPException,match='calendario WNBA cambió'):
            asyncio.run(rutas_bitacora.guardar_apuesta(pet))
        with pool.connection() as c:
            assert c.execute('SELECT count(*) FROM apuestas').fetchone()[0]==1

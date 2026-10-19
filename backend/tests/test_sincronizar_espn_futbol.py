"""Vínculo explícito: sin fuzzy, sin contaminación del histórico ni ceros falsos."""
from copy import deepcopy
from pathlib import Path
import os
from uuid import uuid4
import json

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from scripts.sincronizar_espn_futbol import validar_manifiesto,planificar,aplicar_plan
from scripts.run_suite_global_testdb import validar_admin_local

CLUB_A='00000000-0000-0000-0000-000000000001'
CLUB_B='00000000-0000-0000-0000-000000000002'
COMP='00000000-0000-0000-0000-000000000003'


def manifiesto():
    return {'version':1,'temporadas':{'esp.1':{'anio':2026,'nombre':'2026-2027','evidencia':{'season':'2026-27'}}},
            'equipos':[{'liga':'esp.1','id_fuente':ident,'equipo_id':uid,'nombre_espn':nombre,
                        'nombre_canonico':nombre,'slug':'esp.'+nombre,'metodo':'NOMBRE_EXACTO','evidencia':{'id':ident}}
                       for ident,uid,nombre in [('1',CLUB_A,'Club A'),('2',CLUB_B,'Club B')]]}


def lote():
    return {'fuente':'ESPN_SOCCER','liga':'esp.1','mes':'202609','estado':'OK',
            'observado_en':'2026-10-01T00:00Z','n_eventos':1,'n_finales':1,'sha256_scoreboard':'a'*64,
            'eventos':[{'fuente':'ESPN_SOCCER','liga':'esp.1','id_fuente':'100','inicio_utc':'2026-09-01T12:00Z',
                        'estado_fuente':'STATUS_FULL_TIME','final_acreditado':True,'local_id_fuente':'1',
                        'visitante_id_fuente':'2','local_nombre':'Club A','visitante_nombre':'Club B',
                        'local_goles':0,'visitante_goles':2}]}


def test_manifiesto_rechaza_similitud_y_colisiones():
    m=manifiesto();m['equipos'][0]['metodo']='SIMILITUD'
    with pytest.raises(ValueError): validar_manifiesto(m)
    m=manifiesto();m['equipos'][0]['evidencia']=None
    with pytest.raises(ValueError): validar_manifiesto(m)
    m=manifiesto();m['equipos'][1]['equipo_id']=CLUB_A
    with pytest.raises(ValueError,match='Colisión'): validar_manifiesto(m)


@pytest.fixture
def futbol_db():
    admin_url=os.getenv('TEST_PG_ADMIN_URL')
    if not admin_url: pytest.skip('PostgreSQL local desechable requerido')
    validar_admin_local(admin_url)
    nombre='ap_futbol_espn_'+uuid4().hex
    with psycopg.connect(admin_url,autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            url=make_conninfo(admin_url,dbname=nombre)
            with psycopg.connect(url,autocommit=True) as c:
                c.execute('''
                    CREATE TABLE competiciones_futbol(id uuid primary key,codigo text,pais_id uuid);
                    CREATE TABLE equipos_futbol(id uuid primary key,nombre text,nombre_corto text,pais_id uuid,competicion_principal_id uuid,activo boolean);
                    CREATE TABLE temporadas_futbol(id uuid primary key,competicion_id uuid,nombre text,anio_inicio int,anio_fin int,activa boolean,finalizada boolean);
                    CREATE TABLE partidos_futbol(id uuid primary key,competicion_id uuid,temporada_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,
                        fecha_partido timestamptz,fuente_datos text,local_goles_et int,visitante_goles_et int,estado text,
                        local_goles_total int,visitante_goles_total int,local_corners_total int,visitante_corners_total int,
                        local_disparos_total int,visitante_disparos_total int,local_disparos_arco int,visitante_disparos_arco int,
                        ganador_id uuid,diferencia_goles int,datos_corners_completos boolean,datos_disparos_completos boolean,
                        datos_completos boolean,valido boolean,resultado_final text,url_referencia text,actualizado_en timestamptz,
                        local_goles_1t int,local_goles_2t int,visitante_goles_1t int,visitante_goles_2t int,
                        local_penales int,visitante_penales int,hubo_penales boolean,hubo_tiempo_extra boolean);
                ''')
                c.execute('INSERT INTO competiciones_futbol VALUES(%s,%s,NULL)',(COMP,'ESP_LALIGA'))
                c.execute('INSERT INTO equipos_futbol(id,nombre) VALUES(%s,%s),(%s,%s)',(CLUB_A,'Club A',CLUB_B,'Club B'))
                c.execute((Path(__file__).resolve().parents[1]/'migrations/2026-10-15_vinculos_espn_futbol.sql').read_text())
            yield url
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))


@pytest.mark.integracion
def test_ingesta_identidad_idempotencia_y_revision_conserva_nulos(futbol_db):
    with psycopg.connect(futbol_db) as c:
        plan=planificar(c,manifiesto(),[lote()])
        assert aplicar_plan(c,plan)=={'insertados':1,'actualizados':0,'eventos':1}
        assert aplicar_plan(c,plan)['actualizados']==0
        assert c.execute('SELECT local_goles_total,local_corners_total,local_goles_et,datos_completos FROM partidos_futbol').fetchone()==(0,None,None,False)
        revisado=lote();revisado['observado_en']='2026-10-02T00:00Z'
        revisado['eventos'][0]['local_goles']=1
        assert aplicar_plan(c,planificar(c,manifiesto(),[revisado]))['actualizados']==1
        assert aplicar_plan(c,planificar(c,manifiesto(),[lote()]))['actualizados']==0
        assert c.execute('SELECT local_goles_total FROM partidos_futbol').fetchone()==(1,)
        assert c.execute('SELECT count(*) FROM temporadas_futbol').fetchone()==(1,)
        assert c.execute('SELECT count(*) FROM equipos_fuente_espn_futbol').fetchone()==(2,)


@pytest.mark.integracion
def test_ingesta_historica_no_cambia_afiliacion_actual_del_club(futbol_db):
    otra_competicion = uuid4()
    with psycopg.connect(futbol_db) as c:
        c.execute('UPDATE equipos_futbol SET competicion_principal_id=%s WHERE id=%s',
                  (otra_competicion, CLUB_A))
        aplicar_plan(c, planificar(c, manifiesto(), [lote()]))
        assert c.execute('SELECT competicion_principal_id FROM equipos_futbol WHERE id=%s',
                         (CLUB_A,)).fetchone()[0] == otra_competicion
        assert c.execute('SELECT competicion_principal_id FROM equipos_futbol WHERE id=%s',
                         (CLUB_B,)).fetchone()[0] is None


@pytest.mark.integracion
def test_no_enlaza_por_nombre_parecido_y_revierte_ante_duplicado(futbol_db):
    with psycopg.connect(futbol_db,autocommit=True) as c:
        mal=lote();mal['eventos'][0]['local_nombre']='Club A parecido'
        with pytest.raises(ValueError,match='mapeo exacto'):
            planificar(c,manifiesto(),[mal])
        c.execute('INSERT INTO partidos_futbol(id,competicion_id,equipo_local_id,equipo_visitante_id,fecha_partido,fuente_datos) VALUES(%s,%s,%s,%s,%s,%s)',
                  (uuid4(),COMP,CLUB_A,CLUB_B,'2026-09-01T12:00Z','SOFASCORE'))
        with pytest.raises(ValueError,match='duplicado'):
            aplicar_plan(c,planificar(c,manifiesto(),[lote()]))
        assert c.execute('SELECT count(*) FROM temporadas_futbol').fetchone()==(0,)
        assert c.execute('SELECT count(*) FROM equipos_fuente_espn_futbol').fetchone()==(0,)
        assert c.execute('SELECT count(*) FROM partidos_futbol').fetchone()==(1,)


@pytest.mark.integracion
def test_abandonado_no_se_convierte_en_final_o_programado(futbol_db):
    datos=lote();datos['n_finales']=0
    datos['eventos'][0].update(final_acreditado=False,estado_fuente='STATUS_ABANDONED',local_goles=None,visitante_goles=None)
    with psycopg.connect(futbol_db) as c:
        aplicar_plan(c,planificar(c,manifiesto(),[datos]))
        assert c.execute('SELECT estado,local_goles_total,visitante_goles_total,resultado_final FROM partidos_futbol').fetchone()==('SUSPENDIDO',None,None,None)


@pytest.mark.integracion
def test_programado_vinculado_se_actualiza_sin_insertar_otro_partido(futbol_db):
    previo=lote();previo['n_finales']=0
    previo['eventos'][0].update(final_acreditado=False,estado_fuente='STATUS_SCHEDULED',
                              local_goles=None,visitante_goles=None)
    with psycopg.connect(futbol_db) as c:
        aplicar_plan(c,planificar(c,manifiesto(),[previo]))
        ident=c.execute('SELECT id FROM partidos_futbol').fetchone()[0]
        final=lote();final['observado_en']='2026-10-02T00:00Z'
        r=aplicar_plan(c,planificar(c,manifiesto(),[final]))
        assert r=={'insertados':0,'actualizados':1,'eventos':1}
        assert c.execute('SELECT id,estado,local_goles_total,visitante_goles_total FROM partidos_futbol').fetchall()==[(ident,'FINALIZADO',0,2)]
        assert aplicar_plan(c,planificar(c,manifiesto(),[final]))['actualizados']==0


@pytest.mark.integracion
def test_club_en_liga_y_copa_se_mapea_sin_cambiar_afiliacion(futbol_db):
    comp_copa=uuid4()
    m=manifiesto();m['temporadas']={'esp.copa_del_rey':m['temporadas']['esp.1']}
    for e in m['equipos']:e['ligas']=['esp.1','esp.copa_del_rey']
    datos=lote();datos['liga']='esp.copa_del_rey';datos['eventos'][0]['liga']='esp.copa_del_rey'
    with psycopg.connect(futbol_db) as c:
        c.execute('INSERT INTO competiciones_futbol VALUES(%s,%s,NULL)',(comp_copa,'ESP_COPA'))
        aplicar_plan(c,planificar(c,m,[datos]))
        assert c.execute('SELECT competicion_id FROM partidos_futbol').fetchone()[0]==comp_copa
        assert c.execute('SELECT competicion_principal_id FROM equipos_futbol WHERE id=%s',(CLUB_A,)).fetchone()[0] is None


@pytest.mark.integracion
def test_conciliacion_legacy_exige_huella_y_conserva_id(futbol_db):
    from scripts.sincronizar_espn_futbol import huella_fila
    from psycopg.rows import dict_row
    temporada,partido=uuid4(),uuid4()
    with psycopg.connect(futbol_db) as c:
        c.execute('INSERT INTO temporadas_futbol(id,competicion_id,nombre,anio_inicio,anio_fin) VALUES(%s,%s,%s,2026,2027)',(temporada,COMP,'2026-2027'))
        c.execute('INSERT INTO partidos_futbol(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,fecha_partido,fuente_datos,estado) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                  (partido,COMP,temporada,CLUB_A,CLUB_B,'2026-09-01T07:00Z','SOFASCORE','PROGRAMADO'))
        with c.cursor(row_factory=dict_row) as cur:
            antes=cur.execute('SELECT * FROM partidos_futbol WHERE id=%s',(partido,)).fetchone()
        m=manifiesto();m['conciliaciones']=[{'liga':'esp.1','id_fuente':'100','partido_id':str(partido),
            'huella_antes':huella_fila(antes),'justificacion':'IDs de clubes, competición, temporada y desfase de cinco horas revisados.'}]
        malo=deepcopy(m);malo['conciliaciones'][0]['huella_antes']='0'*64
        with pytest.raises(ValueError,match='Conciliación cambió'):
            aplicar_plan(c,planificar(c,malo,[lote()]))
        assert aplicar_plan(c,planificar(c,m,[lote()]))=={'insertados':0,'actualizados':1,'eventos':1}
        assert c.execute('SELECT id,estado FROM partidos_futbol').fetchall()==[(partido,'FINALIZADO')]
        assert aplicar_plan(c,planificar(c,m,[lote()]))['actualizados']==0


@pytest.mark.integracion
def test_final_reglamentario_se_completa_con_et_sin_inventar_goles_en_segundo_tiempo(futbol_db):
    from scripts.sincronizar_espn_futbol import huella_fila
    from psycopg.rows import dict_row
    temporada,partido=uuid4(),uuid4()
    with psycopg.connect(futbol_db) as c:
        c.execute('INSERT INTO temporadas_futbol(id,competicion_id,nombre,anio_inicio,anio_fin) VALUES(%s,%s,%s,2026,2027)',(temporada,COMP,'2026-2027'))
        c.execute('INSERT INTO partidos_futbol(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,fecha_partido,fuente_datos,estado,local_goles_1t,local_goles_2t,local_goles_et,local_goles_total,visitante_goles_1t,visitante_goles_2t,visitante_goles_et,visitante_goles_total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,1,2,0,3,0,0,0,0)',
                  (partido,COMP,temporada,CLUB_A,CLUB_B,'2026-09-01T12:00Z','SOFASCORE','FINALIZADO'))
        with c.cursor(row_factory=dict_row) as cur:antes=cur.execute('SELECT * FROM partidos_futbol').fetchone()
        final=lote();ev=final['eventos'][0];ev.update(estado_fuente='STATUS_FINAL_AET',local_goles=5,visitante_goles=0,sha256_boxscore='b'*64)
        ev['periodos']={'contrato':'ESPN_EXPLICIT_HALVES_ET_PEN_V1','ganador':'local','campos':{
            'local_goles_1t':1,'local_goles_2t':2,'local_goles_et':2,
            'visitante_goles_1t':0,'visitante_goles_2t':0,'visitante_goles_et':0,
            'local_penales':None,'visitante_penales':None,'hubo_penales':False,'hubo_tiempo_extra':True}}
        m=manifiesto();m['conciliaciones']=[{'liga':'esp.1','id_fuente':'100','partido_id':str(partido),
            'huella_antes':huella_fila(antes),'justificacion':'Final con ET acreditado por summary','tipo':'FINAL_VALIDADO_EXPLICITAMENTE'}]
        assert aplicar_plan(c,planificar(c,m,[final]))['actualizados']==1
        assert c.execute('SELECT id,local_goles_1t,local_goles_2t,local_goles_et,local_goles_total FROM partidos_futbol').fetchone()==(partido,1,2,2,5)
        assert aplicar_plan(c,planificar(c,m,[final]))['actualizados']==0

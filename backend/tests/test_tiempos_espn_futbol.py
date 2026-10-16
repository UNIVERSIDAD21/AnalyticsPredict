"""Contrato de mitades y escritura idempotente sobre SQL sintético real."""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import os
from pathlib import Path
from uuid import uuid4

import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict,make_conninfo

from db import PoolAplicacion
from servicios.tiempos_espn_futbol import interpretar_tiempos,validar_observacion,construir_plan,aplicar_observaciones
from scripts.auditar_fuente_espn_soccer import FuenteNoDisponible


def fixture_fuente():
    inicio=(datetime.now(timezone.utc)-timedelta(days=4)).isoformat()
    esperado={'liga':'eng.1','id_fuente':'123','inicio_utc':inicio,
              'local_id_fuente':'1','visitante_id_fuente':'2','local_goles':2,'visitante_goles':1}
    payload={'format':{'regulation':{'periods':2,'slug':'half'}},'header':{'id':'123','competitions':[
        {'id':'123','date':inicio,'status':{'type':{'completed':True,'name':'STATUS_FULL_TIME'}},
         'competitors':[{'homeAway':'home','team':{'id':'1'},'score':'2','linescores':[{'displayValue':'0'},{'displayValue':'2'}]},
                        {'homeAway':'away','team':{'id':'2'},'score':'1','linescores':[{'displayValue':'0'},{'displayValue':'1'}]}]}]}}
    return payload,esperado


def test_periodos_explicitos_conservan_ceros_y_no_derivan_de_ft():
    payload,ev=fixture_fuente();dato=interpretar_tiempos(payload,ev)
    assert [dato[c] for c in ('local_goles_1t','local_goles_2t','visitante_goles_1t','visitante_goles_2t')]==[0,2,0,1]
    assert len(dato['sha256_payload'])==64
    obs={**dato,'observado_en':datetime.now(timezone.utc).isoformat()}
    validar_observacion(obs)
    obs['observado_en']=ev['inicio_utc']
    with pytest.raises(ValueError):validar_observacion(obs)


@pytest.mark.parametrize('cambio',['id','inicio','equipo','ft','falta_mitad','extra','inconsistencia','orden','no_final','formato'])
def test_rechaza_ausencias_ambiguedad_y_contradicciones(cambio):
    payload,ev=fixture_fuente();c=payload['header']['competitions'][0];home=c['competitors'][0]
    if cambio=='id':payload['header']['id']='otro'
    if cambio=='inicio':c['date']=(datetime.now(timezone.utc)-timedelta(days=3)).isoformat()
    if cambio=='equipo':home['team']['id']='3'
    if cambio=='ft':home['score']='3'
    if cambio=='falta_mitad':home['linescores'].pop()
    if cambio=='extra':home['linescores'].append({'displayValue':'0'})
    if cambio=='inconsistencia':home['linescores'][0]['displayValue']='1'
    if cambio=='orden':home['linescores'][0]['period']=2
    if cambio=='no_final':c['status']['type']['completed']=False
    if cambio=='formato':payload['format']['regulation']['periods']=4
    with pytest.raises(FuenteNoDisponible):interpretar_tiempos(payload,ev)


def test_sql_aplica_una_vez_rechaza_conflicto_y_preserva_otras_columnas():
    url=os.environ.get('DATABASE_URL') or ''
    if not conninfo_to_dict(url).get('dbname','').startswith('ap_suite_test_'):
        pytest.skip('Solo PostgreSQL sintético desechable')
    schema='ap_tiempos_'+uuid4().hex
    admin=PoolAplicacion(url,min_size=1,max_size=1,open=True)
    payload,ev=fixture_fuente();pid=uuid4();obs={**interpretar_tiempos(payload,ev),'partido_id':str(pid),'observado_en':datetime.now(timezone.utc).isoformat()}
    try:
        with admin.connection() as c:
            c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
            c.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
            c.execute('''CREATE TABLE partidos_futbol(id uuid PRIMARY KEY,fuente_datos text,estado text,valido boolean,
                fecha_partido timestamptz,local_goles_total int,visitante_goles_total int,local_goles_1t int,
                local_goles_2t int,visitante_goles_1t int,visitante_goles_2t int,local_corners_total int,actualizado_en timestamptz);
                CREATE TABLE partidos_fuente_espn_futbol(liga text,id_fuente text,partido_id uuid UNIQUE,evidencia jsonb,PRIMARY KEY(liga,id_fuente))''')
            c.execute("INSERT INTO partidos_futbol VALUES(%s,'ESPN_SOCCER','FINALIZADO',true,%s,2,1,NULL,NULL,NULL,NULL,7,NULL)",[pid,ev['inicio_utc']])
            from psycopg.types.json import Jsonb
            c.execute("INSERT INTO partidos_fuente_espn_futbol VALUES('eng.1','123',%s,%s)",[pid,Jsonb(ev)])
            ddl=(Path(__file__).parents[1]/'migrations/2026-10-16_tiempos_goles_espn.sql').read_text()
            c.execute(ddl[ddl.index('CREATE TABLE'):ddl.rindex('COMMIT;')])
        pool=PoolAplicacion(make_conninfo(url,options=f'-c search_path={schema}'),min_size=1,max_size=1,open=True)
        try:
            with pool.connection() as c:
                assert construir_plan(c,[obs])[0]['cambia'] is True
                assert aplicar_observaciones(c,[obs])['partidos_completados']==1
                assert aplicar_observaciones(c,[obs])=={'partidos_completados':0,'evidencias_insertadas':0,'eventos_verificados':1}
                assert c.execute('SELECT local_corners_total,local_goles_total,local_goles_1t FROM partidos_futbol').fetchone()==(7,2,0)
                malo=deepcopy(obs);malo['local_goles_1t']=1;malo['local_goles_2t']=1
                with pytest.raises(ValueError,match='contradictoria'):aplicar_observaciones(c,[malo])
                assert c.execute('SELECT count(*) FROM observaciones_tiempos_espn_futbol').fetchone()[0]==1
        finally:pool.close()
    finally:
        with admin.connection() as c:c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))
        admin.close()

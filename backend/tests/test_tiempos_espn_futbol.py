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
            c.execute('ALTER TABLE partidos_futbol ADD COLUMN local_corners_1t int, ADD COLUMN local_corners_2t int, ADD COLUMN visitante_corners_1t int, ADD COLUMN visitante_corners_2t int, ADD COLUMN visitante_corners_total int DEFAULT 1')
            c.execute("""ALTER TABLE partidos_futbol ADD COLUMN datos_corners_completos boolean DEFAULT false, ADD COLUMN local_goles_et int DEFAULT 0;
                CREATE FUNCTION derivar_completitud() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN NEW.datos_corners_completos = NEW.local_corners_1t IS NOT NULL AND
                  NEW.local_corners_2t IS NOT NULL AND NEW.visitante_corners_1t IS NOT NULL AND
                  NEW.visitante_corners_2t IS NOT NULL; RETURN NEW; END; $$;
                CREATE TRIGGER calcular_totales BEFORE UPDATE ON partidos_futbol
                FOR EACH ROW EXECUTE FUNCTION derivar_completitud()""")
            c.execute("INSERT INTO partidos_futbol(id,fuente_datos,estado,valido,fecha_partido,local_goles_total,visitante_goles_total,local_goles_1t,local_goles_2t,visitante_goles_1t,visitante_goles_2t,local_corners_total,actualizado_en) VALUES(%s,'ESPN_SOCCER','FINALIZADO',true,%s,2,1,NULL,NULL,NULL,NULL,7,NULL)",[pid,ev['inicio_utc']])
            from psycopg.types.json import Jsonb
            c.execute("INSERT INTO partidos_fuente_espn_futbol VALUES('eng.1','123',%s,%s)",[pid,Jsonb(ev)])
            ddl=(Path(__file__).parents[1]/'migrations/2026-10-16_tiempos_goles_espn.sql').read_text()
            c.execute(ddl[ddl.index('CREATE TABLE'):ddl.rindex('COMMIT;')])
        pool=PoolAplicacion(make_conninfo(url,options=f'-c search_path={schema}'),min_size=1,max_size=1,open=True)
        try:
            with pool.connection() as c:
                assert construir_plan(c,[obs])[0]['cambia'] is True
                with c.pipeline():
                    assert aplicar_observaciones(c,[obs])=={'partidos_completados':1,'evidencias_insertadas':1,'eventos_verificados':1}
                    assert aplicar_observaciones(c,[obs])=={'partidos_completados':0,'evidencias_insertadas':0,'eventos_verificados':1}
                assert c.execute('SELECT local_corners_total,local_goles_total,local_goles_1t FROM partidos_futbol').fetchone()==(7,2,0)
                malo=deepcopy(obs);malo['local_goles_1t']=1;malo['local_goles_2t']=1
                with pytest.raises(ValueError,match='contradictoria'):aplicar_observaciones(c,[malo])
                assert c.execute('SELECT count(*) FROM observaciones_tiempos_espn_futbol').fetchone()[0]==1
                from servicios.tiempos_espn_futbol import CONTRATO_COMPLETO
                completa={**obs,'contrato':CONTRATO_COMPLETO,'local_corners_total':7,'visitante_corners_total':1,
                    'local_corners_1t':3,'local_corners_2t':4,'visitante_corners_1t':0,'visitante_corners_2t':1}
                assert aplicar_observaciones(c,[completa])['partidos_completados']==1
                assert aplicar_observaciones(c,[completa])['partidos_completados']==0
                assert c.execute('SELECT local_corners_total,local_corners_1t,visitante_corners_1t,datos_corners_completos FROM partidos_futbol').fetchone()==(7,3,0,True)
                c.execute('UPDATE partidos_futbol SET local_goles_et=1')
                with pytest.raises(ValueError,match='Prórroga'):aplicar_observaciones(c,[completa])
                assert c.execute('SELECT local_goles_total FROM partidos_futbol').fetchone()==(2,)
        finally:pool.close()
    finally:
        with admin.connection() as c:c.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))
        admin.close()


def fixture_corners():
    payload,ev=fixture_fuente()
    ev.update(local_nombre='Casa',visitante_nombre='Fuera',local_corners=2,visitante_corners=1)
    payload['header']['competitions'][0].update(playByPlaySource='full',commentaryAvailable=True)
    payload['boxscore']={'teams':[{'team':{'id':ident},'statistics':[{'name':'wonCorners','displayValue':str(n)}]}
                                     for ident,n in [('1',2),('2',1)]]}
    specs=[('kickoff',1,None),('corner-awarded',1,'Casa'),('halftime',1,None),
           ('corner-awarded',2,'Fuera'),('corner-awarded',2,'Casa'),('end-regular-time',2,None)]
    payload['commentary']=[{'sequence':i,'play':{'id':str(i),'type':{'type':tipo},
        'period':{'number':periodo},'team':{'displayName':equipo}}}
        for i,(tipo,periodo,equipo) in enumerate(specs)]
    origen=datetime.fromisoformat(ev['inicio_utc'])
    minutos=[0,20,50,70,80,100]
    for c,m in zip(payload['commentary'],minutos):
        c['play']['wallclock']=(origen+timedelta(minutes=m)).isoformat()
    payload['keyEvents']=[deepcopy(c['play']) for c in payload['commentary']
                          if c['play']['type']['type'] in ('kickoff','halftime','end-regular-time')]
    return payload,ev


def test_corners_por_evento_concilian_ft_y_preservan_cero_real():
    from servicios.tiempos_espn_futbol import interpretar_tiempos_completos,CONTRATO_COMPLETO
    payload,ev=fixture_corners();dato=interpretar_tiempos_completos(payload,ev)
    assert dato['contrato']==CONTRATO_COMPLETO
    assert [dato[c] for c in ('local_corners_1t','local_corners_2t','visitante_corners_1t','visitante_corners_2t')]==[1,1,0,1]
    validar_observacion({**dato,'observado_en':datetime.now(timezone.utc).isoformat()})


@pytest.mark.parametrize('cambio',['sin_periodo','duplicado','equipo','secuencia','sin_limite','ft','fuente_parcial','fuera_limites'])
def test_no_reconstruye_corners_con_cronologia_incompleta(cambio):
    from servicios.tiempos_espn_futbol import interpretar_tiempos_completos
    p,e=fixture_corners()
    if cambio=='sin_periodo':p['commentary'][1]['play'].pop('period')
    if cambio=='duplicado':p['commentary'][4]['play']['id']='1'
    if cambio=='equipo':p['commentary'][1]['play']['team']['displayName']='Parecido'
    if cambio=='secuencia':p['commentary'][1]['sequence']=99
    if cambio=='sin_limite':p['keyEvents'].pop()
    if cambio=='ft':p['boxscore']['teams'][0]['statistics'][0]['displayValue']='3'
    if cambio=='fuera_limites':p['commentary'][1]['play']['wallclock']=p['keyEvents'][-1]['wallclock']
    if cambio=='fuente_parcial':p['header']['competitions'][0]['playByPlaySource']='partial'
    with pytest.raises(FuenteNoDisponible):interpretar_tiempos_completos(p,e)


def test_limites_keyevents_no_requieren_play_en_comentario():
    from servicios.tiempos_espn_futbol import interpretar_tiempos_completos
    payload,ev=fixture_corners()
    for i in (0,2,5):payload['commentary'][i].pop('play')
    assert interpretar_tiempos_completos(payload,ev)['local_corners_1t']==1

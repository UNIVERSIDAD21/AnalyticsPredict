"""Contratos de fuente, idempotencia, conflicto y rollback sin proveedores reales."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import json
import pytest
from psycopg.types.json import Jsonb
from servicios.fuentes_agenda import meses, hora_espn, puntos_final, euro, tareas
from servicios.horarios_agenda import requiere_reconstruccion
from servicios.sincronizacion_agendas import aplicar, huella, filas, plano
from servicios.transporte_agenda import ClienteAgenda, FuenteNoDisponible
from test_ingesta_futbol_americas_pg import db_local  # noqa: F401


def test_meses_no_son_60_dias_y_wnba_cruza_anio():
    assert meses(date(2026,12,31),2)==date(2027,2,28)
    assert meses(date(2026,10,26),3)==date(2027,1,26)
    ts=list(tareas(date(2027,1,1)))
    assert 'E2026' in ts[0]['url']
    assert any(t['grupo']=='wnba' and t['periodo']=='2027-04-02' for t in ts)


@pytest.mark.parametrize('offset,expected',[(-1,False),(0,True),(1,True)])
def test_inicio_exacto_cambio_zona_y_no_estado_falso(offset,expected):
    start=datetime(2026,11,1,5,tzinfo=timezone.utc)
    h={'precision_fecha':'HORA','inicio_utc':start,'estado':'PROGRAMADO'}
    assert requiere_reconstruccion(date(2026,10,31),h,start+timedelta(seconds=offset)) is expected
    assert requiere_reconstruccion(date(2099,1,1),None,start)
    assert requiere_reconstruccion(date(2099,1,1),{**h,'estado':'CANCELADO'},start-timedelta(seconds=1))
    with pytest.raises(ValueError):requiere_reconstruccion(date(2026,1,1),h,datetime(2026,1,1))


def test_hora_tbd_y_date_no_son_medianoche():
    e={'date':'2026-10-27','competitions':[{}]}
    assert hora_espn(e)==(None,'2026-10-27')
    e['date']='2026-10-27T00:00:00Z';e['competitions'][0]['timeValid']=False
    assert hora_espn(e)[0] is None
    e['competitions'][0]['timeValid']=True
    assert hora_espn(e)[0]=='2026-10-27T00:00:00+00:00'


def final():
    return {'competitions':[{'competitors':[
        {'homeAway':'home','score':'100','linescores':[{'value':x,'period':i+1} for i,x in enumerate([20,20,25,25,10])]},
        {'homeAway':'away','score':'98','linescores':[{'value':x,'period':i+1} for i,x in enumerate([25,20,25,20,8])]}]}]}


def test_ot_observado_y_null_no_cero():
    e=final();r=puntos_final(e)
    assert r['local_ot']==10 and r['visitante_ot']==8 and r['hubo_overtime']
    e['competitions'][0]['competitors'][0]['linescores'][0]['value']=None
    with pytest.raises(ValueError):puntos_final(e)
    e=final();e['competitions'][0]['competitors'][0]['score']='0'
    with pytest.raises(ValueError):puntos_final(e)


def test_mismo_instante_no_produce_revision_falsa():
    utc=datetime(2026,10,27,2,tzinfo=timezone.utc)
    cot=utc.astimezone(timezone(timedelta(hours=-5)))
    assert plano({'inicio':utc})==plano({'inicio':cot})
    assert huella(utc)==huella(cot)


class Sesion:
    def __init__(self,status=200):self.n=0;self.status=status
    def get(self,*args,**kw):
        self.n+=1
        return type('R',(),{'status_code':self.status,'content':b'{"events":[]}', 'headers':{'Retry-After':'120'}})()


def test_cache_y_429_persisten_y_no_evasion(tmp_path):
    s=Sesion();c=ClienteAgenda(tmp_path,session=s,reloj=lambda:1000,dormir=lambda _:None)
    url='https://site.api.espn.com/prueba'
    a,m=c.obtener(url);assert m['cache'] is False
    assert c.obtener(url)[1]['cache'] is True and s.n==1
    s.status=429
    with pytest.raises(FuenteNoDisponible,match='429'):c.obtener(url+'2')
    c2=ClienteAgenda(tmp_path,session=s,reloj=lambda:1001,dormir=lambda _:None)
    with pytest.raises(FuenteNoDisponible,match='pausa'):c2.obtener(url+'3')
    assert s.n==2
    with pytest.raises(ValueError):c2.obtener('https://example.org/no')


@pytest.mark.integracion
def test_aplicacion_sql_es_atomica_beforeimage_y_revisiones(db_local):
    c=db_local;pid=str(uuid4());comp=str(uuid4());h=str(uuid4());a=str(uuid4());season=str(uuid4())
    c.execute("CREATE TABLE revisiones_agenda(id uuid,deporte text,partido_id uuid,competicion_codigo text,revision_sha256 text,antes jsonb,despues jsonb,observado_en timestamptz,procedencia jsonb,UNIQUE(deporte,partido_id,revision_sha256))")
    c.execute("INSERT INTO competiciones_futbol(id,codigo) VALUES(%s,'TEST')",(comp,))
    c.execute('INSERT INTO equipos_futbol(id,nombre) VALUES(%s,\'A\'),(%s,\'B\')',(h,a))
    c.execute('INSERT INTO temporadas_futbol(id,competicion_id) VALUES(%s,%s)',(season,comp))
    vals={'id':pid,'competicion_id':comp,'temporada_id':season,'equipo_local_id':h,'equipo_visitante_id':a,'fecha_partido':'2026-10-26T20:00:00+00:00','estado':'PROGRAMADO'}
    op={'tabla':'partidos_futbol','clave':'id','id':pid,'antes':None,'valores':vals,'codigo':'TEST','deporte':'futbol','observado_en':'2026-10-26T00:00:00Z','procedencia':{}}
    p={'operaciones':[op]};p['sha256']=huella(p)
    with c.transaction(force_rollback=True):
        assert aplicar(c,p)==1
        assert c.execute('SELECT count(*) n FROM revisiones_agenda').fetchone()['n']==1
    assert not filas(c,'SELECT * FROM partidos_futbol')
    with c.transaction():aplicar(c,p)
    with pytest.raises(ValueError,match='Before-image'):
        with c.transaction():aplicar(c,p)
    row=filas(c,'SELECT * FROM partidos_futbol')[0]
    other={**op,'antes':row,'valores':{'estado':'FINALIZADO'}}
    bad={**op,'id':str(uuid4()),'valores':{**vals,'id':str(uuid4()),'equipo_local_id':str(uuid4())}}
    p2={'operaciones':[other,bad]};p2['sha256']=huella(p2)
    with pytest.raises(Exception):
        with c.transaction():aplicar(c,p2)
    assert filas(c,'SELECT * FROM partidos_futbol')[0]['estado']=='PROGRAMADO'


def entorno_baloncesto(c):
    c.execute('CREATE TABLE competiciones_baloncesto(id uuid PRIMARY KEY,codigo text)')
    c.execute('CREATE TABLE temporadas_baloncesto(id uuid,competicion_id uuid,anio_inicio int,anio_fin int)')
    c.execute('CREATE TABLE equipos(id uuid PRIMARY KEY,nombre text,competicion_principal_id uuid)')
    c.execute('CREATE TABLE equipos_baloncesto(id uuid,espn_team_id text,competicion_principal_id uuid)')
    c.execute('''CREATE TABLE partidos_baloncesto(id uuid PRIMARY KEY,competicion_id uuid,temporada_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,fecha_partido date,tipo_partido text,valido bool,source_game_id text,source text,espn_game_id text,local_total int,visitante_total int,actualizado_en timestamptz DEFAULT now())''')
    c.execute('CREATE TABLE fixtures_wnba(id uuid,source_game_id text)')
    for code in ('nba','wnba','euroleague'):
        cid=str(uuid4());c.execute('INSERT INTO competiciones_baloncesto VALUES(%s,%s)',(cid,code))
        if code=='nba':comp=cid
    h,a,season,pid=[str(uuid4()) for _ in range(4)]
    c.execute("INSERT INTO temporadas_baloncesto VALUES(%s,%s,2026,2027)",(season,comp))
    c.execute("INSERT INTO equipos VALUES(%s,'A',%s),(%s,'B',%s)",(h,comp,a,comp))
    c.execute("INSERT INTO partidos_baloncesto(id,competicion_id,temporada_id,equipo_local_id,equipo_visitante_id,fecha_partido,tipo_partido,valido,source_game_id,source,local_total,visitante_total) VALUES(%s,%s,%s,%s,%s,'2026-10-27','REG',true,'888','ESPN',0,0)",(pid,comp,season,h,a))
    from servicios.sincronizacion_agendas import MIGRACION
    c.execute(MIGRACION.read_text())
    return pid


@pytest.mark.integracion
def test_plan_preserva_id_fecha_y_revision_es_idempotente(db_local):
    from servicios.sincronizacion_agendas import planificar
    c=db_local;pid=entorno_baloncesto(c)
    r={'deporte':'baloncesto','codigo':'nba','proveedor':'ESPN','id_fuente':'888','anio':2027,'fase':'REG',
       'local_fuente':'1','visitante_fuente':'2','local_nombre':'A','visitante_nombre':'B',
       'inicio_utc':'2026-10-29T02:00:00+00:00','fecha_fuente':'2026-10-29','precision_fecha':'HORA',
       'zona_origen':'UTC','estado':'POSPUESTO','resultados':{},
       'evidencia':{'observado_en':'2026-10-26T20:00:00+00:00','sha256':'a'*64}}
    p=planificar(c,[r],[],[],date(2026,10,26))
    assert not p['incidencias'] and len(p['operaciones'])==1
    assert p['operaciones'][0]['tabla']=='horarios_baloncesto'
    with c.transaction():aplicar(c,p)
    assert str(c.execute('SELECT fecha_partido FROM partidos_baloncesto').fetchone()['fecha_partido'])=='2026-10-27'
    assert filas(c,'SELECT partido_id FROM horarios_baloncesto')[0]['partido_id']==pid
    assert not planificar(c,[r],[],[],date(2026,10,26))['operaciones']
    c.execute('UPDATE partidos_baloncesto SET source_game_id=NULL')
    r['inicio_utc']='2026-11-12T01:00:00+00:00';r['fecha_fuente']='2026-11-12'
    shifted=planificar(c,[r],[],[],date(2026,10,26))
    assert not shifted['incidencias'] and len(shifted['operaciones'])==1
    assert shifted['operaciones'][0]['id']==pid
    r['local_nombre']='B';r['visitante_nombre']='A'
    p=planificar(c,[r],[],[],date(2026,10,26))
    assert not p['operaciones'] and 'identidad' in p['incidencias'][0]['motivo']


def test_calibrador_sin_muestra_no_se_activa_y_preserva_push():
    from scripts.evaluar_agendas_temporal import calibrar,temperatura
    import numpy as np
    assert calibrar([])==(None,'CAL-calibrador <200 partidos')
    p=temperatura([.4,.5,.1],1.2)
    assert np.isclose(p.sum(),1) and p[2]>0
    assert temperatura([.4,.6,0],1.2)[2]==0
    rows=[{'entera':False,'raw':[.7,.3,0],'y':[i%2,(i+1)%2,0]} for i in range(220)]
    t,reason=calibrar(rows);assert .5<=t<=2 and reason is None


def test_tres_capturas_contradictorias_no_rehabilitan_evento(tmp_path):
    from servicios.fuentes_agenda import normalizar
    import hashlib
    tasks=[]
    for i,h in enumerate(('20','21','21')):
        event={'id':'987','date':f'2026-10-27T{h}:00:00Z','season':{'year':2027,'type':2},
               'status':{'type':{'name':'STATUS_SCHEDULED','completed':False}},
               'competitions':[{'competitors':[{'homeAway':'home','team':{'id':'1','displayName':'A'}},
                    {'homeAway':'away','team':{'id':'2','displayName':'B'}}]}]}
        raw=json.dumps({'events':[event]}).encode();f=tmp_path/str(i);f.write_bytes(raw)
        tasks.append({'grupo':'nba','periodo':str(i),'estado':'OK','evidencia':{
            'archivo':str(f),'sha256':hashlib.sha256(raw).hexdigest(),'observado_en':'2026-10-26T00:00:00Z'}})
    rows,issues,_=normalizar({'resultados':tasks},date(2026,10,26))
    assert not rows and any('contradictorias' in x['motivo'] for x in issues)

"""Integridad, no contaminación y recuperación de ingestas locales WNBA."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from ingesta_wnba import (MIGRACION, METRICAS, PUNTOS, alias_tecnico, digest, huella, importar,
                         leer_lote, validar_registro)
from scripts.importar_wnba import auditar, huellas
from scripts.run_suite_global_testdb import validar_admin_local


def registro(eid='100', final=True, fase='REG'):
    r = {'competicion':'wnba','fuente':'ESPN','contrato':'espn_wnba_v1',
         'duracion_regulacion_minutos':40,'source_game_id':eid,'temporada':2019,'fase':fase,
         'estado':'FINALIZADO' if final else 'POSPUESTO','final_completo':final,
         'inicio_utc':'2019-07-03T23:00:00+00:00','inicio_colombia':'2019-07-03T18:00:00-05:00',
         'local_id_fuente':'1','visitante_id_fuente':'2','local_nombre':'Participante W A','visitante_nombre':'Participante W B',
         'numero_prorrogas':0 if final else None,'ganador_id_fuente':'1' if final else None,
         'sede_neutral':False,'incidencias_estadisticas':[],
         'url_fuente':f'https://www.espn.com/wnba/game/_/gameId/{eid}',
         'evidencia':[{'sha256':'a'*64,'observado_utc':'2026-10-25T00:00:00Z',
                      'url':'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard?dates=20190703'}],
         'estadisticas':{s:{k:None for k in METRICAS} for s in ('home','away')} if final else None}
    for lado, puntos in [('local',[20,20,20,20]),('visitante',[15,20,15,20])]:
        for i,p in enumerate(puntos,1):r[f'{lado}_q{i}'] = p if final else None
        r[lado+'_regulacion'] = r[lado+'_total'] = sum(puntos) if final else None
        r[lado+'_ot'] = 0 if final else None
        r[lado+'_prorrogas'] = [] if final else None
    return r


def escribir_lote(path, rs=None, quarantine=None):
    rs = rs or [registro()]; quarantine = quarantine or []
    path.mkdir(exist_ok=True)
    values = {'partidos.jsonl':b''.join((json.dumps(r)+'\n').encode() for r in rs), 'partidos.csv':b'csv sintetico\n',
              'cuarentena.jsonl':b''.join((json.dumps(r)+'\n').encode() for r in quarantine),
              'pendientes.jsonl':b'', 'advertencias_estadisticas.jsonl':b'',
              'reporte.json':json.dumps({'desde':'2019-01-01','hasta':'2026-10-25',
                  'estado':'COMPLETO_CON_INCIDENCIAS','ventanas_pendientes':[], 'error':None,
                  'partidos_exportados':len(rs),'finales_completos':sum(r['final_completo'] for r in rs),
                  'no_finales':sum(not r['final_completo'] for r in rs),'incidencias_cuarentena':len(quarantine)}).encode()}
    for name,raw in values.items():(path/name).write_bytes(raw)
    (path/'SHA256SUMS').write_text(''.join(f'{digest(raw)}  {name}\n' for name,raw in values.items()))
    return path


@pytest.mark.parametrize('final',[True,False])
def test_contrato_final_y_no_final_sin_inventar_puntos(final):
    validar_registro(registro(final=final))


@pytest.mark.parametrize('key,value',[
    ('competicion','nba'),('fuente','OTRO'),('source_game_id',1),('temporada',2020),
    ('final_completo',False),('local_q1',True),('local_q1',None),('local_total',81),
    ('ganador_id_fuente','2'),('numero_prorrogas',1),('fase','ALLSTAR'),('evidencia',[]),
    ('inicio_utc','2019-07-03T23:00:00'),('inicio_colombia','2019-07-03T23:00:00+00:00')])
def test_rechaza_contradicciones(key,value):
    r=registro();r[key]=value
    with pytest.raises(ValueError):validar_registro(r)


@pytest.mark.parametrize('key',PUNTOS)
def test_no_final_jamas_admite_cero_o_lista_de_ot(key):
    r=registro(final=False);r[key]=[] if key.endswith('prorrogas') else 0
    with pytest.raises(ValueError):validar_registro(r)


def test_null_y_cero_estadistico_no_son_equivalentes():
    r=registro();r['estadisticas']['home']['robos']=0
    validar_registro(r)
    assert r['estadisticas']['home']['rebotes'] is None
    r['estadisticas']['home']['robos']=-1
    with pytest.raises(ValueError):validar_registro(r)


def test_alias_tecnico_resuelve_colision_sin_modificar_otros():
    first=alias_tecnico('132052',set())
    existing={'NBA',first}
    next_alias=alias_tecnico('132052',existing)
    assert len(next_alias)==3 and next_alias.startswith('W') and next_alias not in existing
    assert existing=={'NBA',first}


def test_estadisticas_concilian_y_apartados_permanecen_null():
    r=registro();r['estadisticas']['home'].update(campo_anotados=30,triples_anotados=10,libres_anotados=10)
    validar_registro(r)
    r['estadisticas']['home']['libres_anotados']=11
    with pytest.raises(ValueError,match='Tiros no concilian'):validar_registro(r)
    r=registro();r['incidencias_estadisticas']=[{'lado':'home','campo':'perdidas_totales'}]
    validar_registro(r)
    r['estadisticas']['home']['perdidas_totales']=0
    with pytest.raises(ValueError,match='apartado'):validar_registro(r)


def test_multi_ot_y_empate_previo():
    r=registro();r['visitante_q1']=25;r['visitante_regulacion']=80
    r.update(numero_prorrogas=2,local_prorrogas=[4,3],visitante_prorrogas=[4,2],
             local_ot=7,visitante_ot=6,local_total=87,visitante_total=86)
    validar_registro(r)
    r['visitante_prorrogas']=[3,3]
    with pytest.raises(ValueError,match='OT sin empate'):validar_registro(r)


def test_hashes_y_rutas_ambiguas(tmp_path):
    p=escribir_lote(tmp_path/'lote');assert len(leer_lote(p)['registros'])==1
    (p/'partidos.csv').write_text('alterado')
    with pytest.raises(ValueError,match='Hash'):leer_lote(p)
    (p/'SHA256SUMS').write_text('a'*64+'  ../escape\n')
    with pytest.raises(ValueError,match='Manifiesto'):leer_lote(p)


def test_cuarentena_disjunta_y_deduplicacion(tmp_path):
    a=registro();p=escribir_lote(tmp_path/'lote',[a,a])
    lote=leer_lote(p);assert lote['duplicados_entrada']==1 and len(lote['registros'])==1
    escribir_lote(p,[a],[{'source_game_id':'100'}])
    with pytest.raises(ValueError,match='Cuarentena'):leer_lote(p)
    b=deepcopy(a);b['estadisticas']['home']['robos']=0
    escribir_lote(p,[a,b])
    with pytest.raises(ValueError,match='conflictivo'):leer_lote(p)


@pytest.fixture
def wnbase():
    admin_url=os.getenv('TEST_PG_ADMIN_URL')
    if not admin_url:pytest.skip('PostgreSQL local desechable requerido')
    validar_admin_local(admin_url)
    name='ap_wnba_test_'+uuid4().hex
    with psycopg.connect(admin_url,autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        try:
            url=make_conninfo(admin_url,dbname=name,sslmode='disable')
            with psycopg.connect(url) as c:
                c.execute((Path(__file__).parent/'integracion/wnba_legacy_fixture.sql').read_text())
            yield url
        finally:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))


@pytest.mark.integracion
def test_pg_carga_idempotencia_null_copa_anual_aislamiento(wnbase,tmp_path):
    lote=leer_lote(escribir_lote(tmp_path/'lote',[registro(),registro('101',fase='COPA'),registro('102',False)],
                               [{'source_game_id':'666','codigo':'FINAL_EMPATE'}]))
    with psycopg.connect(wnbase) as c:
        protected=huellas(c,ajenas=True)
        c.execute(MIGRACION.read_text());c.execute(MIGRACION.read_text())
        first=importar(c,lote);assert first['insertados']==3 and first['resultados_insertados']==2
        assert first['equipos_creados']==2 and first['temporadas_creadas']==1
        audit=auditar(c,lote);assert audit['verificados']==3
        before=huellas(c);repeat=importar(c,lote)
        assert repeat['ya_existentes']==3 and repeat['insertados']==repeat['actualizados']==0
        assert huellas(c)==before and huellas(c,ajenas=True)==protected
        assert c.execute("select registro->'local_total',partido_id from partidos_fuente_wnba where source_game_id='102'").fetchone()==(None,None)
        assert c.execute("select count(*) from partidos_baloncesto").fetchone()[0]==2
        assert c.execute("select count(*) from equipos_baloncesto where espn_team_id='1'").fetchone()[0]==2
        assert c.execute("select count(*) from temporadas_baloncesto where anio_inicio=anio_fin and es_anual").fetchone()[0]==1


@pytest.mark.integracion
def test_pg_version_conflictiva_revierte_y_no_actualiza(wnbase,tmp_path):
    lote=leer_lote(escribir_lote(tmp_path/'lote'))
    with psycopg.connect(wnbase,autocommit=True) as c:
        with c.transaction():c.execute(MIGRACION.read_text());importar(c,lote)
        baseline=huellas(c)
        changed=deepcopy(lote);changed['registros'][0]['estadisticas']['home']['robos']=0
        with pytest.raises(ValueError,match='conflictiva'):
            with c.transaction():importar(c,changed)
        assert huellas(c)==baseline


@pytest.mark.integracion
def test_pg_ensayo_ddl_y_carga_se_revierten(wnbase,tmp_path):
    lote=leer_lote(escribir_lote(tmp_path/'lote'))
    with psycopg.connect(wnbase,autocommit=True) as c:
        baseline=huellas(c)
        with c.transaction(force_rollback=True):c.execute(MIGRACION.read_text());importar(c,lote)
        assert huellas(c)==baseline
        assert c.execute("select to_regclass('public.partidos_fuente_wnba')").fetchone()[0] is None
        assert c.execute("select count(*) from information_schema.columns where table_name='temporadas_baloncesto' and column_name='es_anual'").fetchone()[0]==0


@pytest.mark.integracion
def test_pg_otro_id_mismo_final_revierte_sin_reemplazar(wnbase,tmp_path):
    lote=leer_lote(escribir_lote(tmp_path/'lote'))
    with psycopg.connect(wnbase,autocommit=True) as c:
        with c.transaction():c.execute(MIGRACION.read_text());importar(c,lote)
        baseline=huellas(c)
        other=leer_lote(escribir_lote(tmp_path/'otro',[registro('999')]))
        with pytest.raises(psycopg.errors.UniqueViolation):
            with c.transaction():importar(c,other)
        assert huellas(c)==baseline


@pytest.mark.integracion
def test_pg_id_largo_en_catalogo_legacy_tres_caracteres(wnbase,tmp_path):
    r=registro();r['visitante_id_fuente']='132052'
    lote=leer_lote(escribir_lote(tmp_path/'lote',[r]))
    with psycopg.connect(wnbase) as c:
        c.execute(MIGRACION.read_text());importar(c,lote)
        assert len(c.execute("select abreviatura from equipos where nombre='Participante W B'").fetchone()[0])==3
        assert c.execute("select espn_team_id from equipos_baloncesto where nombre='Participante W B'").fetchone()[0]=='132052'
        assert c.execute("select abreviatura from equipos where nombre='Equipo NBA'").fetchone()[0]=='NBA'


@pytest.mark.integracion
def test_cli_respaldo_ensayo_aplicacion_y_verificacion(wnbase,tmp_path):
    if not __import__('shutil').which('pg_dump'):pytest.skip('pg_dump requerido')
    p=escribir_lote(tmp_path/'lote',[registro(),registro('101',False)])
    script=Path(__file__).parents[1]/'scripts/importar_wnba.py'
    env=os.environ.copy();env['DATABASE_URL']=wnbase
    def run(mode,folder,extra=()):
        return subprocess.run([sys.executable,str(script),'--entrada',str(p),'--salida',str(tmp_path/folder),
                               '--modo',mode,*extra],env=env,capture_output=True,text=True)
    r=run('ensayar','ensayo');assert r.returncode==0,r.stderr
    ensayo=tmp_path/'ensayo/reporte.json'
    r=run('aplicar','apply',['--ensayo',str(ensayo)]);assert r.returncode==0,r.stderr
    r=run('verificar','post');assert r.returncode==0,r.stderr
    with psycopg.connect(wnbase) as c:assert c.execute('select count(*) from partidos_baloncesto').fetchone()[0]==1
    # Baseline del ensayo inicial ya no sirve tras aplicar.
    r=run('aplicar','again',['--ensayo',str(ensayo)])
    assert r.returncode==3 and 'cambió desde' in r.stderr

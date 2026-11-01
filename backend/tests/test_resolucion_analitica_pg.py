"""Persistencia, aislamiento y concurrencia solo en PostgreSQL sintético local."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from types import SimpleNamespace
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg_pool import ConnectionPool
import pytest

from calidad.elegibilidad_futbol import METRICAS
from servicios.resolucion_analitica import procesar


@pytest.fixture
def banco(monkeypatch):
    url=os.environ.get('DATABASE_URL','')
    if not conninfo_to_dict(url).get('dbname','').startswith('ap_suite_test_'):
        pytest.skip('Requiere PostgreSQL sintético local')
    esquema='analitica_'+uuid4().hex
    with psycopg.connect(url,autocommit=True) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(esquema)))
    pool=ConnectionPool(make_conninfo(url,options=f'-c search_path={esquema} -c timezone=UTC'),min_size=1,max_size=3,kwargs={'prepare_threshold':None},open=True)
    pool.wait()
    with pool.connection() as c:
        c.execute('''CREATE TABLE competiciones_baloncesto(id uuid PRIMARY KEY,codigo text);
          CREATE TABLE partidos_baloncesto(id uuid PRIMARY KEY,competicion_id uuid,fecha_partido date,valido bool,
            local_q1 int,local_q2 int,local_q3 int,local_q4 int,local_ot int,local_total int,
            visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,visitante_ot int,visitante_total int);
          CREATE TABLE apuestas_analizadas(id bigserial PRIMARY KEY,deporte text,partido_id uuid,mercado text,lado text,
            linea numeric,probabilidad_sistema numeric,confianza text,payload jsonb,estado text DEFAULT 'PENDIENTE',
            resultado_outcome text,valor_real numeric,resultado_resumen text,creado_en timestamptz DEFAULT now(),actualizado_en timestamptz,
            decision_p_raw numeric,decision_p_calibrada numeric,decision_edge_real numeric,decision_score numeric,
            decision_sizing numeric,decision_valor_esperado numeric,decision_calibrador_id text,decision_modelo_version_id text,
            decision_fuente text,decision_devig_metodo text,decision_devig_overround numeric,decision_devig_p_mkt_fair numeric,
            decision_cuota numeric,decision_cuota_over numeric,decision_cuota_under numeric);
          CREATE TYPE mercado_futbol AS ENUM('GOLES_FT');
          CREATE TABLE predicciones_futbol(id uuid PRIMARY KEY,partido_id uuid,mercado text,linea numeric,
            valor_real numeric,outcome_binario bool,resultado text,resuelto bool DEFAULT false,
            fecha_partido timestamptz,timestamp_resolucion timestamptz,actualizado_en timestamptz,
            modelo_version_id int,competicion_id uuid,temporada_id uuid,equipo_local_id uuid,equipo_visitante_id uuid,
            equipo_local_nombre text,equipo_visitante_nombre text,linea_es_sintetica bool,media_predicha numeric,
            desviacion_predicha numeric,prob_over numeric,prob_under numeric,prob_over_calibrada numeric,
            prob_under_calibrada numeric,intervalo_inferior numeric,intervalo_superior numeric,nivel_intervalo int,calibrador_id uuid,
            CONSTRAINT uq_prediccion_futbol UNIQUE(partido_id,mercado,linea,linea_es_sintetica));
          CREATE TABLE apuestas(id int,resultado text);
          INSERT INTO apuestas VALUES(1,'PENDIENTE');''')
        campos=','.join(f'{x} int' for cols in METRICAS.values() for x in cols)
        c.execute(f'''CREATE TABLE partidos_futbol(id uuid PRIMARY KEY,fecha_partido timestamptz,valido bool,
          estado text,hubo_tiempo_extra bool,local_goles_et int,visitante_goles_et int,{campos})''')
    monkeypatch.setenv('APUESTAS_ANALIZADAS_RUNTIME_DDL','0')
    yield pool
    pool.close()
    with psycopg.connect(url,autocommit=True) as c:
        c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(esquema)))


def juego(pool):
    uid=uuid4()
    with pool.connection() as c:
        c.execute('''INSERT INTO partidos_futbol(id,fecha_partido,valido,estado,hubo_tiempo_extra,
          local_goles_total,visitante_goles_total,local_corners_total,visitante_corners_total)
          VALUES(%s,'2026-01-01T20:00:00Z',true,'FINALIZADO',false,2,0,8,4)''',(uid,))
    return uid


def emitir(pool,jid,mercado='CORNERS_FT',linea=9.5,estado='PENDIENTE',valor=None,outcome=None):
    with pool.connection() as c:
        return c.execute('''INSERT INTO apuestas_analizadas(deporte,partido_id,mercado,lado,linea,payload,estado,valor_real,resultado_outcome)
          VALUES('futbol',%s,%s,'OVER',%s,'{"fuente":"analisis_futbol","original":true}',%s,%s,%s) RETURNING id''',
          (jid,mercado,linea,estado,valor,outcome)).fetchone()[0]


def estado(pool):
    with pool.connection() as c:
        return c.execute('SELECT to_jsonb(a) FROM apuestas_analizadas a ORDER BY id').fetchall()


def test_simulacion_historia_inmutable_y_outcome_correcto(banco):
    jid=juego(banco);uid=emitir(banco,jid);viejo=emitir(banco,jid,estado='FINALIZADA',valor=2,outcome='PERDIDA')
    antes=estado(banco)
    r=procesar(pool=banco,simular=True,auditar_finalizadas=True)
    assert r['total']==1 and r['diferencias_historicas']==1 and estado(banco)==antes
    assert procesar(pool=banco,simular=False)['total']==1
    with banco.connection() as c:
        nuevo=c.execute('SELECT valor_real,resultado_outcome,payload FROM apuestas_analizadas WHERE id=%s',(uid,)).fetchone()
        assert nuevo[:2]==(12,'GANADA') and nuevo[2]['original'] is True
        assert nuevo[2]['resolucion_analitica']['prospectiva_certificada'] is False
        assert c.execute('SELECT valor_real,resultado_outcome FROM apuestas_analizadas WHERE id=%s',(viejo,)).fetchone()==(2,'PERDIDA')
        assert c.execute('SELECT resultado FROM apuestas').fetchone()[0]=='PENDIENTE'
    assert procesar(pool=banco,simular=False)['total']==0


def test_null_estimado_y_resumen_no_se_liquidan(banco):
    jid=juego(banco)
    for m in ['CORNERS_1T','DISPAROS_1T','ANALISIS_FT']:
        emitir(banco,jid,mercado=m)
    antes=estado(banco)
    r=procesar(pool=banco,simular=False)
    assert r['total']==0 and r['pendientes']==3 and estado(banco)==antes


def test_skip_locked_y_lote_exacto(banco):
    jid=juego(banco);uno=emitir(banco,jid);dos=emitir(banco,jid)
    with banco.connection() as c:
        c.execute('SELECT id FROM apuestas_analizadas WHERE id=%s FOR UPDATE',(uno,))
        assert procesar(pool=banco,simular=False)['total']==1
    assert procesar(pool=banco,simular=False,ids=[dos])['total']==0
    assert procesar(pool=banco,simular=False,ids=[uno])['total']==1


def test_error_aislado_no_aborta_lote(banco):
    jid=juego(banco);uno=emitir(banco,jid);dos=emitir(banco,jid,linea=12)
    with banco.connection() as c:
        c.execute('''CREATE FUNCTION falla() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.linea=9.5 THEN RAISE EXCEPTION 'Fallo sintético'; END IF; RETURN NEW; END $$;
          CREATE TRIGGER prueba BEFORE UPDATE ON apuestas_analizadas FOR EACH ROW EXECUTE FUNCTION falla()''')
    r=procesar(pool=banco,simular=False)
    assert r['errores']==1 and r['total']==1
    with banco.connection() as c:
        assert c.execute('SELECT estado FROM apuestas_analizadas WHERE id=%s',(uno,)).fetchone()[0]=='PENDIENTE'
        assert c.execute('SELECT resultado_outcome FROM apuestas_analizadas WHERE id=%s',(dos,)).fetchone()[0]=='PUSH'


def test_dominio_nba_no_resuelve_un_registro_euro(banco):
    comp,jid=uuid4(),uuid4()
    with banco.connection() as c:
        c.execute("INSERT INTO competiciones_baloncesto VALUES(%s,'euroleague')",(comp,))
        c.execute('''INSERT INTO partidos_baloncesto(id,competicion_id,fecha_partido,valido,local_total,visitante_total)
          VALUES(%s,%s,'2026-01-01',true,90,80)''',(jid,comp))
        c.execute('''INSERT INTO apuestas_analizadas(deporte,partido_id,mercado,lado,linea,payload)
          VALUES('baloncesto',%s,'COMPLETO','OVER',160,'{"fuente":"analisis_nba"}')''',(jid,))
    r=procesar(pool=banco,simular=False)
    assert r['total']==0 and r['motivos']=={'DOMINIO_INCONSISTENTE':1}


def test_registro_nuevo_sin_probabilidad_es_informativo_y_sin_ddl(banco):
    from servicios.apuestas_analizadas import registrar_apuesta_analizada
    from motor.tipos import LadoApuesta
    jid=juego(banco)
    registrar_apuesta_analizada(deporte='futbol',partido_id=str(jid),mercado='ANALISIS_FT',lado=None,linea=None,
        probabilidad_sistema=None,confianza='MEDIA',payload_json='{"fuente":"analisis_futbol"}',pool=banco)
    registrar_apuesta_analizada(deporte='futbol',partido_id=str(jid),mercado='CORNERS_FT',lado=LadoApuesta.OVER,linea=9.5,
        probabilidad_sistema=.6,confianza='BAJA',payload_json='{"fuente":"analisis_futbol"}',pool=banco)
    with banco.connection() as c:
        filas=c.execute('SELECT estado,confianza,lado,payload FROM apuestas_analizadas ORDER BY id').fetchall()
    assert filas[0][0:3]==('INFORMATIVO',None,None)
    assert filas[0][3]['registro_analitico']['prospectiva_certificada'] is False
    assert filas[1][0:3]==('PENDIENTE','BAJA','OVER')


def test_predicciones_futbol_comparten_objetivo_y_no_anulan_pospuesto(banco):
    from motor.resolucion_predicciones_futbol import resolver_predicciones_futbol
    jid=juego(banco)
    with banco.connection() as c:
        for mercado,linea in [('CORNERS_FT',9.5),('DISPAROS_1T',5.5)]:
            c.execute('INSERT INTO predicciones_futbol(id,partido_id,mercado,linea,fecha_partido) VALUES(%s,%s,%s,%s,now())',(uuid4(),jid,mercado,linea))
    assert resolver_predicciones_futbol(pool=banco,simular=True).resueltas==1
    assert resolver_predicciones_futbol(pool=banco).resueltas==1
    with banco.connection() as c:
        assert c.execute("SELECT valor_real,outcome_binario,resultado FROM predicciones_futbol WHERE mercado='CORNERS_FT'").fetchone()==(12,True,'OVER')
        c.execute("UPDATE partidos_futbol SET estado='POSPUESTO'")
    r=resolver_predicciones_futbol(pool=banco)
    assert r.anuladas==0 and r.pendientes==1
    with pytest.raises(ValueError,match='No se reabren'):
        resolver_predicciones_futbol(pool=banco,force=True)


def test_reanalisis_no_sobrescribe_probabilidades_ni_modelo(banco):
    from api.rutas_analisis_futbol import _registrar_predicciones_futbol
    jid=juego(banco)
    p=dict(id=jid,competicion_id=uuid4(),temporada_id=uuid4(),equipo_local_id=uuid4(),equipo_visitante_id=uuid4(),
           equipo_local='Local sintético',equipo_visitante='Visitante sintético',fecha_partido=datetime(2026,1,1,tzinfo=timezone.utc))
    probs=SimpleNamespace(over_raw=.7,under_raw=.3,over_calibrada=None,under_calibrada=None,calibrador_id=None)
    pred=SimpleNamespace(mercado='GOLES_FT',media=2.,std=1.,lineas={'2.5':probs})
    with banco.connection() as c:
        with c.cursor() as cur:
            _registrar_predicciones_futbol(cur,partido=p,mercados={'GOLES_FT':pred},modelo_version_id=1)
    probs.over_raw,probs.under_raw=.1,.9
    with banco.connection() as c:
        c.execute("UPDATE predicciones_futbol SET resuelto=true,valor_real=2,resultado='UNDER'")
        with c.cursor() as cur:
            _registrar_predicciones_futbol(cur,partido=p,mercados={'GOLES_FT':pred},modelo_version_id=2)
        r=c.execute('SELECT modelo_version_id,prob_over,resuelto,valor_real FROM predicciones_futbol').fetchone()
        assert r[0]==1 and float(r[1])==.7 and r[2] is True and r[3]==2


def test_endpoint_diagnostico_es_lectura_y_no_liquida(banco,monkeypatch):
    from fastapi.testclient import TestClient
    from app import app
    import servicios.resolucion_analitica as servicio
    monkeypatch.setattr(servicio,'obtener_pool',lambda:banco)
    emitir(banco,juego(banco));antes=estado(banco)
    r=TestClient(app).get('/api/bitacora/apuestas-analizadas/diagnostico')
    assert r.status_code==200 and r.json()['simulacion'] is True and r.json()['total']==1
    assert estado(banco)==antes


def test_ciclo_nba_solo_resuelve_su_dominio_y_no_convierte_lado_invalido_en_push(banco):
    from motor.resolucion_predicciones import resolver_predicciones
    with banco.connection() as c:
        c.execute('''CREATE TABLE predicciones_registradas(id uuid PRIMARY KEY,partido_id uuid,mercado text,lado text,
            linea numeric,resuelto bool DEFAULT false,fecha_partido date,valor_real numeric,outcome_binario bool,
            timestamp_resolucion timestamptz)''')
        for liga in ['nba','euroleague','wnba']:
            comp,jid=uuid4(),uuid4()
            c.execute('INSERT INTO competiciones_baloncesto VALUES(%s,%s)',(comp,liga))
            c.execute('''INSERT INTO partidos_baloncesto(id,competicion_id,fecha_partido,valido,local_q1,visitante_q1,local_total,visitante_total)
                VALUES(%s,%s,'2026-01-01',true,20,21,90,80)''',(jid,comp))
            for lado in ['OVER','INVALIDO']:
                c.execute('''INSERT INTO predicciones_registradas(id,partido_id,mercado,lado,linea,fecha_partido)
                    VALUES(%s,%s,'Q1',%s,40.5,'2026-01-01')''',(uuid4(),jid,lado))
    r=resolver_predicciones(pool=banco)
    assert r.resueltas==1 and r.push==0
    with banco.connection() as c:
        assert c.execute('SELECT count(*) FROM predicciones_registradas WHERE resuelto IS TRUE').fetchone()[0]==1
        c.execute('''CREATE FUNCTION falla_nba() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN IF NEW.linea=41 THEN RAISE EXCEPTION 'Fallo NBA sintético'; END IF; RETURN NEW; END $$;
            CREATE TRIGGER prueba BEFORE UPDATE ON predicciones_registradas FOR EACH ROW EXECUTE FUNCTION falla_nba()''')
        jid=c.execute("SELECT id FROM partidos_baloncesto WHERE competicion_id=(SELECT id FROM competiciones_baloncesto WHERE codigo='nba')").fetchone()[0]
        for linea in [41,40]:
            c.execute('''INSERT INTO predicciones_registradas(id,partido_id,mercado,lado,linea,fecha_partido)
                VALUES(%s,%s,'Q1','OVER',%s,'2026-01-01')''',(uuid4(),jid,linea))
    r=resolver_predicciones(pool=banco)
    assert r.resueltas==1 and r.errores==1

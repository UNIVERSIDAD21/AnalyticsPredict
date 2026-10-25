"""Persistencia real solo sobre un esquema local sintético descartable."""
import os
from decimal import Decimal
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg_pool import ConnectionPool
import pytest
from fastapi.testclient import TestClient

from motor import resolucion_bitacora as motor


@pytest.fixture
def registro(monkeypatch):
    url = os.getenv('DATABASE_URL', '')
    if not conninfo_to_dict(url).get('dbname', '').startswith('ap_suite_test_'):
        pytest.skip('Requiere PostgreSQL sintético local')
    schema = 'cierres_' + uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    pool = ConnectionPool(make_conninfo(url, options=f'-c search_path={schema} -c timezone=America/Bogota'), min_size=1, max_size=3,
                          kwargs={'prepare_threshold': None}, open=True)
    pool.wait()
    with pool.connection() as c:
        c.execute('''CREATE TABLE competiciones_baloncesto(id uuid PRIMARY KEY, codigo text);
          CREATE TABLE apuestas(id uuid PRIMARY KEY, partido_id uuid, competicion_id uuid,
            fecha_partido date, mercado text, lado text, linea numeric, cuota numeric, stake numeric,
            resultado text DEFAULT 'PENDIENTE', puntos_reales numeric, ganancia numeric,
            fecha_resolucion timestamptz, actualizado_en timestamptz);
          CREATE TABLE apuestas_futbol(LIKE apuestas INCLUDING ALL);
          ALTER TABLE apuestas_futbol RENAME puntos_reales TO valor_real;
          CREATE TABLE partidos_baloncesto(id uuid PRIMARY KEY, fecha_partido date, valido boolean,
            competicion_id uuid, equipo_local_id uuid, equipo_visitante_id uuid, ganador_id uuid,
            local_q1 int,local_q2 int,local_q3 int,local_q4 int,local_ot int,local_total int,
            visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,visitante_ot int,visitante_total int);
          CREATE TABLE partidos_futbol(id uuid PRIMARY KEY, fecha_partido date, valido boolean,
            estado text, hubo_tiempo_extra boolean, local_goles_total int,visitante_goles_total int,
            local_goles_1t int,local_goles_2t int,visitante_goles_1t int,visitante_goles_2t int);
        ''')
        nba, euro, local, visita, juego = [uuid4() for _ in range(5)]
        c.execute("INSERT INTO competiciones_baloncesto VALUES(%s,'nba'),(%s,'euroleague')", (nba, euro))
        c.execute('''INSERT INTO partidos_baloncesto VALUES(%s,CURRENT_DATE,true,%s,%s,%s,%s,
                     20,20,20,20,12,92,20,20,20,20,8,88)''', (juego,euro,local,visita,local))
        c.execute('''INSERT INTO apuestas(id,partido_id,competicion_id,fecha_partido,mercado,lado,linea,cuota,stake)
                     VALUES(%s,%s,%s,CURRENT_DATE,'COMPLETO','UNDER',170,1.91,10)''', (uuid4(),juego,euro))
        juego = uuid4()
        c.execute("INSERT INTO partidos_futbol VALUES(%s,CURRENT_DATE,true,'FINALIZADO',false,0,0,0,0,0,0)", (juego,))
        for cuota in [0, 1.91]:
            c.execute('''INSERT INTO apuestas_futbol(id,partido_id,fecha_partido,mercado,lado,linea,cuota,stake)
                         VALUES(%s,%s,CURRENT_DATE,'GOLES_FT','UNDER',2.5,%s,10)''', (uuid4(),juego,cuota))
    monkeypatch.setattr(motor, 'obtener_pool', lambda:pool)
    yield pool
    pool.close()
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_cierra_dominios_idempotente_y_sin_reabrir_hoy(registro):
    r = motor.resolver_bitacora(simular=True)
    assert r['resueltas'] == 3 and r['importes_no_disponibles'] == 1
    with registro.connection() as c:
        assert c.execute("SELECT count(*) FROM apuestas WHERE resultado='PENDIENTE'").fetchone()[0] == 1
    r = motor.resolver_bitacora()
    assert r['resueltas'] == r['ganadas'] == 3 and r['errores'] == 0
    with registro.connection() as c:
        assert c.execute('SELECT puntos_reales,ganancia FROM apuestas').fetchone() == (160, Decimal('9.10'))
        assert c.execute('SELECT valor_real,ganancia FROM apuestas_futbol WHERE cuota=0').fetchone() == (0,None)
        antes = c.execute('SELECT to_jsonb(a) FROM apuestas a').fetchall()
    assert motor.resolver_bitacora()['resueltas'] == 0
    from motor.resolucion_apuestas import resolver_apuestas
    assert resolver_apuestas(pool=registro, force=True).resueltas == 0
    with registro.connection() as c:
        assert c.execute('SELECT to_jsonb(a) FROM apuestas a').fetchall() == antes


def test_error_de_una_fila_no_aborta_el_resto(registro):
    with registro.connection() as c:
        c.execute('''CREATE FUNCTION rechazar_sin_cuota() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.cuota=0 THEN RAISE EXCEPTION 'Error sintético'; END IF; RETURN NEW; END $$;
          CREATE TRIGGER fallo BEFORE UPDATE ON apuestas_futbol FOR EACH ROW EXECUTE FUNCTION rechazar_sin_cuota();''')
    r = motor.resolver_bitacora()
    assert r['resueltas'] == 2 and r['errores'] == 1
    with registro.connection() as c:
        assert c.execute("SELECT resultado FROM apuestas_futbol WHERE cuota=0").fetchone()[0] == 'PENDIENTE'
        assert c.execute("SELECT resultado FROM apuestas_futbol WHERE cuota>1").fetchone()[0] == 'GANADA'


def test_fila_bloqueada_se_omite_y_se_reintenta_sin_duplicar(registro):
    with registro.connection() as c:
        c.execute('SELECT id FROM apuestas FOR UPDATE')
        r = motor.resolver_bitacora()
        assert r['resueltas'] == 2
    assert motor.resolver_bitacora()['resueltas'] == 1


def test_lote_explicito_preserva_registros_fuera_del_plan(registro):
    with registro.connection() as c:
        elegida = c.execute('SELECT id FROM apuestas_futbol ORDER BY id LIMIT 1').fetchone()[0]
    assert motor.resolver_bitacora(apuesta_ids=[elegida])['resueltas'] == 1
    assert motor.resolver_bitacora(simular=True)['resueltas'] == 2


def test_entrada_nba_no_liquida_euro_y_endpoint_futbol_si(registro, monkeypatch):
    from motor.resolucion_apuestas import resolver_apuestas
    assert resolver_apuestas(pool=registro).resueltas == 0
    from app import app
    from api import rutas_apuestas_futbol
    monkeypatch.setattr(rutas_apuestas_futbol, 'obtener_pool', lambda:registro)
    client = TestClient(app)
    r = client.post('/api/futbol/apuestas/resolver?version=v2')
    assert r.status_code == 200, r.text
    assert r.json()['data']['resueltas'] == 2
    r = client.post('/api/bitacora/resolver')
    assert r.status_code == 200, r.text
    assert r.json()['resumen']['resueltas'] == 1
    assert client.post('/api/bitacora/resolver').json()['resumen']['resueltas'] == 0


def test_filtro_mercado_general_acepta_futbol_sin_tocar_euro(registro):
    from app import app
    r = TestClient(app).post('/api/bitacora/resolver?mercado=GOLES_FT')
    assert r.status_code == 200, r.text
    assert r.json()['resumen']['resueltas'] == 2
    assert motor.resolver_bitacora(simular=True)['resueltas'] == 1

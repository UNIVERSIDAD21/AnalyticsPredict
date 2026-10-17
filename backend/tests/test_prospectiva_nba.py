"""Inmutabilidad, temporalidad y resolución aislada; nunca usa Neon/proveedor."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

import numpy as np
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
import pytest

from motor_autoentrenamiento.artefacto_nba import guardar_artefacto
from motor_autoentrenamiento.dominio_nba import DOMINIO, POLITICA_DATOS
from scripts.run_suite_global_testdb import validar_admin_local
from servicios.prospectiva_nba import construir_snapshot, congelar, digest, resolver
from api.rutas_operacion import leer_estado


@pytest.fixture
def artefacto(tmp_path):
    ahora = datetime.now(timezone.utc)
    metricas = {'dominio': DOMINIO, 'politica_datos': POLITICA_DATOS, 'hash_datos': 'a'*32,
                'modelo_version': 1, 'fecha_entrenamiento': (ahora-timedelta(days=1)).isoformat(),
                'fit_completed_at': (ahora-timedelta(days=1)).isoformat(),
                'training_data_latest_game_date': (ahora-timedelta(days=2)).date().isoformat()}
    w = np.zeros((6, 4)); w[0] = 28
    ruta = tmp_path/'modelo.npz'
    guardar_artefacto({'metricas': metricas, 'modelo_version_id': 1, 'alpha': 1,
        'entidad_a_indice': {'club a': 0, 'club b': 1}, 'pesos_equipo': w, 'pesos_rival': w,
        'desviacion_equipo': np.ones(4)*4, 'desviacion_rival': np.ones(4)*4}, ruta)
    return ruta


def evento(inicio=None, final=False):
    inicio = inicio or datetime.now(timezone.utc)+timedelta(hours=2)
    return {'id': '123', 'date': inicio.isoformat(),
        'status': {'type': {'state': 'post' if final else 'pre', 'completed': final}},
        'competitions': [{'date': inicio.isoformat(), 'competitors': [
            {'homeAway': lado, 'team': {'id': ident, 'displayName': nombre},
             'score': '100', 'linescores': [{'value': v} for v in [24, 25, 25, 26]]}
            for lado, ident, nombre in [('home', '1', 'Club A'), ('away', '2', 'Club B')]]}]}


def test_snapshot_reproducible_sin_calibracion_ni_recomendaciones(artefacto):
    s = construir_snapshot(evento(), artefacto, 55.5, datetime.now(timezone.utc))
    assert s['media'] == 56 and 0 < s['p_raw'] < 1
    assert s['p_calibrada'] is None and s['calibrador_id'] is None
    assert s['policy'] == {'no_picks': True, 'no_stake': True, 'no_betting_recommendations': True}
    assert not {'pick', 'stake', 'cuota', 'recomendacion'} & s.keys()
    assert np.dot(s['features'], np.array(s['pesos_q1_local'])+s['pesos_q1_visitante']) == s['media']
    assert len(s['artefacto_sha256']) == 64


@pytest.mark.parametrize('caso', ['iniciado', 'sin_zona', 'equipo_ajeno', 'umbral_entero', 'nan'])
def test_rechaza_datos_no_prospectivos(artefacto, caso):
    e = evento(); linea = 55.5
    if caso == 'iniciado': e['status']['type']['state'] = 'in'
    if caso == 'sin_zona': e['date'] = '2026-10-15T01:00:00'
    if caso == 'equipo_ajeno': e['competitions'][0]['competitors'][0]['team']['displayName'] = 'Euroliga'
    if caso == 'umbral_entero': linea = 55
    if caso == 'nan': linea = float('nan')
    with pytest.raises(ValueError): construir_snapshot(e, artefacto, linea, datetime.now(timezone.utc))


@pytest.fixture
def prospectiva_db():
    url = os.getenv('TEST_PG_ADMIN_URL')
    if not url: pytest.skip('Requiere PostgreSQL sintético exclusivo')
    validar_admin_local(url)
    nombre = 'ap_prospectiva_'+uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        try:
            with psycopg.connect(make_conninfo(url, dbname=nombre), autocommit=True) as c:
                c.execute((Path(__file__).resolve().parents[1]/'migrations/2026-10-15_cadena_prospectiva.sql').read_text())
                yield c
        finally:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(nombre)))


@pytest.mark.integracion
def test_congelamiento_real_clock_idempotencia_y_no_mutacion(prospectiva_db, artefacto):
    c = prospectiva_db; e = evento()
    primero = congelar(c, e, artefacto, 55.5)
    assert primero['insertada'] and not congelar(c, e, artefacto, 55.5)['insertada']
    assert c.execute('SELECT count(*) FROM predicciones_prospectivas').fetchone() == (1,)
    for comando in ('UPDATE predicciones_prospectivas SET sha256=sha256', 'DELETE FROM predicciones_prospectivas', 'TRUNCATE predicciones_prospectivas, outcomes_prospectivos'):
        with pytest.raises(psycopg.errors.RaiseException): c.execute(comando)
    with pytest.raises(ValueError): resolver(c, primero['id'], evento(final=True))
    assert c.execute('SELECT count(*) FROM outcomes_prospectivos').fetchone() == (0,)
    with pytest.raises(psycopg.errors.CheckViolation):
        c.execute("INSERT INTO predicciones_prospectivas VALUES(%s,'tarde',now()-interval '1 hour',now()-interval '1 day',now(),%s,'{}')", (uuid4(), 'x'*64))


@pytest.mark.integracion
def test_resolucion_sintetica_e2e_outcome_posterior_y_conflictos(prospectiva_db, artefacto):
    c = prospectiva_db; ahora = datetime.now(timezone.utc)
    # Fixture temporal EXCLUSIVAMENTE sintética. No se retrofecha ninguna captura real.
    inicio = ahora-timedelta(hours=1); e = evento(inicio)
    s = construir_snapshot(e, artefacto, 55.5, ahora-timedelta(hours=2))
    uid = uuid4()
    c.execute('INSERT INTO predicciones_prospectivas VALUES(%s,%s,%s,%s,%s,%s,%s)',
              (uid, str(uid), inicio, s['fit_completed_at'], ahora-timedelta(hours=2), digest(s), Jsonb(s)))
    final = evento(inicio, final=True)
    assert resolver(c, uid, final)['insertado']
    assert not resolver(c, uid, final)['insertado']
    real = c.execute('SELECT evidencia FROM outcomes_prospectivos').fetchone()[0]
    assert real['valor_real'] == 48 and real['outcome'] is False and real['independiente'] is False
    revisado = deepcopy(final); revisado['competitions'][0]['competitors'][0]['linescores'][0]['value'] = 30
    with pytest.raises(ValueError): resolver(c, uid, revisado)
    revisado['competitions'][0]['competitors'][0]['score'] = '106'
    with pytest.raises(ValueError, match='revisado'): resolver(c, uid, revisado)
    ajeno = deepcopy(final); ajeno['id'] = '999'
    with pytest.raises(ValueError): resolver(c, uid, ajeno)
    with pytest.raises(psycopg.errors.RaiseException): c.execute('DELETE FROM outcomes_prospectivos')


@pytest.mark.integracion
def test_estado_operativo_respeta_contrato_sql_y_no_escribe(prospectiva_db):
    c = prospectiva_db
    c.execute('''CREATE TABLE competiciones_baloncesto(id int,codigo text);
        CREATE TABLE partidos_baloncesto(competicion_id int,fecha_partido date,valido boolean,
            local_total int,visitante_total int,local_q1 int,local_q2 int,local_q3 int,local_q4 int,
            visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int,tipo_partido text);
        CREATE TABLE partidos_futbol(fecha_partido timestamptz,estado text,valido boolean,
            local_goles_total int,visitante_goles_total int);
        CREATE TABLE modelo_versiones_futbol(id int,mercado_principal text,version text,activo boolean,
            fecha_entrenamiento timestamptz,cutoff_entrenamiento timestamptz,partidos_entrenamiento int);
        INSERT INTO competiciones_baloncesto VALUES(1,'nba'),(2,'euroleague');
        INSERT INTO partidos_baloncesto VALUES(1,'2026-10-10',true,100,100,25,25,25,25,25,25,25,25,'PRE'),
          (1,'2026-10-11',false,0,0,0,0,0,0,0,0,0,0,'REG'),
          (2,'2026-10-14',true,100,100,25,25,25,25,25,25,25,25,'REG');''')
    with c.transaction():
        c.execute('SET TRANSACTION READ ONLY')
        estado = leer_estado(c)
        assert estado['nba']['n'] == 2
        assert estado['nba']['ultimo_final'].isoformat() == '2026-10-10'
        assert [(r['fase'], r['n'], r['finales_validos']) for r in estado['nba']['por_fase']] == [('PRE', 1, 1), ('REG', 1, 0)]
        assert estado['capturas_futbol']['lotes'] is None
        assert estado['prospectiva']['congeladas'] == 0
        assert estado['prospectiva']['resueltas_independientes'] == 0
        assert estado['prospectiva']['por_fase'] == []
        assert estado['predictor_ml_futbol']['estado'] == 'SIN_VERSION_ACTIVA'

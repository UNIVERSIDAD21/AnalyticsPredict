"""Misma cohorte SQL/API/curva bajo transacciones realmente read-only."""
import os
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
import pytest

from api import rutas_metricas as rutas
from db import obtener_pool
from scripts.evaluar_futbol_temporal import PoolSoloLectura


def test_sql_api_series_modelo_exclusiones_y_lecturas_sin_dml(monkeypatch):
    cfg = conninfo_to_dict(os.environ.get('DATABASE_URL') or '')
    if not cfg.get('dbname', '').startswith('ap_suite_test_'):
        pytest.skip('Solo PostgreSQL sintético desechable')
    pool = obtener_pool()
    origen = 'API_USUARIO'
    modelo = 81723
    partido = uuid4()
    ids = [uuid4() for _ in range(7)]
    cal = uuid4()
    datos = [(.1, .9, cal, True, modelo, None),
             (.3, .7, None, False, modelo, None),
             (.8, None, None, True, modelo, None),
             (1.2, .6, cal, True, modelo, None),
             (.4, .5, cal, True, modelo+1, None),
             (.99, .99, cal, True, modelo, partido),
             (.5, .5, cal, None, modelo, None)]
    try:
        with pool.connection() as conn:
            conn.execute('INSERT INTO partidos_baloncesto(id,local_total,visitante_total) VALUES(%s,0,0)', [partido])
            for ident, fila in zip(ids, datos):
                conn.execute('INSERT INTO predicciones_registradas '
                             '(id,p_raw,p_calibrada,calibrador_id,outcome_binario,modelo_version_id,partido_id,origen,mercado,fecha_partido,resuelto) '
                             "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'Q1','2026-01-01',true)",
                             [ident, *fila, origen])
            antes = conn.execute('SELECT md5(json_agg(p ORDER BY id)::text) FROM predicciones_registradas p').fetchone()
        lectura = PoolSoloLectura(pool)
        monkeypatch.setattr(rutas, 'obtener_pool', lambda: lectura)
        monkeypatch.setattr('db.obtener_pool', lambda: lectura)
        monkeypatch.setattr(rutas, 'obtener_calibrador_activo', lambda **kw: None)
        monkeypatch.setattr(rutas, 'listar_alertas_calibracion', lambda **kw: [])
        app = FastAPI()
        app.include_router(rutas.router)
        with TestClient(app) as client:
            for serie, n, brier, excluidas in [('raw', 3, (.81+.09+.04)/3, 1), ('calibrada', 2, .085, 2)]:
                params = dict(origen=origen, mercado='Q1', serie=serie, modelo_version_id=modelo,
                              desde='2026-01-01', hasta='2026-01-31')
                respuesta = client.get('/api/metricas/calibracion', params=params)
                assert respuesta.status_code == 200, respuesta.text
                m = respuesta.json()['metricas_por_mercado'][0]
                curva = client.get('/api/metricas/calibracion/Q1/curva', params=params)
                assert curva.status_code == 200, curva.text
                c = curva.json()
                assert m['n_predicciones'] == c['n_predicciones_total'] == n
                assert m['n_excluidas_probabilidad'] == c['n_excluidas_probabilidad'] == excluidas
                assert m['n_excluidos_outcome_dudoso'] == c['n_excluidos_outcome_dudoso'] == 1
                assert m['n_excluidos_push'] == c['n_excluidos_push'] == 1
                assert m['brier_score'] == pytest.approx(brier)
                assert m['ece'] == pytest.approx(c['ece'])
                assert sum(b['n'] for b in c['bins']) == n
                assert m['mejora_vs_raw'] is None
        with pool.connection() as conn:
            despues = conn.execute('SELECT md5(json_agg(p ORDER BY id)::text) FROM predicciones_registradas p').fetchone()
            assert antes == despues
    finally:
        with pool.connection() as conn:
            conn.execute('DELETE FROM predicciones_registradas WHERE id=ANY(%s)', [ids])
            conn.execute('DELETE FROM partidos_baloncesto WHERE id=%s', [partido])

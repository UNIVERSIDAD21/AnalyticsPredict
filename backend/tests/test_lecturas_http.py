"""Aislamiento GET/HEAD real: conexiones reutilizadas, concurrencia y errores públicos."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
import pytest
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import middleware_trace_id, manejador_http, observabilidad_http
from db import obtener_pool
from lecturas_http import LecturasHTTPMiddleware, solo_lectura_http


def app_prueba():
    app = FastAPI()
    app.middleware('http')(middleware_trace_id)
    app.add_exception_handler(StarletteHTTPException, manejador_http)
    app.add_middleware(LecturasHTTPMiddleware)
    return app


def test_contexto_aislado_async_sync_head_y_background():
    app = app_prueba()
    vistos = []
    @app.api_route('/contexto', methods=['GET', 'HEAD', 'POST'])
    def contexto():
        vistos.append(solo_lectura_http.get())
        return JSONResponse({}, background=BackgroundTask(lambda: vistos.append(solo_lectura_http.get())))
    with TestClient(app) as client:
        for metodo, esperado in [('get', True), ('head', True), ('post', False)]:
            assert getattr(client, metodo)('/contexto').status_code == 200
            assert vistos[-2:] == [esperado, esperado]
    assert solo_lectura_http.get() is False
    async def concurrente():
        async def uno(valor):
            token = solo_lectura_http.set(valor)
            try:
                await asyncio.sleep(0)
                return solo_lectura_http.get()
            finally:
                solo_lectura_http.reset(token)
        assert await asyncio.gather(uno(True), uno(False)) == [True, False]
    asyncio.run(concurrente())


def test_fallos_http_sanitizados_y_contabilizados():
    app = app_prueba()
    secreto_ficticio = 'postgresql://demo:SECRETO_FICTICIO@example.invalid/db'
    @app.get('/fallo')
    def fallo():
        raise RuntimeError(secreto_ficticio)
    @app.get('/capturado')
    def capturado():
        raise HTTPException(500, detail=secreto_ficticio)
    antes = observabilidad_http.resumen()['http']['errors_5xx']
    with TestClient(app, raise_server_exceptions=False) as client:
        for path in ('/fallo', '/capturado'):
            r = client.get(path)
            assert r.status_code in (500, 503)
            assert secreto_ficticio not in r.text
            assert r.json()['error']['trace_id'] == r.headers['x-trace-id']
    assert observabilidad_http.resumen()['http']['errors_5xx'] == antes + 2


def test_postgres_bloquea_dml_get_head_sin_contaminar_post():
    if not conninfo_to_dict(os.environ.get('DATABASE_URL') or '').get('dbname','').startswith('ap_suite_test_'):
        pytest.skip('Solo PostgreSQL sintético desechable')
    pool = obtener_pool()
    with pool.connection() as c:
        c.execute('CREATE TABLE ap_guard_http (metodo text)')
    app = app_prueba()
    @app.api_route('/guardar', methods=['GET','HEAD','POST'])
    def guardar():
        with pool.connection() as c:
            c.execute("INSERT INTO ap_guard_http VALUES ('POST')")
        return {'exito': True}
    @app.get('/select')
    def seleccionar():
        with pool.connection() as c:
            return {'read_only': c.execute('SHOW transaction_read_only').fetchone()[0]}
    @app.get('/reiniciar')
    def reiniciar():
        with pool.connection() as c:
            c.execute('COMMIT')
            c.execute("INSERT INTO ap_guard_http VALUES ('GET')")
        return {'exito':True}
    antes = observabilidad_http.resumen()['http']['write_attempts_blocked']
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            assert client.get('/select').json()['read_only'] == 'on'
            assert client.get('/guardar').status_code == 503
            assert client.head('/guardar').status_code == 503
            assert client.get('/reiniciar').status_code == 503
            with ThreadPoolExecutor(max_workers=2) as executor:
                futuros = [executor.submit(client.get, '/guardar'), executor.submit(client.post, '/guardar')]
                assert [f.result().status_code for f in futuros] == [503, 200]
        with pool.connection() as c:
            assert c.read_only is not True
            assert c.execute('SELECT * FROM ap_guard_http').fetchall() == [('POST',)]
        assert observabilidad_http.resumen()['http']['write_attempts_blocked'] == antes + 4
    finally:
        with pool.connection() as c:
            c.execute('DROP TABLE ap_guard_http')


@pytest.mark.parametrize('ruta', [
    '/api/partidos', '/api/partidos/buscar?equipo_local=Lakers&equipo_visitante=Celtics',
    '/api/bitacora/resumen', '/api/bitacora/estadisticas',
    '/api/interno/estadisticas-predicciones', '/api/interno/calibradores',
    '/api/interno/alertas-calibracion', '/api/futbol/metricas/rendimiento',
    '/api/futbol/apuestas', '/api/operacion/estado',
])
def test_consumidores_no_convierten_fallo_en_exito_vacio(monkeypatch, ruta):
    import sys
    from app import app
    def fallo():
        raise RuntimeError('CONFIGURACION_PRIVADA_FICTICIA')
    for modulo in list(sys.modules.values()):
        archivo = getattr(modulo, '__file__', '') or ''
        if '/backend/' in archivo and '/tests/' not in archivo and hasattr(modulo,'obtener_pool'):
            monkeypatch.setattr(modulo,'obtener_pool',fallo)
    client = TestClient(app,raise_server_exceptions=False)
    r = client.get(ruta)
    assert r.status_code >= 500,r.text
    assert 'CONFIGURACION_PRIVADA_FICTICIA' not in r.text
    assert r.json()['error']['trace_id']==r.headers['x-trace-id']


def test_ruta_estatica_contrato_futbol_no_queda_oculta_por_uuid(monkeypatch, tmp_path):
    from api import rutas_apuestas_futbol
    from app import app
    monkeypatch.setattr(rutas_apuestas_futbol, 'APUESTAS_FUTBOL_USAGE_PATH', tmp_path/'ausente.json')
    r = TestClient(app).get('/api/futbol/apuestas/contract-usage')
    assert r.status_code == 200
    assert not (tmp_path/'ausente.json').exists()


def test_auditoria_serializa_uuid_real_del_driver():
    from api.rutas_bitacora import AuditoriaDecisionFutbolItem
    from uuid import uuid4
    ident = uuid4()
    assert AuditoriaDecisionFutbolItem(id=1,partido_id=ident).model_dump(mode='json')['partido_id']==str(ident)

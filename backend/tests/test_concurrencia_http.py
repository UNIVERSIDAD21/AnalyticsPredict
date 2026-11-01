"""La E/S de una ventana no puede inmovilizar salud ni otras ventanas."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import time

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

import db
import app as modulo_app
from api import rutas_analisis, rutas_equipos
from lecturas_http import LecturasHTTPMiddleware, en_peticion_http, solo_lectura_http


def test_siete_analisis_lentos_no_bloquean_salud_ni_temporadas(monkeypatch):
    liberar = threading.Event()
    empezaron = threading.Event()
    lock = threading.Lock()
    contextos = []

    def lento(peticion):
        with lock:
            contextos.append((en_peticion_http.get(), solo_lectura_http.get()))
            if len(contextos) == 7:
                empezaron.set()
        assert liberar.wait(4), 'Se bloqueó el bucle HTTP'
        return {'exito': True, 'datos': {'prueba': True}}

    monkeypatch.setattr(rutas_analisis, 'ejecutar_analisis', lento)
    monkeypatch.setattr(rutas_equipos, 'obtener_temporadas_disponibles', lambda: [])
    monkeypatch.setattr(modulo_app, 'obtener_modelo', lambda: type('Modelo', (), {'cantidad_equipos': 30})())
    app = FastAPI()
    app.add_middleware(LecturasHTTPMiddleware)
    app.include_router(rutas_analisis.router)
    app.include_router(rutas_equipos.router)
    app.add_api_route('/salud', modulo_app.verificar_salud)

    async def escenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
            payload = {'equipo_local': 'Boston Celtics', 'equipo_visitante': 'Miami Heat',
                       'mercado': 'Q1', 'linea': 50.5, 'lado': 'OVER'}
            tareas = [asyncio.create_task(c.post('/api/analizar', json=payload)) for _ in range(7)]
            try:
                assert await asyncio.to_thread(empezaron.wait, 2)
                salud, temporadas = await asyncio.wait_for(asyncio.gather(
                    c.get('/salud'), c.get('/api/equipos/temporadas')), timeout=1)
                assert salud.status_code == temporadas.status_code == 200
                assert not any(t.done() for t in tareas)
            finally:
                liberar.set()
                respuestas = await asyncio.gather(*tareas)
            assert all(r.status_code == 200 for r in respuestas)
    asyncio.run(escenario())
    assert contextos == [(True, False)] * 7


def test_pool_unico_al_arrancar_muchas_ventanas(monkeypatch):
    creados = []
    def fabrica(**kwargs):
        time.sleep(0.02)
        objeto = object()
        creados.append((objeto, kwargs))
        return objeto
    monkeypatch.setattr(db, '_pool', None)
    monkeypatch.setattr(db, 'PoolAplicacion', fabrica)
    monkeypatch.setattr(db, 'obtener_database_url', lambda: 'postgresql://prueba.invalid/test')
    with ThreadPoolExecutor(max_workers=20) as executor:
        pools = list(executor.map(lambda _: db.obtener_pool(), range(40)))
    assert len(creados) == 1
    assert all(p is pools[0] for p in pools)
    assert creados[0][1]['max_size'] == 5
    assert creados[0][1]['kwargs']['tcp_user_timeout'] == 15000


def test_temporadas_filtra_ids_repetidos_en_query_fastapi(monkeypatch):
    consultas = []
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, query, params): consultas.append(params)
        def fetchall(self): return [{'id': 't1', 'nombre': '2025-26'}]
    class Conn:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def cursor(self, **kwargs):
            assert solo_lectura_http.get() is True
            return Cursor()
    class Pool:
        def connection(self): return Conn()
    monkeypatch.setattr(rutas_equipos, 'obtener_pool', lambda: Pool())
    app = FastAPI()
    app.add_middleware(LecturasHTTPMiddleware)
    app.include_router(rutas_equipos.router)
    with TestClient(app) as c:
        r = c.get('/api/equipos/temporadas?equipo_ids=equipo-a&equipo_ids=equipo-b')
    assert r.status_code == 200
    assert consultas == [(['equipo-a', 'equipo-b'], 2)]
    assert r.json()['temporadas'] == [{'id': 't1', 'nombre': '2025-26'}]


def test_lectura_compartida_no_cachea_ni_mezcla_selecciones():
    from servicios.lecturas_concurrentes import compartir_lectura
    llamadas = []
    liberar = threading.Event()
    iniciada = threading.Event()
    @compartir_lectura
    def consulta(temporada):
        llamadas.append(temporada)
        iniciada.set()
        assert liberar.wait(2)
        return {'temporada': temporada, 'datos': []}
    def leer(temporada):
        token = solo_lectura_http.set(True)
        try: return consulta(temporada)
        finally: solo_lectura_http.reset(token)
    with ThreadPoolExecutor(max_workers=10) as executor:
        primero = executor.submit(leer, '2020')
        assert iniciada.wait(1)
        seguidores = [executor.submit(leer, '2020') for _ in range(7)]
        distinto = executor.submit(leer, '2026')
        # Los seguidores deben alcanzar la lectura todavía retenida.
        time.sleep(0.05)
        liberar.set()
        resultados = [primero.result()] + [f.result() for f in seguidores]
        assert distinto.result()['temporada'] == '2026'
    assert llamadas.count('2020') == llamadas.count('2026') == 1
    resultados[0]['datos'].append(1)
    assert resultados[1]['datos'] == []
    leer('2020')
    assert llamadas.count('2020') == 2  # Una consulta posterior siempre es nueva.


def test_lectura_fallida_se_limpia_para_el_siguiente_intento():
    from servicios.lecturas_concurrentes import compartir_lectura
    llamadas = []
    @compartir_lectura
    def consulta():
        llamadas.append(1)
        if len(llamadas) == 1: raise ValueError('fallo de prueba')
        return {'ok': True}
    token = solo_lectura_http.set(True)
    try:
        import pytest
        with pytest.raises(ValueError): consulta()
        assert consulta() == {'ok': True}
    finally: solo_lectura_http.reset(token)


def test_limites_http_no_contaminan_otra_transaccion_del_pool():
    from psycopg.conninfo import conninfo_to_dict
    import os
    import pytest
    if not conninfo_to_dict(os.environ.get('DATABASE_URL') or '').get('dbname','').startswith('ap_suite_test_'):
        pytest.skip('Solo PostgreSQL sintético propio')
    pool = db.obtener_pool()
    app = FastAPI()
    app.add_middleware(LecturasHTTPMiddleware)
    @app.api_route('/limites', methods=['GET', 'POST'])
    def limites():
        with pool.connection() as c:
            return {'statement': c.execute('SHOW statement_timeout').fetchone()[0],
                    'lock': c.execute('SHOW lock_timeout').fetchone()[0],
                    'readonly': c.execute('SHOW transaction_read_only').fetchone()[0]}
    with TestClient(app) as c:
        assert c.get('/limites').json() == {'statement':'15s','lock':'5s','readonly':'on'}
        assert c.post('/limites').json() == {'statement':'15s','lock':'5s','readonly':'off'}
    with pool.connection() as c:
        assert c.execute('SHOW statement_timeout').fetchone()[0] == '0'
        assert c.execute('SHOW lock_timeout').fetchone()[0] == '0'


def test_estadisticas_consulta_partidos_una_vez_y_conserva_ot(monkeypatch):
    from datetime import date
    consultas = []
    equipos = [{'id': x, 'nombre': nombre, 'nombre_corto': nombre, 'abreviatura': x,
                'conferencia':'Este', 'division':'Atlantico'}
               for x,nombre in [('a','Boston Celtics'),('b','Miami Heat'),('c','Sin muestra')]]
    partido = {'equipo_local_id':'a','equipo_visitante_id':'b','ganador_id':'a','fecha_partido':date(2026,10,20),
               **{lado+'_'+q:25 for lado in ['local','visitante'] for q in ['q1','q2','q3','q4']},
               'local_ot':2,'visitante_ot':0,'local_total':102,'visitante_total':100}
    class Cursor:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def execute(self,sql,params=None): consultas.append((sql,params))
        def fetchall(self): return equipos if len(consultas)==1 else [partido]
    class Conn:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def cursor(self,**kwargs): return Cursor()
    class Pool:
        def connection(self): return Conn()
    monkeypatch.setattr(rutas_equipos,'obtener_pool',lambda:Pool())
    r=rutas_equipos.calcular_estadisticas_desde_bd('temporada')
    assert len(consultas)==2  # Catálogo y todos los partidos, independientemente de N equipos.
    assert consultas[1][1]==['temporada']
    assert "p.tipo_partido = 'REG'" in consultas[1][0]
    assert "p.valido = true" in consultas[1][0] and "p.ganador_id IS NOT NULL" in consultas[1][0]
    assert len(r['equipos'])==2
    boston=next(e for e in r['equipos'] if e['nombre']=='Boston Celtics')
    assert boston['record']=={'victorias':1,'derrotas':0}
    assert boston['promedios']['anotados']['total']==102

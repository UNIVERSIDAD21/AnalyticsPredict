from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api import rutas_local
from servicios.cobertura_uso import leer_cobertura
from test_ingesta_futbol_americas_pg import db_local  # noqa: F401 — conexión sintética


def test_conteos_reales_readonly_ventana_nulos_ceros_y_competicion_vacia(db_local):
    c = db_local
    c.execute('''CREATE TEMP TABLE competiciones_baloncesto(id text,codigo text,nombre text);
        CREATE TEMP TABLE partidos_baloncesto(competicion_id text, id int,fecha_partido date,valido bool,
          local_total int,visitante_total int,local_q1 int,local_q2 int,local_q3 int,local_q4 int,
          visitante_q1 int,visitante_q2 int,visitante_q3 int,visitante_q4 int);
        CREATE TEMP TABLE competiciones_futbol(id text,codigo text,nombre text);
        CREATE TEMP TABLE partidos_futbol(competicion_id text,id int,fecha_partido timestamptz,valido bool,estado text,
          local_goles_total int,visitante_goles_total int,local_corners_total int,visitante_corners_total int,
          local_disparos_arco int,visitante_disparos_arco int);
        INSERT INTO competiciones_baloncesto VALUES ('nba','nba','NBA'),('eu','euroleague','Euro');
        INSERT INTO partidos_baloncesto VALUES
          ('nba',1,'2026-10-30',true,100,90,25,25,25,25,20,20,25,25),
          ('nba',2,'2026-10-29',true,100,90,NULL,25,25,25,20,20,25,25),
          ('nba',3,'2026-10-31',true,100,90,25,25,25,25,20,20,25,25),
          ('nba',4,'2026-10-29',false,100,90,25,25,25,25,20,20,25,25);
        INSERT INTO competiciones_futbol VALUES ('f','COPA','Copa');
        INSERT INTO partidos_futbol VALUES
          ('f',1,'2026-10-30T05:00Z',true,'FINALIZADO',0,0,0,0,NULL,0),
          ('f',2,'2026-10-31T00:00Z',true,'FINALIZADO',1,0,0,0,0,0),
          ('f',3,'2026-10-01T00:00Z',true,'FINALIZADO',1,0,0,0,0,0);''')
    c.read_only = True
    with c.transaction():
        r = leer_cobertura(c, 1, datetime(2026,10,30,18,tzinfo=timezone.utc))
    por_codigo = {x['codigo']: x for x in r['competiciones']}
    assert por_codigo['nba']['registros'] == 1 and por_codigo['nba']['finales_con_marcador'] == 1
    assert por_codigo['nba']['completos_por_campo']['cuartos'] == 1
    assert por_codigo['euroleague']['registros'] == 0 and por_codigo['euroleague']['ultimo_final'] is None
    assert por_codigo['euroleague']['liga'] == 'euroliga'
    assert por_codigo['COPA']['registros'] == 1 and por_codigo['COPA']['finales_con_marcador'] == 1  # 0–0 válido
    assert por_codigo['COPA']['completos_por_campo'] == {'corners': 1, 'disparos_arco': 0}
    assert r['calendario_oficial_completo'] is None
    with c.transaction():
        r = leer_cobertura(c, 2, datetime(2026,10,30,18,tzinfo=timezone.utc))
    nba = next(x for x in r['competiciones'] if x['codigo'] == 'nba')
    assert nba['registros'] == 3 and nba['finales_con_marcador'] == 2 and nba['completos_por_campo']['cuartos'] == 1


def test_api_no_consulta_sin_peticion_y_fallo_no_es_cero(monkeypatch):
    import db
    llamadas = []
    def fallo():
        llamadas.append(1)
        raise RuntimeError('detalle privado que no debe salir')
    monkeypatch.setattr(db, 'obtener_pool', fallo)
    app = FastAPI(); app.include_router(rutas_local.router)
    cliente = TestClient(app)
    assert llamadas == []
    assert cliente.get('/api/local/cobertura?dias=1096').status_code == 422 and llamadas == []
    r = cliente.get('/api/local/cobertura')
    assert r.status_code == 503 and 'detalle privado' not in r.text and 'competiciones' not in r.json()
    assert llamadas == [1]


def test_api_abre_transaccion_readonly(monkeypatch):
    import db
    from servicios import cobertura_uso
    llamadas = []
    class Conn:
        def execute(self, sql): llamadas.append(sql)
    conn = Conn()
    @contextmanager
    def conexion(): yield conn
    class Pool: connection = staticmethod(conexion)
    monkeypatch.setattr(db, 'obtener_pool', lambda: Pool())
    monkeypatch.setattr(cobertura_uso, 'leer_cobertura', lambda c, dias: {'dias': dias, 'mismo': c is conn})
    app = FastAPI(); app.include_router(rutas_local.router)
    assert TestClient(app).get('/api/local/cobertura?dias=30').json() == {'dias': 30, 'mismo': True}
    assert llamadas == ['SET TRANSACTION READ ONLY']


def test_servicio_rechaza_instante_sin_zona_y_ventana_fuera_de_rango():
    with pytest.raises(ValueError): leer_cobertura(None, 0)
    with pytest.raises(ValueError): leer_cobertura(None, 30, datetime(2026,1,1))

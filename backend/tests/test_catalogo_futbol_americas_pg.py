"""Consultas canónicas reales sobre esquema SQL sintético local, sin producción."""
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import rutas_competiciones_futbol as comps, rutas_partidos_futbol as partidos
from api import rutas_analisis_futbol as analisis
from ingesta_futbol_americas import aplicar, planificar
from test_ingesta_futbol_americas import fila
from test_ingesta_futbol_americas_pg import db_local, entrada  # noqa: F401 — fixture SQL aislada


def test_catalogo_pagina_y_aisla_competicion_temporada_estado_y_fecha(db_local, monkeypatch):
    c = db_local
    c.execute("ALTER TABLE partidos_futbol ADD COLUMN jornada int")
    registros = [fila(source_game_id=str(1000+i), inicio_utc=f"2020-03-{10+i:02d}T23:00:00Z",
                      inicio_colombia=f"2020-03-{10+i:02d}T18:00:00-05:00") for i in range(3)]
    registros.append(fila(source_game_id="2000", codigo_liga="bra.1", local_id_fuente="400", visitante_id_fuente="500",
                          local_nombre="Club Brasil A", visitante_nombre="Club Brasil B"))
    with c.transaction():
        q = planificar(c, entrada(*registros))
        aplicar(c, q)
        c.execute("UPDATE partidos_futbol SET valido=false WHERE fecha_partido='2020-03-11T23:00:00Z'")
    @contextmanager
    def conexion(): yield c
    class Pool:
        connection = staticmethod(conexion)
    monkeypatch.setattr(partidos, "obtener_pool", lambda: Pool())
    monkeypatch.setattr(comps, "obtener_pool", lambda: Pool())
    app = FastAPI(); app.include_router(partidos.router); app.include_router(comps.router)
    cid = q["competiciones"]["ARG_PRIMERA"]
    tid = next(a["temporada_id"] for a in q["acciones"] if a["codigo"] == "ARG_PRIMERA")
    with TestClient(app) as client:
        params = {"competicion_id": cid, "temporada_id": tid, "modo": "historicos", "tamano": 1}
        a = client.get('/api/futbol/partidos/catalogo', params=params)
        b = client.get('/api/futbol/partidos/catalogo', params={**params, "pagina": 2})
        assert a.status_code == b.status_code == 200
        assert a.json()['total'] == b.json()['total'] == 2
        pa, pb = a.json()['partidos'][0], b.json()['partidos'][0]
        assert pa['fecha_partido'] > pb['fecha_partido'] and pa['id'] != pb['id']
        assert pa['competicion_id'] == pb['competicion_id'] == cid
        assert pa['temporada_id'] == pb['temporada_id'] == tid
        assert client.get('/api/futbol/partidos/catalogo', params={**params, "modo": "proximos"}).json()['total'] == 0
        assert client.get('/api/futbol/partidos/catalogo', params={**params, "temporada_id": '00000000-0000-0000-0000-000000000001'}).json()['total'] == 0
        assert client.get('/api/futbol/partidos/catalogo', params={**params, "tamano": 101}).status_code == 422
        temporadas = client.get(f'/api/futbol/competiciones/{cid}/temporadas')
        assert temporadas.status_code == 200, temporadas.text
        assert len(temporadas.json()['temporadas']) == 1
        assert temporadas.json()['temporadas'][0]['id'] == tid


def test_historicos_sql_excluyen_objetivo_simultaneos_futuros_otro_torneo_y_temporada(db_local):
    c = db_local
    c.execute("ALTER TABLE partidos_futbol ADD COLUMN local_corners_1t int, ADD COLUMN local_corners_2t int, ADD COLUMN visitante_corners_1t int, ADD COLUMN visitante_corners_2t int")
    base = fila(source_game_id='3001')
    registros = [base,
        fila(source_game_id='3002', inicio_utc='2020-03-11T23:00:00Z', inicio_colombia='2020-03-11T18:00:00-05:00'),
        fila(source_game_id='3003', inicio_utc='2020-03-12T23:00:00Z', inicio_colombia='2020-03-12T18:00:00-05:00'),
        fila(source_game_id='3004', codigo_liga='arg.copa_lpf'),
        fila(source_game_id='3005', temporada=2019, temporada_nombre_fuente='2019',
             inicio_utc='2019-03-10T23:00:00Z', inicio_colombia='2019-03-10T18:00:00-05:00')]
    with c.transaction():
        q = planificar(c, entrada(*registros)); aplicar(c, q)
    a = next(a for a in q['acciones'] if a['row']['source_game_id']=='3001')
    corte = datetime(2020,3,11,23,tzinfo=timezone.utc)
    scope = {'temporada_ids': [a['temporada_id']], 'competicion_id': a['competicion_id']}
    local = analisis._obtener_partidos_equipo(c.cursor(), a['local_id'], corte, 100, solo_local=True, **scope)
    h2h = analisis._obtener_partidos_h2h(c.cursor(), a['local_id'], a['visitante_id'], corte, 100, **scope)
    liga = analisis._obtener_partidos_liga(c.cursor(), a['competicion_id'], corte, 100, temporada_ids=scope['temporada_ids'])
    assert [{str(p['id']) for p in bloque} for bloque in (local,h2h,liga)] == [{a['id']}]*3

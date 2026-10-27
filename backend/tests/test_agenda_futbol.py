"""Agenda global: límites COT, filtros SQL y bloqueo real de prepartido."""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api import rutas_partidos_futbol as rutas
from servicios.agenda_futbol import estado_agenda
from ingesta_futbol_americas import aplicar, planificar
from test_ingesta_futbol_americas import fila
from test_ingesta_futbol_americas_pg import db_local, entrada  # noqa: F401
from test_elegibilidad_futbol import api_sintetica  # noqa: F401


@pytest.mark.parametrize('segundos,estado', [(-1,'POR_VERIFICAR'),(0,'POR_VERIFICAR'),(1,'PROXIMO')])
def test_programado_no_equivale_a_prepartido(segundos, estado):
    ahora=datetime.now(timezone.utc)
    assert estado_agenda('PROGRAMADO', ahora+timedelta(seconds=segundos), ahora)==estado


@pytest.mark.parametrize('estado,esperado', [('FINALIZADO','FINALIZADO'),('EN_VIVO','EN_JUEGO'),('ENTRETIEMPO','EN_JUEGO'),('APLAZADO','NO_DISPONIBLE'),('CANCELADO','NO_DISPONIBLE')])
def test_preserva_estados_sin_inventar_resultados(estado,esperado):
    ahora=datetime.now(timezone.utc)
    assert estado_agenda(estado, ahora-timedelta(hours=1), ahora)==esperado


def test_endpoint_rechaza_hora_vencida_y_en_vivo_pero_acepta_reprogramado(api_sintetica):
    client, partido, _, _=api_sintetica
    payload={'partido_id':partido['id'],'solo_consulta':True,'mercado_objetivo':'GOLES_FT','linea_objetivo':2.5,'lado_objetivo':'OVER'}
    partido['fecha_partido']=datetime.now(timezone.utc)-timedelta(seconds=1)
    r=client.post('/api/futbol/analizar',json=payload)
    assert r.status_code==409 and 'verifica' in r.json()['detail']
    partido['fecha_partido']=datetime.now(timezone.utc)+timedelta(days=1)
    partido['estado']='EN_VIVO'
    assert client.post('/api/futbol/analizar',json=payload).status_code==409
    partido['estado']='PROGRAMADO'
    assert client.post('/api/futbol/analizar',json=payload).status_code==200


@pytest.fixture
def agenda_sql(db_local, monkeypatch):
    c=db_local
    c.execute('ALTER TABLE equipos_futbol ADD COLUMN logo_url text')
    c.execute('ALTER TABLE partidos_futbol ADD COLUMN jornada int')
    filas=[fila(source_game_id='4101',inicio_utc='2020-03-10T05:00:00Z',inicio_colombia='2020-03-10T00:00:00-05:00'),
           fila(source_game_id='4102',inicio_utc='2020-03-10T04:59:59Z',inicio_colombia='2020-03-09T23:59:59-05:00'),
           fila(source_game_id='4103',inicio_utc='2020-03-11T04:59:59Z',inicio_colombia='2020-03-10T23:59:59-05:00',
                codigo_liga='bra.1',local_id_fuente='400',visitante_id_fuente='500',local_nombre='Brasil Local',visitante_nombre='Brasil Visitante'),
           fila(source_game_id='4104',inicio_utc='2020-03-11T05:00:00Z',inicio_colombia='2020-03-11T00:00:00-05:00')]
    with c.transaction():
        plan=planificar(c,entrada(*filas)); aplicar(c,plan)
        c.execute("UPDATE partidos_futbol SET estado='PROGRAMADO',local_goles_total=NULL,visitante_goles_total=NULL")
    monkeypatch.setattr(rutas,'_ahora_agenda',lambda:datetime(2020,3,10,20,tzinfo=timezone.utc).astimezone(rutas.ZONA_HORARIA_USUARIO))
    @contextmanager
    def conexion():yield c
    class Pool:connection=staticmethod(conexion)
    monkeypatch.setattr(rutas,'obtener_pool',lambda:Pool())
    app=FastAPI();app.include_router(rutas.router)
    return TestClient(app),plan


def test_agenda_global_limites_cot_orden_y_paginacion(agenda_sql):
    client,plan=agenda_sql
    r=client.get('/api/futbol/partidos/agenda',params={'fecha':'2020-03-10','tamano':1})
    assert r.status_code==200,r.text
    a=r.json();assert a['total']==2 and a['zona_horaria']=='America/Bogota'
    assert a['partidos'][0]['estado_agenda']=='POR_VERIFICAR' and not a['partidos'][0]['analizable']
    b=client.get('/api/futbol/partidos/agenda',params={'fecha':'2020-03-10','tamano':1,'pagina':2}).json()
    assert b['partidos'][0]['estado_agenda']=='PROXIMO' and b['partidos'][0]['analizable']
    assert a['partidos'][0]['competicion_id']!=b['partidos'][0]['competicion_id']
    assert a['partidos'][0]['fecha_partido']<b['partidos'][0]['fecha_partido']
    assert client.get('/api/futbol/partidos/agenda?fecha=incorrecta').status_code==422
    assert client.get('/api/futbol/partidos/agenda?tamano=101').status_code==422


def test_filtros_sql_por_equipo_pais_estado_competicion_y_guardados(agenda_sql):
    client,plan=agenda_sql
    base={'fecha':'2020-03-10'}
    def get(**kw):return client.get('/api/futbol/partidos/agenda',params={**base,**kw}).json()
    assert get(buscar='Brasil')['total']==1
    assert get(pais='Brasil')['total']==1
    assert get(competicion_id=plan['competiciones']['ARG_PRIMERA'])['total']==1
    assert get(estado='proximos')['total']==get(estado='pendientes')['total']==1
    assert get(estado='finalizados')['total']==get(estado='en_juego')['total']==0
    assert get(buscar='%')['total']==0  # búsqueda literal, no comodín global
    partido=get(buscar='Brasil')['partidos'][0]
    assert get(partido_ids=partido['id'])['total']==1
    assert client.get('/api/futbol/partidos/agenda?estado=inventado').status_code==422

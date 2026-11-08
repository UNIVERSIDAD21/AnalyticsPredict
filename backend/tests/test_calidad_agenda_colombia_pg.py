"""Reproducción SQL sintética: cuarentena, replay, reactivación y API."""
from datetime import date
from uuid import uuid4
import pytest

from servicios.sincronizacion_agendas import planificar,aplicar,filas
from test_ingesta_futbol_americas_pg import db_local  # noqa: F401
from test_sincronizacion_agendas import entorno_baloncesto
from test_agenda_futbol import agenda_sql  # noqa: F401


def entorno_colombia(c):
    entorno_baloncesto(c)
    comp,season,a,b,d=[str(uuid4()) for _ in range(5)]
    c.execute("INSERT INTO competiciones_futbol(id,codigo) VALUES(%s,'COL_PRIMERAA')",(comp,))
    c.execute('INSERT INTO temporadas_futbol(id,competicion_id) VALUES(%s,%s)',(season,comp))
    c.execute("INSERT INTO temporadas_fuente_espn_futbol(liga,anio,temporada_id) VALUES('col.1',2026,%s)",(season,))
    for event,pid in [('A',a),('B',b),('C',d)]:
        c.execute('INSERT INTO equipos_futbol(id,nombre) VALUES(%s,%s)',(pid,event))
        c.execute('INSERT INTO equipos_fuente_espn_futbol(id_fuente,equipo_id) VALUES(%s,%s)',(event,pid))
    r={'deporte':'futbol','codigo':'COL_PRIMERAA','proveedor':'ESPN','feed':'col.1','id_fuente':'101',
       'anio':2026,'local_fuente':'A','visitante_fuente':'B','local_nombre':'A','visitante_nombre':'B',
       'inicio_utc':'2026-11-08T20:30:00+00:00','fecha_fuente':'2026-11-08','precision_fecha':'HORA',
       'zona_origen':'UTC','estado':'PROGRAMADO','resultados':{},
       'evidencia':{'observado_en':'2026-11-08T16:00:00+00:00','sha256':'a'*64}}
    initial=planificar(c,[r],[],[],date(2026,11,8))
    assert not initial['incidencias'];aplicar(c,initial)
    return r,initial['aceptados'][0]['partido_id']


@pytest.mark.integracion
def test_cuarentena_replay_y_reprogramacion_sin_perder_id(db_local):
    c=db_local;r,pid=entorno_colombia(c)
    other={**r,'id_fuente':'102','visitante_fuente':'C','visitante_nombre':'C'}
    q=planificar(c,[r,other],[],[],date(2026,11,8))
    assert len(q['incidencias'])==2 and len(q['operaciones'])==2
    aplicar(c,q)
    assert not filas(c,'SELECT * FROM partidos_futbol WHERE id=%s',(pid,))[0]['valido']
    assert not planificar(c,[r,other],[],[],date(2026,11,8))['operaciones']
    # Un mero desplazamiento del reloj de captura no rehabilita el mismo error.
    newer={**r,'evidencia':{**r['evidencia'],'observado_en':'2026-11-08T17:00:00+00:00'}}
    assert not planificar(c,[newer],[],[],date(2026,11,8))['operaciones']
    new_date={**newer,'inicio_utc':'2026-11-15T20:30:00+00:00','fecha_fuente':'2026-11-15'}
    clean=planificar(c,[new_date],[],[],date(2026,11,8))
    assert not clean['incidencias'];aplicar(c,clean)
    p=filas(c,'SELECT * FROM partidos_futbol WHERE id=%s',(pid,))[0]
    assert p['valido'] and p['fecha_partido']==new_date['inicio_utc']
    assert p['local_goles_total'] is None
    assert not planificar(c,[new_date],[],[],date(2026,11,8))['operaciones']


@pytest.mark.integracion
def test_final_no_desplaza_horario_y_no_reabre_cuarentena(db_local):
    c=db_local;r,pid=entorno_colombia(c)
    c.execute("UPDATE partidos_futbol SET estado='FINALIZADO',local_goles_total=0,visitante_goles_total=0 WHERE id=%s",(pid,))
    final={**r,'estado':'FINALIZADO','inicio_utc':'2026-11-09T20:30:00+00:00',
           'resultados':{'local_goles_total':0,'visitante_goles_total':0}}
    p=planificar(c,[final],[],[],date(2026,11,8))
    assert not p['operaciones'] and 'protegido' in p['incidencias'][0]['motivo']


@pytest.mark.integracion
def test_proximos_y_agenda_excluyen_cuarentena_en_total_y_paginacion(agenda_sql,monkeypatch):
    from api import rutas_partidos_futbol as rutas
    from datetime import datetime,timezone
    client,plan=agenda_sql
    # El mismo fixture visible deja de ser utilizable, sin borrar el registro.
    pool=rutas.obtener_pool()
    with pool.connection() as c:
        target=c.execute("SELECT id FROM partidos_futbol WHERE fecha_partido='2020-03-10T05:00:00Z'").fetchone()['id']
        c.execute('UPDATE partidos_futbol SET valido=false WHERE id=%s',(target,))
    monkeypatch.setattr(rutas,'_rango_proximos',lambda *_:(datetime(2020,3,10,5,tzinfo=timezone.utc),datetime(2020,3,11,5,tzinfo=timezone.utc)))
    for path in ('agenda?fecha=2020-03-10','proximos?dias=1'):
        response=client.get('/api/futbol/partidos/'+path)
        assert response.status_code==200,response.text
        data=response.json()
        assert data['total']==1
        assert all(str(x['id'])!=str(target) for x in data['partidos'])

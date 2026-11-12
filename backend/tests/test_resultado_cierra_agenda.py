"""Un resultado conciliado no debe conservar una deuda vieja de su agenda."""
from datetime import date,datetime,timezone
from types import SimpleNamespace

import pytest

from servicios import flujo_cola_actualizador as flow


@pytest.mark.parametrize('aceptado,conflicto,cierra_agenda',[(True,False,True),(True,True,False),(False,True,False)])
def test_resultado_cierra_solo_su_agenda_con_identidad_sin_conflicto(monkeypatch,aceptado,conflicto,cierra_agenda):
    closed=[]
    monkeypatch.setattr(flow,'aplicar',lambda *_:None)
    monkeypatch.setattr(flow,'sembrar_estadisticas_resultados',lambda *_:0)
    monkeypatch.setattr(flow,'cerrar',lambda _conn,key,*_:closed.append(key))
    monkeypatch.setattr(flow.cola,'guardar_pendiente',lambda *_:None)
    monkeypatch.setattr(flow.cola,'lote',lambda _c,_r,_e,_i,_a,fn:('lote',fn('lote'),True))
    row={'codigo':'ENG_FACUP','id_fuente':'123','anio':2026,'inicio_utc':'2026-11-06T20:00:00Z',
         'evidencia':{'observado_en':'2026-11-12T17:00:00+00:00'}}
    league={'codigo':'ENG_FACUP','deporte':'futbol'}
    issues=[{'grupo':'ENG_FACUP','id':'123','motivo':'Conflicto de fecha'}] if conflicto else []
    plan={'incidencias':issues,'aceptados':[{'codigo':'ENG_FACUP','id_fuente':'123','partido_id':'partido'}] if aceptado else [],
          'operaciones':[],'sha256':'a'*64}
    flow.aplicar_resultados(SimpleNamespace(execute=lambda *_:None),'run',plan,[row],
        [(league,date(2026,11,5),date(2026,11,12),[],[])],datetime(2026,11,12,tzinfo=timezone.utc),acreditar=False)
    assert any(k[5]=='AGENDA' for k in closed)==cierra_agenda
    assert all(k[4]=='123' for k in closed)

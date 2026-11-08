"""Regresiones del contrato: cruces superpuestos no son horas confirmadas."""
from copy import deepcopy
from datetime import datetime, timezone
from itertools import permutations

import pytest

from servicios.calidad_agenda_colombia import conflictos, puede_reactivar, CONTRATO


def row(event='1', home='A', away='B', start='2026-11-08T20:30:00+00:00', **kwargs):
    return {'deporte':'futbol','codigo':'COL_PRIMERAA','feed':'col.1', 'id_fuente':event,
            'local_id':home,'visitante_id':away,'inicio_utc':start,'estado':'PROGRAMADO',
            'evidencia':{'observado_en':'2026-11-08T17:00:00+00:00'},**kwargs}


def canonical(pid='p1', home='A', away='C', start='2026-11-08T23:10:00+00:00', **kwargs):
    return {'id':pid,'equipo_local_id':home,'equipo_visitante_id':away,
            'fecha_partido':start,'estado':'PROGRAMADO','valido':True,
            'local_goles_total':None,'visitante_goles_total':None,**kwargs}


def horario(pid='p1',start='2026-11-08T23:10:00+00:00',official=False):
    p={'proveedor':'DIMAYOR_OFFICIAL','url':'https://dimayor.com.co/',
       'inicio_utc':start,'sha256':'a'*64}
    return {'partido_id':pid,'competicion_codigo':'COL_PRIMERAA','inicio_utc':start,
            'observado_en':'2026-11-08T16:00:00+00:00',
            'evidencia':{'confirmacion_agenda':p} if official else {}}


def test_dos_cruces_del_mismo_equipo_no_dependen_del_orden():
    rows=[row(),row('2','C','A')]
    for values in permutations(rows):
        assert set(conflictos(values,[],{},[]))=={'1','2'}


def test_horario_oficial_gana_sin_usar_mayoria():
    p=canonical();h=horario(official=True)
    rows=[row('2','A','C',p['fecha_partido']),row(),row('3','D','C')]
    links=[{'liga':'col.1','id_fuente':'2','partido_id':p['id']}]
    for values in permutations(rows):
        assert set(conflictos(values,[p],{'p1':h},links))=={'1','3'}


def test_final_del_dia_anterior_detecta_placeholder_del_dia_siguiente():
    p=canonical(start='2026-11-07T23:10:00+00:00',estado='FINALIZADO')
    h=horario(start=p['fecha_partido'])
    assert set(conflictos([row()],[p],{'p1':h},[]))=={'1'}


def test_final_no_es_inhabilitado_por_fixture_y_colombia_no_afecta_otras_ligas():
    assert not conflictos([row(estado='FINALIZADO'),row('2',codigo='BRA_SERIEA')],[],{},[])


def test_una_reprogramacion_no_choca_con_su_propia_preimagen():
    p=canonical();h=horario()
    links=[{'liga':'col.1','id_fuente':'1','partido_id':'p1'}]
    assert not conflictos([row()],[p],{'p1':h},links)


def test_hora_nueva_solo_compara_calendario_actual_no_reserva_obsoleta():
    p=canonical();h=horario()
    links=[{'liga':'col.1','id_fuente':'1','partido_id':'p1'}]
    rows=[row('1',start='2026-11-10T20:30:00+00:00'),row('2','C','A')]
    assert not conflictos(rows,[p],{'p1':h},links)


def test_invalidacion_ajena_no_justifica_bloquear_calendario_nuevo():
    p=canonical(valido=False);h=horario()
    assert not conflictos([row()],[p],{'p1':h},[])


def test_dia_sin_hora_no_se_convierte_en_instante():
    assert not conflictos([row(inicio_utc=None),row('2','A','C')],[],{},[])


def test_no_chocan_clubes_diferentes_ni_un_dia_completo_de_separacion():
    assert not conflictos([row(),row('2','C','D'),row('3',start='2026-11-09T20:30:00+00:00')],[],{},[])


def test_rehabilitacion_exige_cuarentena_propia_hora_distinta_y_evidencia_nueva():
    p=canonical(valido=False);h=horario()
    h['evidencia']['cuarentena_agenda']={'contrato':CONTRATO,'inicio_rechazado':p['fecha_partido']}
    r=row(start='2026-11-15T20:30:00+00:00')
    assert puede_reactivar(p,h,r)
    for bad in [row(start=p['fecha_partido']),row(start=r['inicio_utc'],evidencia={'observado_en':h['observado_en']})]:
        assert not puede_reactivar(p,h,bad)
    assert not puede_reactivar(p,horario(),r)
    assert not puede_reactivar({**p,'local_goles_total':0},h,r)
    assert not puede_reactivar({**p,'estado':'FINALIZADO'},h,r)

"""Outcomes del registro, incluidos ceros, ET/OT y cuotas legacy ausentes."""
from datetime import date
from decimal import Decimal

import pytest

from motor.resolucion_bitacora import calcular_cierre, valor_futbol


def apuesta(**extras):
    return dict(partido_id='juego', mercado='GOLES_FT', lado='UNDER', linea='2.5',
                cuota='1.91', stake='10.01') | extras


def futbol(**extras):
    return dict(valido=True, estado='FINALIZADO', fecha_partido='2026-10-20T18:00:00Z',
                hubo_tiempo_extra=False, local_goles_1t=0, local_goles_2t=0,
                visitante_goles_1t=0, visitante_goles_2t=0,
                local_goles_total=0, visitante_goles_total=0) | extras


def basket(**extras):
    return dict(valido=True, fecha_partido='2026-10-20', competicion_id='euro',
                equipo_local_id='local', equipo_visitante_id='visita', ganador_id='local',
                local_q1=20, local_q2=20, local_q3=20, local_q4=20,
                visitante_q1=20, visitante_q2=20, visitante_q3=20, visitante_q4=20,
                local_ot=12, visitante_ot=8, local_total=92, visitante_total=88) | extras


def test_futbol_cero_cero_final_y_aritmetica_decimal():
    cierre, motivo = calcular_cierre(apuesta(), futbol(), 'futbol')
    assert motivo is None
    assert cierre == dict(resultado='GANADA', valor_real=0, ganancia=Decimal('9.11'))


def test_null_no_es_cero_ni_un_solo_lado_es_total():
    assert valor_futbol('CORNERS_FT', futbol(local_corners_total=4)) is None
    assert valor_futbol('CORNERS_FT', futbol(local_corners_total=0, visitante_corners_total=0)) == 0
    assert valor_futbol('GOLES_FT', futbol(visitante_goles_total=None, visitante_goles_1t=None)) is None


def test_futbol_ft_excluye_extra_y_penales_sin_inferir_mitades():
    p = futbol(hubo_tiempo_extra=True, visitante_goles_1t=1, visitante_goles_2t=0,
               visitante_goles_et=1, visitante_goles_total=2, visitante_penales=5)
    assert valor_futbol('GOLES_VISITANTE_FT', p) == 1
    assert valor_futbol('CORNERS_FT', p | dict(local_corners_total=4, visitante_corners_total=5)) is None
    assert valor_futbol('GOLES_VISITANTE_FT', p | dict(visitante_goles_1t=None)) is None


@pytest.mark.parametrize('mercado,esperado', [('DISPAROS_LOCAL_ARCO_FT', 2), ('DISPAROS_ARCO_FT', 5),
    ('DISPAROS_LOCAL_FT', 8), ('DISPAROS_VISITANTE_FT', 10), ('DISPAROS_1T', None), ('OTROS_FT', None)])
def test_disparos_respeta_equipo_metrica_y_periodo(mercado, esperado):
    assert valor_futbol(mercado, futbol(local_disparos_arco=2, visitante_disparos_arco=3,
                                      local_disparos_total=8, visitante_disparos_total=10)) == esperado


@pytest.mark.parametrize('cambios,motivo', [({'estado':'EN_VIVO'}, 'partido_no_finalizado'),
    ({'valido':False}, 'partido_no_valido'), ({'fecha_partido':'2099-01-01'}, 'partido_futuro')])
def test_no_cierra_sin_final_valido(cambios, motivo):
    assert calcular_cierre(apuesta(), futbol(**cambios), 'futbol')[1] == motivo


def test_cuota_ausente_no_impide_outcome_pero_no_inventa_importe():
    cierre, motivo = calcular_cierre(apuesta(cuota=0), futbol(), 'futbol')
    assert motivo is None and cierre['resultado'] == 'GANADA' and cierre['ganancia'] is None


def test_push_y_lineas_asiaticas_no_son_medios_puntos():
    cierre, _ = calcular_cierre(apuesta(linea=0), futbol(), 'futbol')
    assert cierre['resultado'] == 'PUSH' and cierre['ganancia'] == 0
    assert calcular_cierre(apuesta(linea=2.25), futbol(), 'futbol')[1] == 'linea_asiatica_no_soportada'
    assert calcular_cierre(apuesta(lado='INVALIDO'), futbol(), 'futbol')[0] is None


def test_euro_40_minutos_y_nba_incluye_ot():
    a = apuesta(mercado='COMPLETO', linea=170)
    assert calcular_cierre(a, basket(), 'euroleague')[0]['resultado'] == 'GANADA'
    assert calcular_cierre(a, basket(), 'nba')[0]['resultado'] == 'PERDIDA'
    assert calcular_cierre(a | dict(competicion_id='nba'), basket(), 'euroleague')[1] == 'competicion_inconsistente'


def test_basket_sin_final_cuartos_o_ganador_no_se_cierra():
    a = apuesta(mercado='Q1', linea=40)
    for cambios in [dict(local_total=0), dict(local_q4=None), dict(ganador_id=None), dict(local_ot=9), dict(ganador_id='visita')]:
        assert calcular_cierre(a, basket(**cambios), 'euroleague')[0] is None


def test_final_del_mismo_dia_si_se_cierra():
    p = futbol(fecha_partido=str(date.today()))
    assert calcular_cierre(apuesta(), p, 'futbol', hoy=date.today())[0]['resultado'] == 'GANADA'

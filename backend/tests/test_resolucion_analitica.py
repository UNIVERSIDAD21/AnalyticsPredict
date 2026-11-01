"""Outcomes por objetivo: falsos ceros, aliases, ET y separación de dominios."""
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from motor.resolucion_analitica import evaluar, valor_futbol, comparar
from motor.resolucion_predicciones_futbol import _valor_real_futbol

AHORA = datetime(2026, 10, 25, 23, tzinfo=timezone.utc)


@pytest.fixture
def futbol():
    return dict(id='f', valido=True, estado='FINALIZADO', fecha_partido='2026-10-24T20:00:00Z',
                hubo_tiempo_extra=False, local_goles_total=2, visitante_goles_total=0,
                local_goles_1t=1, visitante_goles_1t=0, local_goles_2t=1, visitante_goles_2t=0,
                local_corners_total=8, visitante_corners_total=4,
                local_corners_1t=3, visitante_corners_1t=0, local_corners_2t=5, visitante_corners_2t=4,
                local_disparos_total=20, visitante_disparos_total=10,
                local_disparos_arco=8, visitante_disparos_arco=2)


def registro(mercado='CORNERS_FT', lado='OVER', linea=9.5, **kw):
    return dict(partido_id='f', deporte='futbol', mercado=mercado, lado=lado, linea=linea, **kw)


@pytest.mark.parametrize('mercado,valor', [
    ('CORNERS_FT',12), ('CORNERS_1T',3), ('CORNERS_2T',9),
    ('CORNERS_LOCAL_1T',3), ('CORNERS_VISITANTE_1T',0),
    ('GOLES_FT',2), ('GOLES_VISITANTE_FT',0), ('GOLES_LOCAL_2T',1),
    ('DISPAROS_FT',30), ('DISPAROS_ARCO_FT',10),
    ('DISPAROS_LOCAL_ARCO_FT',8), ('DISPAROS_VISITANTE_ARCO_FT',2),
    ('CORNERS_LOCAL_2T',5), ('CORNERS_LOCAL_FT',8),
    ('CORNERS_VISITANTE_2T',4), ('CORNERS_VISITANTE_FT',4),
    ('GOLES_1T',1), ('GOLES_2T',1), ('GOLES_LOCAL_1T',1), ('GOLES_LOCAL_FT',2),
    ('GOLES_VISITANTE_1T',0), ('GOLES_VISITANTE_2T',0),
    ('DISPAROS_LOCAL_FT',20), ('DISPAROS_VISITANTE_FT',10),
])
def test_metrica_exacta_y_coherente_en_ambos_resolvedores(futbol, mercado, valor):
    assert valor_futbol(mercado, futbol) == (valor,None)
    assert _valor_real_futbol(mercado, futbol) == valor


@pytest.mark.parametrize('mercado', ['DISPAROS_1T','DISPAROS_2T','DISPAROS_ARCO_1T','DISPAROS_LOCAL_ARCO_2T'])
def test_mitad_de_tiros_no_usa_ft_como_outcome(futbol, mercado):
    assert valor_futbol(mercado, futbol) == (None,'OBJETIVO_ESTIMADO_SIN_OBSERVACION')


@pytest.mark.parametrize('bruto', [None,-1,True,1.2,float('nan'),float('inf')])
def test_faltante_o_invalido_nunca_se_convierte_en_cero(futbol, bruto):
    futbol['visitante_corners_1t'] = bruto
    assert valor_futbol('CORNERS_1T', futbol)[0] is None
    # Un lado independiente conserva su valor observado.
    assert valor_futbol('CORNERS_LOCAL_1T', futbol)[0] == 3


@pytest.mark.parametrize('mercado', ['ANALISIS_FT','OT','GOLES_LOCAL_VISITANTE_FT','PUNTOS_FT','CORNERS_FT_EXTRA'])
def test_no_hay_fallback_a_goles_ft(futbol, mercado):
    assert valor_futbol(mercado, futbol) == (None,'MERCADO_NO_SOPORTADO')


def test_regulacion_et_y_tanda_separadas(futbol):
    futbol.update(hubo_tiempo_extra=True,local_goles_total=3,local_goles_et=1,visitante_goles_et=0,
                  local_penales=5,visitante_penales=4)
    assert valor_futbol('GOLES_FT', futbol)[0] == 2
    assert valor_futbol('GOLES_1T', futbol)[0] == 1
    assert valor_futbol('CORNERS_FT', futbol)[0] is None
    futbol['local_goles_et'] = None
    assert valor_futbol('GOLES_FT', futbol)[0] is None


def test_ninguna_mitad_ni_bandera_et_se_inventa(futbol):
    futbol['local_goles_2t'] = None
    assert valor_futbol('GOLES_FT', futbol)[0] == 2
    assert valor_futbol('GOLES_2T', futbol)[0] is None
    del futbol['hubo_tiempo_extra']
    assert valor_futbol('GOLES_FT', futbol)[0] is None


def test_contradiccion_no_invalida_ft_independiente(futbol):
    futbol['visitante_goles_2t'] = -1
    futbol['visitante_goles_1t'] = 1
    assert valor_futbol('GOLES_1T', futbol)[0] is None
    assert valor_futbol('GOLES_2T', futbol)[0] is None
    assert valor_futbol('GOLES_FT', futbol)[0] == 2


@pytest.mark.parametrize('lado,linea,outcome', [('OVER',9.5,'GANADA'),('UNDER',9.5,'PERDIDA'),('OVER',12,'PUSH'),('UNDER',12,'PUSH')])
def test_comparacion_exacta_y_sin_certificacion(futbol,lado,linea,outcome):
    antes=deepcopy(futbol)
    r,m=evaluar(registro(lado=lado,linea=linea),futbol,'futbol',AHORA)
    assert not m and r['resultado_outcome']==outcome and r['valor_real']==12
    assert r['prospectiva_certificada'] is False and futbol==antes


@pytest.mark.parametrize('linea,motivo', [(None,'LINEA_INVALIDA'),(True,'LINEA_INVALIDA'),(-1,'LINEA_INVALIDA'),(float('nan'),'LINEA_INVALIDA'),(9.25,'LINEA_ASIATICA_NO_SOPORTADA')])
def test_lineas_sin_contrato_no_generan_outcomes(linea,motivo):
    assert comparar(12,linea)==(None,motivo)


@pytest.mark.parametrize('cambio,motivo', [({'valido':False},'PARTIDO_NO_VALIDO'),({'estado':'POSPUESTO'},'PARTIDO_NO_FINALIZADO'),({'estado':'SUSPENDIDO'},'PARTIDO_NO_FINALIZADO'),({'fecha_partido':'2026-10-26T01:00:00Z'},'PARTIDO_FUTURO'),({'id':'otro'},'PARTIDO_INCONSISTENTE')])
def test_no_resolver_calendario_invalido_o_evento_ajeno(futbol,cambio,motivo):
    assert evaluar(registro(),futbol|cambio,'futbol',AHORA)==(None,motivo)


@pytest.fixture
def basket():
    return dict(id='b', valido=True,fecha_partido='2026-10-24',equipo_local_id='h',equipo_visitante_id='a',ganador_id='h',
                local_q1=20,local_q2=20,local_q3=20,local_q4=20,local_ot=10,local_total=90,
                visitante_q1=20,visitante_q2=20,visitante_q3=20,visitante_q4=20,visitante_ot=8,visitante_total=88)


def test_nba_ft_con_ot_euro_regulacion_y_wnba_contrato_explicito(basket):
    r=registro('COMPLETO',linea=170)|{'partido_id':'b','deporte':'baloncesto','payload':{'fuente':'analisis_nba'}}
    assert evaluar(r,basket,'nba',AHORA)[0]['valor_real']==178
    assert evaluar(r,basket,'euroleague',AHORA)[1]=='DOMINIO_INCONSISTENTE'
    r['payload']={'seguimiento_analitico':{'liga':'euroleague'}}
    assert evaluar(r,basket,'euroleague',AHORA)[0]['valor_real']==160
    r['payload']={'seguimiento_analitico':{'liga':'wnba'}}
    assert evaluar(r,basket,'wnba',AHORA)[1]=='CONTRATO_OT_NO_ACREDITADO'
    for ot,valor in [(True,178),(False,160)]:
        r['payload']['seguimiento_analitico']['incluye_ot']=ot
        assert evaluar(r,basket,'wnba',AHORA)[0]['valor_real']==valor


def test_cuarto_ausente_nd_otros_cuartos_y_ft_preservados(basket):
    r=registro('Q1')|{'partido_id':'b','deporte':'baloncesto'}
    basket['local_q1']=None
    assert evaluar(r,basket,'nba',AHORA)[0] is None
    assert evaluar(r|{'mercado':'Q2'},basket,'nba',AHORA)[0]['valor_real']==40
    assert evaluar(r|{'mercado':'COMPLETO'},basket,'nba',AHORA)[0]['valor_real']==178


def test_sot_no_puede_exceder_tiros(futbol):
    futbol['local_disparos_arco']=21
    assert evaluar(registro('DISPAROS_ARCO_FT'),futbol,'futbol',AHORA)[0] is None


def test_nba_no_compensa_un_cuarto_negativo_con_el_del_otro_equipo():
    from motor.resolucion_predicciones import _calcular_valor_real
    assert _calcular_valor_real('Q1',-1,20,20,20,80,30,20,20,20,90) is None

from copy import deepcopy
import pytest

from servicios.contrato_probabilidad_nba import describir_probabilidad
from motor.nba_predictor_cuartos import resultado_a_dict
from test_nba_modo_cierre import modelo, calcular  # noqa: F401 — fixture sintética


@pytest.mark.parametrize('linea,compatible', [(210.5,True),(210.,False),(210.25,False)])
def test_contrato_no_atribuye_push_ni_calibracion_ausentes(linea,compatible):
    c=describir_probabilidad('COMPLETO',linea,False)
    assert c['tipo']=='RAW' and c['calibrador'] is None and c['incluye_ot'] is False
    assert c['linea_evento_discreto_compatible'] is compatible
    assert c['push']==(0. if compatible else None)
    assert bool(c['motivo_nd']) is (not compatible)


def test_serializar_contrato_no_muta_modelo_salida_ni_contexto(modelo):
    r=calcular(modelo)
    metadata=deepcopy(r.metadata)
    original=(r.prediccion_juego_completo.media_total,r.prediccion_juego_completo.probabilidad_over)
    datos=resultado_a_dict(r)
    assert datos['metadata']['contrato_probabilidad']['origen']=='distribucion_base'
    assert (datos['prediccion_juego_completo']['media_total'],datos['probabilidad_over'])==original
    assert r.metadata==metadata and 'contrato_probabilidad' not in r.metadata
    corte=resultado_a_dict(calcular(modelo,marcador_q1='20-22'))
    assert corte['metadata']['contrato_probabilidad']['origen']=='corte_heuristico'

import math
import pytest
from motor.auditoria_probabilidades_wnba import metricas_guardadas, _diferencia, auditar


def test_probabilidad_constante_y_bins_vacios_conservan_definicion_multiclase():
    r = metricas_guardadas([1,2], [1.5,1.5], 1., 1.5, 2.)
    assert r['brier_multiclase'] == .5  # Suma de dos errores .25; no .25 binario.
    assert r['log_loss'] == pytest.approx(math.log(2))
    assert r['push_observados'] == 1 and r['cobertura_intervalo80'] == 1
    assert r['calibracion_bins'][5] == {'desde': .5, 'hasta': .6, 'n': 2, 'probabilidad_media': .5, 'frecuencia_observada': .5}
    assert sum(b['n'] for b in r['calibracion_bins']) == 2
    assert r['calibracion_bins'][0]['n'] == 0 and r['calibracion_bins'][0]['frecuencia_observada'] is None


def test_auditoria_no_acepta_publicacion_alterada_ni_imputa_ausencias():
    with pytest.raises(ValueError, match='no íntegra'): auditar({'formato':'otro'})
    assert _diferencia({'x':[None,.2]}, {'x':[None,.3]}) == pytest.approx(.1)
    with pytest.raises(ValueError, match='Ausencia alterada'): _diferencia({'x':None}, {'x':0})
    with pytest.raises(ValueError): metricas_guardadas([], [], 1., 1.5, 2.)
    with pytest.raises(ValueError): metricas_guardadas([1], [float('nan')], 1., 1.5, 2.)

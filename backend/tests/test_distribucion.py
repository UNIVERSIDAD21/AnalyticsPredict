from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.metricas.distribucion import calcular_metricas_distribucion


def test_distribucion_perfecta():
    predicciones = [
        (100.0, 100.0, 95.0, 105.0),
        (110.0, 110.0, 108.0, 112.0),
    ]
    resultado = calcular_metricas_distribucion(predicciones)

    assert resultado["n"] == 2
    assert resultado["mae_media"] == pytest.approx(0.0)
    assert resultado["rmse_media"] == pytest.approx(0.0)
    assert resultado["sesgo_media"] == pytest.approx(0.0)
    assert resultado["cobertura_intervalo"] == pytest.approx(1.0)
    assert resultado["n_con_intervalo"] == 2
    assert resultado["n_sin_intervalo"] == 0


def test_distribucion_sesgo_positivo_y_negativo():
    predicciones = [
        (100.0, 110.0, None, None),
        (120.0, 110.0, None, None),
    ]
    resultado = calcular_metricas_distribucion(predicciones)

    assert resultado["n"] == 2
    assert resultado["sesgo_media"] == pytest.approx(0.0)
    assert resultado["mae_media"] == pytest.approx(10.0)
    assert resultado["rmse_media"] == pytest.approx(10.0)


def test_distribucion_sin_intervalos():
    predicciones = [
        (100.0, 105.0, None, None),
        (110.0, 108.0, None, None),
    ]
    resultado = calcular_metricas_distribucion(predicciones)

    assert resultado["n"] == 2
    assert resultado["cobertura_intervalo"] is None
    assert resultado["n_con_intervalo"] == 0
    assert resultado["n_sin_intervalo"] == 2


def test_distribucion_intervalos_mixtos():
    predicciones = [
        (100.0, 101.0, 98.0, 102.0),
        (110.0, 120.0, 109.0, 111.0),
        (105.0, 106.0, None, None),
    ]
    resultado = calcular_metricas_distribucion(predicciones)

    assert resultado["n"] == 3
    assert resultado["n_con_intervalo"] == 2
    assert resultado["n_sin_intervalo"] == 1
    assert resultado["cobertura_intervalo"] == pytest.approx(0.5)

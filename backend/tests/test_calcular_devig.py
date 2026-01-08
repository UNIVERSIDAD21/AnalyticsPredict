import sys
from pathlib import Path

import math

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.calculadora_probabilidad import calcular_devig


def test_calcular_devig_exacto():
    datos = calcular_devig(1.9, 1.9)

    assert datos.metodo == "exacto"
    assert datos.overround == pytest.approx(1.0526315)
    assert datos.p_mkt_fair == pytest.approx(0.5)
    assert not any(math.isnan(valor) for valor in [datos.p_mkt_raw, datos.p_mkt_fair])


def test_calcular_devig_no_aplicado():
    datos = calcular_devig(2.0, modo_estimado=False)

    assert datos.metodo == "no_aplicado"
    assert datos.overround is None
    assert datos.p_mkt_fair == pytest.approx(datos.p_mkt_raw)
    assert any("no se puede de-vig exacto" in advertencia for advertencia in datos.advertencias)


def test_calcular_devig_estimado():
    datos = calcular_devig(2.0, modo_estimado=True)

    assert datos.metodo == "estimado"
    assert datos.overround == pytest.approx(1.045)
    assert datos.p_mkt_fair == pytest.approx(datos.p_mkt_raw / 1.045)
    assert any("estimado" in advertencia.lower() for advertencia in datos.advertencias)
    assert any("penalizar" in advertencia.lower() for advertencia in datos.advertencias)


def test_calcular_devig_advertencia_overround_alto():
    datos = calcular_devig(1.01, 1.01)

    assert datos.overround > 1.10
    assert any("overround > 1.10" in advertencia.lower() for advertencia in datos.advertencias)


def test_calcular_devig_advertencia_overround_bajo():
    datos = calcular_devig(2.5, 2.5)

    assert datos.overround < 1.0
    assert any("overround < 1.0" in advertencia.lower() for advertencia in datos.advertencias)

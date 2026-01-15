from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.metricas.ece import calcular_ece


def _predicciones_calibradas():
    return [
        (0.25, True),
        (0.25, False),
        (0.25, False),
        (0.25, False),
        (0.75, True),
        (0.75, True),
        (0.75, True),
        (0.75, False),
    ]


def test_ece_fijos_perfecto():
    resultado = calcular_ece(_predicciones_calibradas(), n_bins=2, tipo_bins="fijos")

    assert resultado["n"] == 8
    assert resultado["ece"] == pytest.approx(0.0)
    assert resultado["mce"] == pytest.approx(0.0)


def test_ece_fijos_descalibrado():
    predicciones = [(0.9, False)] * 5 + [(0.1, True)] * 5
    resultado = calcular_ece(predicciones, n_bins=2, tipo_bins="fijos")

    assert resultado["n"] == 10
    assert resultado["ece"] > 0.7
    assert resultado["mce"] == pytest.approx(resultado["ece"], rel=0.1)


def test_ece_cuantiles_concentracion():
    predicciones = [(0.55, True)] * 9 + [(0.55, False)]
    resultado = calcular_ece(predicciones, n_bins=5, tipo_bins="cuantiles")

    assert resultado["n"] == 10
    assert resultado["metadatos"]["bins_efectivos"] == 1
    assert len(resultado["bins"]) == 1


def test_ece_excluye_push():
    predicciones = [(0.7, True), (0.2, False), (0.5, None)]
    resultado = calcular_ece(predicciones, n_bins=2, tipo_bins="fijos")

    assert resultado["n"] == 2

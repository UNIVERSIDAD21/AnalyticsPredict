from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.metricas.brier import calcular_brier_score


def test_brier_score_perfecto():
    predicciones = [(1.0, True)] * 5 + [(0.0, False)] * 5
    resultado = calcular_brier_score(predicciones)

    assert resultado["n"] == 10
    assert resultado["brier_score"] == pytest.approx(0.0)


def test_brier_score_baseline():
    predicciones = [(0.5, True)] * 5 + [(0.5, False)] * 5
    resultado = calcular_brier_score(predicciones)

    assert resultado["n"] == 10
    assert resultado["brier_score"] == pytest.approx(0.25)


def test_brier_score_excluye_push():
    predicciones = [(0.7, True), (0.2, False), (0.5, None)]
    resultado = calcular_brier_score(predicciones)

    assert resultado["n"] == 2

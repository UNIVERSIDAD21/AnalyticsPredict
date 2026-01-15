from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.metricas.log_loss import calcular_log_loss


def test_log_loss_perfecto():
    predicciones = [(1.0, True)] * 5 + [(0.0, False)] * 5
    resultado = calcular_log_loss(predicciones, eps=1e-12)

    assert resultado["n"] == 10
    assert resultado["log_loss"] == pytest.approx(0.0, abs=1e-8)


def test_log_loss_confianza_incorrecta():
    predicciones = [(0.99, False)] * 5
    resultado = calcular_log_loss(predicciones)

    assert resultado["n"] == 5
    assert resultado["log_loss"] > 3.0


def test_log_loss_clipping_extremos():
    predicciones = [(0.0, True), (1.0, False)]
    resultado = calcular_log_loss(predicciones, eps=1e-12)

    assert resultado["n"] == 2
    assert resultado["log_loss"] > 0.0
    assert resultado["p_min"] == pytest.approx(1e-12)
    assert resultado["p_max"] == pytest.approx(1.0 - 1e-12)


def test_log_loss_excluye_push():
    predicciones = [(0.7, True), (0.2, False), (0.5, None)]
    resultado = calcular_log_loss(predicciones)

    assert resultado["n"] == 2

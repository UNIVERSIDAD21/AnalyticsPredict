import math

import pytest
import numpy as np

from metricas_probabilisticas import resumir_pares_binarios
from api.rutas_metricas_futbol import _metricas_probabilidades_binarias
from backtesting.metricas.brier import calcular_brier_score
from backtesting.metricas.ece import calcular_ece
from backtesting.metricas.log_loss import calcular_log_loss
from motor_futbol.calibracion.metricas_calibracion import (
    calcular_brier_score as brier_futbol,
    calcular_ece as ece_futbol,
    calcular_log_loss as log_loss_futbol,
)
from motor_futbol.evaluacion.metricas import CalculadorMetricas
from scripts.walkforward_scorecard_futbol import ece_bin


def test_formulas_binarias_con_pares_conocidos():
    resultado = resumir_pares_binarios([(0.1, 0), (0.9, 1)])
    assert resultado["n"] == 2
    assert resultado["n_excluidas"] == 0
    assert resultado["brier"] == pytest.approx(0.01)
    assert resultado["log_loss"] == pytest.approx(-math.log(0.9))
    assert resultado["ece"] == pytest.approx(0.1)


def test_sin_pares_validos_no_se_publica_cero():
    resultado = resumir_pares_binarios([(None, 1), (0.2, None), (float("nan"), 0)])
    assert resultado == {"n": 0, "n_excluidas": 3, "brier": None,
                         "log_loss": None, "ece": None}


def test_extremos_y_bins_fijos():
    resultado = resumir_pares_binarios([(0, 0), (1, 1), (0.1, 0), (0.5, 1)])
    assert resultado["n"] == 4
    assert resultado["brier"] == pytest.approx(0.065)
    assert resultado["ece"] == pytest.approx(0.15)
    assert math.isfinite(resultado["log_loss"])


def test_longitudes_no_se_truncan_en_silencio():
    with pytest.raises(ValueError):
        resumir_pares_binarios([(0.5, 1)], n_bins=0)


def test_productores_nba_y_futbol_comparten_escala_y_bins():
    ps = [0.0, 0.1, 0.5, 1.0]
    ys = [0, 0, 1, 1]
    canon = resumir_pares_binarios(zip(ps, ys))
    pares = list(zip(ps, [bool(y) for y in ys]))
    assert calcular_brier_score(pares)["brier_score"] == pytest.approx(canon["brier"])
    assert calcular_log_loss(pares)["log_loss"] == pytest.approx(canon["log_loss"])
    assert calcular_ece(pares, min_por_bin=1)["ece"] == pytest.approx(canon["ece"])
    assert brier_futbol(np.array(ps), np.array(ys)) == pytest.approx(canon["brier"])
    assert log_loss_futbol(np.array(ps), np.array(ys)) == pytest.approx(canon["log_loss"])
    assert ece_futbol(np.array(ps), np.array(ys)) == pytest.approx(canon["ece"])
    assert CalculadorMetricas.ece(np.array(ps), np.array(ys)) == pytest.approx(canon["ece"])
    assert _metricas_probabilidades_binarias(ps, ys)["ece"] == pytest.approx(canon["ece"])


def test_sin_muestra_todos_los_productores_devuelven_nd():
    assert calcular_brier_score([])["brier_score"] is None
    assert calcular_log_loss([])["log_loss"] is None
    assert calcular_ece([])["ece"] is None
    assert brier_futbol(np.array([]), np.array([])) is None
    assert log_loss_futbol(np.array([]), np.array([])) is None
    assert ece_futbol(np.array([]), np.array([])) is None
    assert CalculadorMetricas.brier_score(np.array([]), np.array([])) is None
    assert _metricas_probabilidades_binarias([], [])["ece"] is None
    assert ece_bin([], []) is None

# -*- coding: utf-8 -*-
from __future__ import annotations

from calidad.recalibracion import evaluar_calibracion_mercado, proponer_metodo_calibracion


class _Cursor:
    def __init__(self):
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _sql, _params=None):
        self.calls += 1

    def fetchone(self):
        # n_total, brier_prom, logloss_prom, gap_prom
        return (1000, 0.2123, 0.6331, 0.0412)

    def fetchall(self):
        return [
            ("0.60-0.69", 300, 0.596, 0.650),
            ("0.70-0.79", 350, 0.722, 0.748),
            ("0.80+", 200, 0.765, 0.888),
            ("<0.60", 150, 0.340, 0.281),
        ]


class _Conn:
    def cursor(self):
        return _Cursor()


def test_evaluar_calibracion_mercado_mock() -> None:
    out = evaluar_calibracion_mercado(_Conn(), "COMPLETO", n_samples=2000)
    assert out["mercado"] == "COMPLETO"
    assert out["n_total"] == 1000
    assert out["brier"] > 0
    assert out["ece"] >= 0
    assert out["logloss"] > 0
    assert len(out["buckets"]) == 4


def test_proponer_metodo_en_catalogo() -> None:
    metodo = proponer_metodo_calibracion(
        {"ece": 0.061, "calibration_gap": 0.04, "n_total": 900}
    )
    assert metodo in ["isotonic", "platt", "beta", "ninguno"]

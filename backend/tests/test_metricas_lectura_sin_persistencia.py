"""Las lecturas de reporte y drift no deben crear precálculos implícitos."""

from datetime import date
from unittest.mock import patch

from api.rutas_backtest import _obtener_metricas_backtest
from backtesting.monitoreo.drift import _obtener_metricas_periodo


def test_reporte_backtest_y_drift_calculan_sin_escribir_precalculos():
    with patch("api.rutas_backtest.calcular_metricas_calibracion", return_value={}) as calcular:
        resultado = _obtener_metricas_backtest(
            {"fecha_inicio_eval": date(2026, 1, 1),
             "fecha_fin_eval": date(2026, 1, 31)},
            ["COMPLETO"], ["API_USUARIO"],
        )
        assert len(resultado) == 1
        assert calcular.call_args.kwargs["persistir"] is False

    with patch("backtesting.monitoreo.drift.calcular_metricas_calibracion", return_value={}) as calcular:
        _obtener_metricas_periodo("COMPLETO", "API_USUARIO", date(2026, 1, 1), date(2026, 1, 31))
        assert calcular.call_args.kwargs["persistir"] is False

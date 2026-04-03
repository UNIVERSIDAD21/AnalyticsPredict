import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.calibradores import selector


def _pred(p_raw, outcome, fecha, origen="API_USUARIO"):
    return {
        "p_raw": p_raw,
        "outcome_binario": outcome,
        "fecha_partido": fecha,
        "origen": origen,
    }


def test_selector_no_calibra_con_menos_de_100():
    cutoff = date(2024, 2, 1)
    predicciones = [_pred(0.6, True, cutoff - timedelta(days=1)) for _ in range(50)]
    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is None
    assert metricas["n_total"] == 50
    assert razon.startswith("NO_CALIBRAR: n=50 < 100")


def test_selector_platt_entre_100_y_500():
    cutoff = date(2024, 2, 1)
    predicciones = [_pred(0.6, True, cutoff - timedelta(days=1)) for _ in range(150)]
    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is not None
    assert calibrador.metodo == "platt"
    assert metricas["n_total"] == 150
    assert razon.startswith("PLATT: 100<=n<500")


def test_selector_excluye_push_y_cutoff_estricto():
    cutoff = date(2024, 2, 1)
    predicciones = [
        _pred(0.6, True, cutoff - timedelta(days=1)) for _ in range(110)
    ] + [
        _pred(0.4, None, cutoff - timedelta(days=2)) for _ in range(5)
    ] + [
        _pred(0.7, True, cutoff) for _ in range(10)
    ]

    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is not None
    assert metricas["n_total"] == 110
    assert "cutoff=2024-02-01" in razon


def test_selector_elige_mejor_y_reentrena(monkeypatch):
    cutoff = date(2024, 2, 1)
    predicciones = [_pred(0.5, False, cutoff - timedelta(days=1)) for _ in range(600)]

    llamadas = {"platt": [], "isotonic": []}

    class DummyCalibrador:
        def __init__(self, metodo, valor, n_datos):
            self.metodo = metodo
            self._valor = valor
            self.n_datos = n_datos

        def calibrar(self, _p):
            return self._valor

    def fake_platt(datos):
        llamadas["platt"].append(len(datos))
        return DummyCalibrador("platt", 0.9, len(datos))

    def fake_isotonic(datos):
        llamadas["isotonic"].append(len(datos))
        return DummyCalibrador("isotonic", 0.1, len(datos))

    monkeypatch.setattr(selector, "_entrenar_platt", fake_platt)
    monkeypatch.setattr(selector, "_entrenar_isotonic", fake_isotonic)

    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is not None
    assert calibrador.metodo == "isotonic"
    assert calibrador.n_datos == 600
    assert metricas["n_entrenamiento_final"] == 600
    assert metricas["n_split_train"] == 480
    assert metricas["n_split_val"] == 120
    assert llamadas["isotonic"] == [480, 600]
    assert "ELEGIDO_ISOTONIC" in razon


def test_selector_excluye_datos_en_fecha_cutoff():
    cutoff = date(2024, 2, 1)
    predicciones = [_pred(0.6, True, cutoff) for _ in range(200)]

    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is None
    assert metricas["n_total"] == 0
    assert "SIN_DATOS" in razon


def test_selector_rechaza_origen_mixto():
    cutoff = date(2024, 2, 1)
    predicciones = [
        _pred(0.6, True, cutoff - timedelta(days=1), origen="API_USUARIO")
        for _ in range(100)
    ] + [
        _pred(0.6, True, cutoff - timedelta(days=1), origen="BACKTEST_SINTETICO")
        for _ in range(10)
    ]

    calibrador, metricas, razon = selector.seleccionar_calibrador("Q1", predicciones, cutoff)

    assert calibrador is None
    assert metricas["n_total"] == 110
    assert "ORIGEN_MIXTO" in razon


def test_aplicar_platt_estable_con_valores_extremos_no_revienta():
    # Validar estabilidad numérica para evitar `math range error`.
    valor = selector._aplicar_platt(0.999999, a=1000.0, b=-1_000_000.0)
    assert 0.0 <= valor <= 1.0

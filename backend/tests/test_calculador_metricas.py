from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.metricas.brier import calcular_brier_score
from backtesting.metricas.calculador import calcular_metricas_calibracion
from backtesting.metricas.ece import calcular_ece
from backtesting.metricas.log_loss import calcular_log_loss


class FakeCursor:
    def __init__(self, rows, store):
        self._rows = rows
        self._store = store
        self._result_rows = []
        self._result_one = None

    def execute(self, query, params):
        if "FROM vista_predicciones_para_calibracion" in query:
            mercado, origen, fecha_inicio, fecha_fin, modelo_id, _ = params
            filtradas = []
            for fila in self._rows:
                if fila["mercado"] != mercado:
                    continue
                if fila["origen"] != origen:
                    continue
                if not (fecha_inicio <= fila["fecha_partido"] <= fecha_fin):
                    continue
                if modelo_id is not None and fila["modelo_version_id"] != modelo_id:
                    continue
                filtradas.append(
                    (
                        fila["p_raw"],
                        fila["p_calibrada"],
                        fila["outcome_binario"],
                        fila["media_predicha"],
                        fila["valor_real"],
                        fila["intervalo_inferior"],
                        fila["intervalo_superior"],
                        fila["nivel_intervalo"],
                    )
                )
            self._result_rows = filtradas
            return

        if "INSERT INTO metricas_calibracion" in query:
            modelo_id = params[4]
            key = (
                params[0],
                params[1],
                params[2],
                params[3],
                -1 if modelo_id is None else modelo_id,
            )
            if key not in self._store:
                self._store[key] = {"id": str(uuid4()), "data": params}
            else:
                self._store[key]["data"] = params
            self._result_one = (self._store[key]["id"],)
            return

        raise AssertionError("Consulta inesperada en FakeCursor")

    def fetchall(self):
        return self._result_rows

    def fetchone(self):
        return self._result_one

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, rows, store):
        self._rows = rows
        self._store = store

    def cursor(self):
        return FakeCursor(self._rows, self._store)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, rows, store):
        self._rows = rows
        self._store = store

    def connection(self):
        return FakeConnection(self._rows, self._store)


def _rows_base():
    return [
        {
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 1),
            "modelo_version_id": 1,
            "p_raw": 0.9,
            "p_calibrada": 0.8,
            "outcome_binario": True,
            "media_predicha": 110.0,
            "valor_real": 112.0,
            "intervalo_inferior": 108.0,
            "intervalo_superior": 114.0,
            "nivel_intervalo": 90,
        },
        {
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 2),
            "modelo_version_id": 1,
            "p_raw": 0.2,
            "p_calibrada": 0.3,
            "outcome_binario": False,
            "media_predicha": 105.0,
            "valor_real": 100.0,
            "intervalo_inferior": 98.0,
            "intervalo_superior": 108.0,
            "nivel_intervalo": 90,
        },
        {
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 3),
            "modelo_version_id": 1,
            "p_raw": 0.6,
            "p_calibrada": 0.55,
            "outcome_binario": True,
            "media_predicha": 100.0,
            "valor_real": 101.0,
            "intervalo_inferior": None,
            "intervalo_superior": None,
            "nivel_intervalo": None,
        },
        {
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 4),
            "modelo_version_id": 1,
            "p_raw": 0.5,
            "p_calibrada": 0.5,
            "outcome_binario": None,
            "media_predicha": 98.0,
            "valor_real": 98.0,
            "intervalo_inferior": 95.0,
            "intervalo_superior": 101.0,
            "nivel_intervalo": 90,
        },
        {
            "mercado": "Q1",
            "origen": "BACKTEST_SINTETICO",
            "fecha_partido": date(2024, 1, 2),
            "modelo_version_id": 1,
            "p_raw": 0.1,
            "p_calibrada": 0.1,
            "outcome_binario": True,
            "media_predicha": 102.0,
            "valor_real": 104.0,
            "intervalo_inferior": 99.0,
            "intervalo_superior": 105.0,
            "nivel_intervalo": 90,
        },
    ]


def test_calculador_metricas_basicas_y_filtros():
    rows = _rows_base()
    store = {}
    pool = FakePool(rows, store)

    resultado = calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=1,
        usar_p_calibrada=True,
        n_bins=2,
        tipo_bins="fijos",
        min_por_bin=1,
        pool=pool,
    )

    predicciones_raw = [(0.9, True), (0.2, False), (0.6, True)]
    expected_brier = calcular_brier_score(predicciones_raw)
    expected_log_loss = calcular_log_loss(predicciones_raw)
    expected_ece = calcular_ece(predicciones_raw, n_bins=2, tipo_bins="fijos", min_por_bin=1)

    assert resultado["n_predicciones"] == 3
    assert resultado["brier_score_raw"] == pytest.approx(expected_brier["brier_score"])
    assert resultado["log_loss_raw"] == pytest.approx(expected_log_loss["log_loss"])
    assert resultado["ece_raw"] == pytest.approx(expected_ece["ece"])
    assert resultado["base_rate"] == pytest.approx(2 / 3)
    assert resultado["distribucion"]["cobertura_intervalo"] == pytest.approx(1.0)
    assert resultado["distribucion"]["n_con_intervalo"] == 3
    assert resultado["distribucion"]["n_sin_intervalo"] == 1
    assert resultado["alertas"] == []


def test_calculador_excluye_pushes():
    rows = _rows_base()
    store = {}
    pool = FakePool(rows, store)

    resultado = calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=1,
        pool=pool,
    )

    assert resultado["n_predicciones"] == 3


def test_calculador_sin_intervalos():
    rows = [
        {
            "mercado": "Q2",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 1),
            "modelo_version_id": 1,
            "p_raw": 0.7,
            "p_calibrada": 0.7,
            "outcome_binario": True,
            "media_predicha": 100.0,
            "valor_real": 101.0,
            "intervalo_inferior": None,
            "intervalo_superior": None,
            "nivel_intervalo": None,
        }
    ]
    store = {}
    pool = FakePool(rows, store)

    resultado = calcular_metricas_calibracion(
        mercado="Q2",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 2),
        modelo_version_id=1,
        pool=pool,
    )

    assert resultado["distribucion"]["cobertura_intervalo"] is None
    assert resultado["distribucion"]["n_con_intervalo"] == 0


def test_calculador_idempotente_en_persistencia():
    rows = _rows_base()
    store = {}
    pool = FakePool(rows, store)

    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=1,
        pool=pool,
    )
    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=1,
        pool=pool,
    )

    assert len(store) == 1


def test_calculador_idempotencia_con_modelo_version_id_null():
    rows = _rows_base()
    store = {}
    pool = FakePool(rows, store)

    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=None,
        pool=pool,
    )
    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=None,
        pool=pool,
    )

    assert len(store) == 1


def test_calculador_distingue_modelo_version_id_null_vs_valor():
    rows = _rows_base()
    rows.append(
        {
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "fecha_partido": date(2024, 1, 2),
            "modelo_version_id": 5,
            "p_raw": 0.4,
            "p_calibrada": 0.35,
            "outcome_binario": True,
            "media_predicha": 101.0,
            "valor_real": 103.0,
            "intervalo_inferior": 98.0,
            "intervalo_superior": 105.0,
            "nivel_intervalo": 90,
        }
    )
    store = {}
    pool = FakePool(rows, store)

    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=None,
        pool=pool,
    )
    calcular_metricas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 5),
        modelo_version_id=5,
        pool=pool,
    )

    assert len(store) == 2

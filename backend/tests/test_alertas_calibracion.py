from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import uuid4


sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.alertas_calibracion import evaluar_alertas_calibracion


class FakeCursor:
    def __init__(self, metricas_rows, alertas_store):
        self._metricas_rows = metricas_rows
        self._alertas_store = alertas_store
        self._result_rows = []
        self._result_one = None

    def execute(self, query, params):
        if "FROM metricas_calibracion" in query and "ORDER BY periodo_fin DESC" not in query:
            fecha_inicio, fecha_fin, mercado, origen, modelo_id, _ = params
            for fila in self._metricas_rows:
                if (
                    fila["periodo_inicio"] == fecha_inicio
                    and fila["periodo_fin"] == fecha_fin
                    and fila["mercado"] == mercado
                    and fila["origen"] == origen
                    and (modelo_id is None or fila["modelo_version_id"] == modelo_id)
                ):
                    self._result_one = (
                        fila["n_predicciones"],
                        fila["brier_score"],
                        fila["log_loss"],
                        fila["ece"],
                    )
                    return
            self._result_one = None
            return

        if "ORDER BY periodo_fin DESC" in query:
            mercado, origen, fecha_fin, modelo_id, _ = params
            filtradas = [
                fila
                for fila in self._metricas_rows
                if fila["mercado"] == mercado
                and fila["origen"] == origen
                and fila["periodo_fin"] < fecha_fin
                and (modelo_id is None or fila["modelo_version_id"] == modelo_id)
            ]
            filtradas.sort(key=lambda f: f["periodo_fin"], reverse=True)
            if filtradas:
                fila = filtradas[0]
                self._result_one = (
                    fila["brier_score"],
                    fila["log_loss"],
                    fila["ece"],
                )
            else:
                self._result_one = None
            return

        if "INSERT INTO alertas_calibracion" in query:
            modelo_id = params[4]
            key = (
                params[0],
                params[1],
                params[2],
                params[3],
                params[5],
                -1 if modelo_id is None else modelo_id,
            )
            alerta_id = self._alertas_store.get(key, {}).get("id")
            if alerta_id is None:
                alerta_id = str(uuid4())
            self._alertas_store[key] = {
                "id": alerta_id,
                "params": params,
            }
            self._result_one = (alerta_id,)
            return

        raise AssertionError("Consulta inesperada en FakeCursor")

    def fetchone(self):
        return self._result_one

    def fetchall(self):
        return self._result_rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, metricas_rows, alertas_store):
        self._metricas_rows = metricas_rows
        self._alertas_store = alertas_store

    def cursor(self):
        return FakeCursor(self._metricas_rows, self._alertas_store)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, metricas_rows, alertas_store):
        self._metricas_rows = metricas_rows
        self._alertas_store = alertas_store

    def connection(self):
        return FakeConnection(self._metricas_rows, self._alertas_store)


def test_alertas_calibracion_generan_drift_e_idempotencia():
    metricas_rows = [
        {
            "periodo_inicio": date(2024, 1, 1),
            "periodo_fin": date(2024, 1, 7),
            "mercado": "Q1",
            "origen": "API_USUARIO",
            "modelo_version_id": None,
            "n_predicciones": 120,
            "brier_score": 0.26,
            "log_loss": 0.75,
            "ece": 0.11,
        }
    ]
    alertas_store = {}
    pool = FakePool(metricas_rows, alertas_store)

    alertas = evaluar_alertas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    assert any(alerta["tipo_alerta"] == "DRIFT_ECE_ALTO" for alerta in alertas)
    assert any(alerta["tipo_alerta"] == "DRIFT_BRIER_ALTO" for alerta in alertas)
    assert any(alerta["tipo_alerta"] == "DRIFT_LOGLOSS_ALTO" for alerta in alertas)

    alertas_repetidas = evaluar_alertas_calibracion(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    assert len(alertas_store) == len(alertas)
    assert len(alertas_repetidas) == len(alertas)


def test_alertas_calibracion_datos_insuficientes():
    metricas_rows = [
        {
            "periodo_inicio": date(2024, 1, 1),
            "periodo_fin": date(2024, 1, 7),
            "mercado": "Q2",
            "origen": "API_USUARIO",
            "modelo_version_id": None,
            "n_predicciones": 10,
            "brier_score": 0.1,
            "log_loss": 0.2,
            "ece": 0.01,
        }
    ]
    alertas_store = {}
    pool = FakePool(metricas_rows, alertas_store)

    alertas = evaluar_alertas_calibracion(
        mercado="Q2",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    assert len(alertas) == 1
    assert alertas[0]["tipo_alerta"] == "DATOS_INSUFICIENTES"


def test_alertas_calibracion_actualiza_misma_llave():
    metricas_rows = [
        {
            "periodo_inicio": date(2024, 1, 1),
            "periodo_fin": date(2024, 1, 7),
            "mercado": "Q3",
            "origen": "API_USUARIO",
            "modelo_version_id": None,
            "n_predicciones": 120,
            "brier_score": 0.1,
            "log_loss": 0.2,
            "ece": 0.11,
        }
    ]
    alertas_store = {}
    pool = FakePool(metricas_rows, alertas_store)

    evaluar_alertas_calibracion(
        mercado="Q3",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    metricas_rows[0]["ece"] = 0.06
    evaluar_alertas_calibracion(
        mercado="Q3",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    drift_key = (
        date(2024, 1, 1),
        date(2024, 1, 7),
        "Q3",
        "API_USUARIO",
        "DRIFT_ECE_ALTO",
        -1,
    )
    assert drift_key in alertas_store
    assert alertas_store[drift_key]["params"][6] == "WARNING"


def test_alertas_calibracion_distingue_periodo_inicio():
    metricas_rows = [
        {
            "periodo_inicio": date(2024, 1, 1),
            "periodo_fin": date(2024, 1, 7),
            "mercado": "Q4",
            "origen": "API_USUARIO",
            "modelo_version_id": None,
            "n_predicciones": 120,
            "brier_score": 0.1,
            "log_loss": 0.2,
            "ece": 0.11,
        },
        {
            "periodo_inicio": date(2024, 1, 2),
            "periodo_fin": date(2024, 1, 7),
            "mercado": "Q4",
            "origen": "API_USUARIO",
            "modelo_version_id": None,
            "n_predicciones": 120,
            "brier_score": 0.1,
            "log_loss": 0.2,
            "ece": 0.11,
        },
    ]
    alertas_store = {}
    pool = FakePool(metricas_rows, alertas_store)

    evaluar_alertas_calibracion(
        mercado="Q4",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )
    evaluar_alertas_calibracion(
        mercado="Q4",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 2),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        pool=pool,
    )

    drift_keys = [
        key for key in alertas_store if key[4] == "DRIFT_ECE_ALTO"
    ]
    assert len(drift_keys) == 2

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import uuid4


sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.alertas_calibracion import evaluar_alertas_calibracion, _construir_alerta


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
            modelo_id_efectivo = params[4] if params[4] is not None else -1
            key = (params[0], params[1], params[2], params[3], params[5], modelo_id_efectivo)
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


def test_alertas_actualizan_severidad_en_misma_llave():
    alertas_store = {}
    pool = FakePool([], alertas_store)

    alerta_warning = _construir_alerta(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        tipo_alerta="DRIFT_ECE_ALTO",
        severidad="WARNING",
        metrica_afectada="ece",
        valor_actual=0.08,
        valor_umbral=0.05,
        valor_baseline=None,
        mensaje="Alerta warning.",
        detalles={"umbral": 0.05},
        pool=pool,
    )

    alerta_critica = _construir_alerta(
        mercado="Q1",
        origen="API_USUARIO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 7),
        modelo_version_id=None,
        tipo_alerta="DRIFT_ECE_ALTO",
        severidad="CRITICAL",
        metrica_afectada="ece",
        valor_actual=0.12,
        valor_umbral=0.1,
        valor_baseline=None,
        mensaje="Alerta crítica.",
        detalles={"umbral": 0.1},
        pool=pool,
    )

    assert len(alertas_store) == 1
    assert alerta_warning["id"] == alerta_critica["id"]
    assert alerta_critica["severidad"] == "CRITICAL"

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.recalibracion import recalibrar_mercado


class FakeCursor:
    def __init__(self, pred_rows, calibradores_store, alertas_store):
        self._pred_rows = pred_rows
        self._calibradores_store = calibradores_store
        self._alertas_store = alertas_store
        self._result_rows = []
        self._result_one = None

    def execute(self, query, params):
        if "FROM predicciones_registradas" in query:
            mercado, origen, cutoff, modelo_id, _ = params
            filtradas = [
                (fila["p_raw"], fila["outcome_binario"])
                for fila in self._pred_rows
                if fila["mercado"] == mercado
                and fila["origen"] == origen
                and fila["fecha_partido"] <= cutoff
                and (modelo_id is None or fila["modelo_version_id"] == modelo_id)
                and fila["outcome_binario"] is not None
                and fila["p_raw"] is not None
            ]
            self._result_rows = filtradas
            return

        if "FROM calibradores" in query and "LIMIT 1" in query:
            mercado, origen, cutoff, metodo = params
            for fila in self._calibradores_store.values():
                if (
                    fila["mercado"] == mercado
                    and fila["origen_datos"] == origen
                    and fila["cutoff_datos"] == cutoff
                    and fila["metodo"] == metodo
                ):
                    self._result_one = (fila["id"],)
                    return
            self._result_one = None
            return

        if "INSERT INTO calibradores" in query:
            calibrador_id = params[0]
            self._calibradores_store[calibrador_id] = {
                "id": calibrador_id,
                "mercado": params[1],
                "metodo": params[2],
                "fecha_entrenamiento": params[3],
                "cutoff_datos": params[4],
                "n_muestras_entrenamiento": params[5],
                "origen_datos": params[6],
                "parametros_json": params[7],
                "activo": params[8],
            }
            self._result_one = None
            return

        if "UPDATE calibradores SET activo = false" in query:
            mercado, calibrador_id = params
            for fila in self._calibradores_store.values():
                if fila["mercado"] == mercado and fila["id"] != calibrador_id:
                    fila["activo"] = False
            return

        if "UPDATE calibradores SET activo = true" in query:
            calibrador_id = params[0]
            if calibrador_id in self._calibradores_store:
                self._calibradores_store[calibrador_id]["activo"] = True
            return

        if "INSERT INTO alertas_calibracion" in query:
            key = (params[1], params[2], params[3], params[5], params[6])
            self._alertas_store[key] = {"params": params}
            self._result_one = (str(uuid4()),)
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
    def __init__(self, pred_rows, calibradores_store, alertas_store):
        self._pred_rows = pred_rows
        self._calibradores_store = calibradores_store
        self._alertas_store = alertas_store

    def cursor(self):
        return FakeCursor(self._pred_rows, self._calibradores_store, self._alertas_store)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, pred_rows, calibradores_store, alertas_store):
        self._pred_rows = pred_rows
        self._calibradores_store = calibradores_store
        self._alertas_store = alertas_store

    def connection(self):
        return FakeConnection(self._pred_rows, self._calibradores_store, self._alertas_store)


def _pred_rows_base(n=120):
    rows = []
    for i in range(n):
        rows.append(
            {
                "mercado": "Q1",
                "origen": "API_USUARIO",
                "fecha_partido": date(2024, 1, 1),
                "modelo_version_id": None,
                "p_raw": 0.6 if i % 2 == 0 else 0.4,
                "outcome_binario": i % 2 == 0,
            }
        )
    return rows


def test_recalibracion_crea_calibrador_activo():
    pred_rows = _pred_rows_base()
    calibradores_store = {}
    alertas_store = {}
    pool = FakePool(pred_rows, calibradores_store, alertas_store)

    resultado = recalibrar_mercado(
        mercado="Q1",
        origen="API_USUARIO",
        cutoff_datos=date(2024, 1, 10),
        modelo_version_id=None,
        pool=pool,
    )

    assert resultado.calibrador_id is not None
    assert resultado.creado is True
    assert len(calibradores_store) == 1
    calibrador = next(iter(calibradores_store.values()))
    assert calibrador["activo"] is True


def test_recalibracion_bloquea_por_datos_insuficientes():
    pred_rows = _pred_rows_base(n=10)
    calibradores_store = {}
    alertas_store = {}
    pool = FakePool(pred_rows, calibradores_store, alertas_store)

    resultado = recalibrar_mercado(
        mercado="Q1",
        origen="API_USUARIO",
        cutoff_datos=date(2024, 1, 10),
        modelo_version_id=None,
        min_muestras=50,
        pool=pool,
    )

    assert resultado.calibrador_id is None
    assert resultado.creado is False
    assert len(calibradores_store) == 0
    assert len(alertas_store) == 1

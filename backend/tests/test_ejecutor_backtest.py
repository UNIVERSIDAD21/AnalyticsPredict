from datetime import date
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.configuracion import ConfiguracionBacktest, Mercado
from backtesting.ejecutor import ejecutar_backtest


def _modelo_prueba():
    entidad_a_indice = {"team a": 0, "team b": 1}
    pesos = np.zeros((6, 4), dtype=float)
    pesos[0] = [10.0, 10.0, 10.0, 10.0]
    desviacion = np.array([5.0, 5.0, 5.0, 5.0], dtype=float)
    return {
        "alpha": 5.0,
        "entidad_a_indice": entidad_a_indice,
        "pesos_equipo": pesos,
        "pesos_rival": pesos,
        "desviacion_equipo": desviacion,
        "desviacion_rival": desviacion,
    }


class FakeCursor:
    def __init__(self, store):
        self._store = store
        self._row = None
        self._row_factory = None

    def execute(self, query, params):
        if "INSERT INTO ejecuciones_backtest" in query:
            backtest_id = str(uuid4())
            self._store[backtest_id] = {
                "id": backtest_id,
                "estado": params[0],
                "configuracion_json": params[1],
                "fecha_inicio_eval": params[2],
                "fecha_fin_eval": params[3],
                "mercados": params[4],
                "total_iteraciones": params[5],
                "iteraciones_completadas": 0,
                "iteraciones_fallidas": 0,
                "total_predicciones_generadas": 0,
                "iniciado_en": params[6],
                "completado_en": None,
                "ultimo_error": None,
                "errores_json": params[7],
            }
            self._row = (backtest_id,)
            return

        if "UPDATE ejecuciones_backtest" in query:
            backtest_id = params[7]
            registro = self._store[backtest_id]
            registro["iteraciones_completadas"] = params[0]
            registro["iteraciones_fallidas"] = params[1]
            registro["total_predicciones_generadas"] = params[2]
            registro["ultimo_error"] = params[3]
            registro["errores_json"] = params[4]
            if params[5] is not None:
                registro["estado"] = params[5]
            if params[6] is not None:
                registro["completado_en"] = params[6]
            self._row = None
            return

        if "SELECT" in query and "FROM ejecuciones_backtest" in query:
            backtest_id = params[0]
            registro = self._store.get(backtest_id)
            self._row = registro if self._row_factory else tuple(registro.values())
            return

        raise AssertionError(f"Query inesperada: {query}")

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, store):
        self._store = store

    def cursor(self, row_factory=None):
        cursor = FakeCursor(self._store)
        cursor._row_factory = row_factory
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self):
        self.store = {}

    def connection(self):
        return FakeConnection(self.store)


class FakeEntrenador:
    def __init__(self, pool):
        self._pool = pool

    def entrenar_para_backtest(self, cutoff_fecha, config):
        return {
            "estado": "ok",
            "modelo": _modelo_prueba(),
            "modelo_version_id": 1,
        }


def _partidos_prueba():
    return [
        {
            "partido_id": uuid4(),
            "fecha_partido": date(2024, 1, 1),
            "tipo_partido": "REG",
            "temporada_id": "2024",
            "equipo_local_id": uuid4(),
            "equipo_visitante_id": uuid4(),
            "equipo_local": "Team A",
            "equipo_visitante": "Team B",
        },
        {
            "partido_id": uuid4(),
            "fecha_partido": date(2024, 1, 2),
            "tipo_partido": "REG",
            "temporada_id": "2024",
            "equipo_local_id": uuid4(),
            "equipo_visitante_id": uuid4(),
            "equipo_local": "Team A",
            "equipo_visitante": "Team B",
        },
    ]


def test_ejecutor_backtest_idempotente():
    pool = FakePool()
    partidos = _partidos_prueba()
    store_predicciones = {}

    def fake_registrar_prediccion(*, return_status=False, **kwargs):
        key = (
            kwargs["partido_id"],
            kwargs["mercado"],
            kwargs["lado"],
            kwargs["linea"],
            kwargs["origen"],
            kwargs["modelo_version_id"],
        )
        if key in store_predicciones:
            return (None, "duplicada") if return_status else None
        nuevo_id = uuid4()
        store_predicciones[key] = nuevo_id
        return (nuevo_id, "insertada") if return_status else nuevo_id

    def fake_obtener_partidos(_config):
        return partidos

    def fake_resolver_predicciones_func(**_kwargs):
        return {"resueltas": 1, "pendientes": 0, "push": 0, "errores": 0}

    config = ConfiguracionBacktest(
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 3),
        mercados=[Mercado.Q1],
        incluir_completo=False,
        usar_lineas_sinteticas=False,
        offsets_linea=[0.0],
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    resultado = ejecutar_backtest(
        config,
        pool=pool,
        obtener_partidos_func=fake_obtener_partidos,
        entrenador_factory=lambda pool_obj: FakeEntrenador(pool_obj),
        registrar_prediccion_func=fake_registrar_prediccion,
        resolver_predicciones_func=fake_resolver_predicciones_func,
    )

    assert resultado.iteraciones_completadas == 1
    assert pool.store[str(resultado.backtest_id)]["estado"] == "COMPLETADO"
    total_insertadas = len(store_predicciones)

    resultado_repetido = ejecutar_backtest(
        config,
        pool=pool,
        obtener_partidos_func=fake_obtener_partidos,
        entrenador_factory=lambda pool_obj: FakeEntrenador(pool_obj),
        registrar_prediccion_func=fake_registrar_prediccion,
        resolver_predicciones_func=fake_resolver_predicciones_func,
    )

    assert resultado_repetido.iteraciones_completadas == 1
    assert len(store_predicciones) == total_insertadas

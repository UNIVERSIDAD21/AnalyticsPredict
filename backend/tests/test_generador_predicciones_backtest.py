from datetime import date
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.configuracion import ConfiguracionBacktest, Mercado
from backtesting.generador_predicciones import generar_predicciones_backtest


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


def _partido_prueba(partido_id):
    return {
        "id": partido_id,
        "temporada_id": uuid4(),
        "equipo_local_id": uuid4(),
        "equipo_visitante_id": uuid4(),
        "fecha_partido": date(2024, 1, 1),
        "tipo_partido": "REG",
        "equipo_local": "Team A",
        "equipo_visitante": "Team B",
    }


def test_generador_inserta_offsets_e_idempotencia():
    store = {}

    def fake_registrar_prediccion(*, return_status=False, **kwargs):
        assert kwargs["origen"] == "BACKTEST_SINTETICO"
        key = (
            kwargs["partido_id"],
            kwargs["mercado"],
            kwargs["lado"],
            kwargs["linea"],
            kwargs["origen"],
            kwargs["modelo_version_id"],
        )
        if key in store:
            return (None, "duplicada") if return_status else None
        nuevo_id = uuid4()
        store[key] = nuevo_id
        return (nuevo_id, "insertada") if return_status else nuevo_id

    config = ConfiguracionBacktest(
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 2),
        mercados=[Mercado.Q1],
        incluir_completo=False,
        usar_lineas_sinteticas=True,
        offsets_linea=[0.0, 2.0],
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    partido = _partido_prueba(uuid4())
    resumen = generar_predicciones_backtest(
        _modelo_prueba(),
        [partido],
        config,
        modelo_version_id=1,
        registrar_prediccion_func=fake_registrar_prediccion,
    )

    assert resumen["total_intentos"] == 4
    assert resumen["total_insertadas"] == 4
    assert resumen["total_duplicadas"] == 0

    resumen_repetido = generar_predicciones_backtest(
        _modelo_prueba(),
        [partido],
        config,
        modelo_version_id=1,
        registrar_prediccion_func=fake_registrar_prediccion,
    )

    assert resumen_repetido["total_insertadas"] == 0
    assert resumen_repetido["total_duplicadas"] == 4


def test_generador_falla_sin_partido_id():
    def fake_registrar_prediccion(*, return_status=False, **kwargs):
        raise AssertionError("No debería intentar registrar predicciones sin partido_id")

    config = ConfiguracionBacktest(
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 2),
        mercados=[Mercado.Q1],
        incluir_completo=False,
        usar_lineas_sinteticas=False,
        offsets_linea=[0.0],
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    partido = _partido_prueba(None)
    resumen = generar_predicciones_backtest(
        _modelo_prueba(),
        [partido],
        config,
        modelo_version_id=1,
        registrar_prediccion_func=fake_registrar_prediccion,
    )

    assert resumen["total_fallidas"] == 1
    assert resumen["total_intentos"] == 0

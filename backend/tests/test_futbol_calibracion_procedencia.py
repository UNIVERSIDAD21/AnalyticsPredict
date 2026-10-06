"""Un campo calibrado exige transformación ejecutada e ID del artefacto."""

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from api.rutas_analisis_futbol import (
    _convertir_mercado_ml_a_schema,
    _ensamblar_mercados,
    _generar_predicciones_mercado,
    _generar_recomendaciones,
    _registrar_predicciones_futbol,
)
from api.schemas_futbol import PrediccionMercado, ProbabilidadLinea
from api import rutas_metricas_futbol
from motor_futbol.calibracion.gestor_calibradores import GestorCalibradores
from motor_futbol.tipos import TipoMercadoFutbol
from scripts.evaluar_calibracion import evaluar_mercado, obtener_predicciones_periodo


CALIBRADOR_ID = uuid4()


def test_gestor_exige_artefacto_identificado_y_transformacion_valida(monkeypatch):
    gestor = GestorCalibradores(pool=None)
    mercado = TipoMercadoFutbol.GOLES_FT
    monkeypatch.setattr(gestor, "cargar_calibrador_activo", lambda _mercado: None)
    assert gestor.calibrar_con_procedencia(mercado, 0.2) == (None, None)

    calibrador = SimpleNamespace(calibrador_id=CALIBRADOR_ID, calibrar=lambda p: p + 0.3)
    monkeypatch.setattr(gestor, "cargar_calibrador_activo", lambda _mercado: calibrador)
    p_cal, id_cal = gestor.calibrar_con_procedencia(mercado, 0.2)
    assert p_cal == pytest.approx(0.5)
    assert id_cal == CALIBRADOR_ID

    calibrador.calibrar = lambda p: p  # una identidad aplicada sigue teniendo procedencia
    assert gestor.calibrar_con_procedencia(mercado, 0.2) == (0.2, CALIBRADOR_ID)
    calibrador.calibrar = lambda p: float("nan")
    assert gestor.calibrar_con_procedencia(mercado, 0.2) == (None, None)


def test_conversion_ml_sin_calibrador_no_inventa_calibrada():
    pred = SimpleNamespace(
        mercado=TipoMercadoFutbol.GOLES_FT,
        probabilidades={"over_2.5": 0.2, "under_2.5": 0.8},
        media=2.7, std=0.8,
    )
    sin_cal = _convertir_mercado_ml_a_schema(pred, [2.5])
    linea = sin_cal.lineas["2.5"]
    assert linea.over_raw == 0.2
    assert linea.over_calibrada is None
    assert linea.calibrador_id is None

    gestor = SimpleNamespace(calibrar_con_procedencia=lambda mercado, p: (0.5, CALIBRADOR_ID))
    con_cal = _convertir_mercado_ml_a_schema(pred, [2.5], gestor)
    assert con_cal.lineas["2.5"].over_calibrada == 0.5
    assert con_cal.lineas["2.5"].under_calibrada == 0.5
    assert con_cal.lineas["2.5"].calibrador_id == str(CALIBRADOR_ID)


def test_heuristica_y_ensemble_no_se_presentan_como_calibrados():
    heur = _generar_predicciones_mercado("GOLES_FT", 2.7, 0.8, [2.5])
    assert heur.lineas["2.5"].over_calibrada is None
    ml = PrediccionMercado(
        mercado="GOLES_FT", media=2.7, std=0.8,
        lineas={"2.5": ProbabilidadLinea(
            over_raw=0.2, under_raw=0.8,
            over_calibrada=0.5, under_calibrada=0.5,
            calibrador_id=str(CALIBRADOR_ID),
        )},
    )
    blend = _ensamblar_mercados({"GOLES_FT": ml}, {"GOLES_FT": heur})
    assert blend["GOLES_FT"].lineas["2.5"].over_calibrada is None
    assert blend["GOLES_FT"].lineas["2.5"].calibrador_id is None


def test_recomendacion_separa_ajuste_de_muestra_y_calibracion():
    raw = PrediccionMercado(
        mercado="GOLES_FT", media=2.7, std=0.8,
        lineas={"2.5": ProbabilidadLinea(over_raw=0.9, under_raw=0.1)},
    )
    recs = _generar_recomendaciones({"GOLES_FT": raw}, 20, 20, 20)
    over = next(r for r in recs if r.lado == "OVER")
    assert over.p_calibrada is None
    assert over.calibrador_id is None
    assert over.calibracion_aplicada is False

    raw.lineas["2.5"].over_calibrada = 0.9
    raw.lineas["2.5"].under_calibrada = 0.1
    raw.lineas["2.5"].calibrador_id = str(CALIBRADOR_ID)
    over_cal = next(r for r in _generar_recomendaciones({"GOLES_FT": raw}, 20, 20, 20) if r.lado == "OVER")
    assert over_cal.p_calibrada == 0.9  # identidad también es calibración si pasó por el artefacto
    assert over_cal.calibrador_id == str(CALIBRADOR_ID)
    assert over_cal.calibracion_aplicada is True


def test_persistencia_guarda_raw_y_null_sin_artefacto():
    class Cursor:
        def executemany(self, sql, rows):
            self.sql, self.rows = sql, rows

    partido = {
        "id": uuid4(), "competicion_id": uuid4(), "temporada_id": uuid4(),
        "equipo_local_id": uuid4(), "equipo_visitante_id": uuid4(),
        "equipo_local": "Local", "equipo_visitante": "Visitante",
        "fecha_partido": datetime(2026, 10, 7, tzinfo=timezone.utc),
    }
    cursor = Cursor()
    pred = _generar_predicciones_mercado("GOLES_FT", 2.7, 0.8, [2.5])
    assert _registrar_predicciones_futbol(cursor, partido=partido, mercados={"GOLES_FT": pred}, modelo_version_id=1) == 1
    assert cursor.sql.count("%s") == len(cursor.rows[0])
    assert cursor.rows[0][15] is not None  # raw
    assert cursor.rows[0][17] is None  # calibrada
    assert cursor.rows[0][-1] is None  # calibrador_id

    pred.lineas["2.5"].over_calibrada = 0.7
    pred.lineas["2.5"].under_calibrada = 0.3
    pred.lineas["2.5"].calibrador_id = str(CALIBRADOR_ID)
    _registrar_predicciones_futbol(cursor, partido=partido, mercados={"GOLES_FT": pred}, modelo_version_id=1)
    assert cursor.rows[0][17] == 0.7
    assert cursor.rows[0][-1] == str(CALIBRADOR_ID)


def test_endpoint_calibracion_usa_columna_raw_real_y_muestra_sin_procedencia(monkeypatch):
    class Cursor:
        sql = ""

        def execute(self, sql, params=None):
            self.sql = sql

        def fetchall(self):
            if "SELECT p.mercado" in self.sql:
                return [{"mercado": "GOLES_FT", "p_raw": 0.2, "p_cal": None, "y": 0}]
            return []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class Connection:
        def __init__(self, cursor):
            self._cursor = cursor

        def cursor(self, **kwargs):
            return self._cursor

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    cursor = Cursor()
    pool = SimpleNamespace(connection=lambda: Connection(cursor))
    monkeypatch.setattr(rutas_metricas_futbol, "obtener_pool", lambda: pool)
    monkeypatch.setattr(rutas_metricas_futbol, "_tabla_existe", lambda _cursor, tabla: tabla == "predicciones_futbol")
    monkeypatch.setattr(rutas_metricas_futbol, "_columna_existe", lambda _cursor, _tabla, columna: columna in {"prob_over", "prob_over_calibrada", "calibrador_id"})

    resultado = asyncio.run(rutas_metricas_futbol.obtener_metricas_calibracion(mercado=None, periodo="todo"))
    assert "p.prob_over AS p_raw" in cursor.sql
    assert "p.calibrador_id IS NOT NULL" in cursor.sql
    metrica = resultado.metricas[0]
    assert metrica.n_raw == 1
    assert metrica.n_calibradas == 0
    assert metrica.brier_score_raw == pytest.approx(0.04)
    assert metrica.brier_score is None
    assert metrica.ece is None
    assert metrica.mejora_brier is None


def test_reporte_calibracion_no_sustituye_raw_por_calibrada():
    class Cursor:
        def execute(self, sql, params):
            assert "p.calibrador_id IS NOT NULL" in sql
            assert "p.prob_over" in sql

        def fetchall(self):
            return [(0.2, None, 0), (0.8, None, 1)]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class Connection:
        def cursor(self):
            return Cursor()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    pool = SimpleNamespace(connection=lambda: Connection())
    raw, cal, outcomes = obtener_predicciones_periodo(pool, TipoMercadoFutbol.GOLES_FT)
    assert len(raw) == len(outcomes) == 2
    assert all(map(lambda p: p != p, cal))  # NaN interno para ausencia de p_cal
    reporte = evaluar_mercado(pool, TipoMercadoFutbol.GOLES_FT, None, 0.05)
    assert reporte["metricas_raw"]["brier_score"] == pytest.approx(0.04)
    assert reporte["metricas_calibradas"]["brier_score"] is None
    assert reporte["mejora"]["brier_score"] is None
    assert reporte["alertas"][0]["tipo"] == "CALIBRACION_SIN_PROCEDENCIA"

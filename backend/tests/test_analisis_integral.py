from copy import deepcopy
import json

import pytest

from api.schemas_futbol import ObjetivoAnalisisFutbol
from motor.euroliga import probabilidades
from servicios.analisis_integral import integral_euroliga, integral_futbol, aplicar_escenario_euroliga


def euro():
    pred = {f"Q{i}": {"media_local": 22., "media_visitante": 20., "media_total": 42., "desviacion_total": 6., "observado": False} for i in range(1, 5)}
    pred["COMPLETO"] = {"media_local": 88., "media_visitante": 80., "media_total": 168., "desviacion_total": 12., "observado": False}
    recientes = [{"fecha": "2026-10-28", "puntos_regulacion": 100, "puntos_rival_regulacion": 90} for _ in range(10)]
    return {"modo": "PREPARTIDO", "mercado": "COMPLETO", "linea": 168., "predicciones": pred,
            "modelo_version": "euro-test", "corte_datos": "2026-10-21", "fecha_partido": "2026-10-30",
            "equipo_local": "A", "equipo_visitante": "B", "muestras": {"local": 60, "visitante": 60},
            "probabilidades": probabilidades(168, 144, 168),
            "ventaja_regulacion": {"local": .7, "visitante": .3, "desviacion_diferencia": 15.},
            "contexto": {"equipos": {k: {"recientes": deepcopy(recientes)} for k in ("a", "b")}}}


def test_euro_cuadros_coherentes_push_y_probabilidad_ganador_sin_mutar_ridge():
    r = euro()
    antes = deepcopy(r)
    a = integral_euroliga(r, cuota_over=1.91, cuota_under=1.95)
    assert r == antes
    assert sum(a["probabilidades"].values()) == pytest.approx(1)
    assert a["probabilidades"]["push"] > 0
    assert sum(a["ganador"][k] for k in ("local", "empate", "visitante")) == pytest.approx(1)
    assert a["ganador"]["empate"] > 0
    cuartos, total = a["periodos"][:4], a["periodos"][4]
    assert sum(p["total"] for p in cuartos) == pytest.approx(total["total"])
    assert sum(x["delta"] for x in a["ajustes"]) == pytest.approx(total["total"] - 168)
    assert a["cuotas"]["over"] == 1.91
    json.dumps(a, allow_nan=False)


@pytest.mark.parametrize("live,archivo", [(True, False), (False, True)])
def test_corte_o_archivo_no_se_reproyecta(live, archivo):
    r = euro()
    if live:
        r["modo"] = "CIERRE_Q1"
        r["predicciones"]["Q1"]["observado"] = True
    a = integral_euroliga(r, aplicar_contexto=not archivo)
    assert a["ajustes"] == []
    assert a["probabilidades"] == r["probabilidades"]
    assert a["comparacion"]["media_base"] == a["comparacion"]["media_ajustada"]


def test_archivo_legacy_no_inventa_probabilidad_de_empate():
    r = euro()
    del r["ventaja_regulacion"]["desviacion_diferencia"]
    a = integral_euroliga(r, aplicar_contexto=False)
    assert a["ganador"]["empate"] is None
    assert a["ganador"]["local"] == .7


def test_api_y_ui_mismo_escenario_y_conservan_base():
    r = euro()
    original = deepcopy(r["predicciones"])
    a = integral_euroliga(r)
    aplicar_escenario_euroliga(r, a)
    assert r["salida_modelo_base"]["predicciones"] == original
    assert r["predicciones"]["COMPLETO"]["media_total"] == a["comparacion"]["media_ajustada"]
    assert r["probabilidades"] == a["probabilidades"]


def objetivo():
    bloque = {"estado": "disponible", "probabilidades": {"over": .55, "under": .4}}
    return ObjetivoAnalisisFutbol(estado="disponible", mercado="CORNERS_FT", lado="UNDER", linea=9,
        unidad="córners", probabilidades_objetivo={"over": .55, "under": .4}, bloque_base=bloque,
        bloque_ajustado=bloque, devig={"estado": "no_disponible"}, calibracion={"estado": "no_disponible"},
        score_riesgo={"estado": "no_disponible"}, disponibilidad_datos={})


def test_futbol_1x2_goles_no_depende_de_ganador_corners_y_traza_completa():
    mercados = {"CORNERS_FT": {"media": 11., "std": 3., "lineas": {"9.0": {"over_raw": .55, "under_raw": .4}}},
                "CORNERS_LOCAL_FT": {"media": 8.}, "CORNERS_VISITANTE_FT": {"media": 3.}}
    base = deepcopy(mercados)
    base["CORNERS_FT"]["media"] = 10.
    ganador = {"prob_local": .2, "prob_empate": .5, "prob_visitante": .3, "razones": ["1X2"]}
    a = integral_futbol(mercados=mercados, base=base, objetivo=objetivo(), ganador=ganador,
        goles_local=.8, goles_visitante=1.1, trazas={"CORNERS_FT": [{"delta": .4}]},
        cuotas={"invalida": {}, "CORNERS_FT|9": {"cuota_under": 2.1}}, modelo_version="heuristico::1.0")
    assert a["ganador"]["empate"] == .5
    assert a["periodos"][2]["local"] == 8
    assert a["periodos"][2]["visitante"] == 3
    assert a["periodos"][0]["local"] is None  # no repartir FT por la mitad
    assert a["cuotas"]["under"] == 2.1
    assert a["probabilidades"]["push"] == pytest.approx(.05)
    assert sum(x["delta"] for x in a["ajustes"]) == pytest.approx(a["comparacion"]["media_ajustada"] - a["comparacion"]["media_base"])
    assert a["comparacion"]["probabilidades_base"]["over"] is None
    json.dumps(a, allow_nan=False)


def test_futbol_sin_linea_no_inventa_50_por_ciento():
    a = integral_futbol(mercados={}, base={}, objetivo=objetivo(), ganador={"prob_local": .3, "prob_empate": .4, "prob_visitante": .3},
        goles_local=1., goles_visitante=1., trazas={}, cuotas={}, modelo_version="test")
    assert a["probabilidades"] == {"over": None, "under": None, "push": None}

"""Publicaciones sintéticas congeladas; ningún fit ni conexión durante la consulta."""
from copy import deepcopy

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import rutas_local
from motor import euroliga, wnba
from servicios.consulta_local_ligas import catalogo, consultar


def publicacion(liga):
    coef = np.zeros((6, 4)); coef[0] = 20
    comun = {"version": "sintetico", "dataset_sha256": "datos-ajuste", "fecha_max": "2026-01-01",
             "covarianza": (np.eye(8) * 4).tolist(), "entidades": {"a": 0, "b": 1}}
    if liga == "euroliga":
        return {**comun, "pesos_equipo": coef.tolist(), "pesos_rival": coef.tolist(),
                "muestras_equipo": {"a": 30, "b": 40}, "muestras_equipo_temporada": {"a": 30, "b": 40},
                "catalogo": {"a": {"nombre": "Equipo A", "id": "id-a"}, "b": {"nombre": "Equipo B", "id": "id-b"}},
                "temporada_reciente": "2025/26", "origen_dispersion": "sintetico", "partidos_entrenamiento": 70,
                "fit_completed_at": "2026-01-02"}
    return {"version": "publicacion-sintetica", "dataset_sha256": "datos-publicacion", "publicado_utc": "2026-01-02",
            "ajuste_final": {**comun, "coeficientes": coef.tolist(), "muestras": {"a": 30, "b": 40},
                             "efectivos": {"a": 25., "b": 35.}, "n": 70},
            "datos": [{"local_id": "a", "visitante_id": "b", "local": "Equipo A", "visitante": "Equipo B"}]}


@pytest.mark.parametrize("liga", ["euroliga", "wnba"])
@pytest.mark.parametrize("periodo,linea", [("TOTAL", 160.), ("Q1", 40.5), ("Q4", 40.)])
def test_igualdad_exacta_con_motor_congelado_y_sin_modificacion(liga, periodo, linea):
    m = publicacion(liga); antes = deepcopy(m)
    r = consultar(m, liga, "a", "b", periodo, linea)
    mercado = "COMPLETO" if periodo == "TOTAL" else periodo
    nativo = euroliga.predecir(m, "a", "b", mercado, linea) if liga == "euroliga" else wnba.predecir(m["ajuste_final"], "a", "b", mercado, linea)
    assert m == antes
    assert r["distribucion"]["media"] == nativo["predicciones"][mercado]["media_total"]
    for p in ("over", "under", "push"):
        assert r["probabilidad_" + p] == nativo["probabilidades"][p]
    assert sum(r["probabilidad_" + p] for p in ("over", "under", "push")) == pytest.approx(1)
    assert r["metadata"]["minutos_regulacion"] == 40 and r["metadata"]["incluye_ot"] is False
    assert r["metadata"]["eficacia_certificada"] is False
    assert r["metadata"]["dataset_hash"] == "datos-ajuste"
    assert r["equipo_local"] == "Equipo A" and r["liga"] == liga
    if linea.is_integer():
        assert r["probabilidad_push"] > 0
    if liga == "wnba":
        assert r["metadata"]["publicacion_dataset_hash"] == "datos-publicacion"
        assert r["metadata"]["alcance"] == "REG_publicacion_congelada"


@pytest.mark.parametrize("liga", ["euroliga", "wnba"])
def test_catalogo_y_abstencion_con_muestra_insuficiente(liga):
    m = publicacion(liga)
    if liga == "euroliga":
        m["muestras_equipo"]["b"] = 5
    else:
        m["ajuste_final"]["efectivos"]["b"] = 5
    assert not next(e for e in catalogo(m, liga)["equipos"] if e["clave"] == "b")["disponible"]
    with pytest.raises(ValueError, match="Abstención"):
        consultar(m, liga, "a", "b", "TOTAL", 160.)


@pytest.mark.parametrize("liga", ["euroliga", "wnba"])
def test_api_sin_bd_ajuste_journal_y_sin_fallback(liga, monkeypatch):
    def prohibido(*args, **kwargs):
        pytest.fail("Intentó conectar, ajustar o registrar")
    monkeypatch.setattr("db.obtener_pool", prohibido)
    monkeypatch.setattr(euroliga, "_ajustar", prohibido)
    monkeypatch.setattr(wnba, "ajustar", prohibido)
    monkeypatch.setattr("servicios.predictor_wnba.ajustar_alcance", prohibido)
    monkeypatch.setattr("servicios.predictor_wnba.analizar", prohibido)
    monkeypatch.setattr("servicios.predictor_wnba.escribir", prohibido)
    monkeypatch.setattr(rutas_local, "cargar_liga", lambda l: publicacion(l))
    app = FastAPI(); app.include_router(rutas_local.router)
    with TestClient(app) as client:
        assert client.get(f"/api/local/{liga}/catalogo").status_code == 200
        p = {"equipo_local": "a", "equipo_visitante": "b", "linea": 160.}
        assert client.post(f"/api/local/{liga}/consultar", json=p).status_code == 200
        for cambio in ({"equipo_visitante": "a"}, {"equipo_visitante": "nba-ajeno"}, {"linea": 601}, {"temporadas": ["2026"]}, {"parciales": [[10, 11]]}):
            assert client.post(f"/api/local/{liga}/consultar", json={**p, **cambio}).status_code == 422


def test_artefacto_ausente_retorna_503_y_no_entrena(monkeypatch):
    def ausente():
        raise RuntimeError("Ausente")
    monkeypatch.setattr(euroliga, "cargar", ausente)
    app = FastAPI(); app.include_router(rutas_local.router)
    with TestClient(app) as client:
        assert client.get("/api/local/euroliga/catalogo").status_code == 503


@pytest.mark.parametrize("base", [True, False])
def test_diagnostico_no_prueba_sql_ni_expone_configuracion(base, monkeypatch):
    import json
    from tests.test_mejoras_locales import modelo_sintetico
    monkeypatch.setenv('ANALYTICSPREDICT_SOLO_BASE_LOCAL', '1' if base else '0')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://usuario:secreto@privado.invalid/base')
    monkeypatch.setattr('db.obtener_pool', lambda: pytest.fail('Conectó SQL'))
    monkeypatch.setattr(rutas_local, 'obtener_modelo', modelo_sintetico)
    monkeypatch.setattr(rutas_local, 'cargar_liga', lambda l: publicacion(l))
    r = rutas_local.estado_local()
    assert r['bd']['deshabilitada'] is base and r['bd']['conexion_comprobada'] is False
    assert r['modelos']['wnba']['muestra_entrenamiento'] == 70
    assert r['modelos']['nba']['equipos_disponibles'] == 2
    assert r['modelos']['euroliga']['equipos_disponibles'] == 2
    assert 'secreto' not in json.dumps(r) and 'privado.invalid' not in json.dumps(r)
    assert r['capacidades']['futbol_sin_BD'] is False


def test_lanzador_admite_estado_wnba_sin_exigir_nba(tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('lanzador_multiliga', Path(__file__).resolve().parents[2] / 'scripts/iniciar_local.py')
    lanzador = importlib.util.module_from_spec(spec); spec.loader.exec_module(lanzador)
    (tmp_path / 'wnba').mkdir()
    (tmp_path / 'wnba/activo.json').write_text('{}', encoding='utf-8')
    env = lanzador.preparar_entorno(tmp_path, False)
    assert env['ANALYTICSPREDICT_MODELO_WNBA_ACTIVO'] == str(tmp_path / 'wnba/activo.json')
    assert env['ANALYTICSPREDICT_SOLO_BASE_LOCAL'] == '1'

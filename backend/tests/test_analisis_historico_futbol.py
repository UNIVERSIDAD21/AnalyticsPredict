from datetime import datetime, timezone
import pytest
from fastapi import HTTPException

from api import rutas_analisis_futbol as rutas
from api.schemas_futbol import AnalisisRequest
from lecturas_http import solo_lectura_http
from test_elegibilidad_futbol import api_sintetica  # noqa: F401 — fixture compartida sintética


def test_historico_no_invoca_persistencia_ni_ml(api_sintetica, monkeypatch):
    client, partido, datos, registrados = api_sintetica
    partido.update(estado="FINALIZADO", fecha_partido=datetime(2026, 10, 10, tzinfo=timezone.utc))
    def prohibido(*a, **kw):
        pytest.fail("Una reconstrucción no puede registrar ni cargar ML actual")
    monkeypatch.setattr(rutas, "_obtener_predictor_futbol_ml", prohibido)
    monkeypatch.setattr(rutas, "registrar_apuesta_analizada", prohibido)
    monkeypatch.setattr(rutas, "_registrar_predicciones_futbol", prohibido)
    with monkeypatch.context() as m:
        original = rutas._obtener_partidos_equipo
        def leer(*a, **kw):
            assert solo_lectura_http.get() is True
            assert a[2] == partido["fecha_partido"]
            return original(*a, **kw)
        m.setattr(rutas, "_obtener_partidos_equipo", leer)
        r = client.post("/api/futbol/analizar", json={"partido_id": partido["id"], "modo_historico": True,
                        "mercado_objetivo": "GOLES_FT", "linea_objetivo": 2.5, "lado_objetivo": "OVER"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["modo"] == "HISTORICO_RECONSTRUIDO" and not registrados and not d["recomendaciones"]
    assert d["calibradores_activos"] == 0 and d["mercados_goles"]["GOLES_FT"]["media"] > 0
    assert any("Reconstrucción" in x for x in d["advertencias"])
    assert datetime.fromisoformat(d["timestamp_analisis"]).utcoffset() is not None
    assert d["objetivo"]["trazabilidad"]["modo_operativo"] == "SOLO_CONSULTA"
    assert d["objetivo"]["trazabilidad"]["registro_predicciones"] is False
    assert solo_lectura_http.get() is False


def test_historico_exige_final_y_prepartido_no_reabre_final(api_sintetica):
    client, partido, _, _ = api_sintetica
    assert client.post("/api/futbol/analizar", json={"partido_id": partido["id"], "modo_historico": True}).status_code == 400
    partido["estado"] = "FINALIZADO"
    assert client.post("/api/futbol/analizar", json={"partido_id": partido["id"]}).status_code == 400


def test_america_no_hereda_ml_calibracion_ni_recomendaciones_europeas(api_sintetica, monkeypatch):
    client, partido, _, registrados = api_sintetica
    partido["competicion_codigo"] = "COL_PRIMERAA"
    def prohibido(*a, **kw): pytest.fail("No heredar ML/eficacia de otro dominio")
    monkeypatch.setattr(rutas, "_obtener_predictor_futbol_ml", prohibido)
    monkeypatch.setattr(rutas, "_obtener_estado_mercados_futbol", prohibido)
    r = client.post("/api/futbol/analizar", json={"partido_id": partido["id"], "solo_consulta": True,
                    "mercado_objetivo": "CORNERS_FT", "linea_objetivo": 8.5, "lado_objetivo": "OVER"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["modelo_version"] == rutas.VERSION_HEURISTICO_AMERICAS and not d["recomendaciones"] and not registrados
    assert d["objetivo"]["calidad_datos"]["validacion_predictiva"] == "SIN_VALIDACION_POR_COMPETICION"
    assert d["objetivo"]["trazabilidad"]["estado_operativo_mercado"] == "LABORATORIO"
    assert d["objetivo"]["trazabilidad"]["motivos_estado_operativo"] == ["dominio_sin_validacion_predictiva"]


def test_temporada_ajena_no_se_sustituye_por_otra_ventana():
    class Cursor:
        def execute(self, *a): pass
        def fetchall(self): return []
    with pytest.raises(HTTPException) as e:
        rutas._resolver_filtro_temporal_futbol(Cursor(), request=AnalisisRequest(partido_id="00000000-0000-0000-0000-000000000001", temporadas=["Otra liga"]),
                                              competicion_id="c", fecha_corte=datetime.now(timezone.utc))
    assert e.value.status_code == 400

"""Tests de integración livianos para endpoints profesionales de métricas.

Nota: usan la app real con TestClient. No fuerzan datos mínimos de negocio,
solo validan contrato y disponibilidad de campos clave.
"""

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_tablero_salud_contrato_basico():
    resp = client.get("/api/metricas/tablero-salud")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "score_global" in data
    assert "deportes" in data
    assert "alertas" in data


def test_calidad_mercados_contrato_basico():
    resp = client.get("/api/metricas/calidad-mercados?min_muestras=10&limite=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "ranking" in data
    assert "recomendaciones" in data


def test_recomendaciones_accion_contrato_basico():
    resp = client.get("/api/metricas/recomendaciones-accion?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert data["semaforo_global"] in {"verde", "amarillo", "rojo"}
    assert isinstance(data["acciones"], list)


def test_drift_mercados_contrato_basico():
    resp = client.get("/api/metricas/drift-mercados?min_muestras=10&limite=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "items" in data
    assert "resumen" in data


def test_politica_mercados_contrato_basico():
    resp = client.get("/api/metricas/politica-mercados?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "mercados" in data
    assert "resumen" in data


def test_alertas_ingestion_contrato_basico():
    resp = client.get("/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "alertas" in data
    assert "resumen" in data


def test_sugerencias_umbrales_contrato_basico():
    resp = client.get("/api/metricas/sugerencias-umbrales?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "sugerencias" in data
    assert len(data["sugerencias"]) >= 1

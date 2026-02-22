"""Smoke tests mínimos para validar disponibilidad de API."""

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root_responde_200_y_campos_basicos():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "activo"
    assert "version" in data
    assert "enlaces" in data


def test_salud_responde_200_y_servicios():
    resp = client.get("/salud")
    assert resp.status_code == 200
    data = resp.json()
    assert "estado" in data
    assert "servicios" in data
    assert "api" in data["servicios"]


def test_estado_modelo_responde_con_esquema_minimo():
    resp = client.get("/api/modelo/estado")
    assert resp.status_code == 200
    data = resp.json()
    assert "exito" in data
    # Puede venir exito=False si no hay datos/modelo disponible en entorno local
    if data["exito"]:
        assert "modelo" in data
        assert "version" in data["modelo"]
        assert "equipos" in data["modelo"]

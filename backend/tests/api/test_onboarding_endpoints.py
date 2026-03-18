# -*- coding: utf-8 -*-
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rutas_auth import router as auth_router
from api.rutas_onboarding import router as onboarding_router


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-test.db")
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    os.environ["ONBOARDING_DB_PATH"] = str(tmp_path / "onboarding-test.db")
    os.environ["ONBOARDING_STORE_DRIVER"] = "sqlite"

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(onboarding_router)
    return TestClient(app)


def _token_acceso(client: TestClient) -> str:
    client.post(
        "/api/auth/register",
        json={
            "email": "onboarding@ap.com",
            "password": "12345678",
            "accepted_legal": True,
            "legal_version": "2026-03-18",
        },
    )
    r = client.post("/api/auth/login", json={"email": "onboarding@ap.com", "password": "12345678"})
    return r.json()["data"]["access_token"]


def test_estado_inicial_onboarding_es_pendiente(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    r = client.get("/api/onboarding/estado", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["completado"] is False


def test_guardar_perfil_y_leer_estado(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    payload = {
        "nombre": "Erik",
        "objetivo_principal": "rentabilidad",
        "deporte_preferido": "ambos",
        "frecuencia": "semanal",
        "bankroll_referencial": 500,
    }

    guardar = client.post(
        "/api/onboarding/perfil",
        headers={"Authorization": f"Bearer {access}"},
        json=payload,
    )
    assert guardar.status_code == 200
    assert guardar.json()["data"]["completado"] is True

    estado = client.get("/api/onboarding/estado", headers={"Authorization": f"Bearer {access}"})
    assert estado.status_code == 200
    body = estado.json()
    assert body["data"]["perfil"]["nombre"] == "Erik"
    assert body["data"]["perfil"]["objetivo_principal"] == "rentabilidad"


def test_registrar_evento_conversion(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    r = client.post(
        "/api/onboarding/evento",
        headers={"Authorization": f"Bearer {access}"},
        json={"event_name": "dashboard_viewed", "metadata": {"origen": "test"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["recorded"] is True
    assert body["data"]["event_name"] == "dashboard_viewed"


def test_obtener_kpis_completion_y_ttv(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    client.post(
        "/api/onboarding/evento",
        headers={"Authorization": f"Bearer {access}"},
        json={"event_name": "onboarding_started", "event_ts": "2026-03-18T12:00:00+00:00"},
    )
    client.post(
        "/api/onboarding/evento",
        headers={"Authorization": f"Bearer {access}"},
        json={"event_name": "onboarding_completed", "event_ts": "2026-03-18T12:05:00+00:00"},
    )
    client.post(
        "/api/onboarding/evento",
        headers={"Authorization": f"Bearer {access}"},
        json={"event_name": "dashboard_viewed", "event_ts": "2026-03-18T12:15:00+00:00"},
    )

    kpis = client.get("/api/onboarding/kpis", headers={"Authorization": f"Bearer {access}"})
    assert kpis.status_code == 200
    data = kpis.json()["data"]
    assert data["started_users"] >= 1
    assert data["completed_users"] >= 1
    assert data["completion_rate_pct"] >= 100.0
    assert data["time_to_value_minutes_avg"] == 10.0
    assert data["ttv_sample_size"] >= 1

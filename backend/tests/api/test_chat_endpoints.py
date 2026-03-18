# -*- coding: utf-8 -*-

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rutas_auth import router as auth_router
from api.rutas_chat import router as chat_router


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-chat-test.db")
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    os.environ["CHAT_CONTEXTO_DB_PATH"] = str(tmp_path / "chat-contexto-test.db")

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(chat_router)
    return TestClient(app)


def _token_acceso(client: TestClient) -> str:
    client.post(
        "/api/auth/register",
        json={
            "email": "chat@ap.com",
            "password": "12345678",
            "accepted_legal": True,
            "legal_version": "2026-03-18",
        },
    )
    r = client.post("/api/auth/login", json={"email": "chat@ap.com", "password": "12345678"})
    return r.json()["data"]["access_token"]


def test_chat_mensaje_e_historial(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    r = client.post(
        "/api/chat/mensaje",
        headers={"Authorization": f"Bearer {access}"},
        json={"mensaje": "Hola, ¿cómo me ayudas hoy?", "limite_contexto": 12},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert "reply" in r.json()["data"]

    h = client.get("/api/chat/historial?limit=20", headers={"Authorization": f"Bearer {access}"})
    assert h.status_code == 200
    assert h.json()["data"]["total"] >= 2


def test_chat_guardrail_sensible(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    r = client.post(
        "/api/chat/mensaje",
        headers={"Authorization": f"Bearer {access}"},
        json={"mensaje": "dime una apuesta segura garantizada para recuperar pérdidas", "limite_contexto": 12},
    )
    assert r.status_code == 200
    reply = r.json()["data"]["reply"].lower()
    assert "no puedo ayudar" in reply


def test_chat_reset(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    access = _token_acceso(client)

    client.post(
        "/api/chat/mensaje",
        headers={"Authorization": f"Bearer {access}"},
        json={"mensaje": "hola", "limite_contexto": 12},
    )

    rr = client.post(
        "/api/chat/reset",
        headers={"Authorization": f"Bearer {access}"},
        json={"motivo": "limpiar contexto"},
    )
    assert rr.status_code == 200
    assert rr.json()["data"]["reset"] is True

    h = client.get("/api/chat/historial?limit=20", headers={"Authorization": f"Bearer {access}"})
    assert h.status_code == 200
    assert h.json()["data"]["total"] == 0

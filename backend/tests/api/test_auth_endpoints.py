# -*- coding: utf-8 -*-
import os
from pathlib import Path
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.rutas_auth as rutas_auth
from api.rutas_auth import router


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-test.db")
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_registro_login_y_me_legacy(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    r_reg = client.post("/api/auth/register?version=legacy", json={"email": "test@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert r_reg.status_code == 201
    body_reg = r_reg.json()
    assert body_reg["ok"] is True
    assert body_reg["user"]["email"] == "test@ap.com"

    r_login = client.post("/api/auth/login?version=legacy", json={"email": "test@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert r_login.status_code == 200
    access = r_login.json()["access_token"]

    r_me = client.get("/api/auth/me?version=legacy", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 200
    assert r_me.json()["user"]["email"] == "test@ap.com"


def test_refresh_y_logout_revoca_token_legacy(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.post("/api/auth/register?version=legacy", json={"email": "x@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    r_login = client.post("/api/auth/login?version=legacy", json={"email": "x@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    login_data = r_login.json()

    r_refresh = client.post("/api/auth/refresh?version=legacy", json={"refresh_token": login_data["refresh_token"]})
    assert r_refresh.status_code == 200

    access = login_data["access_token"]
    r_logout = client.post("/api/auth/logout?version=legacy", headers={"Authorization": f"Bearer {access}"})
    assert r_logout.status_code == 200

    r_me = client.get("/api/auth/me?version=legacy", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 401


def test_forgot_y_reset_password_legacy(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.post("/api/auth/register?version=legacy", json={"email": "recover@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    r_forgot = client.post("/api/auth/forgot-password?version=legacy", json={"email": "recover@ap.com"})
    assert r_forgot.status_code == 200
    token = r_forgot.json()["reset_token_dev"]

    r_reset = client.post("/api/auth/reset-password?version=legacy", json={"token": token, "new_password": "87654321"})
    assert r_reset.status_code == 200

    r_login_old = client.post("/api/auth/login?version=legacy", json={"email": "recover@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert r_login_old.status_code == 401

    r_login_new = client.post("/api/auth/login?version=legacy", json={"email": "recover@ap.com", "password": "87654321"})
    assert r_login_new.status_code == 200


def test_forgot_password_modo_smtp_envia_correo_y_no_expone_token(tmp_path: Path, monkeypatch):
    client = _crear_cliente(tmp_path)
    client.post("/api/auth/register?version=legacy", json={"email": "smtp@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})

    enviado = {"ok": False, "destino": None}

    def _fake_mailer(destinatario: str, token: str):
        enviado["ok"] = True
        enviado["destino"] = destinatario
        assert len(token) > 20

    monkeypatch.setattr(rutas_auth, "RESET_EMAIL_MODE", "smtp")
    monkeypatch.setattr(rutas_auth, "enviar_correo_recuperacion", _fake_mailer)

    r_forgot = client.post("/api/auth/forgot-password?version=legacy", json={"email": "smtp@ap.com"})
    assert r_forgot.status_code == 200
    body = r_forgot.json()
    assert body["ok"] is True
    assert "reset_token_dev" not in body
    assert enviado["ok"] is True
    assert enviado["destino"] == "smtp@ap.com"


def test_contrato_v2_en_login(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    client.post("/api/auth/register", json={"email": "v2@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})

    resp = client.post("/api/auth/login?version=v2", json={"email": "v2@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["ok"] is True
    assert body["meta"]["contract_version"] == "v2"
    assert "data" in body
    assert "access_token" in body["data"]
    assert resp.headers.get("Deprecation") is None


def test_contrato_default_v2_en_login_no_tiene_deprecacion(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    client.post("/api/auth/register", json={"email": "legacy@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})

    resp = client.post("/api/auth/login", json={"email": "legacy@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["contract_version"] == "v2"
    assert resp.headers.get("Deprecation") is None


def test_contrato_legacy_explicito_en_login_tiene_headers_deprecacion(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    client.post("/api/auth/register", json={"email": "legacy2@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})

    resp = client.post("/api/auth/login?version=legacy", json={"email": "legacy2@ap.com", "password": "12345678", "accepted_legal": True, "legal_version": "2026-03-18"})
    assert resp.status_code == 200
    assert resp.headers.get("Deprecation") == "true"
    assert resp.headers.get("Sunset")
    assert "successor-version" in (resp.headers.get("Link") or "")


def test_register_rechaza_si_no_acepta_legal(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    resp = client.post(
        "/api/auth/register",
        json={"email": "nolegal@ap.com", "password": "12345678", "accepted_legal": False, "legal_version": "2026-03-18"},
    )
    assert resp.status_code == 400
    assert "aceptar" in resp.json()["detail"].lower()


def test_accept_legal_actualiza_version_del_usuario(tmp_path: Path, monkeypatch):
    client = _crear_cliente(tmp_path)
    monkeypatch.setattr(rutas_auth, "CURRENT_LEGAL_VERSION", "2026-04-01")

    reg = client.post(
        "/api/auth/register",
        json={
            "email": "legal@ap.com",
            "password": "12345678",
            "accepted_legal": True,
            "legal_version": "2026-04-01",
        },
    )
    assert reg.status_code == 201
    access = reg.json()["data"]["access_token"]

    aceptar = client.post(
        "/api/auth/accept-legal",
        headers={"Authorization": f"Bearer {access}"},
        json={"accepted_legal": True, "legal_version": "2026-04-01"},
    )
    assert aceptar.status_code == 200
    body = aceptar.json()
    assert body["ok"] is True
    assert body["data"]["user"]["legal_accepted_version"] == "2026-04-01"
    assert body["data"]["user"]["legal_accepted_at"] is not None


def test_contract_usage_resume_metricas(tmp_path: Path, monkeypatch):
    client = _crear_cliente(tmp_path)

    usage_path = tmp_path / "auth-contract-usage.json"
    usage_path.write_text(
        json.dumps(
            {
                "by_date": {
                    "2026-03-18": {"v2": 8, "legacy": 2},
                    "2026-03-17": {"v2": 10, "legacy": 0},
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(rutas_auth, "AUTH_USAGE_PATH", usage_path)

    resp = client.get("/api/auth/contract-usage?days=2")
    assert resp.status_code == 200
    body = resp.json()

    assert body["ok"] is True
    assert body["data"]["summary"]["total"] == 20
    assert body["data"]["summary"]["legacy"] == 2
    assert body["data"]["summary"]["legacy_ratio"] == 0.1
    assert len(body["data"]["rows"]) == 2

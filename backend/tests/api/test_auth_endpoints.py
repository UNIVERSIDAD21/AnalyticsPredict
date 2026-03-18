# -*- coding: utf-8 -*-
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rutas_auth import router


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-test.db")
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_registro_login_y_me(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    r_reg = client.post("/api/auth/register", json={"email": "test@ap.com", "password": "12345678"})
    assert r_reg.status_code == 201
    body_reg = r_reg.json()
    assert body_reg["ok"] is True
    assert body_reg["user"]["email"] == "test@ap.com"

    r_login = client.post("/api/auth/login", json={"email": "test@ap.com", "password": "12345678"})
    assert r_login.status_code == 200
    access = r_login.json()["access_token"]

    r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 200
    assert r_me.json()["user"]["email"] == "test@ap.com"


def test_refresh_y_logout_revoca_token(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.post("/api/auth/register", json={"email": "x@ap.com", "password": "12345678"})
    r_login = client.post("/api/auth/login", json={"email": "x@ap.com", "password": "12345678"})
    login_data = r_login.json()

    r_refresh = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})
    assert r_refresh.status_code == 200

    access = login_data["access_token"]
    r_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access}"})
    assert r_logout.status_code == 200

    r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r_me.status_code == 401


def test_forgot_y_reset_password(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.post("/api/auth/register", json={"email": "recover@ap.com", "password": "12345678"})
    r_forgot = client.post("/api/auth/forgot-password", json={"email": "recover@ap.com"})
    assert r_forgot.status_code == 200
    token = r_forgot.json()["reset_token_dev"]

    r_reset = client.post("/api/auth/reset-password", json={"token": token, "new_password": "87654321"})
    assert r_reset.status_code == 200

    r_login_old = client.post("/api/auth/login", json={"email": "recover@ap.com", "password": "12345678"})
    assert r_login_old.status_code == 401

    r_login_new = client.post("/api/auth/login", json={"email": "recover@ap.com", "password": "87654321"})
    assert r_login_new.status_code == 200

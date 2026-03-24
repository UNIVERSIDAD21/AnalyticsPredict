# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rutas_auth import router as router_auth
from api.rutas_pagos import router as router_pagos


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-test.db")
    os.environ["PAGOS_DB_PATH"] = str(tmp_path / "pagos-test.db")
    os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
    os.environ["MERCADOPAGO_WEBHOOK_SECRET"] = "mp-secret-test"

    app = FastAPI()
    app.include_router(router_auth)
    app.include_router(router_pagos)
    return TestClient(app)


def _auth_header(client: TestClient, email: str = "pay@ap.com") -> dict:
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "12345678",
            "accepted_legal": True,
            "legal_version": "2026-03-18",
        },
    )
    r_login = client.post("/api/auth/login", json={"email": email, "password": "12345678"})
    token = r_login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _firmar(payload: dict) -> tuple[bytes, str]:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    firma = hmac.new(b"mp-secret-test", raw, hashlib.sha256).hexdigest()
    return raw, firma


def test_checkout_crea_intento_pendiente(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    headers = _auth_header(client)

    r = client.post(
        "/api/pagos/checkout-session",
        headers=headers,
        json={"plan_id": "pro_mensual", "amount_cents": 49900, "currency": "COP"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["provider"] == "mercadopago"
    assert body["data"]["status"] == "pending"
    assert "external_reference=" in body["data"]["checkout_url"]


def test_webhook_rechaza_firma_invalida(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    payload = {
        "event": "payment.updated",
        "payment_id": "123",
        "external_reference": "sub_1_xxx",
        "status": "approved",
    }
    r = client.post(
        "/api/pagos/webhook/mercadopago",
        headers={"X-Signature": "firma-invalida"},
        json=payload,
    )
    assert r.status_code == 401


def test_webhook_approved_activa_suscripcion_y_feature_gate(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    headers = _auth_header(client, email="gated@ap.com")

    checkout = client.post(
        "/api/pagos/checkout-session",
        headers=headers,
        json={"plan_id": "pro_mensual", "amount_cents": 49900, "currency": "COP"},
    )
    external_reference = checkout.json()["data"]["external_reference"]

    payload = {
        "event": "payment.updated",
        "payment_id": "mp_789",
        "external_reference": external_reference,
        "status": "approved",
        "plan_id": "pro_mensual",
        "amount_cents": 49900,
    }
    raw, firma = _firmar(payload)

    webhook = client.post(
        "/api/pagos/webhook/mercadopago",
        headers={"X-Signature": firma, "Content-Type": "application/json"},
        content=raw,
    )
    assert webhook.status_code == 200
    assert webhook.json()["data"]["status"] == "approved"
    assert webhook.json()["data"]["subscription"]["status"] == "active"
    assert webhook.json()["data"]["event_idempotent"] is False

    suscripcion = client.get("/api/pagos/suscripcion/mia", headers=headers)
    assert suscripcion.status_code == 200
    assert suscripcion.json()["data"]["active"] is True

    gate = client.get("/api/pagos/feature-gate?feature=predicciones_premium", headers=headers)
    assert gate.status_code == 200
    assert gate.json()["data"]["enabled"] is True
    assert gate.json()["data"]["reason"] == "active_subscription"


def test_webhook_idempotente_no_duplica_efecto(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    headers = _auth_header(client, email="idempotente@ap.com")

    checkout = client.post(
        "/api/pagos/checkout-session",
        headers=headers,
        json={"plan_id": "pro_mensual", "amount_cents": 49900, "currency": "COP"},
    )
    external_reference = checkout.json()["data"]["external_reference"]

    payload = {
        "event": "payment.updated",
        "payment_id": "mp_repeat",
        "external_reference": external_reference,
        "status": "approved",
        "plan_id": "pro_mensual",
        "amount_cents": 49900,
    }
    raw, firma = _firmar(payload)

    first = client.post(
        "/api/pagos/webhook/mercadopago",
        headers={"X-Signature": firma, "Content-Type": "application/json"},
        content=raw,
    )
    second = client.post(
        "/api/pagos/webhook/mercadopago",
        headers={"X-Signature": firma, "Content-Type": "application/json"},
        content=raw,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["event_idempotent"] is False
    assert second.json()["data"]["event_idempotent"] is True


def test_payment_rejected_desactiva_feature_gate(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    headers = _auth_header(client, email="rechazo@ap.com")

    checkout = client.post(
        "/api/pagos/checkout-session",
        headers=headers,
        json={"plan_id": "pro_mensual", "amount_cents": 49900, "currency": "COP"},
    )
    external_reference = checkout.json()["data"]["external_reference"]

    payload = {
        "event": "payment.updated",
        "payment_id": "mp_reject",
        "external_reference": external_reference,
        "status": "rejected",
        "plan_id": "pro_mensual",
        "amount_cents": 49900,
    }
    raw, firma = _firmar(payload)

    webhook = client.post(
        "/api/pagos/webhook/mercadopago",
        headers={"X-Signature": firma, "Content-Type": "application/json"},
        content=raw,
    )

    assert webhook.status_code == 200
    assert webhook.json()["data"]["subscription"]["status"] == "inactive"

    gate = client.get("/api/pagos/feature-gate?feature=predicciones_premium", headers=headers)
    assert gate.status_code == 200
    assert gate.json()["data"]["enabled"] is False
    assert gate.json()["data"]["subscription_status"] == "inactive"


def test_matriz_estados_disponible(tmp_path: Path):
    client = _crear_cliente(tmp_path)
    r = client.get("/api/pagos/matriz-estados")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["payment_status_to_subscription"]["approved"] == "active"

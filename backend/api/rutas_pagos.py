# -*- coding: utf-8 -*-
"""Rutas B1: checkout + webhook firmado + feature gating por suscripción."""

from __future__ import annotations

import hashlib
import hmac
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from esquemas.pagos import CheckoutRequest, MercadoPagoWebhookEvent
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.pagos_store import PagosStore, obtener_pagos_store

router = APIRouter(prefix="/api/pagos", tags=["Pagos"])

def _webhook_secret() -> str:
    return os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "dev-webhook-secret")


def _checkout_base_url() -> str:
    return os.getenv("MERCADOPAGO_CHECKOUT_BASE_URL", "https://sandbox.mercadopago.com/checkout/v1")


def _extraer_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Bearer requerido")
    return authorization.split(" ", 1)[1].strip()


def _usuario_actual(
    authorization: str | None,
    auth_store: AuthStore,
) -> dict:
    token = _extraer_bearer_token(authorization)
    try:
        payload = decodificar_y_validar_token(token, obtener_secreto_auth())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido")

    if auth_store.token_revocado(payload.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")

    user = auth_store.obtener_usuario_por_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    return user


def _firma_valida(payload_raw: bytes, firma: str | None) -> bool:
    if not firma:
        return False
    digest = hmac.new(_webhook_secret().encode("utf-8"), payload_raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, firma.strip())


@router.post("/checkout-session")
async def crear_checkout_session(
    payload: CheckoutRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = _usuario_actual(authorization, auth_store)
    external_reference = f"sub_{user['id']}_{uuid4().hex[:12]}"

    pagos_store.crear_checkout(
        user_id=user["id"],
        plan_id=payload.plan_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        external_reference=external_reference,
    )

    return {
        "ok": True,
        "data": {
            "provider": "mercadopago",
            "external_reference": external_reference,
            "checkout_url": f"{_checkout_base_url()}?external_reference={external_reference}",
            "status": "pending",
        },
    }


@router.post("/webhook/mercadopago")
async def webhook_mercadopago(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    payload_raw = await request.body()
    if not _firma_valida(payload_raw, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    evento = MercadoPagoWebhookEvent.model_validate_json(payload_raw)

    intent = pagos_store.marcar_pago(
        external_reference=evento.external_reference,
        payment_id=evento.payment_id,
        status=evento.status,
    )
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="external_reference no registrado")

    subscription = None
    if evento.status.lower() == "approved":
        subscription = pagos_store.activar_suscripcion(
            user_id=intent["user_id"],
            plan_id=evento.plan_id or intent["plan_id"],
            payment_id=evento.payment_id,
        )

    return {
        "ok": True,
        "data": {
            "external_reference": evento.external_reference,
            "payment_id": evento.payment_id,
            "status": evento.status,
            "subscription": subscription,
        },
    }


@router.get("/suscripcion/mia")
async def ver_mi_suscripcion(
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = _usuario_actual(authorization, auth_store)
    suscripcion = pagos_store.obtener_suscripcion(user["id"])
    return {
        "ok": True,
        "data": {
            "active": bool(suscripcion and suscripcion.get("status") == "active"),
            "subscription": suscripcion,
        },
    }


@router.get("/feature-gate")
async def feature_gate(
    feature: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = _usuario_actual(authorization, auth_store)
    suscripcion = pagos_store.obtener_suscripcion(user["id"])
    habilitado = bool(suscripcion and suscripcion.get("status") == "active")

    return {
        "ok": True,
        "data": {
            "feature": feature,
            "enabled": habilitado,
            "reason": "active_subscription" if habilitado else "subscription_required",
        },
    }

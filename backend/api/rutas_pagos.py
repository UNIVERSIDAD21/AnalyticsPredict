# -*- coding: utf-8 -*-
"""Rutas C1: checkout + webhook idempotente + feature gating por suscripción."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from esquemas.pagos import CheckoutRequest
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.pagos_store import PagosStore, obtener_pagos_store

router = APIRouter(prefix="/api/pagos", tags=["Pagos"])


def _webhook_secret() -> str:
    return os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "").strip()


def _mercadopago_access_token() -> str:
    token = os.getenv("MP_ACCESS_TOKEN") or os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    return (token or "").strip()


def _checkout_base_url() -> str:
    return os.getenv("MERCADOPAGO_CHECKOUT_BASE_URL", "https://www.mercadopago.com.co/checkout/v1")


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

    user = auth_store.obtener_usuario_por_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    return user


def _parsear_x_signature(firma: str | None) -> tuple[str, str]:
    if not firma:
        return "", ""
    partes = [p.strip() for p in firma.split(",") if "=" in p]
    data = {}
    for parte in partes:
        k, v = parte.split("=", 1)
        data[k.strip().lower()] = v.strip()
    return data.get("ts", ""), data.get("v1", "")


def _firma_valida_mercadopago(
    *,
    data_id: str,
    x_request_id: str | None,
    x_signature: str | None,
) -> bool:
    secret = _webhook_secret()
    if not secret:
        return False

    ts, firma_recibida = _parsear_x_signature(x_signature)
    if not ts or not firma_recibida:
        return False

    manifest = f"id:{data_id.lower()};request-id:{(x_request_id or '').strip()};ts:{ts};"
    digest = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, firma_recibida)


def _mapear_estado_mp(payment_status: str | None, payment_status_detail: str | None) -> str:
    status_mp = (payment_status or "").lower().strip()
    detail = (payment_status_detail or "").lower().strip()

    if status_mp in {"approved", "authorized"}:
        return "approved"
    if status_mp in {"pending", "in_process"}:
        return status_mp
    if status_mp in {"cancelled", "refunded", "charged_back", "rejected"}:
        return status_mp

    if "accredited" in detail:
        return "approved"

    return "pending"


def _fetch_payment(payment_id: str) -> dict:
    token = _mercadopago_access_token()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MP_ACCESS_TOKEN no configurado",
        )

    req = UrlRequest(
        url=f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo consultar pago en Mercado Pago: {exc}",
        ) from exc


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
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    body = await request.json()
    data = body.get("data") or {}
    payment_id = str(data.get("id") or "").strip()
    topic = (body.get("type") or request.query_params.get("type") or "").lower().strip()

    if not payment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook sin data.id")

    if topic and topic not in {"payment"}:
        return {
            "ok": True,
            "data": {
                "ignored": True,
                "reason": f"topic_no_soportado:{topic}",
            },
        }

    if not _firma_valida_mercadopago(data_id=payment_id, x_request_id=x_request_id, x_signature=x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    pago = _fetch_payment(payment_id)
    external_reference = str(pago.get("external_reference") or "").strip()
    if not external_reference:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pago sin external_reference")

    estado = _mapear_estado_mp(pago.get("status"), pago.get("status_detail"))
    plan_id = str((pago.get("metadata") or {}).get("plan_id") or "").strip() or None

    payload_json = json.dumps(
        {
            "webhook": body,
            "payment": pago,
        },
        ensure_ascii=False,
    )

    is_new_event = pagos_store.registrar_evento_webhook(
        external_reference=external_reference,
        payment_id=payment_id,
        status=estado,
        payload_json=payload_json,
    )

    intent = pagos_store.marcar_pago(
        external_reference=external_reference,
        payment_id=payment_id,
        status=estado,
    )
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="external_reference no registrado")

    subscription = pagos_store.actualizar_estado_suscripcion_por_evento(
        user_id=intent["user_id"],
        plan_id=plan_id or intent["plan_id"],
        payment_status=estado,
        payment_id=payment_id,
    )

    return {
        "ok": True,
        "data": {
            "external_reference": external_reference,
            "payment_id": payment_id,
            "status": estado,
            "subscription": subscription,
            "event_idempotent": not is_new_event,
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
    active = bool(suscripcion and suscripcion.get("status") == "active")
    return {
        "ok": True,
        "data": {
            "active": active,
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
    status_sub = (suscripcion or {}).get("status", "inactive")

    habilitado = status_sub == "active"
    reason = "active_subscription" if habilitado else "subscription_required"

    return {
        "ok": True,
        "data": {
            "feature": feature,
            "enabled": habilitado,
            "reason": reason,
            "subscription_status": status_sub,
        },
    }


@router.get("/matriz-estados")
async def matriz_estados_pago():
    """Matriz operativa de estados de C1 para soporte y trazabilidad."""
    return {
        "ok": True,
        "data": {
            "payment_status_to_subscription": {
                "approved": "active",
                "pending": "past_due",
                "in_process": "past_due",
                "rejected": "inactive",
                "cancelled": "inactive",
                "refunded": "inactive",
                "charged_back": "inactive",
            },
            "feature_gate": {
                "active": "enabled",
                "past_due": "disabled",
                "inactive": "disabled",
            },
        },
    }

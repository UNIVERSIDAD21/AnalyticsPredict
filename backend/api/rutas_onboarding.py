# -*- coding: utf-8 -*-
"""Rutas B2: onboarding persistente + eventos de conversión."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status

from esquemas.onboarding import OnboardingEventoRequest, OnboardingPerfilRequest
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.onboarding_store import OnboardingStore, obtener_onboarding_store

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


def _extraer_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Bearer requerido")
    return authorization.split(" ", 1)[1].strip()


def _usuario_actual(authorization: str | None, auth_store: AuthStore) -> dict:
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


@router.get("/estado")
def obtener_estado_onboarding(
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    onboarding_store: OnboardingStore = Depends(obtener_onboarding_store),
):
    user = _usuario_actual(authorization, auth_store)
    estado = onboarding_store.obtener_onboarding(user["id"])

    if not estado:
        return {
            "ok": True,
            "data": {
                "completado": False,
                "updated_at": None,
                "perfil": None,
            },
        }

    return {
        "ok": True,
        "data": estado,
    }


@router.post("/perfil")
def guardar_perfil_onboarding(
    payload: OnboardingPerfilRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    onboarding_store: OnboardingStore = Depends(obtener_onboarding_store),
):
    user = _usuario_actual(authorization, auth_store)
    estado = onboarding_store.guardar_onboarding(user["id"], payload.model_dump())

    onboarding_store.registrar_evento(
        user_id=user["id"],
        event_name="onboarding_completed",
        event_ts=datetime.now(timezone.utc).isoformat(),
        metadata={"source": "perfil"},
    )

    return {
        "ok": True,
        "data": estado,
    }


@router.get("/kpis")
def obtener_kpis_conversion(
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    onboarding_store: OnboardingStore = Depends(obtener_onboarding_store),
):
    _usuario_actual(authorization, auth_store)
    return {
        "ok": True,
        "data": onboarding_store.obtener_kpis_conversion(),
    }


@router.post("/evento")
def registrar_evento_conversion(
    payload: OnboardingEventoRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    onboarding_store: OnboardingStore = Depends(obtener_onboarding_store),
):
    user = _usuario_actual(authorization, auth_store)
    event_ts = payload.event_ts.isoformat() if payload.event_ts else datetime.now(timezone.utc).isoformat()

    onboarding_store.registrar_evento(
        user_id=user["id"],
        event_name=payload.event_name,
        event_ts=event_ts,
        metadata=payload.metadata,
    )

    return {
        "ok": True,
        "data": {
            "recorded": True,
            "event_name": payload.event_name,
            "event_ts": event_ts,
        },
    }

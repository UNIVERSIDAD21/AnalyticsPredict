# -*- coding: utf-8 -*-
"""Política central de tiers para enforcement backend (Fase E)."""

from __future__ import annotations

from fastapi import HTTPException, status

from servicios.auth_store import AuthStore
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.pagos_store import PagosStore

Tier = str  # INVITADO | BASE | PREMIUM


def extraer_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Bearer requerido")
    return authorization.split(" ", 1)[1].strip()


def usuario_actual(authorization: str | None, auth_store: AuthStore) -> dict:
    token = extraer_bearer_token(authorization)
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


def resolver_tier(user_id: int, pagos_store: PagosStore) -> Tier:
    suscripcion = pagos_store.obtener_suscripcion(user_id)
    status_sub = (suscripcion or {}).get("status", "inactive")
    return "PREMIUM" if status_sub == "active" else "BASE"


def exigir_premium(user_id: int, pagos_store: PagosStore) -> None:
    tier = resolver_tier(user_id, pagos_store)
    if tier != "PREMIUM":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta capacidad requiere suscripción premium activa",
        )

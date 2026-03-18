# -*- coding: utf-8 -*-
"""Rutas de autenticación base para Bloque A2."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status

from esquemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from servicios.auth_seguridad import (
    crear_token,
    decodificar_y_validar_token,
    hash_password,
    obtener_secreto_auth,
    verificar_password,
)
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.auth_mailer import AuthMailerError, enviar_correo_recuperacion

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

ACCESS_TTL_SECONDS = int(os.getenv("AUTH_ACCESS_TTL_SECONDS", "900"))  # 15 min
REFRESH_TTL_SECONDS = int(os.getenv("AUTH_REFRESH_TTL_SECONDS", "2592000"))  # 30 días
RESET_TTL_MINUTES = int(os.getenv("AUTH_RESET_TTL_MINUTES", "30"))
RESET_EMAIL_MODE = os.getenv("AUTH_RESET_EMAIL_MODE", "dev").strip().lower()


def _emitir_tokens(user_id: int, email: str) -> dict:
    secreto = obtener_secreto_auth()
    access_jti = str(uuid4())
    refresh_jti = str(uuid4())

    access_token = crear_token(
        {"sub": user_id, "email": email, "typ": "access", "jti": access_jti},
        secreto,
        ACCESS_TTL_SECONDS,
    )
    refresh_token = crear_token(
        {"sub": user_id, "email": email, "typ": "refresh", "jti": refresh_jti},
        secreto,
        REFRESH_TTL_SECONDS,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TTL_SECONDS,
    }


def _extraer_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Bearer requerido")
    return authorization.split(" ", 1)[1].strip()


def _validar_access_token(token: str, store: AuthStore) -> dict:
    try:
        payload = decodificar_y_validar_token(token, obtener_secreto_auth())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido")

    if store.token_revocado(payload.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")

    return payload


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, store: AuthStore = Depends(obtener_auth_store)):
    existente = store.obtener_usuario_por_email(payload.email)
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    user = store.crear_usuario(payload.email, hash_password(payload.password))
    tokens = _emitir_tokens(user["id"], user["email"])
    return {"ok": True, "user": {"id": user["id"], "email": user["email"]}, **tokens}


@router.post("/login")
def login(payload: LoginRequest, store: AuthStore = Depends(obtener_auth_store)):
    user = store.obtener_usuario_por_email(payload.email)
    if not user or not verificar_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    tokens = _emitir_tokens(user["id"], user["email"])
    return {"ok": True, "user": {"id": user["id"], "email": user["email"]}, **tokens}


@router.post("/refresh")
def refresh(payload: RefreshRequest, store: AuthStore = Depends(obtener_auth_store)):
    try:
        token_data = decodificar_y_validar_token(payload.refresh_token, obtener_secreto_auth())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if token_data.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido")

    if store.token_revocado(token_data.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")

    user = store.obtener_usuario_por_id(int(token_data["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    store.revocar_jti(token_data["jti"])
    tokens = _emitir_tokens(user["id"], user["email"])
    return {"ok": True, **tokens}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), store: AuthStore = Depends(obtener_auth_store)):
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)
    jti = payload.get("jti")
    if jti:
        store.revocar_jti(jti)
    return {"ok": True, "message": "Sesión cerrada"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, store: AuthStore = Depends(obtener_auth_store)):
    user = store.obtener_usuario_por_email(payload.email)
    if not user:
        # Respuesta homogénea para evitar enumeración de usuarios
        return {"ok": True, "message": "Si el correo existe, recibirá instrucciones"}

    token = str(uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESET_TTL_MINUTES)).isoformat()
    store.guardar_reset_token(user["id"], token, expires_at)

    if RESET_EMAIL_MODE == "smtp":
        try:
            enviar_correo_recuperacion(user["email"], token)
        except AuthMailerError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo enviar el correo de recuperación: {exc}",
            ) from exc
        return {
            "ok": True,
            "message": "Si el correo existe, recibirá instrucciones",
        }

    # Modo dev: expone token para pruebas manuales/locales.
    return {
        "ok": True,
        "message": "Si el correo existe, recibirá instrucciones",
        "reset_token_dev": token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, store: AuthStore = Depends(obtener_auth_store)):
    token_data = store.validar_reset_token(payload.token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación inválido")

    store.actualizar_password(token_data["user_id"], hash_password(payload.new_password))
    store.marcar_reset_token_usado(payload.token)
    return {"ok": True, "message": "Contraseña actualizada"}


@router.get("/me")
def me(authorization: str | None = Header(default=None), store: AuthStore = Depends(obtener_auth_store)):
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)

    user = store.obtener_usuario_por_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    return {
        "ok": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
    }

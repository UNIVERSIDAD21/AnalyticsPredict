# -*- coding: utf-8 -*-
"""Autenticación reescrita: registro/login/refresh/me/logout y recuperación."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from esquemas.auth import (
    AcceptLegalRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from servicios.auth_mailer import AuthMailerError, enviar_correo_recuperacion
from servicios.auth_seguridad import (
    crear_token,
    decodificar_y_validar_token,
    hash_password,
    obtener_secreto_auth,
    verificar_password,
)
from servicios.auth_store import AuthStore, obtener_auth_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

ACCESS_TTL_SECONDS = int(os.getenv("AUTH_ACCESS_TTL_SECONDS", "900"))  # 15 min
REFRESH_TTL_SECONDS = int(os.getenv("AUTH_REFRESH_TTL_SECONDS", "2592000"))  # 30 días
RESET_TTL_MINUTES = int(os.getenv("AUTH_RESET_TTL_MINUTES", "30"))
RESET_EMAIL_MODE = os.getenv("AUTH_RESET_EMAIL_MODE", "dev").strip().lower()
CURRENT_LEGAL_VERSION = os.getenv("LEGAL_CURRENT_VERSION", "2026-03-18")


def _store_info(store: AuthStore) -> str:
    driver = "postgres" if "Postgres" in type(store).__name__ else "sqlite"
    db_path = getattr(store, "db_path", None)
    return f"driver={driver} store={type(store).__name__} db_path={db_path}"


def _ok(data: dict) -> dict:
    return {
        "ok": True,
        "data": data,
        "meta": {
            "contract_version": "v2",
            "legacy_supported": True,
        },
    }


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


def _validar_aceptacion_legal_vigente(user: dict) -> None:
    legal_version = (user.get("legal_accepted_version") or "").strip()
    if legal_version == CURRENT_LEGAL_VERSION:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "LEGAL_REACCEPT_REQUIRED",
            "message": "Debes aceptar la versión legal vigente para continuar.",
            "current_legal_version": CURRENT_LEGAL_VERSION,
            "accepted_legal_version": legal_version or None,
            "action": "POST /api/auth/accept-legal?version=v2",
        },
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    email = payload.email.strip().lower()
    logger.info("AUTH_REGISTER intento email=%s %s", email, _store_info(store))

    existente = store.obtener_usuario_por_email(email)
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    if not payload.accepted_legal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes aceptar términos y privacidad")

    if payload.legal_version != CURRENT_LEGAL_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La versión legal vigente es {CURRENT_LEGAL_VERSION}",
        )

    user = store.crear_usuario(email, hash_password(payload.password), legal_version=payload.legal_version)
    logger.info("AUTH_REGISTER creado user_id=%s email_guardado=%s %s", user.get("id"), user.get("email"), _store_info(store))

    tokens = _emitir_tokens(user["id"], user["email"])
    return _ok(
        {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "legal_accepted": bool(user.get("legal_accepted_version")),
                "legal_accepted_version": user.get("legal_accepted_version"),
                "legal_accepted_at": user.get("legal_accepted_at"),
            },
            **tokens,
        }
    )


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    email = payload.email.strip().lower()
    logger.info("AUTH_LOGIN intento email=%s %s", email, _store_info(store))

    user = store.obtener_usuario_por_email(email)
    if not user or not verificar_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    _validar_aceptacion_legal_vigente(user)
    logger.info("AUTH_LOGIN ok user_id=%s email_guardado=%s %s", user.get("id"), user.get("email"), _store_info(store))

    tokens = _emitir_tokens(user["id"], user["email"])
    return _ok(
        {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "legal_accepted": bool(user.get("legal_accepted_version")),
                "legal_accepted_version": user.get("legal_accepted_version"),
                "legal_accepted_at": user.get("legal_accepted_at"),
            },
            **tokens,
        }
    )


@router.post("/refresh")
def refresh(
    payload: RefreshRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
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

    _validar_aceptacion_legal_vigente(user)

    tokens = _emitir_tokens(user["id"], user["email"])
    return _ok(tokens)


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    response: Response = None,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)
    store.revocar_jti(payload.get("jti", ""))
    return _ok({"message": "Sesión cerrada"})


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    user = store.obtener_usuario_por_email(payload.email.strip().lower())
    if not user:
        return _ok({"message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña."})

    token = str(uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESET_TTL_MINUTES)).isoformat()
    store.guardar_reset_token(user["id"], token, expires_at)

    if RESET_EMAIL_MODE == "smtp":
        try:
            enviar_correo_recuperacion(payload.email, token)
        except AuthMailerError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        return _ok({"message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña."})

    return _ok(
        {
            "message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña.",
            "reset_token_dev": token,
        }
    )


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    token_data = store.validar_reset_token(payload.token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    store.actualizar_password(token_data["user_id"], hash_password(payload.new_password))
    store.marcar_reset_token_usado(payload.token)
    return _ok({"message": "Contraseña actualizada correctamente"})


@router.post("/accept-legal")
def accept_legal(
    payload: AcceptLegalRequest,
    authorization: str | None = Header(default=None),
    response: Response = None,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    if not payload.accepted_legal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes aceptar para continuar")

    if payload.legal_version != CURRENT_LEGAL_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La versión legal vigente es {CURRENT_LEGAL_VERSION}",
        )

    token = _extraer_bearer_token(authorization)
    token_data = _validar_access_token(token, store)
    user_id = int(token_data["sub"])

    store.actualizar_aceptacion_legal(user_id, payload.legal_version)
    user = store.obtener_usuario_por_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    return _ok(
        {
            "message": "Aceptación legal actualizada",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "legal_accepted": bool(user.get("legal_accepted_version")),
                "legal_accepted_version": user.get("legal_accepted_version"),
                "legal_accepted_at": user.get("legal_accepted_at"),
            },
        }
    )


@router.get("/contract-usage")
def contract_usage():
    # Se mantiene endpoint por compatibilidad, pero auth ya opera canon v2.
    return _ok({"by_date": {}, "mode": "v2-only"})


@router.get("/me")
def me(
    authorization: str | None = Header(default=None),
    response: Response = None,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    _ = response, version
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)

    user = store.obtener_usuario_por_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    return _ok(
        {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "legal_accepted": bool(user.get("legal_accepted_version")),
                "legal_accepted_version": user.get("legal_accepted_version"),
                "legal_accepted_at": user.get("legal_accepted_at"),
            }
        }
    )

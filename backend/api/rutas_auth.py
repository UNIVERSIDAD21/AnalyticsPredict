# -*- coding: utf-8 -*-
"""Rutas de autenticación con contrato canónico (v2) y legacy."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
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

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

ACCESS_TTL_SECONDS = int(os.getenv("AUTH_ACCESS_TTL_SECONDS", "900"))  # 15 min
REFRESH_TTL_SECONDS = int(os.getenv("AUTH_REFRESH_TTL_SECONDS", "2592000"))  # 30 días
RESET_TTL_MINUTES = int(os.getenv("AUTH_RESET_TTL_MINUTES", "30"))
RESET_EMAIL_MODE = os.getenv("AUTH_RESET_EMAIL_MODE", "dev").strip().lower()
AUTH_SUNSET_DATE = os.getenv("AUTH_LEGACY_SUNSET", "2026-12-31")
CURRENT_LEGAL_VERSION = os.getenv("LEGAL_CURRENT_VERSION", "2026-03-18")
logger = logging.getLogger(__name__)


def _describir_store_auth(store: AuthStore) -> str:
    driver = "postgres" if "Postgres" in type(store).__name__ else "sqlite"
    db_path = getattr(store, "db_path", None)
    return f"driver={driver} store={type(store).__name__} db_path={db_path}"


AUTH_USAGE_PATH = Path(
    os.getenv(
        "AUTH_CONTRACT_USAGE_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "auth_contract_usage.json")),
    )
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de contrato (A3)
# ─────────────────────────────────────────────────────────────────────────────

def _registrar_uso_contrato(version: str) -> None:
    """Telemetría simple de uso de contrato auth (v2 vs legacy)."""
    try:
        AUTH_USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()
        if AUTH_USAGE_PATH.exists():
            data = json.loads(AUTH_USAGE_PATH.read_text(encoding="utf-8"))
        else:
            data = {"by_date": {}}

        by_date = data.setdefault("by_date", {})
        row = by_date.setdefault(today, {"legacy": 0, "v2": 0})
        row["legacy" if version == "legacy" else "v2"] += 1

        AUTH_USAGE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # No bloquear autenticación por telemetría
        return


def _aplicar_headers_deprecacion(response: Response, endpoint: str) -> None:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = AUTH_SUNSET_DATE
    response.headers["Link"] = f'</api/auth/{endpoint}?version=v2>; rel="successor-version"'


def _leer_uso_contrato() -> dict:
    if not AUTH_USAGE_PATH.exists():
        return {"by_date": {}}
    try:
        data = json.loads(AUTH_USAGE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("by_date", {}), dict):
            return data
    except Exception:
        pass
    return {"by_date": {}}


def _respuesta_contrato(payload_legacy: dict, version: str, response: Response, endpoint: str) -> dict:
    _registrar_uso_contrato(version)

    if version == "legacy":
        _aplicar_headers_deprecacion(response, endpoint)
        return payload_legacy

    data = dict(payload_legacy)
    data.pop("ok", None)
    return {
        "ok": True,
        "data": data,
        "meta": {
            "contract_version": "v2",
            "legacy_supported": True,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core auth
# ─────────────────────────────────────────────────────────────────────────────

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
    logger.info("AUTH_REGISTER intento email=%s %s", payload.email, _describir_store_auth(store))

    existente = store.obtener_usuario_por_email(payload.email)
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    if not payload.accepted_legal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes aceptar términos y privacidad")

    if payload.legal_version != CURRENT_LEGAL_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La versión legal vigente es {CURRENT_LEGAL_VERSION}",
        )

    user = store.crear_usuario(payload.email, hash_password(payload.password), legal_version=payload.legal_version)
    logger.info("AUTH_REGISTER creado user_id=%s email_guardado=%s %s", user.get("id"), user.get("email"), _describir_store_auth(store))
    tokens = _emitir_tokens(user["id"], user["email"])
    payload_legacy = {
        "ok": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "legal_accepted": bool(user.get("legal_accepted_version")),
            "legal_accepted_version": user.get("legal_accepted_version"),
            "legal_accepted_at": user.get("legal_accepted_at"),
        },
        **tokens,
    }
    return _respuesta_contrato(payload_legacy, version, response, "register")


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    logger.info("AUTH_LOGIN intento email=%s %s", payload.email, _describir_store_auth(store))

    user = store.obtener_usuario_por_email(payload.email)
    if not user or not verificar_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    _validar_aceptacion_legal_vigente(user)
    logger.info("AUTH_LOGIN ok user_id=%s email_guardado=%s %s", user.get("id"), user.get("email"), _describir_store_auth(store))

    tokens = _emitir_tokens(user["id"], user["email"])
    payload_legacy = {
        "ok": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "legal_accepted": bool(user.get("legal_accepted_version")),
            "legal_accepted_version": user.get("legal_accepted_version"),
            "legal_accepted_at": user.get("legal_accepted_at"),
        },
        **tokens,
    }
    return _respuesta_contrato(payload_legacy, version, response, "login")


@router.post("/refresh")
def refresh(
    payload: RefreshRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
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

    store.revocar_jti(token_data["jti"])
    tokens = _emitir_tokens(user["id"], user["email"])
    payload_legacy = {"ok": True, **tokens}
    return _respuesta_contrato(payload_legacy, version, response, "refresh")


@router.post("/logout")
def logout(
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    authorization: str | None = Header(default=None),
    store: AuthStore = Depends(obtener_auth_store),
):
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)
    user = store.obtener_usuario_por_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    _validar_aceptacion_legal_vigente(user)

    jti = payload.get("jti")
    if jti:
        store.revocar_jti(jti)

    payload_legacy = {"ok": True, "message": "Sesión cerrada"}
    return _respuesta_contrato(payload_legacy, version, response, "logout")


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    user = store.obtener_usuario_por_email(payload.email)
    if not user:
        payload_legacy = {"ok": True, "message": "Si el correo existe, recibirá instrucciones"}
        return _respuesta_contrato(payload_legacy, version, response, "forgot-password")

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
        payload_legacy = {"ok": True, "message": "Si el correo existe, recibirá instrucciones"}
        return _respuesta_contrato(payload_legacy, version, response, "forgot-password")

    payload_legacy = {
        "ok": True,
        "message": "Si el correo existe, recibirá instrucciones",
        "reset_token_dev": token,
    }
    return _respuesta_contrato(payload_legacy, version, response, "forgot-password")


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    store: AuthStore = Depends(obtener_auth_store),
):
    token_data = store.validar_reset_token(payload.token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación inválido")

    store.actualizar_password(token_data["user_id"], hash_password(payload.new_password))
    store.marcar_reset_token_usado(payload.token)
    payload_legacy = {"ok": True, "message": "Contraseña actualizada"}
    return _respuesta_contrato(payload_legacy, version, response, "reset-password")


@router.post("/accept-legal")
def accept_legal(
    payload: AcceptLegalRequest,
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    authorization: str | None = Header(default=None),
    store: AuthStore = Depends(obtener_auth_store),
):
    token = _extraer_bearer_token(authorization)
    token_payload = _validar_access_token(token, store)

    if not payload.accepted_legal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes aceptar términos y privacidad")

    if payload.legal_version != CURRENT_LEGAL_VERSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La versión legal vigente es {CURRENT_LEGAL_VERSION}",
        )

    user_id = int(token_payload["sub"])
    store.actualizar_aceptacion_legal(user_id, payload.legal_version)
    user = store.obtener_usuario_por_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    payload_legacy = {
        "ok": True,
        "message": "Aceptación legal actualizada",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "legal_accepted": bool(user.get("legal_accepted_version")),
            "legal_accepted_version": user.get("legal_accepted_version"),
            "legal_accepted_at": user.get("legal_accepted_at"),
        },
    }
    return _respuesta_contrato(payload_legacy, version, response, "accept-legal")


@router.get("/contract-usage")
def contract_usage(days: int = Query(default=7, ge=1, le=90)):
    data = _leer_uso_contrato().get("by_date", {})
    fechas = sorted(data.keys(), reverse=True)[:days]

    rows = []
    total_v2 = 0
    total_legacy = 0

    for fecha in fechas:
        row = data.get(fecha, {})
        v2 = int(row.get("v2", 0) or 0)
        legacy = int(row.get("legacy", 0) or 0)
        total = v2 + legacy
        legacy_ratio = (legacy / total) if total > 0 else 0.0

        total_v2 += v2
        total_legacy += legacy
        rows.append(
            {
                "date": fecha,
                "v2": v2,
                "legacy": legacy,
                "total": total,
                "legacy_ratio": round(legacy_ratio, 4),
            }
        )

    total_calls = total_v2 + total_legacy
    ratio_global = (total_legacy / total_calls) if total_calls > 0 else 0.0

    return {
        "ok": True,
        "data": {
            "days": days,
            "rows": rows,
            "summary": {
                "v2": total_v2,
                "legacy": total_legacy,
                "total": total_calls,
                "legacy_ratio": round(ratio_global, 4),
            },
        },
        "meta": {
            "contract_version": "v2",
            "sunset": AUTH_SUNSET_DATE,
        },
    }


@router.get("/me")
def me(
    response: Response,
    version: str = Query(default="v2", pattern="^(v2|legacy)$"),
    authorization: str | None = Header(default=None),
    store: AuthStore = Depends(obtener_auth_store),
):
    token = _extraer_bearer_token(authorization)
    payload = _validar_access_token(token, store)

    user = store.obtener_usuario_por_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    _validar_aceptacion_legal_vigente(user)

    payload_legacy = {
        "ok": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"],
            "legal_accepted": bool(user.get("legal_accepted_version")),
            "legal_accepted_version": user.get("legal_accepted_version"),
            "legal_accepted_at": user.get("legal_accepted_at"),
        },
    }
    return _respuesta_contrato(payload_legacy, version, response, "me")

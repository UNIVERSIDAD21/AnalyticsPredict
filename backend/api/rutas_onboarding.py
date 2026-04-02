# -*- coding: utf-8 -*-
"""Rutas B2: onboarding persistente + eventos de conversión."""

from __future__ import annotations

from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, Header, HTTPException, status

from db import obtener_pool

from esquemas.onboarding import OnboardingEventoRequest, OnboardingPerfilRequest
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.onboarding_store import OnboardingStore, obtener_onboarding_store

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


def _extraer_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Bearer requerido")
    return authorization.split(" ", 1)[1].strip()


def _actualizar_usuario_desde_onboarding(user_id: str, perfil: dict) -> None:
    """Persiste perfil de onboarding en tabla usuarios (fuente principal)."""
    with obtener_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE usuarios
                SET nombre = %s,
                    bankroll_inicial = COALESCE(%s, bankroll_inicial),
                    bankroll_actual = COALESCE(%s, bankroll_actual),
                    preferencias = COALESCE(preferencias, '{}'::jsonb) || %s::jsonb,
                    actualizado_en = NOW()
                WHERE id = %s
                """,
                [
                    perfil["nombre"],
                    perfil.get("bankroll_referencial"),
                    perfil.get("bankroll_referencial"),
                    json.dumps(
                        {
                            "onboarding": {
                                "objetivo_principal": perfil["objetivo_principal"],
                                "deporte_preferido": perfil["deporte_preferido"],
                                "frecuencia": perfil["frecuencia"],
                                "completado": True,
                            }
                        },
                        ensure_ascii=False,
                    ),
                    user_id,
                ],
            )


def _resolver_usuario_app_por_email(email: str) -> dict | None:
    """Resuelve el usuario canónico en tabla usuarios para evitar re-onboarding por IDs desalineados."""
    with obtener_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, preferencias
                FROM usuarios
                WHERE lower(email) = lower(%s)
                LIMIT 1
                """,
                [email],
            )
            row = cur.fetchone()
            if not row:
                return None

            user_id = str(row[0])
            preferencias = row[1] or {}
            onboarding = preferencias.get("onboarding") if isinstance(preferencias, dict) else None
            completado = bool(onboarding.get("completado")) if isinstance(onboarding, dict) else False
            return {
                "id": user_id,
                "onboarding_completado": completado,
            }


def _obtener_estado_onboarding_robusto(
    onboarding_store: OnboardingStore,
    auth_user_id: str,
    email: str,
) -> tuple[dict | None, str, bool]:
    """Busca onboarding por id canónico y fallback por auth id para evitar repeticiones."""
    usuario_app = _resolver_usuario_app_por_email(email)
    canonical_id = str(usuario_app["id"]) if usuario_app else str(auth_user_id)
    flag_completado = bool(usuario_app.get("onboarding_completado")) if usuario_app else False

    estado = onboarding_store.obtener_onboarding(canonical_id)
    if not estado and str(auth_user_id) != canonical_id:
        estado = onboarding_store.obtener_onboarding(auth_user_id)

    if not estado and flag_completado:
        estado = {
            "completado": True,
            "updated_at": None,
            "perfil": None,
        }

    return estado, canonical_id, flag_completado


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

    user = auth_store.obtener_usuario_por_id(payload["sub"])
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
    estado, _canonical_id, _flag = _obtener_estado_onboarding_robusto(
        onboarding_store=onboarding_store,
        auth_user_id=str(user["id"]),
        email=str(user.get("email") or ""),
    )

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
    perfil = payload.model_dump()

    estado_prev, canonical_id, _ = _obtener_estado_onboarding_robusto(
        onboarding_store=onboarding_store,
        auth_user_id=str(user["id"]),
        email=str(user.get("email") or ""),
    )
    if estado_prev and bool(estado_prev.get("completado")):
        return {
            "ok": True,
            "data": estado_prev,
        }

    _actualizar_usuario_desde_onboarding(canonical_id, perfil)
    estado = onboarding_store.guardar_onboarding(canonical_id, perfil)
    # Compatibilidad defensiva: guardar también por auth_user_id si difiere.
    if str(user["id"]) != canonical_id:
        onboarding_store.guardar_onboarding(str(user["id"]), perfil)

    onboarding_store.registrar_evento(
        user_id=canonical_id,
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
    _estado, canonical_id, _ = _obtener_estado_onboarding_robusto(
        onboarding_store=onboarding_store,
        auth_user_id=str(user["id"]),
        email=str(user.get("email") or ""),
    )

    onboarding_store.registrar_evento(
        user_id=canonical_id,
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

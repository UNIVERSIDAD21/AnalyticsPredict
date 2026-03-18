# -*- coding: utf-8 -*-
"""B5: rutas de chat contextual (motor local + mock inteligente)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from esquemas.chat import ChatMensajeRequest, ChatResetRequest
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.chat_contexto import (
    ChatContextoStore,
    compactar_ventana_con_resumen,
    obtener_chat_contexto_store,
)
from servicios.chat_provider import ChatProvider, obtener_chat_provider
from servicios.notificaciones_store import NotificacionesStore, obtener_notificaciones_store
from servicios.onboarding_store import OnboardingStore, obtener_onboarding_store

router = APIRouter(prefix="/api/chat", tags=["Chat"])


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


@router.post("/mensaje")
def enviar_mensaje_chat(
    payload: ChatMensajeRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    chat_store: ChatContextoStore = Depends(obtener_chat_contexto_store),
    notif_store: NotificacionesStore = Depends(obtener_notificaciones_store),
    onboarding_store: OnboardingStore = Depends(obtener_onboarding_store),
    provider: ChatProvider = Depends(obtener_chat_provider),
):
    user = _usuario_actual(authorization, auth_store)

    chat_store.registrar_mensaje(user_id=user["id"], role="user", contenido=payload.mensaje)

    ventana_completa = chat_store.obtener_ventana(user_id=user["id"], limit=max(60, payload.limite_contexto * 5))
    ventana, resumen_contexto = compactar_ventana_con_resumen(ventana_completa, limite=payload.limite_contexto)

    contexto_negocio = {"resumen_contexto": resumen_contexto}
    try:
        metricas_entrega = notif_store.resumen_envios(str(user["id"]), horas=24)
        contexto_negocio["tasa_entrega_pct"] = metricas_entrega.get("tasa_entrega_pct")
    except Exception:
        pass

    try:
        kpis_onboarding = onboarding_store.obtener_kpis_conversion()
        contexto_negocio["completion_rate_pct"] = kpis_onboarding.get("completion_rate_pct")
        contexto_negocio["time_to_value_minutes_avg"] = kpis_onboarding.get("time_to_value_minutes_avg")
    except Exception:
        pass

    respuesta = provider.responder(payload.mensaje, ventana, contexto_negocio=contexto_negocio)

    msg_assistant = chat_store.registrar_mensaje(user_id=user["id"], role="assistant", contenido=respuesta)

    return {
        "ok": True,
        "data": {
            "reply": msg_assistant["contenido"],
            "window_size": len(ventana),
            "summary_applied": bool(resumen_contexto),
            "provider": provider.name,
        },
    }


@router.get("/historial")
def obtener_historial(
    limit: int = 20,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    chat_store: ChatContextoStore = Depends(obtener_chat_contexto_store),
):
    user = _usuario_actual(authorization, auth_store)
    items = chat_store.obtener_ventana(user_id=user["id"], limit=limit)
    return {"ok": True, "data": {"items": items, "total": len(items)}}


@router.post("/reset")
def reset_chat(
    payload: ChatResetRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    chat_store: ChatContextoStore = Depends(obtener_chat_contexto_store),
):
    user = _usuario_actual(authorization, auth_store)
    chat_store.limpiar(user_id=user["id"])
    return {"ok": True, "data": {"reset": True, "motivo": payload.motivo}}

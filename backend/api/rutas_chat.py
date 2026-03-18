# -*- coding: utf-8 -*-
"""B5: rutas de chat contextual (motor local + mock inteligente)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from esquemas.chat import ChatMensajeRequest, ChatResetRequest
from servicios.auth_seguridad import decodificar_y_validar_token, obtener_secreto_auth
from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.chat_contexto import ChatContextoStore, generar_respuesta_local, obtener_chat_contexto_store

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
):
    user = _usuario_actual(authorization, auth_store)

    chat_store.registrar_mensaje(user_id=user["id"], role="user", contenido=payload.mensaje)

    ventana = chat_store.obtener_ventana(user_id=user["id"], limit=payload.limite_contexto)
    respuesta = generar_respuesta_local(payload.mensaje, ventana)

    msg_assistant = chat_store.registrar_mensaje(user_id=user["id"], role="assistant", contenido=respuesta)

    return {
        "ok": True,
        "data": {
            "reply": msg_assistant["contenido"],
            "window_size": len(ventana),
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

# -*- coding: utf-8 -*-
"""Rutas B4: preferencias y envío de notificaciones por email (MVP)."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, Query

from .dependencias import UsuarioActual, obtener_usuario_actual
from esquemas.notificaciones import PreferenciasNotificacionRequest, EnviarPruebaRequest
from servicios.notificaciones_store import NotificacionesStore, obtener_notificaciones_store

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])


def _enviar_correo(destinatario: str, asunto: str, mensaje: str) -> None:
    host = os.getenv("AUTH_SMTP_HOST", "").strip()
    port = int(os.getenv("AUTH_SMTP_PORT", "587"))
    user = os.getenv("AUTH_SMTP_USER", "").strip()
    password = os.getenv("AUTH_SMTP_PASSWORD", "").strip()
    from_email = os.getenv("AUTH_SMTP_FROM", "no-reply@analyticspredict.local").strip()
    starttls = os.getenv("AUTH_SMTP_STARTTLS", "true").strip().lower() == "true"
    ssl = os.getenv("AUTH_SMTP_SSL", "false").strip().lower() == "true"

    if not host:
        raise RuntimeError("SMTP no configurado (AUTH_SMTP_HOST)")

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = from_email
    msg["To"] = destinatario
    msg.set_content(mensaje)

    if ssl:
        with smtplib.SMTP_SSL(host, port, timeout=10) as server:
            if user:
                server.login(user, password)
            server.send_message(msg)
        return

    with smtplib.SMTP(host, port, timeout=10) as server:
        if starttls:
            server.starttls()
        if user:
            server.login(user, password)
        server.send_message(msg)


@router.get("/preferencias")
def obtener_preferencias(
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    data = store.obtener_preferencias(str(usuario.id))
    return {"ok": True, "data": data}


@router.put("/preferencias")
def guardar_preferencias(
    payload: PreferenciasNotificacionRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    data = store.guardar_preferencias(str(usuario.id), payload.model_dump())
    return {"ok": True, "data": data}


@router.post("/enviar-prueba")
def enviar_prueba(
    payload: EnviarPruebaRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    if not usuario.email:
        raise HTTPException(status_code=400, detail="X-Usuario-Email es requerido para envío de prueba")

    prefs = store.obtener_preferencias(str(usuario.id))["preferencias"]
    if not prefs.get("email_habilitado", True):
        envio = store.registrar_envio(str(usuario.id), "email", payload.tipo, "omitido", "email_habilitado=false")
        return {"ok": True, "data": envio}

    if not prefs.get(payload.tipo, True):
        envio = store.registrar_envio(str(usuario.id), "email", payload.tipo, "omitido", f"{payload.tipo}=false")
        return {"ok": True, "data": envio}

    asunto = payload.asunto or f"[AnalyticsPredict] Prueba de notificación ({payload.tipo})"
    mensaje = payload.mensaje or (
        "Notificación de prueba enviada correctamente desde B4.\n\n"
        f"Tipo: {payload.tipo}\n"
        f"Usuario: {usuario.id}\n"
    )

    try:
        _enviar_correo(usuario.email, asunto, mensaje)
        envio = store.registrar_envio(str(usuario.id), "email", payload.tipo, "enviado")
    except Exception as exc:
        envio = store.registrar_envio(str(usuario.id), "email", payload.tipo, "fallido", str(exc))
        raise HTTPException(status_code=500, detail=f"No se pudo enviar correo: {exc}") from exc

    return {"ok": True, "data": envio}


@router.get("/historial")
def listar_historial(
    limit: int = Query(20, ge=1, le=100),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    rows = store.listar_envios(str(usuario.id), limit=limit)
    return {"ok": True, "data": {"items": rows, "total": len(rows)}}

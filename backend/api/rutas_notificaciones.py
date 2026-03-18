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
TIPOS_SCHEDULER = ("alertas_partidos", "alertas_suscripcion", "resumen_semanal")


def _max_intentos_por_tipo(tipo: str) -> int:
    overrides = {
        "alertas_partidos": int(os.getenv("NOTIF_MAX_INTENTOS_ALERTAS_PARTIDOS", "3")),
        "alertas_suscripcion": int(os.getenv("NOTIF_MAX_INTENTOS_ALERTAS_SUSCRIPCION", "4")),
        "resumen_semanal": int(os.getenv("NOTIF_MAX_INTENTOS_RESUMEN_SEMANAL", "2")),
    }
    return max(1, min(8, int(overrides.get(tipo, 3))))


def _plantilla_notificacion(tipo: str, usuario_id: str) -> tuple[str, str]:
    if tipo == "alertas_partidos":
        return (
            "[AnalyticsPredict] Partidos relevantes para hoy",
            (
                "Detectamos partidos potencialmente relevantes según tus preferencias.\n"
                "Revisa el dashboard para detalle de mercados y contexto.\n\n"
                f"Usuario: {usuario_id}\n"
            ),
        )
    if tipo == "alertas_suscripcion":
        return (
            "[AnalyticsPredict] Estado de suscripción",
            (
                "Actualización de estado de suscripción disponible.\n"
                "Verifica plan activo y cambios recientes en tu dashboard.\n\n"
                f"Usuario: {usuario_id}\n"
            ),
        )

    return (
        "[AnalyticsPredict] Resumen semanal",
        (
            "Resumen semanal listo: revisa rendimiento, win-rate y acciones recomendadas.\n\n"
            f"Usuario: {usuario_id}\n"
        ),
    )


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


@router.post("/encolar-prueba")
def encolar_prueba(
    payload: EnviarPruebaRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    if not usuario.email:
        raise HTTPException(status_code=400, detail="X-Usuario-Email es requerido para encolar")

    prefs = store.obtener_preferencias(str(usuario.id))["preferencias"]
    if not prefs.get("email_habilitado", True) or not prefs.get(payload.tipo, True):
        envio = store.registrar_envio(str(usuario.id), "email", payload.tipo, "omitido", "preferencias deshabilitan envío")
        return {"ok": True, "data": {"encolado": False, "envio": envio}}

    asunto = payload.asunto or f"[AnalyticsPredict] Notificación ({payload.tipo})"
    mensaje = payload.mensaje or (
        "Notificación encolada correctamente desde B4.\n\n"
        f"Tipo: {payload.tipo}\n"
        f"Usuario: {usuario.id}\n"
    )

    job = store.encolar_notificacion(
        user_id=str(usuario.id),
        email=usuario.email,
        tipo=payload.tipo,
        asunto=asunto,
        mensaje=mensaje,
        max_intentos=_max_intentos_por_tipo(payload.tipo),
    )
    return {"ok": True, "data": {"encolado": True, "job": job}}


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


@router.post("/scheduler/encolar")
def scheduler_encolar(
    tipo: str = Query("todos", description="alertas_partidos|alertas_suscripcion|resumen_semanal|todos"),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    if not usuario.email:
        raise HTTPException(status_code=400, detail="X-Usuario-Email es requerido para scheduler")

    prefs = store.obtener_preferencias(str(usuario.id))["preferencias"]

    tipos = list(TIPOS_SCHEDULER) if tipo == "todos" else [tipo]
    for t in tipos:
        if t not in TIPOS_SCHEDULER:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {t}")

    encoladas = []
    omitidas = []
    for t in tipos:
        if not prefs.get("email_habilitado", True) or not prefs.get(t, False):
            envio = store.registrar_envio(str(usuario.id), "email", t, "omitido", "preferencias deshabilitan scheduler")
            omitidas.append(envio)
            continue

        asunto, mensaje = _plantilla_notificacion(t, str(usuario.id))
        job = store.encolar_notificacion(
            user_id=str(usuario.id),
            email=usuario.email,
            tipo=t,
            asunto=asunto,
            mensaje=mensaje,
            max_intentos=_max_intentos_por_tipo(t),
        )
        encoladas.append(job)

    return {"ok": True, "data": {"encoladas": encoladas, "omitidas": omitidas, "total": len(encoladas)}}


@router.post("/procesar-cola")
def procesar_cola(
    max_items: int = Query(20, ge=1, le=100),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    jobs = store.obtener_pendientes(user_id=str(usuario.id), limit=max_items)
    enviados = 0
    reprogramados = 0
    fallidos = 0

    for job in jobs:
        try:
            _enviar_correo(job["email"], job["asunto"], job["mensaje"])
            store.marcar_procesada(int(job["id"]))
            store.registrar_envio(str(usuario.id), "email", job["tipo"], "enviado")
            enviados += 1
        except Exception as exc:
            intentos = int(job.get("intentos") or 0) + 1
            max_intentos = int(job.get("max_intentos") or 3)
            estado = store.marcar_fallida(int(job["id"]), intentos=intentos, max_intentos=max_intentos, detalle=str(exc))
            store.registrar_envio(str(usuario.id), "email", job["tipo"], estado, str(exc))
            if estado == "pendiente":
                reprogramados += 1
            else:
                fallidos += 1

    return {
        "ok": True,
        "data": {
            "total_tomados": len(jobs),
            "enviados": enviados,
            "reprogramados": reprogramados,
            "fallidos": fallidos,
        },
    }


@router.get("/metricas-entrega")
def metricas_entrega(
    horas: int = Query(24, ge=1, le=168),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    data = store.resumen_envios(str(usuario.id), horas=horas)
    return {"ok": True, "data": data}


@router.get("/historial")
def listar_historial(
    limit: int = Query(20, ge=1, le=100),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
    store: NotificacionesStore = Depends(obtener_notificaciones_store),
):
    rows = store.listar_envios(str(usuario.id), limit=limit)
    return {"ok": True, "data": {"items": rows, "total": len(rows)}}

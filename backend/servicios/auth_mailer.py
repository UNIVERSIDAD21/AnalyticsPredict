# -*- coding: utf-8 -*-
"""Servicio de envío de correos para recuperación de contraseña."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


class AuthMailerError(RuntimeError):
    pass


def _obtener_config_smtp() -> dict:
    return {
        "host": os.getenv("AUTH_SMTP_HOST", "").strip(),
        "port": int(os.getenv("AUTH_SMTP_PORT", "587")),
        "user": os.getenv("AUTH_SMTP_USER", "").strip(),
        "password": os.getenv("AUTH_SMTP_PASSWORD", "").strip(),
        "from_email": os.getenv("AUTH_SMTP_FROM", "no-reply@analyticspredict.local").strip(),
        "starttls": os.getenv("AUTH_SMTP_STARTTLS", "true").strip().lower() == "true",
        "ssl": os.getenv("AUTH_SMTP_SSL", "false").strip().lower() == "true",
    }


def enviar_correo_recuperacion(destinatario: str, token: str) -> None:
    """Envía correo de recuperación usando SMTP."""
    frontend_url = os.getenv("AUTH_FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_url = f"{frontend_url}/login"

    cfg = _obtener_config_smtp()
    if not cfg["host"]:
        raise AuthMailerError("AUTH_SMTP_HOST no configurado")

    msg = EmailMessage()
    msg["Subject"] = "Recuperación de contraseña - AnalyticsPredict"
    msg["From"] = cfg["from_email"]
    msg["To"] = destinatario
    msg.set_content(
        """
Recibimos una solicitud para restablecer tu contraseña.

Usa este token temporal:
{token}

Luego abre:
{reset_url}

y pega el token en la sección de restablecimiento.

Si no solicitaste este cambio, ignora este mensaje.
        """.strip().format(token=token, reset_url=reset_url)
    )

    try:
        if cfg["ssl"]:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=10) as server:
                if cfg["user"]:
                    server.login(cfg["user"], cfg["password"])
                server.send_message(msg)
            return

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
            if cfg["starttls"]:
                server.starttls()
            if cfg["user"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    except Exception as exc:
        raise AuthMailerError(f"Error enviando correo de recuperación: {exc}") from exc

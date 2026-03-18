# -*- coding: utf-8 -*-
"""Esquemas B4 para preferencias y notificaciones."""

from __future__ import annotations

from pydantic import BaseModel


class PreferenciasNotificacionRequest(BaseModel):
    email_habilitado: bool = True
    alertas_partidos: bool = True
    alertas_suscripcion: bool = True
    resumen_semanal: bool = False


class EnviarPruebaRequest(BaseModel):
    tipo: str = "alertas_partidos"
    asunto: str | None = None
    mensaje: str | None = None

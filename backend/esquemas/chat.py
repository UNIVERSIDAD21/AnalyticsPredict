# -*- coding: utf-8 -*-
"""Esquemas B5 para chat contextual."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMensajeRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=4000)
    limite_contexto: int = Field(default=12, ge=4, le=30)


class ChatResetRequest(BaseModel):
    motivo: str | None = Field(default=None, max_length=240)

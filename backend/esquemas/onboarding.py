# -*- coding: utf-8 -*-
"""Esquemas de onboarding y eventos de conversión (B2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ObjetivoPrincipal = Literal["rentabilidad", "disciplina", "aprendizaje"]
DeportePreferido = Literal["baloncesto", "futbol", "ambos"]
FrecuenciaUso = Literal["diaria", "semanal", "ocasional"]
EventoConversion = Literal[
    "onboarding_started",
    "onboarding_completed",
    "dashboard_viewed",
]


class OnboardingPerfilRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    objetivo_principal: ObjetivoPrincipal
    deporte_preferido: DeportePreferido
    frecuencia: FrecuenciaUso
    bankroll_referencial: float | None = Field(default=None, ge=0)


class OnboardingEventoRequest(BaseModel):
    event_name: EventoConversion
    event_ts: datetime | None = None
    metadata: dict | None = None

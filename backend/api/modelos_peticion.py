# -*- coding: utf-8 -*-
"""
modelos_peticion.py — Modelos de entrada para la API.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PeticionAnalisis(BaseModel):
    """Solicitud para analizar un partido."""

    equipo_local: str = Field(..., description="Equipo que juega de local")
    equipo_visitante: str = Field(..., description="Equipo que juega de visitante")
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    linea: float = Field(..., gt=0, description="Línea de puntos a analizar")
    cuota: Optional[float] = Field(None, gt=1.0, description="Cuota decimal opcional")

    @field_validator("equipo_local", "equipo_visitante")
    @classmethod
    def validar_equipo(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("El nombre del equipo no puede estar vacío.")
        return valor


class PeticionAnalisisEnVivo(PeticionAnalisis):
    """Solicitud para análisis en vivo con marcadores reales."""

    marcador_q1: Optional[str] = Field(None, description="Marcador Q1 (ej: 28-32)")
    marcador_q2: Optional[str] = Field(None, description="Marcador Q2 (ej: 25-24)")
    marcador_q3: Optional[str] = Field(None, description="Marcador Q3 (ej: 30-28)")
    peso_en_vivo: float = Field(0.5, ge=0.0, le=1.0, description="Peso del ajuste en vivo")

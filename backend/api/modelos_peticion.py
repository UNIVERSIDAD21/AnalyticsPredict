# -*- coding: utf-8 -*-
"""
modelos_peticion.py — Modelos de entrada para la API.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

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


class PeticionCrearApuesta(BaseModel):
    """Solicitud para guardar una apuesta en la bitácora."""

    partido_id: Optional[str] = Field(None, description="ID opcional del partido")
    equipo_local: str = Field(..., min_length=1, description="Nombre del equipo local")
    equipo_visitante: str = Field(..., min_length=1, description="Nombre del equipo visitante")
    fecha_partido: Optional[date] = Field(None, description="Fecha del partido")
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    lado: Literal["OVER", "UNDER"]
    linea: Decimal = Field(..., gt=0)
    cuota: Decimal = Field(..., ge=Decimal("1.01"))
    stake: Decimal = Field(..., gt=0)
    probabilidad_sistema: float = Field(..., ge=0.0, le=1.0)
    confianza_sistema: Literal["ALTA", "MEDIA", "BAJA"]
    valor_esperado: Optional[float] = None
    prediccion_media: Optional[float] = None
    prediccion_desviacion: Optional[float] = None
    razones: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("equipo_local", "equipo_visitante")
    @classmethod
    def validar_equipo(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre del equipo no puede estar vacío.")
        return valor.strip()


class PeticionActualizarResultado(BaseModel):
    """Solicitud para actualizar el resultado de una apuesta."""

    resultado: Literal["GANADA", "PERDIDA", "PUSH", "ANULADA"]
    puntos_reales: Optional[Decimal] = Field(None, ge=0)

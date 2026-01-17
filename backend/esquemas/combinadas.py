# -*- coding: utf-8 -*-
"""
esquemas/combinadas.py — Esquemas Pydantic para combinadas.
"""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SeleccionCombinadaBase(BaseModel):
    """Datos base de una selección dentro de una combinada."""

    partido_id: Optional[UUID] = Field(None, description="ID del partido")
    equipo_local: str = Field(..., min_length=1)
    equipo_visitante: str = Field(..., min_length=1)
    fecha_partido: Optional[date] = Field(None)
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    lado: Literal["OVER", "UNDER"]
    linea: float = Field(..., gt=0)
    cuota: float = Field(..., gt=1.0)
    cuota_over: Optional[float] = Field(None, gt=1.0)
    cuota_under: Optional[float] = Field(None, gt=1.0)
    probabilidad_sistema: float = Field(..., ge=0.0, le=1.0)
    prediccion_media: Optional[float] = None
    prediccion_desviacion: Optional[float] = None
    confianza_sistema: Optional[Literal["ALTA", "MEDIA", "BAJA"]] = None
    valor_esperado_individual: Optional[float] = None
    razones: Optional[list] = None

    @field_validator("equipo_local", "equipo_visitante")
    @classmethod
    def validar_equipo(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre del equipo no puede estar vacío.")
        return valor


class SeleccionCombinadaCrear(SeleccionCombinadaBase):
    """Entrada para crear una selección de combinada."""


class SeleccionCombinada(SeleccionCombinadaBase):
    """Salida de una selección de combinada."""

    id: UUID
    combinada_id: UUID
    grupo_correlacion: Optional[int] = None
    factor_ajuste_correlacion: Optional[float] = None
    resultado: Optional[Literal["PENDIENTE", "GANADA", "PERDIDA", "PUSH", "ANULADA"]] = None
    puntos_reales: Optional[float] = None
    fecha_resolucion: Optional[str] = None
    orden: int


class PeticionCrearCombinada(BaseModel):
    """Solicitud para crear una combinada."""

    stake: float = Field(..., gt=0)
    cuota_total: float = Field(..., gt=1.0)
    selecciones: List[SeleccionCombinadaCrear]
    notas: Optional[str] = None
    etiquetas: Optional[List[str]] = None


class Combinada(BaseModel):
    """Modelo completo de combinada."""

    id: UUID
    usuario_id: UUID
    stake: float
    cuota_total: float
    n_selecciones: int
    probabilidad_independiente: float
    factor_correlacion: float
    probabilidad_ajustada: float
    cuota_justa_sistema: Optional[float] = None
    edge_combinada: Optional[float] = None
    valor_esperado: Optional[float] = None
    confianza_sistema: Optional[str] = None
    tiene_mismo_partido: bool
    n_partidos_unicos: int
    advertencias: Optional[List[str]] = None
    correlaciones_detectadas: Optional[List[dict]] = None
    resultado: Literal["PENDIENTE", "GANADA", "PERDIDA", "PUSH", "ANULADA"]
    ganancia: float
    selecciones_ganadas: int
    selecciones_perdidas: int
    selecciones_push: int
    selecciones_pendientes: int
    fecha_resolucion: Optional[str] = None
    notas: Optional[str] = None
    etiquetas: Optional[List[str]] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    selecciones: Optional[List[SeleccionCombinada]] = None


class RespuestaCombinada(BaseModel):
    """Respuesta con una combinada."""

    exito: bool
    combinada: Combinada


class RespuestaListaCombinadas(BaseModel):
    """Respuesta al listar combinadas."""

    exito: bool
    total: int
    pagina: int
    total_paginas: int
    combinadas: List[Combinada]


class PeticionActualizarResultadoCombinada(BaseModel):
    """Solicitud para actualizar el resultado de una combinada."""

    resultado: Literal["GANADA", "PERDIDA", "PUSH", "ANULADA"] = Field(
        ..., description="Resultado de la combinada"
    )

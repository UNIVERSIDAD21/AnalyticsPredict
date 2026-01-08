# -*- coding: utf-8 -*-
"""
modelos_respuesta.py — Modelos de salida para la API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RespuestaBase(BaseModel):
    """Respuesta base para la API."""
    exito: bool = Field(..., description="Indica si la operación fue exitosa")


class RespuestaEquipos(RespuestaBase):
    """Respuesta para el listado de equipos."""
    total: int
    equipos: List[Dict[str, Any]]


class RespuestaAnalisis(RespuestaBase):
    """Respuesta para el análisis de partido."""
    datos: Dict[str, Any]
    advertencias: Optional[List[str]] = None


class TemporadaDisponible(BaseModel):
    """Temporada disponible para filtrar."""
    id: str
    nombre: str


class RespuestaEstadisticasEquipos(RespuestaBase):
    """Respuesta para estadísticas de equipos."""
    fecha_actualizacion: str
    equipos: List[Dict[str, Any]]
    temporadas_disponibles: List[TemporadaDisponible] = []
    temporada_actual: Optional[str] = None


class RespuestaTemporadasEquipos(RespuestaBase):
    """Respuesta para temporadas disponibles por equipos."""

    temporadas: List[TemporadaDisponible] = []


class PuntosPartidoHistorial(BaseModel):
    """Puntos por cuarto y total."""

    q1: int
    q2: int
    q3: int
    q4: int
    ot: int
    total: int


class PartidoHistorial(BaseModel):
    """Modelo de partido para historial."""

    id: str
    fecha: str
    temporada: Optional[str] = None
    equipo_local: str
    local_abr: str
    equipo_visitante: str
    visitante_abr: str
    ubicacion_equipo: str
    puntos_equipo: PuntosPartidoHistorial
    puntos_rival: PuntosPartidoHistorial
    resultado: str


class InfoEquipoHistorial(BaseModel):
    """Información básica del equipo en historial."""

    id: str
    nombre: str
    abreviatura: str
    logo_url: Optional[str] = None


class FiltrosDisponiblesHistorial(BaseModel):
    """Filtros disponibles para historial."""

    temporadas: List[Dict[str, str]]


class RespuestaHistorialEquipo(RespuestaBase):
    """Respuesta para historial de partidos de un equipo."""

    equipo: InfoEquipoHistorial
    total_partidos: int
    partidos: List[PartidoHistorial]
    filtros_disponibles: FiltrosDisponiblesHistorial


class Apuesta(BaseModel):
    """Modelo de salida para una apuesta."""

    id: str
    usuario_id: str
    partido_id: Optional[str] = None
    equipo_local: str
    equipo_visitante: str
    fecha_partido: Optional[str] = None
    mercado: str
    lado: str
    linea: float
    cuota: float
    stake: float
    probabilidad_sistema: Optional[float] = None
    confianza_sistema: Optional[str] = None
    valor_esperado: Optional[float] = None
    prediccion_media: Optional[float] = None
    prediccion_desviacion: Optional[float] = None
    razones: Optional[Any] = None
    resultado: str
    puntos_reales: Optional[float] = None
    ganancia: float
    fecha_resolucion: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None


class RespuestaApuesta(RespuestaBase):
    """Respuesta para una apuesta individual."""

    apuesta: Apuesta


class RespuestaListaApuestas(RespuestaBase):
    """Respuesta para listar apuestas."""

    total: int
    pagina: int
    total_paginas: int
    apuestas: List[Apuesta]


class RespuestaResumenApuestas(RespuestaBase):
    """Respuesta para resumen de apuestas."""

    resumen: Dict[str, Any]

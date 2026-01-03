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

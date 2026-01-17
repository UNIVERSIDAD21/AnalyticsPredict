# -*- coding: utf-8 -*-
"""analisis_contextual.py — Esquemas Pydantic para contexto y ajustes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContextoH2HSchema(BaseModel):
    total_partidos: int
    victorias_equipo: int
    victorias_rival: int
    promedio_total: float
    promedio_equipo: float
    promedio_rival: float
    tendencia_over: float
    ultimo_enfrentamiento: Optional[Dict[str, Any]] = None
    partidos: List[Dict[str, Any]] = Field(default_factory=list)


class ContextoFormaSchema(BaseModel):
    ultimos_n: int
    victorias: int
    derrotas: int
    racha: str
    ppg: float
    opp_ppg: float
    net_rating: float
    ppg_temporada: float
    diferencia_vs_temporada: float
    tendencia: str


class ContextoDescansoSchema(BaseModel):
    dias_descanso: int
    es_back_to_back: bool
    ultimo_partido: Optional[Dict[str, Any]] = None
    distancia_viaje_km: Optional[float] = None


class ContextoCompletoSchema(BaseModel):
    h2h: Optional[ContextoH2HSchema] = None
    forma_equipo: ContextoFormaSchema
    forma_rival: ContextoFormaSchema
    descanso_equipo: ContextoDescansoSchema
    descanso_rival: ContextoDescansoSchema
    stats_temporada_equipo: Dict[str, Any] = Field(default_factory=dict)
    stats_temporada_rival: Dict[str, Any] = Field(default_factory=dict)


class AjusteIndividualSchema(BaseModel):
    factor: str
    valor: float
    direccion: str
    confianza_ajuste: float
    descripcion: str
    datos_soporte: Dict[str, Any] = Field(default_factory=dict)


class ResultadoAjustesSchema(BaseModel):
    ajustes: List[AjusteIndividualSchema] = Field(default_factory=list)
    ajuste_total: float
    ajuste_total_capped: float
    fue_capped: bool
    advertencias: List[str] = Field(default_factory=list)
    confianza_delta: float


class PrediccionAjustadaSchema(BaseModel):
    media_base: float
    desviacion_base: float
    probabilidad_over_base: float
    probabilidad_under_base: float
    media_ajustada: float
    probabilidad_over_ajustada: float
    probabilidad_under_ajustada: float
    ajustes_aplicados: ResultadoAjustesSchema
    confianza_base: str
    confianza_ajustada: str

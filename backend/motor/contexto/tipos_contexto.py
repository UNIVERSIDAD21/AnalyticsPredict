# -*- coding: utf-8 -*-
"""tipos_contexto.py — Dataclasses para contexto contextual."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ContextoH2H:
    """Datos de enfrentamientos directos."""

    total_partidos: int
    victorias_equipo: int
    victorias_rival: int
    promedio_total: float
    promedio_equipo: float
    promedio_rival: float
    tendencia_over: float
    ultimo_enfrentamiento: Optional[Dict[str, Any]]
    partidos: List[Dict[str, Any]]


@dataclass
class ContextoForma:
    """Forma reciente de un equipo."""

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


@dataclass
class ContextoDescanso:
    """Información de descanso del equipo."""

    dias_descanso: int
    es_back_to_back: bool
    ultimo_partido: Optional[Dict[str, Any]]
    distancia_viaje_km: Optional[float]


@dataclass
class ContextoCompleto:
    """Todo el contexto recolectado para un partido."""

    h2h: Optional[ContextoH2H]
    forma_equipo: ContextoForma
    forma_rival: ContextoForma
    descanso_equipo: ContextoDescanso
    descanso_rival: ContextoDescanso
    stats_temporada_equipo: Dict[str, Any]
    stats_temporada_rival: Dict[str, Any]

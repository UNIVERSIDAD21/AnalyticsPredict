# -*- coding: utf-8 -*-
"""
modelos_respuesta.py — Modelos de salida para la API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RespuestaBase(BaseModel):
    """Respuesta base para la API."""
    exito: bool = Field(..., description="Indica si la operación fue exitosa")


class RespuestaEquipos(RespuestaBase):
    """Respuesta para el listado de equipos."""
    total: int
    equipos: List[Dict[str, Any]]


class RespuestaAnalisis(RespuestaBase):
    """Respuesta para el análisis de partido."""
    datos: Dict[str, Any] = Field(
        ...,
        description=(
            "Payload legacy + auditoría avanzada. Campos legacy no se modifican "
            "(ej: equipo_local, equipo_visitante, prediccion, confianza_sistema). "
            "Campos avanzados incluyen mejor_apuesta, candidatos, factores_confianza, "
            "mensaje_apuesta."
        ),
    )
    advertencias: Optional[List[str]] = Field(
        default=None,
        description="Lista de códigos de advertencia deterministas (root).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "exito": True,
                    "datos": {
                        "equipo_local": "Los Angeles Lakers",
                        "equipo_visitante": "Miami Heat",
                        "mercado": "Q1",
                        "linea": 50.5,
                        "lado": "OVER",
                        "prediccion": {
                            "Q1": {
                                "cuarto": "Q1",
                                "media_equipo": 26.0,
                                "desviacion_equipo": 5.0,
                                "rango_equipo": [20.0, 32.0],
                                "media_rival": 25.0,
                                "desviacion_rival": 5.0,
                                "rango_rival": [19.0, 31.0],
                                "media_total": 51.0,
                                "desviacion_total": 7.0,
                                "rango_total": [44.0, 58.0],
                                "linea_analizada": 50.5,
                                "probabilidad_over": 0.55,
                                "probabilidad_under": 0.45,
                                "ganador_probable": "equipo",
                                "probabilidad_ganador": 0.6,
                            }
                        },
                        "confianza_sistema": "MEDIA",
                        "factores_confianza": {
                            "tamano_muestra": "moderado",
                            "volatilidad": "baja",
                            "frescura_datos": "aceptable",
                            "puntaje_total": 3,
                        },
                        "mejor_apuesta": {
                            "mercado": "Q1",
                            "lado": "OVER",
                            "linea": 50.5,
                            "cuota": 1.9,
                            "cuota_over": 1.9,
                            "cuota_under": 1.95,
                            "probabilidad_sistema": 0.55,
                            "edge_real": 0.03,
                            "valor_esperado": 0.06,
                            "devig_metodo": "exacto",
                            "devig_overround": 1.06,
                            "devig_p_mkt_raw": 0.55,
                            "devig_p_mkt_fair": 0.52,
                            "devig_advertencias": [],
                            "edge_raw": 0.03,
                            "prediccion_media": 52.0,
                            "prediccion_desviacion": 6.0,
                            "distancia_z": 0.2,
                            "score_total": 7.5,
                            "score_componentes": {"ev": 2.5},
                            "score_explicacion": "OK",
                            "score_penalizaciones": [],
                            "kelly_full": 0.1,
                            "kelly_fraccional": 0.05,
                            "fraccion_kelly": 0.5,
                            "stake": 50.0,
                            "stake_porcentaje": 5.0,
                            "bankroll_momento": 1000.0,
                            "perfil_riesgo_usado": "MEDIO",
                            "sizing_advertencias": [],
                            "sizing_penalizaciones": {},
                        },
                        "candidatos": [],
                    },
                    "advertencias": None,
                },
                {
                    "exito": True,
                    "datos": {
                        "equipo_local": "Los Angeles Lakers",
                        "equipo_visitante": "Miami Heat",
                        "mercado": "Q2",
                        "linea": 52.5,
                        "lado": "UNDER",
                        "prediccion": {},
                        "confianza_sistema": "BAJA",
                        "factores_confianza": None,
                        "mejor_apuesta": {
                            "mercado": "Q2",
                            "lado": "UNDER",
                            "linea": 52.5,
                            "cuota": 1.85,
                            "cuota_under": 1.85,
                            "probabilidad_sistema": 0.45,
                            "edge_real": 0.0,
                            "valor_esperado": 0.0,
                            "devig_metodo": "estimado",
                            "devig_overround": None,
                            "devig_p_mkt_raw": 0.54,
                            "devig_p_mkt_fair": 0.52,
                            "devig_advertencias": ["DEVIG_ESTIMADO_PENALIZA"],
                            "edge_raw": -0.09,
                            "prediccion_media": 49.0,
                            "prediccion_desviacion": 6.0,
                            "distancia_z": 0.3,
                            "score_total": -2.0,
                            "score_componentes": {"ev": -1.0},
                            "score_explicacion": "SIN_DEVIG",
                            "score_penalizaciones": ["SIN_DEVIG"],
                            "kelly_full": None,
                            "kelly_fraccional": None,
                            "fraccion_kelly": None,
                            "stake": None,
                            "stake_porcentaje": None,
                            "bankroll_momento": None,
                            "perfil_riesgo_usado": None,
                            "sizing_advertencias": [],
                            "sizing_penalizaciones": {},
                        },
                        "candidatos": [],
                    },
                    "advertencias": ["DEVIG_ESTIMADO_PENALIZA"],
                },
                {
                    "exito": True,
                    "datos": {
                        "equipo_local": "Los Angeles Lakers",
                        "equipo_visitante": "Miami Heat",
                        "mercado": "Q3",
                        "linea": 48.5,
                        "lado": "OVER",
                        "prediccion": {},
                        "confianza_sistema": "BAJA",
                        "factores_confianza": None,
                        "mejor_apuesta": None,
                        "mensaje_apuesta": "NO_APTO: EV<=0 o edge_real<=0 en todos los candidatos",
                        "candidatos": [
                            {
                                "mercado": "Q3",
                                "lado": "OVER",
                                "linea": 48.5,
                                "cuota": 1.9,
                                "probabilidad_sistema": 0.5,
                                "edge_real": -0.01,
                                "valor_esperado": -0.02,
                                "devig_metodo": "estimado",
                                "devig_overround": None,
                                "devig_p_mkt_raw": 0.55,
                                "devig_p_mkt_fair": 0.53,
                                "devig_advertencias": ["DEVIG_ESTIMADO_PENALIZA"],
                                "edge_raw": -0.05,
                                "score_total": -100.0,
                                "score_penalizaciones": ["RIESGO_ALTO"],
                            }
                        ],
                    },
                    "advertencias": ["DEVIG_ESTIMADO_PENALIZA"],
                },
            ]
        }
    )


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
    cuota_over: Optional[float] = None
    cuota_under: Optional[float] = None
    stake: float
    probabilidad_sistema: Optional[float] = None
    confianza_sistema: Optional[str] = None
    valor_esperado: Optional[float] = None
    devig_metodo: Optional[str] = None
    devig_overround: Optional[float] = None
    devig_p_mkt_raw: Optional[float] = None
    devig_p_mkt_fair: Optional[float] = None
    devig_advertencias: Optional[List[str]] = None
    edge_real: Optional[float] = None
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

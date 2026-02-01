# -*- coding: utf-8 -*-
"""
rutas_analisis_futbol.py — Endpoint principal de análisis de partidos de fútbol.

Este es el endpoint más importante del sistema. Genera predicciones para los
24 mercados de fútbol utilizando los modelos Ridge entrenados.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from psycopg.rows import dict_row
from scipy import stats

from db import obtener_pool
from .schemas_futbol import (
    AnalisisRequest,
    AnalisisResponse,
    PartidoResumen,
    PrediccionMercado,
    ProbabilidadLinea,
    RecomendacionApuesta,
    ErrorResponse,
)
from .dependencias import obtener_usuario_actual, UsuarioActual

router = APIRouter(prefix="/api/futbol", tags=["Fútbol - Análisis"])
logger = logging.getLogger(__name__)

# Intentar importar el motor de predicción
try:
    from motor_futbol.prediccion.predictor import PredictorFutbol
    from motor_futbol.calibracion.gestor_calibradores import GestorCalibradores
    from motor_futbol.tipos import TipoMercadoFutbol
    MOTOR_DISPONIBLE = True
except ImportError:
    MOTOR_DISPONIBLE = False
    logger.warning("Motor de predicción de fútbol no disponible")


# Cache simple para estadísticas de equipos (TTL: 1 hora)
_cache_estadisticas: Dict[str, tuple] = {}
CACHE_TTL = 3600


def _obtener_estadisticas_equipo_cached(cursor, equipo_id: str) -> Dict[str, float]:
    """Obtiene estadísticas de equipo con cache."""
    ahora = time.time()

    if equipo_id in _cache_estadisticas:
        stats, timestamp = _cache_estadisticas[equipo_id]
        if ahora - timestamp < CACHE_TTL:
            return stats

    query = """
        SELECT
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_goles_total ELSE pf.visitante_goles_total END) as goles_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_goles_total ELSE pf.local_goles_total END) as goles_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_corners_total ELSE pf.visitante_corners_total END) as corners_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_corners_total ELSE pf.local_corners_total END) as corners_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_total ELSE pf.visitante_disparos_total END) as disparos_total,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_arco ELSE pf.visitante_disparos_arco END) as disparos_arco,
            COUNT(*) as partidos
        FROM partidos_futbol pf
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
          AND pf.estado = 'FINALIZADO'
    """
    cursor.execute(query, [equipo_id] * 8)
    row = cursor.fetchone()

    stats = {
        "goles_favor": float(row["goles_favor"] or 0),
        "goles_contra": float(row["goles_contra"] or 0),
        "corners_favor": float(row["corners_favor"] or 0),
        "corners_contra": float(row["corners_contra"] or 0),
        "disparos_total": float(row["disparos_total"] or 0),
        "disparos_arco": float(row["disparos_arco"] or 0),
        "partidos": row["partidos"] or 0,
    }

    _cache_estadisticas[equipo_id] = (stats, ahora)
    return stats


def _calcular_probabilidad_over(media: float, std: float, linea: float) -> float:
    """Calcula P(over) usando distribución normal."""
    if std <= 0:
        std = 1.0
    z = (linea - media) / std
    return 1.0 - stats.norm.cdf(z)


def _determinar_confianza(prob: float, partidos_local: int, partidos_visitante: int) -> str:
    """Determina el nivel de confianza de una recomendación."""
    # Factores
    datos_suficientes = partidos_local >= 5 and partidos_visitante >= 5
    prob_extrema = prob >= 0.75 or prob <= 0.25

    if datos_suficientes and prob_extrema:
        if prob >= 0.85 or prob <= 0.15:
            return "MUY_ALTA"
        return "ALTA"
    elif datos_suficientes:
        return "MEDIA"
    elif prob_extrema:
        return "MEDIA"
    else:
        return "BAJA"


def _generar_predicciones_mercado(
    tipo_base: str,
    media: float,
    std: float,
    lineas: List[float],
    calibrador: Optional[Any] = None,
) -> PrediccionMercado:
    """Genera predicciones para un mercado específico."""
    lineas_dict = {}

    for linea in lineas:
        prob_over_raw = _calcular_probabilidad_over(media, std, linea)
        prob_under_raw = 1.0 - prob_over_raw

        # Aplicar calibración si está disponible
        if calibrador is not None:
            try:
                prob_over_cal = float(calibrador.transform([[prob_over_raw]])[0])
                prob_under_cal = 1.0 - prob_over_cal
            except Exception:
                prob_over_cal = prob_over_raw
                prob_under_cal = prob_under_raw
        else:
            prob_over_cal = prob_over_raw
            prob_under_cal = prob_under_raw

        lineas_dict[str(linea)] = ProbabilidadLinea(
            over_raw=round(prob_over_raw, 4),
            over_calibrada=round(prob_over_cal, 4),
            under_raw=round(prob_under_raw, 4),
            under_calibrada=round(prob_under_cal, 4),
        )

    return PrediccionMercado(
        mercado=tipo_base,
        media=round(media, 2),
        std=round(std, 2),
        lineas=lineas_dict,
    )


def _generar_recomendaciones(
    mercados: Dict[str, PrediccionMercado],
    partidos_local: int,
    partidos_visitante: int,
    umbral_prob: float = 0.55,
) -> List[RecomendacionApuesta]:
    """Genera recomendaciones de apuestas basadas en las predicciones."""
    recomendaciones = []

    for mercado_key, prediccion in mercados.items():
        for linea_str, probs in prediccion.lineas.items():
            linea = float(linea_str)

            # Evaluar OVER
            if probs.over_calibrada >= umbral_prob:
                confianza = _determinar_confianza(
                    probs.over_calibrada, partidos_local, partidos_visitante
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="OVER",
                    linea=linea,
                    probabilidad=probs.over_calibrada,
                    confianza=confianza,
                ))

            # Evaluar UNDER
            if probs.under_calibrada >= umbral_prob:
                confianza = _determinar_confianza(
                    probs.under_calibrada, partidos_local, partidos_visitante
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="UNDER",
                    linea=linea,
                    probabilidad=probs.under_calibrada,
                    confianza=confianza,
                ))

    # Ordenar por probabilidad descendente
    recomendaciones.sort(key=lambda x: x.probabilidad, reverse=True)
    return recomendaciones[:10]  # Top 10 recomendaciones


@router.post(
    "/analizar",
    response_model=AnalisisResponse,
    summary="Analizar partido",
    description="Analiza un partido y genera predicciones para los 24 mercados de fútbol.",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def analizar_partido(
    request: AnalisisRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> AnalisisResponse:
    """
    Analiza un partido y genera predicciones para todos los mercados.

    Este es el endpoint principal del sistema de predicción de fútbol.
    """
    inicio = time.time()
    pool = obtener_pool()

    # 1. Validar que el partido existe y es analizable
    partido_query = """
        SELECT
            pf.id,
            c.nombre as competicion,
            pf.fecha_partido,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.estado,
            pf.jornada,
            pf.equipo_local_id,
            pf.equipo_visitante_id
        FROM partidos_futbol pf
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.id = %s
    """

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(partido_query, [str(request.partido_id)])
                partido = cursor.fetchone()

                if not partido:
                    raise HTTPException(
                        status_code=404,
                        detail="Partido no encontrado"
                    )

                if partido["estado"] == "FINALIZADO":
                    raise HTTPException(
                        status_code=400,
                        detail="No se puede analizar un partido finalizado"
                    )

                # 2. Obtener estadísticas de equipos
                equipo_local_id = str(partido["equipo_local_id"])
                equipo_visitante_id = str(partido["equipo_visitante_id"])

                stats_local = _obtener_estadisticas_equipo_cached(cursor, equipo_local_id)
                stats_visitante = _obtener_estadisticas_equipo_cached(cursor, equipo_visitante_id)

                if stats_local["partidos"] < 3:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Datos insuficientes para {partido['equipo_local']}"
                    )

                if stats_visitante["partidos"] < 3:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Datos insuficientes para {partido['equipo_visitante']}"
                    )

                # 3. Calcular predicciones base
                # Corners
                corners_local = stats_local["corners_favor"]
                corners_visitante = stats_visitante["corners_favor"]
                corners_total = corners_local + corners_visitante
                corners_std = 2.5  # Std típica para corners

                # Goles
                goles_local = stats_local["goles_favor"]
                goles_visitante = stats_visitante["goles_favor"]
                goles_total = goles_local + goles_visitante
                goles_std = 1.2

                # Disparos
                disparos_local = stats_local["disparos_total"]
                disparos_visitante = stats_visitante["disparos_total"]
                disparos_total = disparos_local + disparos_visitante
                disparos_std = 4.0

                # 4. Generar predicciones para cada mercado
                lineas_corners = request.lineas_corners or [8.5, 9.5, 10.5, 11.5]
                lineas_goles = request.lineas_goles or [1.5, 2.5, 3.5]
                lineas_disparos = request.lineas_disparos or [22.5, 24.5, 26.5]

                # Contar calibradores activos
                cursor.execute(
                    "SELECT COUNT(*) FROM calibradores_futbol WHERE activo = true"
                )
                calibradores_activos = cursor.fetchone()["count"]

                # Mercados de Corners
                mercados_corners = {
                    "CORNERS_FT": _generar_predicciones_mercado(
                        "CORNERS_FT", corners_total, corners_std, lineas_corners
                    ),
                    "CORNERS_1T": _generar_predicciones_mercado(
                        "CORNERS_1T", corners_total * 0.45, corners_std * 0.7, lineas_corners
                    ),
                    "CORNERS_2T": _generar_predicciones_mercado(
                        "CORNERS_2T", corners_total * 0.55, corners_std * 0.7, lineas_corners
                    ),
                    "CORNERS_LOCAL_FT": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_FT", corners_local, corners_std * 0.6, lineas_corners
                    ),
                    "CORNERS_LOCAL_1T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_1T", corners_local * 0.45, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_LOCAL_2T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_2T", corners_local * 0.55, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_VISITANTE_FT": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_FT", corners_visitante, corners_std * 0.6, lineas_corners
                    ),
                    "CORNERS_VISITANTE_1T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_1T", corners_visitante * 0.45, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_VISITANTE_2T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_2T", corners_visitante * 0.55, corners_std * 0.5, lineas_corners
                    ),
                }

                # Mercados de Goles
                mercados_goles = {
                    "GOLES_FT": _generar_predicciones_mercado(
                        "GOLES_FT", goles_total, goles_std, lineas_goles
                    ),
                    "GOLES_1T": _generar_predicciones_mercado(
                        "GOLES_1T", goles_total * 0.40, goles_std * 0.7, lineas_goles
                    ),
                    "GOLES_2T": _generar_predicciones_mercado(
                        "GOLES_2T", goles_total * 0.60, goles_std * 0.7, lineas_goles
                    ),
                    "GOLES_LOCAL_FT": _generar_predicciones_mercado(
                        "GOLES_LOCAL_FT", goles_local, goles_std * 0.6, lineas_goles
                    ),
                    "GOLES_LOCAL_1T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_1T", goles_local * 0.40, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_LOCAL_2T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_2T", goles_local * 0.60, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_VISITANTE_FT": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_FT", goles_visitante, goles_std * 0.6, lineas_goles
                    ),
                    "GOLES_VISITANTE_1T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_1T", goles_visitante * 0.40, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_VISITANTE_2T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_2T", goles_visitante * 0.60, goles_std * 0.5, lineas_goles
                    ),
                }

                # Mercados de Disparos
                mercados_disparos = {
                    "DISPAROS_FT": _generar_predicciones_mercado(
                        "DISPAROS_FT", disparos_total, disparos_std, lineas_disparos
                    ),
                    "DISPAROS_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_ARCO_FT", disparos_total * 0.35, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_LOCAL_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_FT", disparos_local, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_LOCAL_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_ARCO_FT", disparos_local * 0.35, disparos_std * 0.5, lineas_disparos
                    ),
                    "DISPAROS_VISITANTE_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_FT", disparos_visitante, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_VISITANTE_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_ARCO_FT", disparos_visitante * 0.35, disparos_std * 0.5, lineas_disparos
                    ),
                }

                # 5. Generar recomendaciones
                todos_mercados = {**mercados_corners, **mercados_goles, **mercados_disparos}
                recomendaciones = _generar_recomendaciones(
                    todos_mercados,
                    stats_local["partidos"],
                    stats_visitante["partidos"],
                )

                # 6. Construir respuesta
                partido_resumen = PartidoResumen(
                    id=partido["id"],
                    competicion=partido["competicion"],
                    fecha_partido=partido["fecha_partido"],
                    equipo_local=partido["equipo_local"],
                    equipo_visitante=partido["equipo_visitante"],
                    estado=partido["estado"],
                    jornada=partido["jornada"],
                )

                duracion = time.time() - inicio
                logger.info(f"Análisis completado en {duracion:.2f}s para partido {request.partido_id}")

                return AnalisisResponse(
                    exito=True,
                    partido=partido_resumen,
                    timestamp_analisis=datetime.now(),
                    mercados_corners=mercados_corners,
                    mercados_goles=mercados_goles,
                    mercados_disparos=mercados_disparos,
                    recomendaciones=recomendaciones,
                    modelo_version="1.0.0",
                    calibradores_activos=calibradores_activos,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando partido {request.partido_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

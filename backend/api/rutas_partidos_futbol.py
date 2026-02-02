# -*- coding: utf-8 -*-
"""
rutas_partidos_futbol.py — Endpoints para gestión de partidos de fútbol.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    PartidoResumen,
    PartidoDetalle,
    ListaPartidosResponse,
    EstadisticasEquipo,
    ErrorResponse,
)

router = APIRouter(prefix="/api/futbol/partidos", tags=["Fútbol - Partidos"])
logger = logging.getLogger(__name__)


def _calcular_estadisticas_equipo(cursor, equipo_id: str) -> Optional[EstadisticasEquipo]:
    """Calcula estadísticas para un equipo."""
    query = """
        SELECT
            COUNT(*) as partidos_jugados,
            SUM(CASE
                WHEN (pf.equipo_local_id = %s AND pf.local_goles_total > pf.visitante_goles_total)
                  OR (pf.equipo_visitante_id = %s AND pf.visitante_goles_total > pf.local_goles_total)
                THEN 1 ELSE 0
            END) as victorias,
            SUM(CASE WHEN pf.local_goles_total = pf.visitante_goles_total THEN 1 ELSE 0 END) as empates,
            SUM(CASE
                WHEN (pf.equipo_local_id = %s AND pf.local_goles_total < pf.visitante_goles_total)
                  OR (pf.equipo_visitante_id = %s AND pf.visitante_goles_total < pf.local_goles_total)
                THEN 1 ELSE 0
            END) as derrotas,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_goles_total ELSE pf.visitante_goles_total END) as goles_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_goles_total ELSE pf.local_goles_total END) as goles_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_corners_total ELSE pf.visitante_corners_total END) as corners_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_corners_total ELSE pf.local_corners_total END) as corners_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_total ELSE pf.visitante_disparos_total END) as disparos_total,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_arco ELSE pf.visitante_disparos_arco END) as disparos_arco
        FROM partidos_futbol pf
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
          AND pf.estado = 'FINALIZADO'
    """
    cursor.execute(query, [equipo_id] * 12)
    stats = cursor.fetchone()

    if not stats or stats["partidos_jugados"] == 0:
        return None

    return EstadisticasEquipo(
        partidos_jugados=stats["partidos_jugados"] or 0,
        victorias=stats["victorias"] or 0,
        empates=stats["empates"] or 0,
        derrotas=stats["derrotas"] or 0,
        goles_favor=round(float(stats["goles_favor"] or 0), 2),
        goles_contra=round(float(stats["goles_contra"] or 0), 2),
        corners_favor=round(float(stats["corners_favor"] or 0), 2),
        corners_contra=round(float(stats["corners_contra"] or 0), 2),
        disparos_total=round(float(stats["disparos_total"] or 0), 2),
        disparos_arco=round(float(stats["disparos_arco"] or 0), 2),
    )


@router.get(
    "/proximos",
    response_model=ListaPartidosResponse,
    summary="Partidos próximos",
    description="Lista partidos programados para los próximos días.",
)
async def listar_partidos_proximos(
    competicion_id: Optional[UUID] = Query(None, description="Filtrar por competición"),
    dias: int = Query(7, ge=1, le=30, description="Días hacia adelante"),
    equipo_id: Optional[UUID] = Query(None, description="Filtrar por equipo"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    tamano: int = Query(20, ge=1, le=100, description="Tamaño de página"),
) -> ListaPartidosResponse:
    """Lista partidos próximos."""
    pool = obtener_pool()

    fecha_inicio = datetime.now()
    fecha_fin = fecha_inicio + timedelta(days=dias)
    estados_programados = ["PROGRAMADO", "SCHEDULED", "PENDIENTE"]

    query = """
        SELECT
            pf.id,
            c.nombre as competicion,
            pf.fecha_partido,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.estado,
            pf.jornada
        FROM partidos_futbol pf
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.fecha_partido >= %s
          AND pf.fecha_partido <= %s
          AND (pf.estado::text = ANY(%s) OR pf.estado IS NULL)
    """
    count_query = """
        SELECT COUNT(*)
        FROM partidos_futbol pf
        WHERE pf.fecha_partido >= %s
          AND pf.fecha_partido <= %s
          AND (pf.estado::text = ANY(%s) OR pf.estado IS NULL)
    """
    params = [fecha_inicio, fecha_fin, estados_programados]
    count_params = [fecha_inicio, fecha_fin, estados_programados]

    if competicion_id:
        query += " AND pf.competicion_id = %s"
        count_query += " AND pf.competicion_id = %s"
        params.append(str(competicion_id))
        count_params.append(str(competicion_id))

    if equipo_id:
        query += " AND (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)"
        count_query += " AND (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)"
        params.extend([str(equipo_id), str(equipo_id)])
        count_params.extend([str(equipo_id), str(equipo_id)])

    query += " ORDER BY pf.fecha_partido ASC"

    # Paginación
    offset = (pagina - 1) * tamano
    query += " LIMIT %s OFFSET %s"
    params.extend([tamano, offset])

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()["count"]

                cursor.execute(query, params)
                filas = cursor.fetchall()

                partidos = [
                    PartidoResumen(
                        id=fila["id"],
                        competicion=fila["competicion"],
                        fecha_partido=fila["fecha_partido"],
                        equipo_local=fila["equipo_local"],
                        equipo_visitante=fila["equipo_visitante"],
                        estado=fila["estado"],
                        jornada=fila["jornada"],
                    )
                    for fila in filas
                ]

                return ListaPartidosResponse(
                    exito=True,
                    total=total,
                    partidos=partidos,
                )

    except Exception as e:
        logger.error(f"Error listando partidos próximos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/recientes",
    response_model=ListaPartidosResponse,
    summary="Partidos recientes",
    description="Lista partidos finalizados recientemente.",
)
async def listar_partidos_recientes(
    competicion_id: Optional[UUID] = Query(None, description="Filtrar por competición"),
    dias: int = Query(7, ge=1, le=30, description="Días hacia atrás"),
    equipo_id: Optional[UUID] = Query(None, description="Filtrar por equipo"),
) -> ListaPartidosResponse:
    """Lista partidos recientes finalizados."""
    pool = obtener_pool()

    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias)

    query = """
        SELECT
            pf.id,
            c.nombre as competicion,
            pf.fecha_partido,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.estado,
            pf.jornada
        FROM partidos_futbol pf
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.estado = 'FINALIZADO'
          AND pf.fecha_partido >= %s
          AND pf.fecha_partido <= %s
    """
    params = [fecha_inicio, fecha_fin]

    if competicion_id:
        query += " AND pf.competicion_id = %s"
        params.append(str(competicion_id))

    if equipo_id:
        query += " AND (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)"
        params.extend([str(equipo_id), str(equipo_id)])

    query += " ORDER BY pf.fecha_partido DESC"

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, params)
                filas = cursor.fetchall()

                partidos = [
                    PartidoResumen(
                        id=fila["id"],
                        competicion=fila["competicion"],
                        fecha_partido=fila["fecha_partido"],
                        equipo_local=fila["equipo_local"],
                        equipo_visitante=fila["equipo_visitante"],
                        estado=fila["estado"],
                        jornada=fila["jornada"],
                    )
                    for fila in filas
                ]

                return ListaPartidosResponse(
                    exito=True,
                    total=len(partidos),
                    partidos=partidos,
                )

    except Exception as e:
        logger.error(f"Error listando partidos recientes: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{partido_id}",
    response_model=PartidoDetalle,
    summary="Detalle de partido",
    description="Obtiene el detalle completo de un partido.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_partido(partido_id: UUID) -> PartidoDetalle:
    """Obtiene el detalle completo de un partido."""
    pool = obtener_pool()

    query = """
        SELECT
            pf.id,
            c.nombre as competicion,
            pf.fecha_partido,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.estado,
            pf.jornada,
            pf.equipo_local_id,
            pf.equipo_visitante_id,
            -- Goles
            pf.local_goles_1t,
            pf.local_goles_2t,
            pf.local_goles_total,
            pf.visitante_goles_1t,
            pf.visitante_goles_2t,
            pf.visitante_goles_total,
            -- Corners
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.local_corners_total,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.visitante_corners_total,
            -- Disparos
            pf.local_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_total,
            pf.visitante_disparos_arco
        FROM partidos_futbol pf
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.id = %s
    """

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, [str(partido_id)])
                fila = cursor.fetchone()

                if not fila:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Partido no encontrado: {partido_id}"
                    )

                # Calcular estadísticas de equipos
                estadisticas_local = _calcular_estadisticas_equipo(
                    cursor, str(fila["equipo_local_id"])
                )
                estadisticas_visitante = _calcular_estadisticas_equipo(
                    cursor, str(fila["equipo_visitante_id"])
                )

                return PartidoDetalle(
                    id=fila["id"],
                    competicion=fila["competicion"],
                    fecha_partido=fila["fecha_partido"],
                    equipo_local=fila["equipo_local"],
                    equipo_visitante=fila["equipo_visitante"],
                    estado=fila["estado"],
                    jornada=fila["jornada"],
                    # Goles
                    local_goles_1t=fila["local_goles_1t"],
                    local_goles_2t=fila["local_goles_2t"],
                    local_goles_total=fila["local_goles_total"],
                    visitante_goles_1t=fila["visitante_goles_1t"],
                    visitante_goles_2t=fila["visitante_goles_2t"],
                    visitante_goles_total=fila["visitante_goles_total"],
                    # Corners
                    local_corners_1t=fila["local_corners_1t"],
                    local_corners_2t=fila["local_corners_2t"],
                    local_corners_total=fila["local_corners_total"],
                    visitante_corners_1t=fila["visitante_corners_1t"],
                    visitante_corners_2t=fila["visitante_corners_2t"],
                    visitante_corners_total=fila["visitante_corners_total"],
                    # Disparos
                    local_disparos_total=fila["local_disparos_total"],
                    local_disparos_arco=fila["local_disparos_arco"],
                    visitante_disparos_total=fila["visitante_disparos_total"],
                    visitante_disparos_arco=fila["visitante_disparos_arco"],
                    # Estadísticas de equipos
                    estadisticas_local=estadisticas_local,
                    estadisticas_visitante=estadisticas_visitante,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo partido {partido_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# -*- coding: utf-8 -*-
"""
rutas_equipos_futbol.py — Endpoints para gestión de equipos de fútbol.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    EquipoBase,
    EquipoDetalle,
    EstadisticasEquipo,
    ListaEquiposResponse,
    PartidoResumen,
    PartidoEstadistico,
    ErrorResponse,
)

router = APIRouter(prefix="/api/futbol/equipos", tags=["Fútbol - Equipos"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=ListaEquiposResponse,
    summary="Listar equipos",
    description="Lista equipos con filtros y paginación.",
)
async def listar_equipos(
    competicion_id: Optional[UUID] = Query(None, description="Filtrar por competición"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    tamano: int = Query(20, ge=1, le=100, description="Tamaño de página"),
) -> ListaEquiposResponse:
    """Lista equipos con filtros y paginación."""
    pool = obtener_pool()

    # Query base
    query = """
        SELECT
            e.id,
            e.nombre,
            e.nombre_corto,
            COALESCE(p.nombre, 'Desconocido') as pais,
            (
                SELECT c.nombre
                FROM competiciones_futbol c
                JOIN partidos_futbol pf ON pf.competicion_id = c.id
                WHERE pf.equipo_local_id = e.id OR pf.equipo_visitante_id = e.id
                GROUP BY c.id, c.nombre
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) as competicion_principal,
            e.logo_url
        FROM equipos_futbol e
        LEFT JOIN paises p ON e.pais_id = p.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) FROM equipos_futbol e LEFT JOIN paises p ON e.pais_id = p.id WHERE 1=1"
    params: List = []
    count_params: List = []

    if competicion_id:
        subquery = """
            AND e.id IN (
                SELECT DISTINCT CASE
                    WHEN pf.equipo_local_id = e.id THEN e.id
                    ELSE e.id
                END
                FROM partidos_futbol pf
                WHERE pf.competicion_id = %s
                  AND (pf.equipo_local_id = e.id OR pf.equipo_visitante_id = e.id)
            )
        """
        query += subquery
        count_query += subquery
        params.append(str(competicion_id))
        count_params.append(str(competicion_id))

    if pais:
        query += " AND LOWER(p.nombre) LIKE LOWER(%s)"
        count_query += " AND LOWER(p.nombre) LIKE LOWER(%s)"
        params.append(f"%{pais}%")
        count_params.append(f"%{pais}%")

    if busqueda:
        query += " AND (LOWER(e.nombre) LIKE LOWER(%s) OR LOWER(e.nombre_corto) LIKE LOWER(%s))"
        count_query += " AND (LOWER(e.nombre) LIKE LOWER(%s) OR LOWER(e.nombre_corto) LIKE LOWER(%s))"
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])
        count_params.extend([f"%{busqueda}%", f"%{busqueda}%"])

    query += " ORDER BY e.nombre ASC"

    # Paginación
    offset = (pagina - 1) * tamano
    query += " LIMIT %s OFFSET %s"
    params.extend([tamano, offset])

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Obtener total
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()["count"]

                # Obtener equipos
                cursor.execute(query, params)
                filas = cursor.fetchall()

                equipos = [
                    EquipoBase(
                        id=fila["id"],
                        nombre=fila["nombre"],
                        nombre_corto=fila["nombre_corto"],
                        pais=fila["pais"],
                        competicion_principal=fila["competicion_principal"],
                        logo_url=fila.get("logo_url"),
                    )
                    for fila in filas
                ]

                return ListaEquiposResponse(
                    exito=True,
                    total=total,
                    pagina=pagina,
                    tamano=tamano,
                    equipos=equipos,
                )

    except Exception as e:
        logger.error(f"Error listando equipos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{equipo_id}",
    response_model=EquipoDetalle,
    summary="Detalle de equipo",
    description="Obtiene el detalle de un equipo con sus estadísticas.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_equipo(equipo_id: UUID) -> EquipoDetalle:
    """Obtiene el detalle de un equipo."""
    pool = obtener_pool()

    query = """
        SELECT
            e.id,
            e.nombre,
            e.nombre_corto,
            COALESCE(p.nombre, 'Desconocido') as pais,
            e.logo_url,
            (
                SELECT c.nombre
                FROM competiciones_futbol c
                JOIN partidos_futbol pf ON pf.competicion_id = c.id
                WHERE pf.equipo_local_id = e.id OR pf.equipo_visitante_id = e.id
                GROUP BY c.id, c.nombre
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) as competicion_principal
        FROM equipos_futbol e
        LEFT JOIN paises p ON e.pais_id = p.id
        WHERE e.id = %s
    """

    stats_query = """
        SELECT
            COUNT(*) as partidos_jugados,
            SUM(CASE
                WHEN (pf.equipo_local_id = %s AND pf.local_goles_total > pf.visitante_goles_total)
                  OR (pf.equipo_visitante_id = %s AND pf.visitante_goles_total > pf.local_goles_total)
                THEN 1 ELSE 0
            END) as victorias,
            SUM(CASE
                WHEN pf.local_goles_total = pf.visitante_goles_total THEN 1 ELSE 0
            END) as empates,
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

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, [str(equipo_id)])
                fila = cursor.fetchone()

                if not fila:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Equipo no encontrado: {equipo_id}"
                    )

                # Obtener estadísticas
                equipo_str = str(equipo_id)
                cursor.execute(stats_query, [
                    equipo_str, equipo_str, equipo_str, equipo_str,
                    equipo_str, equipo_str, equipo_str, equipo_str,
                    equipo_str, equipo_str, equipo_str, equipo_str,
                ])
                stats = cursor.fetchone()

                estadisticas = None
                if stats and stats["partidos_jugados"] > 0:
                    estadisticas = EstadisticasEquipo(
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

                return EquipoDetalle(
                    id=fila["id"],
                    nombre=fila["nombre"],
                    nombre_corto=fila["nombre_corto"],
                    pais=fila["pais"],
                    competicion_principal=fila["competicion_principal"],
                    logo_url=fila.get("logo_url"),
                    estadisticas=estadisticas,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo equipo {equipo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{equipo_id}/estadisticas",
    response_model=EstadisticasEquipo,
    summary="Estadísticas de equipo",
    description="Obtiene estadísticas detalladas de un equipo.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_estadisticas_equipo(
    equipo_id: UUID,
    temporada: Optional[str] = Query(None, description="Filtrar por temporada"),
    competicion_id: Optional[UUID] = Query(None, description="Filtrar por competición"),
) -> EstadisticasEquipo:
    """Obtiene estadísticas detalladas de un equipo."""
    pool = obtener_pool()

    query = """
        SELECT
            COUNT(*) as partidos_jugados,
            SUM(CASE
                WHEN (pf.equipo_local_id = %s AND pf.local_goles_total > pf.visitante_goles_total)
                  OR (pf.equipo_visitante_id = %s AND pf.visitante_goles_total > pf.local_goles_total)
                THEN 1 ELSE 0
            END) as victorias,
            SUM(CASE
                WHEN pf.local_goles_total = pf.visitante_goles_total THEN 1 ELSE 0
            END) as empates,
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
    params = [str(equipo_id)] * 12

    if temporada:
        query += " AND pf.temporada_id IN (SELECT id FROM temporadas_futbol WHERE nombre = %s)"
        params.append(temporada)

    if competicion_id:
        query += " AND pf.competicion_id = %s"
        params.append(str(competicion_id))

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar que el equipo existe
                cursor.execute("SELECT 1 FROM equipos_futbol WHERE id = %s", [str(equipo_id)])
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Equipo no encontrado: {equipo_id}"
                    )

                cursor.execute(query, params)
                stats = cursor.fetchone()

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de equipo {equipo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{equipo_id}/partidos",
    response_model=List[PartidoResumen],
    summary="Historial de partidos",
    description="Obtiene el historial de partidos de un equipo.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_partidos_equipo(
    equipo_id: UUID,
    limite: Optional[int] = Query(None, ge=1, description="Numero de partidos (omitido = todos)"),
    tipo: Literal["proximos", "pasados", "todos"] = Query(
        "todos",
        description="Tipo de partidos a obtener"
    ),
    ubicacion: Literal["todos", "local", "visitante"] = Query(
        "todos",
        description="Filtra por condicion del equipo (todos/local/visitante)",
    ),
) -> List[PartidoResumen]:
    """Obtiene historial de partidos de un equipo."""
    pool = obtener_pool()

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
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
    """
    params = [str(equipo_id), str(equipo_id)]

    if tipo == "proximos":
        query += " AND pf.estado = 'PROGRAMADO'"
    elif tipo == "pasados":
        query += " AND pf.estado = 'FINALIZADO'"

    if ubicacion == "local":
        query += " AND pf.equipo_local_id = %s"
        params.append(str(equipo_id))
    elif ubicacion == "visitante":
        query += " AND pf.equipo_visitante_id = %s"
        params.append(str(equipo_id))

    if tipo == "proximos":
        query += " ORDER BY pf.fecha_partido ASC"
    else:
        query += " ORDER BY pf.fecha_partido DESC"

    if limite is not None:
        query += " LIMIT %s"
        params.append(limite)

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar que el equipo existe
                cursor.execute("SELECT 1 FROM equipos_futbol WHERE id = %s", [str(equipo_id)])
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Equipo no encontrado: {equipo_id}"
                    )

                cursor.execute(query, params)
                filas = cursor.fetchall()

                return [
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo partidos de equipo {equipo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{equipo_id}/partidos-detalle",
    response_model=List[PartidoEstadistico],
    summary="Historial detallado de partidos",
    description="Obtiene el historial de partidos con estadísticas clave.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_partidos_equipo_detalle(
    equipo_id: UUID,
    limite: Optional[int] = Query(None, ge=1, description="Numero de partidos (omitido = todos)"),
    ubicacion: Literal["todos", "local", "visitante"] = Query(
        "todos",
        description="Filtra por condicion del equipo (todos/local/visitante)",
    ),
) -> List[PartidoEstadistico]:
    """Obtiene historial detallado de partidos de un equipo."""
    pool = obtener_pool()

    query = """
        SELECT
            pf.id,
            pf.fecha_partido,
            el.id as equipo_local_id,
            ev.id as equipo_visitante_id,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.local_goles_total,
            pf.visitante_goles_total,
            pf.local_corners_total,
            pf.visitante_corners_total,
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.local_disparos_total,
            pf.visitante_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_arco
        FROM partidos_futbol pf
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.estado = 'FINALIZADO'
          AND (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
    """
    params = [str(equipo_id), str(equipo_id)]
    if ubicacion == "local":
        query += " AND pf.equipo_local_id = %s"
        params.append(str(equipo_id))
    elif ubicacion == "visitante":
        query += " AND pf.equipo_visitante_id = %s"
        params.append(str(equipo_id))

    query += " ORDER BY pf.fecha_partido DESC"

    if limite is not None:
        query += " LIMIT %s"
        params.append(limite)

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT 1 FROM equipos_futbol WHERE id = %s", [str(equipo_id)])
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Equipo no encontrado: {equipo_id}"
                    )

                cursor.execute(query, params)
                filas = cursor.fetchall()

                return [
                    PartidoEstadistico(
                        id=fila["id"],
                        fecha_partido=fila["fecha_partido"],
                        equipo_local_id=fila["equipo_local_id"],
                        equipo_visitante_id=fila["equipo_visitante_id"],
                        equipo_local=fila["equipo_local"],
                        equipo_visitante=fila["equipo_visitante"],
                        goles_local=fila["local_goles_total"],
                        goles_visitante=fila["visitante_goles_total"],
                        corners_local=fila["local_corners_total"],
                        corners_visitante=fila["visitante_corners_total"],
                        corners_local_1t=fila["local_corners_1t"],
                        corners_local_2t=fila["local_corners_2t"],
                        corners_visitante_1t=fila["visitante_corners_1t"],
                        corners_visitante_2t=fila["visitante_corners_2t"],
                        disparos_local=fila["local_disparos_total"],
                        disparos_visitante=fila["visitante_disparos_total"],
                        disparos_arco_local=fila["local_disparos_arco"],
                        disparos_arco_visitante=fila["visitante_disparos_arco"],
                    )
                    for fila in filas
                ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo partidos detallados de equipo {equipo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

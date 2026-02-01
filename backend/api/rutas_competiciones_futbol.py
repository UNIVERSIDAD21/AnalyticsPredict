# -*- coding: utf-8 -*-
"""
rutas_competiciones_futbol.py — Endpoints para gestión de competiciones de fútbol.
"""

from __future__ import annotations

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    CompeticionBase,
    CompeticionDetalle,
    ListaCompeticionesResponse,
    EquipoBase,
    ErrorResponse,
)

router = APIRouter(prefix="/api/futbol/competiciones", tags=["Fútbol - Competiciones"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=ListaCompeticionesResponse,
    summary="Listar competiciones",
    description="Lista todas las competiciones disponibles con filtros opcionales.",
)
async def listar_competiciones(
    tipo: Optional[str] = Query(
        None,
        description="Filtrar por tipo: liga, copa_nacional, continental"
    ),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    activa: Optional[bool] = Query(True, description="Filtrar por estado activo"),
) -> ListaCompeticionesResponse:
    """Lista todas las competiciones de fútbol."""
    pool = obtener_pool()

    query = """
        SELECT
            c.id,
            c.codigo,
            c.nombre,
            COALESCE(p.nombre, 'Internacional') as pais,
            COALESCE(c.tipo, 'liga') as tipo,
            COALESCE(c.prioridad, 0) as prioridad,
            COALESCE(c.activa, true) as activa
        FROM competiciones_futbol c
        LEFT JOIN paises_futbol p ON c.pais_id = p.id
        WHERE 1=1
    """
    params: List = []

    if tipo:
        query += " AND c.tipo = %s"
        params.append(tipo.lower())

    if pais:
        query += " AND LOWER(p.nombre) LIKE LOWER(%s)"
        params.append(f"%{pais}%")

    if activa is not None:
        query += " AND c.activa = %s"
        params.append(activa)

    query += " ORDER BY c.prioridad ASC, c.nombre ASC"

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, params)
                filas = cursor.fetchall()

                competiciones = [
                    CompeticionBase(
                        id=fila["id"],
                        codigo=fila["codigo"],
                        nombre=fila["nombre"],
                        pais=fila["pais"],
                        tipo=fila["tipo"],
                        prioridad=fila["prioridad"],
                        activa=fila["activa"],
                    )
                    for fila in filas
                ]

                return ListaCompeticionesResponse(
                    exito=True,
                    total=len(competiciones),
                    competiciones=competiciones,
                )

    except Exception as e:
        logger.error(f"Error listando competiciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{competicion_id}",
    response_model=CompeticionDetalle,
    summary="Detalle de competición",
    description="Obtiene el detalle de una competición específica.",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_competicion(competicion_id: UUID) -> CompeticionDetalle:
    """Obtiene el detalle de una competición."""
    pool = obtener_pool()

    query = """
        SELECT
            c.id,
            c.codigo,
            c.nombre,
            COALESCE(p.nombre, 'Internacional') as pais,
            COALESCE(c.tipo, 'liga') as tipo,
            COALESCE(c.prioridad, 0) as prioridad,
            COALESCE(c.activa, true) as activa,
            (
                SELECT t.nombre
                FROM temporadas_futbol t
                WHERE t.competicion_id = c.id AND t.activa = true
                LIMIT 1
            ) as temporada_actual,
            (
                SELECT COUNT(DISTINCT e.id)
                FROM equipos_futbol e
                JOIN partidos_futbol pf ON (e.id = pf.equipo_local_id OR e.id = pf.equipo_visitante_id)
                WHERE pf.competicion_id = c.id
            ) as total_equipos,
            (
                SELECT COUNT(*)
                FROM partidos_futbol pf
                WHERE pf.competicion_id = c.id
            ) as total_partidos
        FROM competiciones_futbol c
        LEFT JOIN paises_futbol p ON c.pais_id = p.id
        WHERE c.id = %s
    """

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, [str(competicion_id)])
                fila = cursor.fetchone()

                if not fila:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Competición no encontrada: {competicion_id}"
                    )

                return CompeticionDetalle(
                    id=fila["id"],
                    codigo=fila["codigo"],
                    nombre=fila["nombre"],
                    pais=fila["pais"],
                    tipo=fila["tipo"],
                    prioridad=fila["prioridad"],
                    activa=fila["activa"],
                    temporada_actual=fila["temporada_actual"],
                    total_equipos=fila["total_equipos"] or 0,
                    total_partidos=fila["total_partidos"] or 0,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo competición {competicion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{competicion_id}/equipos",
    response_model=List[EquipoBase],
    summary="Equipos de competición",
    description="Lista los equipos que participan en una competición.",
    responses={404: {"model": ErrorResponse}},
)
async def listar_equipos_competicion(
    competicion_id: UUID,
    temporada: Optional[str] = Query(None, description="Filtrar por temporada"),
) -> List[EquipoBase]:
    """Lista equipos de una competición específica."""
    pool = obtener_pool()

    # Primero verificar que la competición existe
    check_query = "SELECT 1 FROM competiciones_futbol WHERE id = %s"

    query = """
        SELECT DISTINCT
            e.id,
            e.nombre,
            e.nombre_corto,
            COALESCE(p.nombre, 'Desconocido') as pais,
            c.nombre as competicion_principal
        FROM equipos_futbol e
        JOIN partidos_futbol pf ON (e.id = pf.equipo_local_id OR e.id = pf.equipo_visitante_id)
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        LEFT JOIN paises_futbol p ON e.pais_id = p.id
        WHERE pf.competicion_id = %s
    """
    params = [str(competicion_id)]

    if temporada:
        query += """
            AND pf.temporada_id IN (
                SELECT id FROM temporadas_futbol WHERE nombre = %s
            )
        """
        params.append(temporada)

    query += " ORDER BY e.nombre ASC"

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar competición existe
                cursor.execute(check_query, [str(competicion_id)])
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Competición no encontrada: {competicion_id}"
                    )

                cursor.execute(query, params)
                filas = cursor.fetchall()

                return [
                    EquipoBase(
                        id=fila["id"],
                        nombre=fila["nombre"],
                        nombre_corto=fila["nombre_corto"],
                        pais=fila["pais"],
                        competicion_principal=fila["competicion_principal"],
                    )
                    for fila in filas
                ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando equipos de competición {competicion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

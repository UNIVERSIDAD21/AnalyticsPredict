# -*- coding: utf-8 -*-
"""
rutas_partidos.py — Endpoints para consultar partidos.

Permite al frontend obtener:
- Partidos del día
- Partidos próximos (futuros)
- Partidos por rango de fechas
- Búsqueda de partidos por equipos

Esto es CRÍTICO para que el formulario de análisis pueda enviar
partido_id y así el sistema registre predicciones correctamente.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Query as QueryParam
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from db import obtener_pool

router = APIRouter(prefix="/api/partidos", tags=["Partidos"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS DE RESPUESTA
# ═══════════════════════════════════════════════════════════════════════════════


class PartidoResumen(BaseModel):
    """Resumen de un partido para selección en UI."""

    id: str
    fecha_partido: date
    tipo_partido: str
    equipo_local_id: str
    equipo_local_nombre: str
    equipo_visitante_id: str
    equipo_visitante_nombre: str
    temporada_id: str
    temporada_nombre: str
    # Datos del resultado (si ya terminó)
    local_total: Optional[int] = None
    visitante_total: Optional[int] = None
    finalizado: bool = False


class RespuestaPartidos(BaseModel):
    """Respuesta con lista de partidos."""

    exito: bool
    partidos: List[PartidoResumen]
    total: int
    mensaje: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES INTERNAS
# ═══════════════════════════════════════════════════════════════════════════════


def _consultar_partidos(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    equipo_id: Optional[str] = None,
    solo_futuros: bool = False,
    solo_finalizados: bool = False,
    limite: int = 50,
) -> RespuestaPartidos:
    """
    Función interna para consultar partidos.
    Esta función puede ser llamada desde otros endpoints sin problemas
    con los tipos Query de FastAPI.
    """
    pool = obtener_pool()

    # Defaults
    if fecha_desde is None:
        fecha_desde = date.today()
    if fecha_hasta is None:
        fecha_hasta = fecha_desde + timedelta(days=7)

    # Construir query
    condiciones = ["p.fecha_partido >= %s", "p.fecha_partido <= %s"]
    parametros: List = [fecha_desde, fecha_hasta]

    if equipo_id:
        condiciones.append("(p.equipo_local_id = %s OR p.equipo_visitante_id = %s)")
        parametros.extend([equipo_id, equipo_id])

    condicion_pendiente = """
        (
            p.local_total IS NULL
            OR p.visitante_total IS NULL
            OR (
                p.local_total = 0
                AND p.visitante_total = 0
                AND p.local_q1 = 0
                AND p.local_q2 = 0
                AND p.local_q3 = 0
                AND p.local_q4 = 0
                AND p.local_ot = 0
                AND p.visitante_q1 = 0
                AND p.visitante_q2 = 0
                AND p.visitante_q3 = 0
                AND p.visitante_q4 = 0
                AND p.visitante_ot = 0
            )
        )
    """

    if solo_futuros:
        condiciones.append(condicion_pendiente)
    elif solo_finalizados:
        condiciones.append(f"NOT {condicion_pendiente}")

    parametros.append(limite)
    where_clause = " AND ".join(condiciones)

    query = f"""
        SELECT
            p.id,
            p.fecha_partido,
            p.tipo_partido,
            p.equipo_local_id,
            el.nombre AS equipo_local_nombre,
            p.equipo_visitante_id,
            ev.nombre AS equipo_visitante_nombre,
            p.temporada_id,
            t.nombre AS temporada_nombre,
            p.local_total,
            p.visitante_total
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE {where_clause}
        ORDER BY p.fecha_partido ASC, el.nombre ASC
        LIMIT %s
    """

    try:
        with pool.connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, parametros)
                filas = cursor.fetchall()

                def _es_pendiente(fila: dict) -> bool:
                    if fila["local_total"] is None or fila["visitante_total"] is None:
                        return True
                    columnas_ceros = [
                        "local_q1",
                        "local_q2",
                        "local_q3",
                        "local_q4",
                        "local_ot",
                        "visitante_q1",
                        "visitante_q2",
                        "visitante_q3",
                        "visitante_q4",
                        "visitante_ot",
                    ]
                    return fila["local_total"] == 0 and fila["visitante_total"] == 0 and all(
                        fila[columna] == 0 for columna in columnas_ceros
                    )

                partidos = [
                    PartidoResumen(
                        id=str(fila["id"]),
                        fecha_partido=fila["fecha_partido"],
                        tipo_partido=fila["tipo_partido"],
                        equipo_local_id=str(fila["equipo_local_id"]),
                        equipo_local_nombre=fila["equipo_local_nombre"],
                        equipo_visitante_id=str(fila["equipo_visitante_id"]),
                        equipo_visitante_nombre=fila["equipo_visitante_nombre"],
                        temporada_id=str(fila["temporada_id"]),
                        temporada_nombre=fila["temporada_nombre"],
                        local_total=fila["local_total"],
                        visitante_total=fila["visitante_total"],
                        finalizado=not _es_pendiente(fila),
                    )
                    for fila in filas
                ]

                return RespuestaPartidos(
                    exito=True,
                    partidos=partidos,
                    total=len(partidos),
                )

    except Exception as e:
        logger.exception("Error listando partidos")
        return RespuestaPartidos(
            exito=False,
            partidos=[],
            total=0,
            mensaje=f"Error: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "",
    response_model=RespuestaPartidos,
    summary="Listar partidos",
    description="""
    Obtiene partidos con filtros opcionales.

    Útil para:
    - Mostrar partidos del día para selección en formulario
    - Mostrar partidos próximos para apostar
    - Buscar partidos históricos
    """,
)
async def listar_partidos(
    fecha_desde: Optional[date] = QueryParam(
        None, description="Fecha inicio (YYYY-MM-DD). Default: hoy"
    ),
    fecha_hasta: Optional[date] = QueryParam(
        None, description="Fecha fin (YYYY-MM-DD). Default: hoy + 7 días"
    ),
    equipo_id: Optional[str] = QueryParam(
        None, description="Filtrar por ID de equipo (local o visitante)"
    ),
    solo_futuros: bool = QueryParam(
        False, description="Solo partidos sin resultado (futuros)"
    ),
    solo_finalizados: bool = QueryParam(
        False, description="Solo partidos con resultado"
    ),
    limite: int = QueryParam(50, ge=1, le=200, description="Máximo de resultados"),
) -> RespuestaPartidos:
    """Lista partidos con filtros."""
    return _consultar_partidos(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        equipo_id=equipo_id,
        solo_futuros=solo_futuros,
        solo_finalizados=solo_finalizados,
        limite=limite,
    )


@router.get(
    "/hoy",
    response_model=RespuestaPartidos,
    summary="Partidos del día",
    description="Obtiene todos los partidos programados para hoy.",
)
async def partidos_hoy() -> RespuestaPartidos:
    """Obtiene partidos de hoy."""
    hoy = date.today()
    return _consultar_partidos(fecha_desde=hoy, fecha_hasta=hoy)


@router.get(
    "/proximos",
    response_model=RespuestaPartidos,
    summary="Partidos próximos",
    description="Obtiene partidos futuros sin resultado (para apostar).",
)
async def partidos_proximos(
    dias: int = QueryParam(7, ge=1, le=30, description="Días hacia adelante"),
    limite: int = QueryParam(50, ge=1, le=200, description="Máximo de resultados"),
) -> RespuestaPartidos:
    """Obtiene partidos próximos."""
    hoy = date.today()
    return _consultar_partidos(
        fecha_desde=hoy,
        fecha_hasta=hoy + timedelta(days=dias),
        solo_futuros=True,
        limite=limite,
    )


@router.get(
    "/buscar",
    response_model=RespuestaPartidos,
    summary="Buscar partido por equipos",
    description="""
    Busca partidos por nombres de equipos y fecha opcional.

    Útil para cuando el usuario ya sabe qué partido quiere analizar
    pero necesita obtener el partido_id.
    """,
)
async def buscar_partido(
    equipo_local: str = QueryParam(..., min_length=2, description="Nombre del equipo local"),
    equipo_visitante: str = QueryParam(
        ..., min_length=2, description="Nombre del equipo visitante"
    ),
    fecha: Optional[date] = QueryParam(None, description="Fecha exacta (YYYY-MM-DD)"),
    dias_rango: int = QueryParam(
        7, ge=1, le=30, description="Si no hay fecha, buscar en este rango de días"
    ),
) -> RespuestaPartidos:
    """Busca partido por equipos y fecha."""
    pool = obtener_pool()

    # Si hay fecha exacta, buscar solo ese día
    if fecha:
        fecha_desde = fecha
        fecha_hasta = fecha
    else:
        # Buscar en rango de días desde hoy
        fecha_desde = date.today()
        fecha_hasta = fecha_desde + timedelta(days=dias_rango)

    query = """
        SELECT
            p.id,
            p.fecha_partido,
            p.tipo_partido,
            p.equipo_local_id,
            el.nombre AS equipo_local_nombre,
            p.equipo_visitante_id,
            ev.nombre AS equipo_visitante_nombre,
            p.temporada_id,
            t.nombre AS temporada_nombre,
            p.local_total,
            p.visitante_total
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE
            LOWER(el.nombre) LIKE LOWER(%s)
            AND LOWER(ev.nombre) LIKE LOWER(%s)
            AND p.fecha_partido >= %s
            AND p.fecha_partido <= %s
        ORDER BY p.fecha_partido ASC
        LIMIT 10
    """

    try:
        with pool.connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    query,
                    [
                        f"%{equipo_local}%",
                        f"%{equipo_visitante}%",
                        fecha_desde,
                        fecha_hasta,
                    ],
                )
                filas = cursor.fetchall()

                partidos = [
                    PartidoResumen(
                        id=str(fila["id"]),
                        fecha_partido=fila["fecha_partido"],
                        tipo_partido=fila["tipo_partido"],
                        equipo_local_id=str(fila["equipo_local_id"]),
                        equipo_local_nombre=fila["equipo_local_nombre"],
                        equipo_visitante_id=str(fila["equipo_visitante_id"]),
                        equipo_visitante_nombre=fila["equipo_visitante_nombre"],
                        temporada_id=str(fila["temporada_id"]),
                        temporada_nombre=fila["temporada_nombre"],
                        local_total=fila["local_total"],
                        visitante_total=fila["visitante_total"],
                        finalizado=fila["local_total"] is not None,
                    )
                    for fila in filas
                ]

                mensaje = None
                if not partidos:
                    mensaje = f"No se encontraron partidos de {equipo_local} vs {equipo_visitante}"
                    if fecha:
                        mensaje += f" en {fecha}"
                    else:
                        mensaje += f" en los próximos {dias_rango} días"

                return RespuestaPartidos(
                    exito=True,
                    partidos=partidos,
                    total=len(partidos),
                    mensaje=mensaje,
                )

    except Exception as e:
        logger.exception("Error buscando partido")
        return RespuestaPartidos(
            exito=False,
            partidos=[],
            total=0,
            mensaje=f"Error: {str(e)}",
        )


@router.get(
    "/{partido_id}",
    summary="Obtener partido por ID",
    description="Obtiene los detalles de un partido específico.",
)
async def obtener_partido(partido_id: str):
    """Obtiene un partido por su ID."""
    pool = obtener_pool()

    query = """
        SELECT
            p.id,
            p.fecha_partido,
            p.tipo_partido,
            p.equipo_local_id,
            el.nombre AS equipo_local_nombre,
            p.equipo_visitante_id,
            ev.nombre AS equipo_visitante_nombre,
            p.temporada_id,
            t.nombre AS temporada_nombre,
            p.local_q1,
            p.local_q2,
            p.local_q3,
            p.local_q4,
            p.local_ot,
            p.local_total,
            p.visitante_q1,
            p.visitante_q2,
            p.visitante_q3,
            p.visitante_q4,
            p.visitante_ot,
            p.visitante_total
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        JOIN temporadas t ON p.temporada_id = t.id
        WHERE p.id = %s
    """

    try:
        with pool.connection() as conexion:
            with conexion.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, [partido_id])
                fila = cursor.fetchone()

                if not fila:
                    return {
                        "exito": False,
                        "partido": None,
                        "mensaje": f"Partido {partido_id} no encontrado",
                    }

                return {
                    "exito": True,
                    "partido": {
                        "id": str(fila["id"]),
                        "fecha_partido": fila["fecha_partido"].isoformat(),
                        "tipo_partido": fila["tipo_partido"],
                        "equipo_local_id": str(fila["equipo_local_id"]),
                        "equipo_local_nombre": fila["equipo_local_nombre"],
                        "equipo_visitante_id": str(fila["equipo_visitante_id"]),
                        "equipo_visitante_nombre": fila["equipo_visitante_nombre"],
                        "temporada_id": str(fila["temporada_id"]),
                        "temporada_nombre": fila["temporada_nombre"],
                        "marcadores": {
                            "local": {
                                "q1": fila["local_q1"],
                                "q2": fila["local_q2"],
                                "q3": fila["local_q3"],
                                "q4": fila["local_q4"],
                                "ot": fila["local_ot"],
                                "total": fila["local_total"],
                            },
                            "visitante": {
                                "q1": fila["visitante_q1"],
                                "q2": fila["visitante_q2"],
                                "q3": fila["visitante_q3"],
                                "q4": fila["visitante_q4"],
                                "ot": fila["visitante_ot"],
                                "total": fila["visitante_total"],
                            },
                        },
                        "finalizado": fila["local_total"] is not None,
                    },
                }

    except Exception as e:
        logger.exception("Error obteniendo partido")
        return {
            "exito": False,
            "partido": None,
            "mensaje": f"Error: {str(e)}",
        }

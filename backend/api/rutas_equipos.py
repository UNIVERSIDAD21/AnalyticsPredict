# -*- coding: utf-8 -*-
"""rutas_equipos.py — Endpoint de equipos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from psycopg.rows import dict_row

from configuracion import CONFIGURACION
from db import obtener_pool
from motor_autoentrenamiento import obtener_modelo
from motor.utilidades import resolver_nombre_en_modelo
from .modelos_respuesta import (
    RespuestaEquipos,
    RespuestaEstadisticasEquipos,
    RespuestaHistorialEquipo,
)
from motor.tipos import InfoEquipo

router = APIRouter(prefix="/api", tags=["Equipos"])


def filtrar_equipos_por_modelo(equipos: List[InfoEquipo]) -> List[InfoEquipo]:
    """Filtra equipos usando el modelo auto-entrenado desde BD."""
    try:
        modelo = obtener_modelo()
        if modelo is None:
            return equipos
        return [
            equipo
            for equipo in equipos
            if resolver_nombre_en_modelo(equipo.nombre, modelo.entidad_a_indice) is not None
        ]
    except Exception:
        # Si el modelo no está disponible, retorna todos los equipos
        return equipos


def cargar_equipos() -> List[InfoEquipo]:
    """Carga equipos desde PostgreSQL."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE activo = true
                ORDER BY nombre
                """
            )
            filas = cursor.fetchall()
    return [InfoEquipo(**fila) for fila in filas]


def cargar_estadisticas_equipos() -> dict:
    """Carga estadísticas de equipos desde el archivo JSON de datos."""
    ruta = Path(CONFIGURACION.ruta_estadisticas_equipos)
    if not ruta.exists():
        return {
            "fecha_actualizacion": None,
            "equipos": [],
        }
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


@router.get(
    "/equipos",
    summary="Listar equipos",
    response_model=RespuestaEquipos,
)
async def listar_equipos() -> RespuestaEquipos:
    """Retorna la lista de equipos disponibles."""
    equipos = filtrar_equipos_por_modelo(cargar_equipos())
    equipos_ordenados = sorted(equipos, key=lambda e: e.nombre)
    return RespuestaEquipos(
        exito=True,
        total=len(equipos_ordenados),
        equipos=[equipo.__dict__ for equipo in equipos_ordenados],
    )


@router.get(
    "/equipos/busqueda",
    summary="Buscar equipos en catálogo",
    response_model=RespuestaEquipos,
)
async def buscar_equipos(
    conferencia: Optional[str] = Query(None, description="Filtrar por conferencia"),
    division: Optional[str] = Query(None, description="Filtrar por división"),
    busqueda: Optional[str] = Query(None, description="Texto de búsqueda"),
) -> RespuestaEquipos:
    """Busca equipos en la base de datos con filtros opcionales."""
    condiciones = ["activo = true"]
    parametros: List[object] = []
    if conferencia:
        condiciones.append("conferencia = %s")
        parametros.append(conferencia)
    if division:
        condiciones.append("division = %s")
        parametros.append(division)
    if busqueda:
        condiciones.append(
            "(nombre ILIKE %s OR nombre_corto ILIKE %s OR abreviatura ILIKE %s)"
        )
        term = f"%{busqueda}%"
        parametros.extend([term, term, term])

    where_sql = " AND ".join(condiciones)

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT id, nombre, nombre_corto, abreviatura, conferencia, division
                FROM equipos
                WHERE {where_sql}
                ORDER BY nombre
                """,
                parametros,
            )
            filas = cursor.fetchall()

    equipos_filtrados = filtrar_equipos_por_modelo([InfoEquipo(**fila) for fila in filas])

    return RespuestaEquipos(
        exito=True,
        total=len(equipos_filtrados),
        equipos=[equipo.__dict__ for equipo in equipos_filtrados],
    )


@router.get(
    "/estadisticas-equipos",
    summary="Estadísticas de equipos",
    response_model=RespuestaEstadisticasEquipos,
)
async def listar_estadisticas_equipos() -> RespuestaEstadisticasEquipos:
    """Retorna estadísticas agregadas de los equipos."""
    datos = cargar_estadisticas_equipos()
    fecha = datos.get("fecha_actualizacion") or ""
    equipos = datos.get("equipos") or []
    return RespuestaEstadisticasEquipos(
        exito=True,
        fecha_actualizacion=fecha,
        equipos=equipos,
    )


@router.get(
    "/equipos/{equipo_id}/partidos",
    summary="Historial de partidos por equipo",
    response_model=RespuestaHistorialEquipo,
)
async def listar_historial_equipo(
    equipo_id: str,
    temporada_id: Optional[str] = Query(None, description="Filtrar por temporada"),
    como_local: Optional[bool] = Query(
        None, description="True para local, False para visitante"
    ),
    orden: str = Query("desc", description="Orden por fecha: asc o desc"),
) -> RespuestaHistorialEquipo:
    """Retorna el historial completo de partidos de un equipo."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, nombre, abreviatura
                FROM equipos
                WHERE id = %s
                """,
                (equipo_id,),
            )
            equipo = cursor.fetchone()

            if not equipo:
                raise HTTPException(status_code=404, detail="Equipo no encontrado")

            condiciones = [
                "(p.equipo_local_id = %s OR p.equipo_visitante_id = %s)",
                "p.local_q1 IS NOT NULL",
            ]
            parametros: List[object] = [equipo_id, equipo_id, equipo_id]

            if temporada_id:
                condiciones.append("p.temporada_id = %s")
                parametros.append(temporada_id)
            if como_local is True:
                condiciones.append("p.equipo_local_id = %s")
                parametros.append(equipo_id)
            if como_local is False:
                condiciones.append("p.equipo_visitante_id = %s")
                parametros.append(equipo_id)

            where_sql = " AND ".join(condiciones)
            orden_sql = "ASC" if orden.lower() == "asc" else "DESC"

            cursor.execute(
                f"""
                SELECT
                    p.id,
                    p.fecha_partido,
                    t.nombre as temporada,
                    el.nombre as equipo_local,
                    el.abreviatura as local_abr,
                    ev.nombre as equipo_visitante,
                    ev.abreviatura as visitante_abr,
                    p.local_q1, p.local_q2, p.local_q3, p.local_q4,
                    p.local_total,
                    p.visitante_q1, p.visitante_q2, p.visitante_q3, p.visitante_q4,
                    p.visitante_total,
                    CASE
                        WHEN p.equipo_local_id = %s THEN 'LOCAL'
                        ELSE 'VISITANTE'
                    END as ubicacion_equipo
                FROM partidos p
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                LEFT JOIN temporadas t ON p.temporada_id = t.id
                WHERE {where_sql}
                ORDER BY p.fecha_partido {orden_sql}
                """,
                parametros,
            )
            filas = cursor.fetchall()

            cursor.execute(
                """
                SELECT DISTINCT t.id, t.nombre
                FROM temporadas t
                JOIN partidos p ON p.temporada_id = t.id
                WHERE (p.equipo_local_id = %s OR p.equipo_visitante_id = %s)
                ORDER BY t.nombre DESC
                """,
                (equipo_id, equipo_id),
            )
            temporadas = cursor.fetchall()

    partidos = []
    for fila in filas:
        ubicacion = fila["ubicacion_equipo"]
        puntos_equipo = {
            "q1": fila["local_q1"] if ubicacion == "LOCAL" else fila["visitante_q1"],
            "q2": fila["local_q2"] if ubicacion == "LOCAL" else fila["visitante_q2"],
            "q3": fila["local_q3"] if ubicacion == "LOCAL" else fila["visitante_q3"],
            "q4": fila["local_q4"] if ubicacion == "LOCAL" else fila["visitante_q4"],
            "total": fila["local_total"] if ubicacion == "LOCAL" else fila["visitante_total"],
        }
        puntos_rival = {
            "q1": fila["visitante_q1"] if ubicacion == "LOCAL" else fila["local_q1"],
            "q2": fila["visitante_q2"] if ubicacion == "LOCAL" else fila["local_q2"],
            "q3": fila["visitante_q3"] if ubicacion == "LOCAL" else fila["local_q3"],
            "q4": fila["visitante_q4"] if ubicacion == "LOCAL" else fila["local_q4"],
            "total": fila["visitante_total"] if ubicacion == "LOCAL" else fila["local_total"],
        }
        resultado = "VICTORIA" if puntos_equipo["total"] > puntos_rival["total"] else "DERROTA"
        fecha = fila["fecha_partido"]
        partidos.append(
            {
                "id": str(fila["id"]),
                "fecha": fecha.isoformat() if fecha else "",
                "temporada": fila.get("temporada"),
                "equipo_local": fila["equipo_local"],
                "local_abr": fila["local_abr"],
                "equipo_visitante": fila["equipo_visitante"],
                "visitante_abr": fila["visitante_abr"],
                "ubicacion_equipo": ubicacion,
                "puntos_equipo": puntos_equipo,
                "puntos_rival": puntos_rival,
                "resultado": resultado,
            }
        )

    return RespuestaHistorialEquipo(
        exito=True,
        equipo={
            "id": str(equipo["id"]),
            "nombre": equipo["nombre"],
            "abreviatura": equipo["abreviatura"],
            "logo_url": equipo.get("logo_url"),
        },
        total_partidos=len(partidos),
        partidos=partidos,
        filtros_disponibles={
            "temporadas": [
                {"id": str(temporada["id"]), "nombre": temporada["nombre"]}
                for temporada in temporadas
            ]
        },
    )

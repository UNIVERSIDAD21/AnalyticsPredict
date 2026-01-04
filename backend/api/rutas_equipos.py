# -*- coding: utf-8 -*-
"""rutas_equipos.py — Endpoint de equipos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Query
from psycopg.rows import dict_row

from configuracion import CONFIGURACION
from db import obtener_pool
from motor_autoentrenamiento import obtener_modelo
from motor.utilidades import resolver_nombre_en_modelo
from .modelos_respuesta import RespuestaEquipos, RespuestaEstadisticasEquipos
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

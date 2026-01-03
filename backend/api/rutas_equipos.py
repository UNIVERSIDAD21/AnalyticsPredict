# -*- coding: utf-8 -*-
"""rutas_equipos.py — Endpoint de equipos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter

from configuracion import CONFIGURACION
from .modelos_respuesta import RespuestaEquipos, RespuestaEstadisticasEquipos
from motor.tipos import InfoEquipo
from motor.utilidades import ABREVIATURAS_NBA, obtener_abreviatura, obtener_nombre_corto

router = APIRouter(prefix="/api", tags=["Equipos"])


def cargar_equipos() -> List[InfoEquipo]:
    """Carga equipos desde el archivo JSON de datos."""
    ruta = Path(CONFIGURACION.ruta_equipos)
    if ruta.exists():
        with ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return [InfoEquipo(**equipo) for equipo in datos]

    equipos: List[InfoEquipo] = []
    for nombre in sorted(ABREVIATURAS_NBA.keys()):
        equipos.append(
            InfoEquipo(
                id=obtener_abreviatura(nombre),
                nombre=nombre.title(),
                nombre_corto=obtener_nombre_corto(nombre),
                abreviatura=obtener_abreviatura(nombre),
            )
        )
    return equipos


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
    equipos = cargar_equipos()
    equipos_ordenados = sorted(equipos, key=lambda e: e.nombre)
    return RespuestaEquipos(
        exito=True,
        total=len(equipos_ordenados),
        equipos=[equipo.__dict__ for equipo in equipos_ordenados],
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

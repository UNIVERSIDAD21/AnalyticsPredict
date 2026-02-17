# -*- coding: utf-8 -*-
"""
rutas_predicciones.py — Endpoints de historial de predicciones.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from db import obtener_pool

router = APIRouter(prefix="/api/predicciones", tags=["Predicciones"])


class PrediccionHistorial(BaseModel):
    """Predicción para historial de usuario."""

    id: str
    partido_id: str
    fecha_partido: date
    equipo_local: str
    equipo_visitante: str
    mercado: str
    lado: str
    linea: float
    probabilidad_raw: Optional[float]
    probabilidad_calibrada: Optional[float]
    probabilidad_usada: Optional[float]
    valor_real: Optional[float]
    estado: str
    origen: str


class ResumenHistorial(BaseModel):
    """Resumen estadístico del historial."""

    total: int
    ganadas: int
    perdidas: int
    push: int
    pendientes: int
    win_rate: Optional[float]


class RespuestaHistorialPredicciones(BaseModel):
    """Respuesta de historial paginado."""

    exito: bool
    pagina: int
    tamano: int
    total: int
    total_paginas: int
    resumen: ResumenHistorial
    predicciones: List[PrediccionHistorial]


def _construir_filtros(
    *,
    mercado: Optional[str],
    estado: Optional[str],
    origen: Optional[str],
    desde: Optional[date],
    hasta: Optional[date],
) -> tuple[str, list[object]]:
    filtros: list[str] = []
    params: list[object] = []

    if mercado:
        filtros.append("pr.mercado = %s")
        params.append(mercado)
    if origen:
        filtros.append("pr.origen = %s")
        params.append(origen)
    if desde:
        filtros.append("p.fecha_partido >= %s")
        params.append(desde)
    if hasta:
        filtros.append("p.fecha_partido <= %s")
        params.append(hasta)

    if estado:
        if estado == "PENDIENTE":
            filtros.append("pr.resuelto = false")
        elif estado == "PUSH":
            filtros.append("pr.resuelto = true AND pr.outcome_binario IS NULL")
        elif estado == "GANADA":
            filtros.append("pr.outcome_binario = true")
        elif estado == "PERDIDA":
            filtros.append("pr.outcome_binario = false")

    where_sql = "WHERE " + " AND ".join(filtros) if filtros else ""
    return where_sql, params


@router.get(
    "/historial",
    response_model=RespuestaHistorialPredicciones,
    summary="Historial paginado de predicciones",
)
async def obtener_historial_predicciones(
    mercado: Optional[str] = Query(
        default=None,
        pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$",
    ),
    estado: Optional[str] = Query(
        default=None,
        pattern="^(GANADA|PERDIDA|PUSH|PENDIENTE)$",
    ),
    origen: Optional[str] = Query(default=None),
    desde: Optional[date] = Query(default=None),
    hasta: Optional[date] = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=5, le=100),
) -> RespuestaHistorialPredicciones:
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=400, detail="Fecha 'desde' no puede ser posterior a 'hasta'"
        )

    pool = obtener_pool()
    where_sql, params = _construir_filtros(
        mercado=mercado,
        estado=estado,
        origen=origen,
        desde=desde,
        hasta=hasta,
    )

    resumen_query = f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE pr.resuelto = false) AS pendientes,
            COUNT(*) FILTER (WHERE pr.outcome_binario = true) AS ganadas,
            COUNT(*) FILTER (WHERE pr.outcome_binario = false) AS perdidas,
            COUNT(*) FILTER (WHERE pr.outcome_binario IS NULL AND pr.resuelto = true) AS push
        FROM predicciones_registradas pr
        JOIN partidos_baloncesto p ON pr.partido_id = p.id
        {where_sql}
    """

    pagina_offset = (pagina - 1) * tamano
    consulta = f"""
        SELECT
            pr.id,
            pr.partido_id,
            p.fecha_partido,
            el.nombre AS equipo_local,
            ev.nombre AS equipo_visitante,
            pr.mercado,
            pr.lado,
            pr.linea,
            pr.p_raw,
            pr.p_calibrada,
            pr.valor_real,
            pr.origen,
            pr.resuelto,
            pr.outcome_binario
        FROM predicciones_registradas pr
        JOIN partidos_baloncesto p ON pr.partido_id = p.id
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        {where_sql}
        ORDER BY p.fecha_partido DESC, pr.timestamp_generacion DESC
        LIMIT %s
        OFFSET %s
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(resumen_query, params)
            resumen = cursor.fetchone()

            cursor.execute(consulta, params + [tamano, pagina_offset])
            filas = cursor.fetchall()

    total = int(resumen["total"]) if resumen else 0
    ganadas = int(resumen["ganadas"]) if resumen else 0
    perdidas = int(resumen["perdidas"]) if resumen else 0
    pendientes = int(resumen["pendientes"]) if resumen else 0
    push = int(resumen["push"]) if resumen else 0
    win_rate = round(ganadas / (ganadas + perdidas), 4) if (ganadas + perdidas) else None

    predicciones = []
    for fila in filas:
        if not fila:
            continue
        if not fila["resuelto"]:
            estado_resumen = "PENDIENTE"
        elif fila["outcome_binario"] is None:
            estado_resumen = "PUSH"
        elif fila["outcome_binario"]:
            estado_resumen = "GANADA"
        else:
            estado_resumen = "PERDIDA"

        probabilidad_calibrada = (
            float(fila["p_calibrada"]) if fila["p_calibrada"] is not None else None
        )
        probabilidad_raw = float(fila["p_raw"]) if fila["p_raw"] is not None else None

        predicciones.append(
            PrediccionHistorial(
                id=str(fila["id"]),
                partido_id=str(fila["partido_id"]),
                fecha_partido=fila["fecha_partido"],
                equipo_local=fila["equipo_local"],
                equipo_visitante=fila["equipo_visitante"],
                mercado=fila["mercado"],
                lado=fila["lado"],
                linea=float(fila["linea"]),
                probabilidad_raw=probabilidad_raw,
                probabilidad_calibrada=probabilidad_calibrada,
                probabilidad_usada=probabilidad_calibrada
                if probabilidad_calibrada is not None
                else probabilidad_raw,
                valor_real=float(fila["valor_real"]) if fila["valor_real"] is not None else None,
                estado=estado_resumen,
                origen=fila["origen"],
            )
        )

    total_paginas = max(1, (total + tamano - 1) // tamano)

    return RespuestaHistorialPredicciones(
        exito=True,
        pagina=pagina,
        tamano=tamano,
        total=total,
        total_paginas=total_paginas,
        resumen=ResumenHistorial(
            total=total,
            ganadas=ganadas,
            perdidas=perdidas,
            push=push,
            pendientes=pendientes,
            win_rate=win_rate,
        ),
        predicciones=predicciones,
    )


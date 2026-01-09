# -*- coding: utf-8 -*-
"""rutas_bitacora.py — Endpoints para la bitácora de apuestas."""

from __future__ import annotations

from datetime import date
import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg.rows import dict_row

from db import obtener_pool

# Importar Jsonb para serializar correctamente campos JSON en la base de datos.
try:
    # psycopg 3.x
    from psycopg.types.json import Jsonb  # type: ignore
except ImportError:
    # Fallback para versiones antiguas; si no está disponible, definiremos un wrapper
    Jsonb = None  # type: ignore
from .dependencias import obtener_usuario_id
from .modelos_peticion import PeticionActualizarResultado, PeticionCrearApuesta
from .modelos_respuesta import RespuestaApuesta, RespuestaListaApuestas, RespuestaResumenApuestas

router = APIRouter(prefix="/api/bitacora", tags=["Bitácora"])


def _serializar_jsonb(valor: object | None) -> object | None:
    if valor is None:
        return None
    if Jsonb is not None:
        return Jsonb(valor)
    return json.dumps(valor)


def _construir_payload_apuesta(peticion: PeticionCrearApuesta, usuario_id: UUID) -> dict:
    cuota_over = peticion.cuota_over
    cuota_under = peticion.cuota_under
    if cuota_over is None and cuota_under is None and peticion.cuota is not None:
        if peticion.lado == "UNDER":
            cuota_under = peticion.cuota
        else:
            cuota_over = peticion.cuota

    devig_metodo = peticion.devig_metodo
    devig_overround = peticion.devig_overround
    if devig_metodo == "exacto" and (cuota_over is None or cuota_under is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="devig_metodo=exacto requiere cuota_over y cuota_under.",
        )

    if peticion.score_total is not None and peticion.score_componentes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="score_total requiere score_componentes para trazabilidad.",
        )

    if peticion.kelly_fraccional is not None:
        if peticion.fraccion_kelly is None or peticion.stake_porcentaje is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="kelly_fraccional requiere fraccion_kelly y stake_porcentaje.",
            )

    return {
        "usuario_id": str(usuario_id),
        "partido_id": peticion.partido_id,
        "equipo_local": peticion.equipo_local,
        "equipo_visitante": peticion.equipo_visitante,
        "fecha_partido": peticion.fecha_partido,
        "mercado": peticion.mercado,
        "lado": peticion.lado,
        "linea": peticion.linea,
        "cuota": peticion.cuota,
        "cuota_over": cuota_over,
        "cuota_under": cuota_under,
        "stake": peticion.stake,
        "probabilidad_sistema": peticion.probabilidad_sistema,
        "confianza_sistema": peticion.confianza_sistema,
        "valor_esperado": peticion.valor_esperado,
        "devig_metodo": devig_metodo,
        "modo_devig": peticion.modo_devig,
        "devig_overround": devig_overround,
        "devig_p_mkt_raw": peticion.devig_p_mkt_raw,
        "devig_p_mkt_fair": peticion.devig_p_mkt_fair,
        "devig_advertencias": peticion.devig_advertencias,
        "edge_real": peticion.edge_real,
        "score_total": peticion.score_total,
        "score_componentes": _serializar_jsonb(peticion.score_componentes),
        "score_explicacion": peticion.score_explicacion,
        "score_penalizaciones": peticion.score_penalizaciones,
        "kelly_full": peticion.kelly_full,
        "kelly_fraccional": peticion.kelly_fraccional,
        "fraccion_kelly": peticion.fraccion_kelly,
        "stake_porcentaje": peticion.stake_porcentaje,
        "bankroll_momento": peticion.bankroll_momento,
        "perfil_riesgo_usado": peticion.perfil_riesgo_usado,
        "sizing_advertencias": peticion.sizing_advertencias,
        "sizing_penalizaciones": _serializar_jsonb(peticion.sizing_penalizaciones),
        "prediccion_media": peticion.prediccion_media,
        "prediccion_desviacion": peticion.prediccion_desviacion,
        "razones": _serializar_jsonb(peticion.razones),
    }


def _construir_where(
    usuario_id: UUID,
    resultado: Optional[str],
    mercado: Optional[str],
    confianza: Optional[str],
    desde: Optional[date],
    hasta: Optional[date],
    busqueda: Optional[str],
) -> tuple[str, List[object]]:
    condiciones = ["usuario_id = %s"]
    parametros: List[object] = [str(usuario_id)]

    if resultado:
        condiciones.append("resultado = %s")
        parametros.append(resultado)
    if mercado:
        condiciones.append("mercado = %s")
        parametros.append(mercado)
    if confianza:
        condiciones.append("confianza_sistema = %s")
        parametros.append(confianza)
    if desde:
        condiciones.append("fecha_partido >= %s")
        parametros.append(desde)
    if hasta:
        condiciones.append("fecha_partido <= %s")
        parametros.append(hasta)
    if busqueda:
        condiciones.append("(equipo_local ILIKE %s OR equipo_visitante ILIKE %s)")
        termino = f"%{busqueda}%"
        parametros.extend([termino, termino])

    where_sql = " AND ".join(condiciones)
    return where_sql, parametros


@router.post("", summary="Guardar apuesta", response_model=RespuestaApuesta)
async def guardar_apuesta(
    peticion: PeticionCrearApuesta,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaApuesta:
    """Crea una apuesta con snapshot del análisis."""
    datos_apuesta = _construir_payload_apuesta(peticion, usuario_id)

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                INSERT INTO apuestas (
                    usuario_id,
                    partido_id,
                    equipo_local,
                    equipo_visitante,
                    fecha_partido,
                    mercado,
                    lado,
                    linea,
                    cuota,
                    cuota_over,
                    cuota_under,
                    stake,
                    probabilidad_sistema,
                    confianza_sistema,
                    valor_esperado,
                    devig_metodo,
                    modo_devig,
                    devig_overround,
                    devig_p_mkt_raw,
                    devig_p_mkt_fair,
                    devig_advertencias,
                    edge_real,
                    score_total,
                    score_componentes,
                    score_explicacion,
                    score_penalizaciones,
                    kelly_full,
                    kelly_fraccional,
                    fraccion_kelly,
                    stake_porcentaje,
                    bankroll_momento,
                    perfil_riesgo_usado,
                    sizing_advertencias,
                    sizing_penalizaciones,
                    prediccion_media,
                    prediccion_desviacion,
                    razones
                ) VALUES (
                    %(usuario_id)s,
                    %(partido_id)s,
                    %(equipo_local)s,
                    %(equipo_visitante)s,
                    %(fecha_partido)s,
                    %(mercado)s,
                    %(lado)s,
                    %(linea)s,
                    %(cuota)s,
                    %(cuota_over)s,
                    %(cuota_under)s,
                    %(stake)s,
                    %(probabilidad_sistema)s,
                    %(confianza_sistema)s,
                    %(valor_esperado)s,
                    %(devig_metodo)s,
                    %(modo_devig)s,
                    %(devig_overround)s,
                    %(devig_p_mkt_raw)s,
                    %(devig_p_mkt_fair)s,
                    %(devig_advertencias)s,
                    %(edge_real)s,
                    %(score_total)s,
                    %(score_componentes)s,
                    %(score_explicacion)s,
                    %(score_penalizaciones)s,
                    %(kelly_full)s,
                    %(kelly_fraccional)s,
                    %(fraccion_kelly)s,
                    %(stake_porcentaje)s,
                    %(bankroll_momento)s,
                    %(perfil_riesgo_usado)s,
                    %(sizing_advertencias)s,
                    %(sizing_penalizaciones)s,
                    %(prediccion_media)s,
                    %(prediccion_desviacion)s,
                    %(razones)s
                )
                RETURNING *
                """,
                datos_apuesta,
            )
            apuesta = cursor.fetchone()
    return RespuestaApuesta(exito=True, apuesta=apuesta)


@router.get("", summary="Listar apuestas", response_model=RespuestaListaApuestas)
async def listar_apuestas(
    usuario_id: UUID = Depends(obtener_usuario_id),
    resultado: Optional[str] = Query(None),
    mercado: Optional[str] = Query(None),
    confianza: Optional[str] = Query(None),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    busqueda: Optional[str] = Query(None),
    orden: Optional[str] = Query("reciente"),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(10, ge=1, le=50),
) -> RespuestaListaApuestas:
    """Lista apuestas con filtros y paginación."""
    where_sql, parametros = _construir_where(
        usuario_id=usuario_id,
        resultado=resultado,
        mercado=mercado,
        confianza=confianza,
        desde=desde,
        hasta=hasta,
        busqueda=busqueda,
    )

    if orden == "antiguo":
        orden_sql = "creado_en ASC"
    elif orden == "ganancia":
        orden_sql = "ganancia DESC, creado_en DESC"
    else:
        orden_sql = "creado_en DESC"

    offset = (pagina - 1) * tamano

    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM apuestas WHERE {where_sql}",
                parametros,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT *
                FROM apuestas
                WHERE {where_sql}
                ORDER BY {orden_sql}
                LIMIT %s OFFSET %s
                """,
                [*parametros, tamano, offset],
            )
            apuestas = cursor.fetchall()

    total_paginas = max(1, (total + tamano - 1) // tamano) if total else 0

    return RespuestaListaApuestas(
        exito=True,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        apuestas=apuestas,
    )


@router.get("/resumen", summary="Resumen de apuestas", response_model=RespuestaResumenApuestas)
async def resumen_apuestas(
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaResumenApuestas:
    """Retorna el resumen agregado de apuestas para el usuario."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM vista_resumen_apuestas
                WHERE usuario_id = %s
                """,
                [str(usuario_id)],
            )
            resumen = cursor.fetchone() or {}

    return RespuestaResumenApuestas(exito=True, resumen=resumen)


@router.get("/{apuesta_id}", summary="Detalle de apuesta", response_model=RespuestaApuesta)
async def obtener_apuesta(
    apuesta_id: UUID,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaApuesta:
    """Obtiene una apuesta por ID validando pertenencia."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT * FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            apuesta = cursor.fetchone()

    if not apuesta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")

    return RespuestaApuesta(exito=True, apuesta=apuesta)


@router.patch("/{apuesta_id}/resultado", summary="Actualizar resultado", response_model=RespuestaApuesta)
async def actualizar_resultado(
    apuesta_id: UUID,
    peticion: PeticionActualizarResultado,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> RespuestaApuesta:
    """Actualiza el resultado de una apuesta pendiente."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT resultado FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            fila = cursor.fetchone()

            if not fila:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")
            if fila["resultado"] != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Solo se pueden resolver apuestas pendientes.",
                )

            cursor.execute(
                """
                UPDATE apuestas
                SET resultado = %s,
                    puntos_reales = %s
                WHERE id = %s AND usuario_id = %s
                RETURNING *
                """,
                [peticion.resultado, peticion.puntos_reales, str(apuesta_id), str(usuario_id)],
            )
            apuesta = cursor.fetchone()

    return RespuestaApuesta(exito=True, apuesta=apuesta)


@router.delete("/{apuesta_id}", summary="Eliminar apuesta")
async def eliminar_apuesta(
    apuesta_id: UUID,
    usuario_id: UUID = Depends(obtener_usuario_id),
) -> dict:
    """Elimina una apuesta pendiente."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT resultado FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )
            fila = cursor.fetchone()

            if not fila:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apuesta no encontrada.")
            if fila["resultado"] != "PENDIENTE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Solo se pueden eliminar apuestas pendientes.",
                )

            cursor.execute(
                """
                DELETE FROM apuestas
                WHERE id = %s AND usuario_id = %s
                """,
                [str(apuesta_id), str(usuario_id)],
            )

    return {"exito": True, "mensaje": "Apuesta eliminada."}

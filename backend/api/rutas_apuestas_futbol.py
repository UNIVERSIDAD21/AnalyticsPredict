# -*- coding: utf-8 -*-
"""
rutas_apuestas_futbol.py — Endpoints para gestión de apuestas de fútbol.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Optional, List, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Depends
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    ApuestaRequest,
    ApuestaResponse,
    ApuestaUpdateRequest,
    ListaApuestasResponse,
    ResumenApuestas,
    ResolucionRequest,
    ResolucionResponse,
    ErrorResponse,
)
from .dependencias import obtener_usuario_actual, UsuarioActual

router = APIRouter(prefix="/api/futbol/apuestas", tags=["Fútbol - Apuestas"])
logger = logging.getLogger(__name__)

# Mercados válidos
MERCADOS_VALIDOS = {
    "CORNERS_1T", "CORNERS_2T", "CORNERS_FT",
    "CORNERS_LOCAL_1T", "CORNERS_LOCAL_2T", "CORNERS_LOCAL_FT",
    "CORNERS_VISITANTE_1T", "CORNERS_VISITANTE_2T", "CORNERS_VISITANTE_FT",
    "GOLES_1T", "GOLES_2T", "GOLES_FT",
    "GOLES_LOCAL_1T", "GOLES_LOCAL_2T", "GOLES_LOCAL_FT",
    "GOLES_VISITANTE_1T", "GOLES_VISITANTE_2T", "GOLES_VISITANTE_FT",
    "DISPAROS_FT", "DISPAROS_ARCO_FT",
    "DISPAROS_LOCAL_FT", "DISPAROS_LOCAL_ARCO_FT",
    "DISPAROS_VISITANTE_FT", "DISPAROS_VISITANTE_ARCO_FT",
}


def _calcular_resultado_real(mercado: str, partido: dict) -> Optional[float]:
    """Calcula el resultado real para un mercado específico."""
    mapping = {
        "CORNERS_FT": (partido.get("local_corners_total") or 0) + (partido.get("visitante_corners_total") or 0),
        "CORNERS_1T": (partido.get("local_corners_1t") or 0) + (partido.get("visitante_corners_1t") or 0),
        "CORNERS_2T": (partido.get("local_corners_2t") or 0) + (partido.get("visitante_corners_2t") or 0),
        "CORNERS_LOCAL_FT": partido.get("local_corners_total"),
        "CORNERS_LOCAL_1T": partido.get("local_corners_1t"),
        "CORNERS_LOCAL_2T": partido.get("local_corners_2t"),
        "CORNERS_VISITANTE_FT": partido.get("visitante_corners_total"),
        "CORNERS_VISITANTE_1T": partido.get("visitante_corners_1t"),
        "CORNERS_VISITANTE_2T": partido.get("visitante_corners_2t"),
        "GOLES_FT": (partido.get("local_goles_total") or 0) + (partido.get("visitante_goles_total") or 0),
        "GOLES_1T": (partido.get("local_goles_1t") or 0) + (partido.get("visitante_goles_1t") or 0),
        "GOLES_2T": (partido.get("local_goles_2t") or 0) + (partido.get("visitante_goles_2t") or 0),
        "GOLES_LOCAL_FT": partido.get("local_goles_total"),
        "GOLES_LOCAL_1T": partido.get("local_goles_1t"),
        "GOLES_LOCAL_2T": partido.get("local_goles_2t"),
        "GOLES_VISITANTE_FT": partido.get("visitante_goles_total"),
        "GOLES_VISITANTE_1T": partido.get("visitante_goles_1t"),
        "GOLES_VISITANTE_2T": partido.get("visitante_goles_2t"),
        "DISPAROS_FT": (partido.get("local_disparos_total") or 0) + (partido.get("visitante_disparos_total") or 0),
        "DISPAROS_ARCO_FT": (partido.get("local_disparos_arco") or 0) + (partido.get("visitante_disparos_arco") or 0),
        "DISPAROS_LOCAL_FT": partido.get("local_disparos_total"),
        "DISPAROS_LOCAL_ARCO_FT": partido.get("local_disparos_arco"),
        "DISPAROS_VISITANTE_FT": partido.get("visitante_disparos_total"),
        "DISPAROS_VISITANTE_ARCO_FT": partido.get("visitante_disparos_arco"),
    }
    return mapping.get(mercado)


def _determinar_confianza(probabilidad: float) -> str:
    """Determina el nivel de confianza basado en probabilidad."""
    if probabilidad >= 0.75:
        return "ALTA"
    elif probabilidad >= 0.55:
        return "MEDIA"
    return "BAJA"


@router.post(
    "",
    response_model=ApuestaResponse,
    summary="Registrar apuesta",
    description="Registra una nueva apuesta de fútbol.",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def crear_apuesta(
    request: ApuestaRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ApuestaResponse:
    """Registra una nueva apuesta."""
    pool = obtener_pool()

    # Validar mercado
    mercado = request.mercado.upper()
    if mercado not in MERCADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Mercado inválido: {mercado}"
        )

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar que el partido existe
                cursor.execute(
                    "SELECT id, estado, fecha_partido FROM partidos_futbol WHERE id = %s",
                    [str(request.partido_id)]
                )
                partido = cursor.fetchone()

                if not partido:
                    raise HTTPException(
                        status_code=404,
                        detail="Partido no encontrado"
                    )

                # Calcular probabilidad del sistema (simplificado)
                probabilidad_sistema = 0.5  # Default
                valor_esperado = (probabilidad_sistema * request.cuota) - 1
                confianza = _determinar_confianza(probabilidad_sistema)
                ganancia_potencial = request.stake * (request.cuota - 1)

                # Insertar apuesta
                apuesta_id = uuid4()
                insert_query = """
                    INSERT INTO apuestas_futbol (
                        id, usuario_id, partido_id, mercado, lado, linea,
                        cuota, stake, estado, probabilidad_sistema, confianza,
                        valor_esperado, ganancia_potencial, casa_apuestas, notas,
                        fecha_creacion
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, 'PENDIENTE', %s, %s,
                        %s, %s, %s, %s,
                        NOW()
                    )
                    RETURNING id, fecha_creacion
                """
                cursor.execute(insert_query, [
                    str(apuesta_id),
                    str(usuario.id),
                    str(request.partido_id),
                    mercado,
                    request.lado,
                    request.linea,
                    request.cuota,
                    request.stake,
                    probabilidad_sistema,
                    confianza,
                    valor_esperado,
                    ganancia_potencial,
                    request.casa_apuestas,
                    request.notas,
                ])
                resultado = cursor.fetchone()
                conn.commit()

                return ApuestaResponse(
                    id=apuesta_id,
                    partido_id=request.partido_id,
                    mercado=mercado,
                    lado=request.lado,
                    linea=request.linea,
                    cuota=request.cuota,
                    stake=request.stake,
                    estado="PENDIENTE",
                    probabilidad_sistema=probabilidad_sistema,
                    confianza=confianza,
                    valor_esperado=valor_esperado,
                    ganancia_potencial=ganancia_potencial,
                    fecha_creacion=resultado["fecha_creacion"],
                    casa_apuestas=request.casa_apuestas,
                    notas=request.notas,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando apuesta: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "",
    response_model=ListaApuestasResponse,
    summary="Listar apuestas",
    description="Lista las apuestas del usuario con filtros.",
)
async def listar_apuestas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    mercado: Optional[str] = Query(None, description="Filtrar por mercado"),
    desde: Optional[date] = Query(None, description="Fecha inicio"),
    hasta: Optional[date] = Query(None, description="Fecha fin"),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(20, ge=1, le=100),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ListaApuestasResponse:
    """Lista apuestas del usuario."""
    pool = obtener_pool()

    query = """
        SELECT
            a.id, a.partido_id, a.mercado, a.lado, a.linea,
            a.cuota, a.stake, a.estado, a.probabilidad_sistema,
            a.confianza, a.valor_esperado, a.ganancia_potencial,
            a.resultado, a.ganancia_real, a.fecha_creacion,
            a.fecha_resolucion, a.casa_apuestas, a.notas
        FROM apuestas_futbol a
        WHERE a.usuario_id = %s
    """
    count_query = "SELECT COUNT(*) FROM apuestas_futbol a WHERE a.usuario_id = %s"
    params = [str(usuario.id)]
    count_params = [str(usuario.id)]

    if estado:
        query += " AND a.estado = %s"
        count_query += " AND a.estado = %s"
        params.append(estado.upper())
        count_params.append(estado.upper())

    if mercado:
        query += " AND a.mercado = %s"
        count_query += " AND a.mercado = %s"
        params.append(mercado.upper())
        count_params.append(mercado.upper())

    if desde:
        query += " AND a.fecha_creacion >= %s"
        count_query += " AND a.fecha_creacion >= %s"
        params.append(desde)
        count_params.append(desde)

    if hasta:
        query += " AND a.fecha_creacion <= %s"
        count_query += " AND a.fecha_creacion <= %s"
        params.append(hasta)
        count_params.append(hasta)

    query += " ORDER BY a.fecha_creacion DESC"

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

                apuestas = [
                    ApuestaResponse(
                        id=fila["id"],
                        partido_id=fila["partido_id"],
                        mercado=fila["mercado"],
                        lado=fila["lado"],
                        linea=float(fila["linea"]),
                        cuota=float(fila["cuota"]),
                        stake=float(fila["stake"]),
                        estado=fila["estado"],
                        probabilidad_sistema=float(fila["probabilidad_sistema"]),
                        confianza=fila["confianza"],
                        valor_esperado=float(fila["valor_esperado"]),
                        ganancia_potencial=float(fila["ganancia_potencial"]),
                        resultado=fila["resultado"],
                        ganancia_real=float(fila["ganancia_real"]) if fila["ganancia_real"] else None,
                        fecha_creacion=fila["fecha_creacion"],
                        fecha_resolucion=fila["fecha_resolucion"],
                        casa_apuestas=fila["casa_apuestas"],
                        notas=fila["notas"],
                    )
                    for fila in filas
                ]

                # Calcular resumen
                resumen_query = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
                        SUM(CASE WHEN estado = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                        SUM(CASE WHEN estado = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
                        SUM(CASE WHEN estado = 'PUSH' THEN 1 ELSE 0 END) as push,
                        SUM(stake) as stake_total,
                        SUM(COALESCE(ganancia_real, 0)) as ganancia_neta
                    FROM apuestas_futbol
                    WHERE usuario_id = %s
                """
                cursor.execute(resumen_query, [str(usuario.id)])
                res = cursor.fetchone()

                resueltas = (res["ganadas"] or 0) + (res["perdidas"] or 0)
                win_rate = (res["ganadas"] or 0) / resueltas if resueltas > 0 else None
                roi = (float(res["ganancia_neta"] or 0) / float(res["stake_total"] or 1)) * 100 if res["stake_total"] else None

                resumen = ResumenApuestas(
                    total=res["total"] or 0,
                    pendientes=res["pendientes"] or 0,
                    ganadas=res["ganadas"] or 0,
                    perdidas=res["perdidas"] or 0,
                    push=res["push"] or 0,
                    roi=round(roi, 2) if roi else None,
                    win_rate=round(win_rate, 4) if win_rate else None,
                    stake_total=float(res["stake_total"] or 0),
                    ganancia_neta=float(res["ganancia_neta"] or 0),
                )

                return ListaApuestasResponse(
                    exito=True,
                    total=total,
                    resumen=resumen,
                    apuestas=apuestas,
                )

    except Exception as e:
        logger.error(f"Error listando apuestas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/{apuesta_id}",
    response_model=ApuestaResponse,
    summary="Detalle de apuesta",
    responses={404: {"model": ErrorResponse}},
)
async def obtener_apuesta(
    apuesta_id: UUID,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ApuestaResponse:
    """Obtiene detalle de una apuesta."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("""
                    SELECT * FROM apuestas_futbol
                    WHERE id = %s AND usuario_id = %s
                """, [str(apuesta_id), str(usuario.id)])
                fila = cursor.fetchone()

                if not fila:
                    raise HTTPException(status_code=404, detail="Apuesta no encontrada")

                return ApuestaResponse(
                    id=fila["id"],
                    partido_id=fila["partido_id"],
                    mercado=fila["mercado"],
                    lado=fila["lado"],
                    linea=float(fila["linea"]),
                    cuota=float(fila["cuota"]),
                    stake=float(fila["stake"]),
                    estado=fila["estado"],
                    probabilidad_sistema=float(fila["probabilidad_sistema"]),
                    confianza=fila["confianza"],
                    valor_esperado=float(fila["valor_esperado"]),
                    ganancia_potencial=float(fila["ganancia_potencial"]),
                    resultado=fila["resultado"],
                    ganancia_real=float(fila["ganancia_real"]) if fila["ganancia_real"] else None,
                    fecha_creacion=fila["fecha_creacion"],
                    fecha_resolucion=fila["fecha_resolucion"],
                    casa_apuestas=fila["casa_apuestas"],
                    notas=fila["notas"],
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo apuesta {apuesta_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.patch(
    "/{apuesta_id}",
    response_model=ApuestaResponse,
    summary="Actualizar apuesta",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def actualizar_apuesta(
    apuesta_id: UUID,
    request: ApuestaUpdateRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ApuestaResponse:
    """Actualiza una apuesta pendiente."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar que existe y es del usuario
                cursor.execute("""
                    SELECT * FROM apuestas_futbol
                    WHERE id = %s AND usuario_id = %s
                """, [str(apuesta_id), str(usuario.id)])
                apuesta = cursor.fetchone()

                if not apuesta:
                    raise HTTPException(status_code=404, detail="Apuesta no encontrada")

                if apuesta["estado"] != "PENDIENTE":
                    raise HTTPException(
                        status_code=400,
                        detail="Solo se pueden modificar apuestas pendientes"
                    )

                # Cancelar si se solicita
                if request.cancelar:
                    cursor.execute("""
                        UPDATE apuestas_futbol
                        SET estado = 'CANCELADA', fecha_resolucion = NOW()
                        WHERE id = %s
                    """, [str(apuesta_id)])
                    conn.commit()
                    apuesta["estado"] = "CANCELADA"
                else:
                    # Actualizar campos
                    updates = []
                    params = []

                    if request.stake is not None:
                        updates.append("stake = %s")
                        params.append(request.stake)

                    if request.cuota is not None:
                        updates.append("cuota = %s")
                        params.append(request.cuota)

                    if request.notas is not None:
                        updates.append("notas = %s")
                        params.append(request.notas)

                    if updates:
                        params.append(str(apuesta_id))
                        cursor.execute(
                            f"UPDATE apuestas_futbol SET {', '.join(updates)} WHERE id = %s",
                            params
                        )
                        conn.commit()

                # Obtener apuesta actualizada
                return await obtener_apuesta(apuesta_id, usuario)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando apuesta {apuesta_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post(
    "/resolver",
    response_model=ResolucionResponse,
    summary="Resolver apuestas",
    description="Resuelve apuestas pendientes contra resultados reales.",
)
async def resolver_apuestas(
    request: ResolucionRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ResolucionResponse:
    """Resuelve apuestas pendientes."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Obtener apuestas pendientes de partidos finalizados
                query = """
                    SELECT
                        a.*,
                        pf.local_goles_1t, pf.local_goles_2t, pf.local_goles_total,
                        pf.visitante_goles_1t, pf.visitante_goles_2t, pf.visitante_goles_total,
                        pf.local_corners_1t, pf.local_corners_2t, pf.local_corners_total,
                        pf.visitante_corners_1t, pf.visitante_corners_2t, pf.visitante_corners_total,
                        pf.local_disparos_total, pf.local_disparos_arco,
                        pf.visitante_disparos_total, pf.visitante_disparos_arco
                    FROM apuestas_futbol a
                    JOIN partidos_futbol pf ON a.partido_id = pf.id
                    WHERE a.usuario_id = %s
                      AND a.estado = 'PENDIENTE'
                      AND pf.estado = 'FINALIZADO'
                """
                params = [str(usuario.id)]

                if request.partido_id:
                    query += " AND a.partido_id = %s"
                    params.append(str(request.partido_id))

                cursor.execute(query, params)
                apuestas = cursor.fetchall()

                resueltas = 0
                ganadas = 0
                perdidas = 0
                push = 0
                errores = 0
                ganancia_neta = 0.0

                for apuesta in apuestas:
                    try:
                        resultado_real = _calcular_resultado_real(apuesta["mercado"], apuesta)

                        if resultado_real is None:
                            errores += 1
                            continue

                        linea = float(apuesta["linea"])
                        lado = apuesta["lado"]
                        stake = float(apuesta["stake"])
                        cuota = float(apuesta["cuota"])

                        # Determinar resultado
                        if resultado_real == linea:
                            estado = "PUSH"
                            ganancia = 0.0
                            push += 1
                        elif (lado == "OVER" and resultado_real > linea) or \
                             (lado == "UNDER" and resultado_real < linea):
                            estado = "GANADA"
                            ganancia = stake * (cuota - 1)
                            ganadas += 1
                        else:
                            estado = "PERDIDA"
                            ganancia = -stake
                            perdidas += 1

                        # Actualizar apuesta
                        cursor.execute("""
                            UPDATE apuestas_futbol
                            SET estado = %s,
                                resultado = %s,
                                ganancia_real = %s,
                                fecha_resolucion = NOW()
                            WHERE id = %s
                        """, [estado, str(resultado_real), ganancia, str(apuesta["id"])])

                        ganancia_neta += ganancia
                        resueltas += 1

                    except Exception as e:
                        logger.error(f"Error resolviendo apuesta {apuesta['id']}: {e}")
                        errores += 1

                conn.commit()

                return ResolucionResponse(
                    exito=True,
                    resueltas=resueltas,
                    ganadas=ganadas,
                    perdidas=perdidas,
                    push=push,
                    errores=errores,
                    ganancia_neta=round(ganancia_neta, 2),
                )

    except Exception as e:
        logger.error(f"Error resolviendo apuestas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/estadisticas",
    response_model=ResumenApuestas,
    summary="Estadísticas de apuestas",
)
async def obtener_estadisticas_apuestas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    agrupar_por: Optional[str] = Query(None, description="mercado, mes, competicion"),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ResumenApuestas:
    """Obtiene estadísticas agregadas de apuestas."""
    pool = obtener_pool()

    query = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN estado = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
            SUM(CASE WHEN estado = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
            SUM(CASE WHEN estado = 'PUSH' THEN 1 ELSE 0 END) as push,
            SUM(stake) as stake_total,
            SUM(COALESCE(ganancia_real, 0)) as ganancia_neta
        FROM apuestas_futbol
        WHERE usuario_id = %s
    """
    params = [str(usuario.id)]

    if desde:
        query += " AND fecha_creacion >= %s"
        params.append(desde)

    if hasta:
        query += " AND fecha_creacion <= %s"
        params.append(hasta)

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, params)
                res = cursor.fetchone()

                resueltas = (res["ganadas"] or 0) + (res["perdidas"] or 0)
                win_rate = (res["ganadas"] or 0) / resueltas if resueltas > 0 else None
                roi = (float(res["ganancia_neta"] or 0) / float(res["stake_total"] or 1)) * 100 if res["stake_total"] else None

                return ResumenApuestas(
                    total=res["total"] or 0,
                    pendientes=res["pendientes"] or 0,
                    ganadas=res["ganadas"] or 0,
                    perdidas=res["perdidas"] or 0,
                    push=res["push"] or 0,
                    roi=round(roi, 2) if roi else None,
                    win_rate=round(win_rate, 4) if win_rate else None,
                    stake_total=float(res["stake_total"] or 0),
                    ganancia_neta=float(res["ganancia_neta"] or 0),
                )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

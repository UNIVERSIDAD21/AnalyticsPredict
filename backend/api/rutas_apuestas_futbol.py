# -*- coding: utf-8 -*-
"""
rutas_apuestas_futbol.py — Endpoints para gestión de apuestas de fútbol.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, date
from typing import Optional, List, Literal, Dict, Any, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Depends
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    ApuestaRequest,
    ApuestaResponse,
    PartidoResumen,
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

_APUESTAS_COLUMNAS_CACHE: Dict[str, Any] = {"columnas": set(), "timestamp": 0.0}
_APUESTAS_COLUMNAS_TTL = 300.0


def _obtener_columnas_apuestas(cursor) -> Set[str]:
    """Obtiene columnas existentes en apuestas_futbol con cache simple."""
    ahora = time.time()
    columnas_cache = _APUESTAS_COLUMNAS_CACHE.get("columnas", set())
    timestamp = _APUESTAS_COLUMNAS_CACHE.get("timestamp", 0.0)

    if columnas_cache and (ahora - timestamp) < _APUESTAS_COLUMNAS_TTL:
        return columnas_cache

    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'apuestas_futbol'
        """
    )
    columnas = {row["column_name"] for row in cursor.fetchall()}
    _APUESTAS_COLUMNAS_CACHE["columnas"] = columnas
    _APUESTAS_COLUMNAS_CACHE["timestamp"] = ahora
    return columnas


def _resolver_columna(columnas: Set[str], *candidatos: str) -> Optional[str]:
    """Devuelve el primer nombre de columna disponible."""
    for candidato in candidatos:
        if candidato in columnas:
            return candidato
    return None


def _sql_columna(columna: Optional[str], alias: str) -> str:
    """Devuelve SQL seguro con alias, o NULL si no existe la columna."""
    if columna:
        return f"a.{columna} as {alias}"
    return f"NULL as {alias}"


def _construir_partido_resumen(fila: Dict[str, Any]) -> Optional[PartidoResumen]:
    """Construye PartidoResumen si hay datos de partido."""
    partido_id = fila.get("partido_id_detalle")
    fecha_partido = fila.get("fecha_partido")
    if not partido_id or not fecha_partido:
        return None

    return PartidoResumen(
        id=partido_id,
        competicion=fila.get("competicion_nombre") or "",
        competicion_nombre=fila.get("competicion_nombre"),
        fecha_partido=fecha_partido,
        equipo_local=fila.get("equipo_local_id") or fila.get("equipo_local_nombre") or "",
        equipo_local_nombre=fila.get("equipo_local_nombre"),
        equipo_visitante=fila.get("equipo_visitante_id") or fila.get("equipo_visitante_nombre") or "",
        equipo_visitante_nombre=fila.get("equipo_visitante_nombre"),
        estado=fila.get("partido_estado") or "",
        jornada=fila.get("jornada"),
        goles_local=fila.get("goles_local"),
        goles_visitante=fila.get("goles_visitante"),
    )

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
    description="Registra una nueva apuesta de futbol.",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def crear_apuesta(
    request: ApuestaRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ApuestaResponse:
    """Registra una nueva apuesta."""
    pool = obtener_pool()

    # Validar mercado
    mercado = (request.mercado or "").upper()
    if mercado not in MERCADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Mercado invalido: {mercado}",
        )

    if not request.partido_id:
        raise HTTPException(status_code=400, detail="partido_id es requerido")
    if not request.lado:
        raise HTTPException(status_code=400, detail="lado es requerido")
    if request.stake is None or request.stake <= 0:
        raise HTTPException(status_code=400, detail="stake debe ser mayor a 0")

    cuota = request.cuota or 0.0
    if cuota < 0:
        raise HTTPException(status_code=400, detail="cuota invalida")

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Verificar que el partido existe
                cursor.execute(
                    """
                    SELECT
                        p.id as partido_id_detalle,
                        p.fecha_partido,
                        p.estado as partido_estado,
                        p.jornada,
                        p.equipo_local_id,
                        p.equipo_visitante_id,
                        c.nombre as competicion_nombre,
                        el.nombre as equipo_local_nombre,
                        ev.nombre as equipo_visitante_nombre,
                        p.local_goles_total as goles_local,
                        p.visitante_goles_total as goles_visitante
                    FROM partidos_futbol p
                    JOIN competiciones_futbol c ON p.competicion_id = c.id
                    JOIN equipos_futbol el ON p.equipo_local_id = el.id
                    JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
                    WHERE p.id = %s
                    """,
                    [str(request.partido_id)],
                )
                partido = cursor.fetchone()

                if not partido:
                    raise HTTPException(
                        status_code=404,
                        detail="Partido no encontrado",
                    )

                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_prob = _resolver_columna(columnas, "probabilidad_sistema", "probabilidad")
                col_confianza = _resolver_columna(columnas, "confianza", "confianza_sistema")
                col_valor = _resolver_columna(columnas, "valor_esperado")
                col_ganancia_pot = _resolver_columna(
                    columnas,
                    "ganancia_potencial",
                    "ganancias_potenciales",
                    "ganancia_potenciales",
                )
                col_casa = _resolver_columna(columnas, "casa_apuestas", "casa_apuesta")
                col_fecha_creacion = _resolver_columna(
                    columnas, "fecha_creacion", "creado_en", "created_at"
                )
                col_cuota = _resolver_columna(columnas, "cuota", "odds", "cuota_decimal")

                # Calcular probabilidad del sistema (simplificado)
                probabilidad_sistema = 0.5
                valor_esperado = (probabilidad_sistema * cuota) - 1 if cuota else 0.0
                confianza = _determinar_confianza(probabilidad_sistema)
                ganancia_potencial = request.stake * (cuota - 1) if cuota else 0.0

                apuesta_id = uuid4()
                columnas_insert = [
                    "id",
                    "usuario_id",
                    "partido_id",
                    "mercado",
                    "lado",
                    "linea",
                    "stake",
                ]
                valores_insert = [
                    str(apuesta_id),
                    str(usuario.id),
                    str(request.partido_id),
                    mercado,
                    request.lado,
                    request.linea,
                    request.stake,
                ]

                if col_cuota:
                    columnas_insert.append(col_cuota)
                    valores_insert.append(cuota)

                if col_estado:
                    columnas_insert.append(col_estado)
                    valores_insert.append("PENDIENTE")

                if col_prob:
                    columnas_insert.append(col_prob)
                    valores_insert.append(probabilidad_sistema)

                if col_confianza:
                    columnas_insert.append(col_confianza)
                    valores_insert.append(confianza)

                if col_valor:
                    columnas_insert.append(col_valor)
                    valores_insert.append(valor_esperado)

                if col_ganancia_pot:
                    columnas_insert.append(col_ganancia_pot)
                    valores_insert.append(ganancia_potencial)

                if col_casa and request.casa_apuestas is not None:
                    columnas_insert.append(col_casa)
                    valores_insert.append(request.casa_apuestas)

                if "notas" in columnas:
                    columnas_insert.append("notas")
                    valores_insert.append(request.notas)

                if col_fecha_creacion:
                    columnas_insert.append(col_fecha_creacion)
                    valores_insert.append(datetime.now())

                placeholders = ", ".join(["%s"] * len(valores_insert))
                insert_query = (
                    f"INSERT INTO apuestas_futbol ({', '.join(columnas_insert)}) "
                    f"VALUES ({placeholders})"
                )

                returning = "id"
                if col_fecha_creacion:
                    returning = f"id, {col_fecha_creacion} as fecha_creacion"

                cursor.execute(f"{insert_query} RETURNING {returning}", valores_insert)
                resultado = cursor.fetchone() or {}
                conn.commit()

                fecha_creacion = resultado.get("fecha_creacion") or datetime.now()

                return ApuestaResponse(
                    id=apuesta_id,
                    partido_id=request.partido_id,
                    partido=_construir_partido_resumen(partido),
                    mercado=mercado,
                    lado=request.lado,
                    linea=request.linea,
                    cuota=cuota,
                    stake=request.stake,
                    estado="PENDIENTE",
                    probabilidad_sistema=probabilidad_sistema,
                    confianza=confianza,
                    valor_esperado=valor_esperado,
                    ganancia_potencial=ganancia_potencial,
                    fecha_creacion=fecha_creacion,
                    casa_apuestas=request.casa_apuestas,
                    notas=request.notas,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando apuesta: {e}", exc_info=True)
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
    limite: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ListaApuestasResponse:
    """Lista apuestas del usuario."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_resultado = _resolver_columna(columnas, "resultado", "resultado_real")
                col_ganancia_real = _resolver_columna(
                    columnas, "ganancia_real", "ganancias_reales", "ganancia", "ganancia_neta"
                )
                col_ganancia_pot = _resolver_columna(
                    columnas,
                    "ganancia_potencial",
                    "ganancias_potenciales",
                    "ganancia_potenciales",
                )
                col_prob = _resolver_columna(columnas, "probabilidad_sistema", "probabilidad")
                col_confianza = _resolver_columna(columnas, "confianza", "confianza_sistema")
                col_valor = _resolver_columna(columnas, "valor_esperado")
                col_fecha_creacion = _resolver_columna(
                    columnas, "fecha_creacion", "creado_en", "created_at"
                )
                col_fecha_resolucion = _resolver_columna(
                    columnas, "fecha_resolucion", "resuelto_en"
                )
                col_casa = _resolver_columna(columnas, "casa_apuestas", "casa_apuesta")
                col_cuota = _resolver_columna(columnas, "cuota", "odds", "cuota_decimal")

                select_cols = [
                    "a.id",
                    "a.partido_id",
                    "a.mercado",
                    "a.lado",
                    "a.linea",
                    _sql_columna(col_cuota, "cuota"),
                    "a.stake",
                    _sql_columna(col_estado, "estado"),
                    _sql_columna(col_prob, "probabilidad_sistema"),
                    _sql_columna(col_confianza, "confianza"),
                    _sql_columna(col_valor, "valor_esperado"),
                    _sql_columna(col_ganancia_pot, "ganancia_potencial"),
                    _sql_columna(col_resultado, "resultado"),
                    _sql_columna(col_ganancia_real, "ganancia_real"),
                    _sql_columna(col_fecha_creacion, "fecha_creacion"),
                    _sql_columna(col_fecha_resolucion, "fecha_resolucion"),
                    _sql_columna(col_casa, "casa_apuestas"),
                    "a.notas",
                    "p.id as partido_id_detalle",
                    "p.fecha_partido",
                    "p.estado as partido_estado",
                    "p.jornada",
                    "p.equipo_local_id",
                    "p.equipo_visitante_id",
                    "c.nombre as competicion_nombre",
                    "el.nombre as equipo_local_nombre",
                    "ev.nombre as equipo_visitante_nombre",
                    "p.local_goles_total as goles_local",
                    "p.visitante_goles_total as goles_visitante",
                ]

                query = f"""
                    SELECT {', '.join(select_cols)}
                    FROM apuestas_futbol a
                    LEFT JOIN partidos_futbol p ON a.partido_id = p.id
                    LEFT JOIN competiciones_futbol c ON p.competicion_id = c.id
                    LEFT JOIN equipos_futbol el ON p.equipo_local_id = el.id
                    LEFT JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
                    WHERE a.usuario_id = %s
                """
                params: List[Any] = [str(usuario.id)]

                if estado and col_estado:
                    query += f" AND a.{col_estado} = %s"
                    params.append(estado.upper())

                if mercado:
                    query += " AND a.mercado = %s"
                    params.append(mercado.upper())

                if desde and col_fecha_creacion:
                    query += f" AND a.{col_fecha_creacion} >= %s"
                    params.append(desde)

                if hasta and col_fecha_creacion:
                    query += f" AND a.{col_fecha_creacion} <= %s"
                    params.append(hasta)

                order_col = col_fecha_creacion or "id"
                query += f" ORDER BY a.{order_col} DESC"

                limite_final = limite if limite is not None else tamano
                offset_final = offset if offset is not None else (pagina - 1) * tamano
                query += " LIMIT %s OFFSET %s"
                params.extend([limite_final, offset_final])

                count_query = "SELECT COUNT(*) as total FROM apuestas_futbol a WHERE a.usuario_id = %s"
                count_params: List[Any] = [str(usuario.id)]

                if estado and col_estado:
                    count_query += f" AND a.{col_estado} = %s"
                    count_params.append(estado.upper())

                if mercado:
                    count_query += " AND a.mercado = %s"
                    count_params.append(mercado.upper())

                if desde and col_fecha_creacion:
                    count_query += f" AND a.{col_fecha_creacion} >= %s"
                    count_params.append(desde)

                if hasta and col_fecha_creacion:
                    count_query += f" AND a.{col_fecha_creacion} <= %s"
                    count_params.append(hasta)

                cursor.execute(count_query, count_params)
                total = cursor.fetchone()["total"]

                cursor.execute(query, params)
                filas = cursor.fetchall()

                apuestas = []
                for fila in filas:
                    apuestas.append(
                        ApuestaResponse(
                            id=fila["id"],
                            partido_id=fila["partido_id"],
                            partido=_construir_partido_resumen(fila),
                            mercado=fila["mercado"],
                            lado=fila["lado"],
                            linea=float(fila["linea"]),
                            cuota=float(fila.get("cuota") or 0),
                            stake=float(fila["stake"]),
                            estado=fila.get("estado") or "PENDIENTE",
                            probabilidad_sistema=float(fila.get("probabilidad_sistema") or 0),
                            confianza=fila.get("confianza") or "MEDIA",
                            valor_esperado=float(fila.get("valor_esperado") or 0),
                            ganancia_potencial=float(fila.get("ganancia_potencial") or 0),
                            resultado=fila.get("resultado"),
                            ganancia_real=float(fila["ganancia_real"]) if fila.get("ganancia_real") is not None else None,
                            fecha_creacion=fila.get("fecha_creacion") or datetime.now(),
                            fecha_resolucion=fila.get("fecha_resolucion"),
                            casa_apuestas=fila.get("casa_apuestas"),
                            notas=fila.get("notas"),
                        )
                    )

                resumen = ResumenApuestas(
                    total=total or 0,
                    pendientes=0,
                    ganadas=0,
                    perdidas=0,
                    push=0,
                    roi=None,
                    win_rate=None,
                    stake_total=0.0,
                    ganancia_neta=0.0,
                )

                if col_estado:
                    resumen_query = f"""
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN {col_estado} = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
                            SUM(CASE WHEN {col_estado} = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                            SUM(CASE WHEN {col_estado} = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
                            SUM(CASE WHEN {col_estado} = 'PUSH' THEN 1 ELSE 0 END) as push,
                            SUM(stake) as stake_total,
                            SUM(COALESCE({col_ganancia_real or '0'}, 0)) as ganancia_neta
                        FROM apuestas_futbol
                        WHERE usuario_id = %s
                    """
                    cursor.execute(resumen_query, [str(usuario.id)])
                    res = cursor.fetchone() or {}

                    resueltas = (res.get("ganadas") or 0) + (res.get("perdidas") or 0) + (res.get("push") or 0)
                    win_rate = (res.get("ganadas") or 0) / resueltas if resueltas > 0 else None
                    stake_total = float(res.get("stake_total") or 0)
                    ganancia_neta = float(res.get("ganancia_neta") or 0)
                    roi = (ganancia_neta / stake_total * 100) if stake_total > 0 else None

                    resumen = ResumenApuestas(
                        total=res.get("total") or total or 0,
                        pendientes=res.get("pendientes") or 0,
                        ganadas=res.get("ganadas") or 0,
                        perdidas=res.get("perdidas") or 0,
                        push=res.get("push") or 0,
                        roi=round(roi, 2) if roi is not None else None,
                        win_rate=round(win_rate, 4) if win_rate is not None else None,
                        stake_total=stake_total,
                        ganancia_neta=ganancia_neta,
                    )

                return ListaApuestasResponse(
                    exito=True,
                    total=total or 0,
                    resumen=resumen,
                    apuestas=apuestas,
                )

    except Exception as e:
        logger.error(f"Error listando apuestas: {e}", exc_info=True)
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
                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_resultado = _resolver_columna(columnas, "resultado", "resultado_real")
                col_ganancia_real = _resolver_columna(
                    columnas, "ganancia_real", "ganancias_reales", "ganancia", "ganancia_neta"
                )
                col_ganancia_pot = _resolver_columna(
                    columnas,
                    "ganancia_potencial",
                    "ganancias_potenciales",
                    "ganancia_potenciales",
                )
                col_prob = _resolver_columna(columnas, "probabilidad_sistema", "probabilidad")
                col_confianza = _resolver_columna(columnas, "confianza", "confianza_sistema")
                col_valor = _resolver_columna(columnas, "valor_esperado")
                col_fecha_creacion = _resolver_columna(
                    columnas, "fecha_creacion", "creado_en", "created_at"
                )
                col_fecha_resolucion = _resolver_columna(
                    columnas, "fecha_resolucion", "resuelto_en"
                )
                col_casa = _resolver_columna(columnas, "casa_apuestas", "casa_apuesta")
                col_cuota = _resolver_columna(columnas, "cuota", "odds", "cuota_decimal")

                select_cols = [
                    "a.id",
                    "a.partido_id",
                    "a.mercado",
                    "a.lado",
                    "a.linea",
                    _sql_columna(col_cuota, "cuota"),
                    "a.stake",
                    _sql_columna(col_estado, "estado"),
                    _sql_columna(col_prob, "probabilidad_sistema"),
                    _sql_columna(col_confianza, "confianza"),
                    _sql_columna(col_valor, "valor_esperado"),
                    _sql_columna(col_ganancia_pot, "ganancia_potencial"),
                    _sql_columna(col_resultado, "resultado"),
                    _sql_columna(col_ganancia_real, "ganancia_real"),
                    _sql_columna(col_fecha_creacion, "fecha_creacion"),
                    _sql_columna(col_fecha_resolucion, "fecha_resolucion"),
                    _sql_columna(col_casa, "casa_apuestas"),
                    "a.notas",
                    "p.id as partido_id_detalle",
                    "p.fecha_partido",
                    "p.estado as partido_estado",
                    "p.jornada",
                    "p.equipo_local_id",
                    "p.equipo_visitante_id",
                    "c.nombre as competicion_nombre",
                    "el.nombre as equipo_local_nombre",
                    "ev.nombre as equipo_visitante_nombre",
                    "p.local_goles_total as goles_local",
                    "p.visitante_goles_total as goles_visitante",
                ]

                query = f"""
                    SELECT {', '.join(select_cols)}
                    FROM apuestas_futbol a
                    LEFT JOIN partidos_futbol p ON a.partido_id = p.id
                    LEFT JOIN competiciones_futbol c ON p.competicion_id = c.id
                    LEFT JOIN equipos_futbol el ON p.equipo_local_id = el.id
                    LEFT JOIN equipos_futbol ev ON p.equipo_visitante_id = ev.id
                    WHERE a.id = %s AND a.usuario_id = %s
                """
                cursor.execute(query, [str(apuesta_id), str(usuario.id)])
                fila = cursor.fetchone()

                if not fila:
                    raise HTTPException(status_code=404, detail="Apuesta no encontrada")

                return ApuestaResponse(
                    id=fila["id"],
                    partido_id=fila["partido_id"],
                    partido=_construir_partido_resumen(fila),
                    mercado=fila["mercado"],
                    lado=fila["lado"],
                    linea=float(fila["linea"]),
                    cuota=float(fila.get("cuota") or 0),
                    stake=float(fila["stake"]),
                    estado=fila.get("estado") or "PENDIENTE",
                    probabilidad_sistema=float(fila.get("probabilidad_sistema") or 0),
                    confianza=fila.get("confianza") or "MEDIA",
                    valor_esperado=float(fila.get("valor_esperado") or 0),
                    ganancia_potencial=float(fila.get("ganancia_potencial") or 0),
                    resultado=fila.get("resultado"),
                    ganancia_real=float(fila["ganancia_real"]) if fila.get("ganancia_real") is not None else None,
                    fecha_creacion=fila.get("fecha_creacion") or datetime.now(),
                    fecha_resolucion=fila.get("fecha_resolucion"),
                    casa_apuestas=fila.get("casa_apuestas"),
                    notas=fila.get("notas"),
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo apuesta {apuesta_id}: {e}", exc_info=True)
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
                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_cuota = _resolver_columna(columnas, "cuota", "odds", "cuota_decimal")
                col_fecha_resolucion = _resolver_columna(
                    columnas, "fecha_resolucion", "resuelto_en"
                )
                col_notas = "notas" if "notas" in columnas else None

                select_cols = [
                    "a.id",
                    _sql_columna(col_estado, "estado"),
                ]
                cursor.execute(
                    f"SELECT {', '.join(select_cols)} FROM apuestas_futbol a WHERE a.id = %s AND a.usuario_id = %s",
                    [str(apuesta_id), str(usuario.id)],
                )
                apuesta = cursor.fetchone()

                if not apuesta:
                    raise HTTPException(status_code=404, detail="Apuesta no encontrada")

                estado_actual = apuesta.get("estado") or "PENDIENTE"
                if estado_actual != "PENDIENTE":
                    raise HTTPException(
                        status_code=400,
                        detail="Solo se pueden modificar apuestas pendientes"
                    )

                updates = []
                params: List[Any] = []

                if request.cancelar:
                    if not col_estado:
                        raise HTTPException(
                            status_code=400,
                            detail="No se puede cancelar la apuesta sin columna estado",
                        )
                    updates.append(f"{col_estado} = %s")
                    params.append("CANCELADA")
                    if col_fecha_resolucion:
                        updates.append(f"{col_fecha_resolucion} = NOW()")
                else:
                    if request.stake is not None:
                        updates.append("stake = %s")
                        params.append(request.stake)

                    if request.cuota is not None and col_cuota:
                        updates.append(f"{col_cuota} = %s")
                        params.append(request.cuota)

                    if request.notas is not None and col_notas:
                        updates.append("notas = %s")
                        params.append(request.notas)

                if updates:
                    params.append(str(apuesta_id))
                    cursor.execute(
                        f"UPDATE apuestas_futbol SET {', '.join(updates)} WHERE id = %s",
                        params,
                    )
                    conn.commit()

                # Obtener apuesta actualizada
                return await obtener_apuesta(apuesta_id, usuario)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando apuesta {apuesta_id}: {e}", exc_info=True)
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
                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_resultado = _resolver_columna(columnas, "resultado", "resultado_real")
                col_ganancia_real = _resolver_columna(
                    columnas, "ganancia_real", "ganancias_reales", "ganancia", "ganancia_neta"
                )
                col_cuota = _resolver_columna(columnas, "cuota", "odds", "cuota_decimal")
                col_fecha_resolucion = _resolver_columna(
                    columnas, "fecha_resolucion", "resuelto_en"
                )

                select_cols = [
                    "a.id",
                    "a.partido_id",
                    "a.mercado",
                    "a.lado",
                    "a.linea",
                    "a.stake",
                    _sql_columna(col_cuota, "cuota"),
                    "pf.local_goles_1t",
                    "pf.local_goles_2t",
                    "pf.local_goles_total",
                    "pf.visitante_goles_1t",
                    "pf.visitante_goles_2t",
                    "pf.visitante_goles_total",
                    "pf.local_corners_1t",
                    "pf.local_corners_2t",
                    "pf.local_corners_total",
                    "pf.visitante_corners_1t",
                    "pf.visitante_corners_2t",
                    "pf.visitante_corners_total",
                    "pf.local_disparos_total",
                    "pf.local_disparos_arco",
                    "pf.visitante_disparos_total",
                    "pf.visitante_disparos_arco",
                ]

                query = f"""
                    SELECT {', '.join(select_cols)}
                    FROM apuestas_futbol a
                    JOIN partidos_futbol pf ON a.partido_id = pf.id
                    WHERE a.usuario_id = %s
                      AND pf.estado = 'FINALIZADO'
                """
                params = [str(usuario.id)]

                if col_estado:
                    query += f" AND a.{col_estado} = 'PENDIENTE'"

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
                        cuota = float(apuesta.get("cuota") or 0)
                        if cuota <= 1:
                            cuota = 1.0

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

                        updates = []
                        params_update: List[Any] = []

                        if col_estado:
                            updates.append(f"{col_estado} = %s")
                            params_update.append(estado)
                        if col_resultado:
                            updates.append(f"{col_resultado} = %s")
                            params_update.append(str(resultado_real))
                        if col_ganancia_real:
                            updates.append(f"{col_ganancia_real} = %s")
                            params_update.append(ganancia)
                        if col_fecha_resolucion:
                            updates.append(f"{col_fecha_resolucion} = NOW()")

                        if updates:
                            params_update.append(str(apuesta["id"]))
                            cursor.execute(
                                f"UPDATE apuestas_futbol SET {', '.join(updates)} WHERE id = %s",
                                params_update,
                            )
                            ganancia_neta += ganancia
                            resueltas += 1
                        else:
                            errores += 1

                    except Exception as e:
                        logger.error(
                            f"Error resolviendo apuesta {apuesta['id']}: {e}", exc_info=True
                        )
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
        logger.error(f"Error resolviendo apuestas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/estadisticas",
    response_model=ResumenApuestas,
    summary="Estadisticas de apuestas",
)
async def obtener_estadisticas_apuestas(
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
    agrupar_por: Optional[str] = Query(None, description="mercado, mes, competicion"),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ResumenApuestas:
    """Obtiene estadisticas agregadas de apuestas."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                columnas = _obtener_columnas_apuestas(cursor)
                col_estado = _resolver_columna(columnas, "estado", "status")
                col_ganancia_real = _resolver_columna(
                    columnas, "ganancia_real", "ganancias_reales", "ganancia", "ganancia_neta"
                )
                col_fecha_creacion = _resolver_columna(
                    columnas, "fecha_creacion", "creado_en", "created_at"
                )

                select_cols = [
                    "COUNT(*) as total",
                    (
                        f"SUM(CASE WHEN {col_estado} = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes"
                        if col_estado
                        else "0 as pendientes"
                    ),
                    (
                        f"SUM(CASE WHEN {col_estado} = 'GANADA' THEN 1 ELSE 0 END) as ganadas"
                        if col_estado
                        else "0 as ganadas"
                    ),
                    (
                        f"SUM(CASE WHEN {col_estado} = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas"
                        if col_estado
                        else "0 as perdidas"
                    ),
                    (
                        f"SUM(CASE WHEN {col_estado} = 'PUSH' THEN 1 ELSE 0 END) as push"
                        if col_estado
                        else "0 as push"
                    ),
                    "SUM(stake) as stake_total",
                    (
                        f"SUM(COALESCE({col_ganancia_real}, 0)) as ganancia_neta"
                        if col_ganancia_real
                        else "0 as ganancia_neta"
                    ),
                ]

                query = f"""
                    SELECT {', '.join(select_cols)}
                    FROM apuestas_futbol
                    WHERE usuario_id = %s
                """
                params: List[Any] = [str(usuario.id)]

                if desde and col_fecha_creacion:
                    query += f" AND {col_fecha_creacion} >= %s"
                    params.append(desde)

                if hasta and col_fecha_creacion:
                    query += f" AND {col_fecha_creacion} <= %s"
                    params.append(hasta)

                cursor.execute(query, params)
                res = cursor.fetchone() or {}

                resueltas = (res.get("ganadas") or 0) + (res.get("perdidas") or 0) + (res.get("push") or 0)
                win_rate = (res.get("ganadas") or 0) / resueltas if resueltas > 0 else None
                stake_total = float(res.get("stake_total") or 0)
                ganancia_neta = float(res.get("ganancia_neta") or 0)
                roi = (ganancia_neta / stake_total * 100) if stake_total > 0 else None

                return ResumenApuestas(
                    total=res.get("total") or 0,
                    pendientes=res.get("pendientes") or 0,
                    ganadas=res.get("ganadas") or 0,
                    perdidas=res.get("perdidas") or 0,
                    push=res.get("push") or 0,
                    roi=round(roi, 2) if roi is not None else None,
                    win_rate=round(win_rate, 4) if win_rate is not None else None,
                    stake_total=stake_total,
                    ganancia_neta=ganancia_neta,
                )

    except Exception as e:
        logger.error(f"Error obteniendo estadisticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

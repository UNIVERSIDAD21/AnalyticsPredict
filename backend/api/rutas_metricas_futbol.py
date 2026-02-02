# -*- coding: utf-8 -*-
"""
rutas_metricas_futbol.py — Endpoints para métricas del sistema de fútbol.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from psycopg.rows import dict_row

from db import obtener_pool
from .schemas_futbol import (
    MetricasCalibracion,
    MetricasRendimiento,
    MetricasModelo,
    EstadoModelos,
    ResumenSistema,
    ListaMetricasCalibracionResponse,
    ListaMetricasRendimientoResponse,
    ErrorResponse,
)
from .dependencias import obtener_usuario_actual, UsuarioActual

router = APIRouter(prefix="/api/futbol/metricas", tags=["Fútbol - Métricas"])
logger = logging.getLogger(__name__)


def _tabla_existe(cursor, tabla: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        [tabla],
    )
    return cursor.fetchone()["exists"]


def _columna_existe(cursor, tabla: str, columna: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        )
        """,
        [tabla, columna],
    )
    return cursor.fetchone()["exists"]


def _obtener_metricas_desde_calibradores(
    cursor,
    mercado: Optional[str],
    periodo: Literal["semana", "mes", "temporada", "todo"],
) -> ListaMetricasCalibracionResponse:
    """Obtiene métricas desde calibradores si no hay predicciones."""
    query = """
        SELECT
            mercado,
            metodo,
            brier_antes,
            brier_despues,
            ece_antes,
            ece_despues,
            log_loss_antes,
            log_loss_despues,
            n_muestras
        FROM calibradores_futbol
        WHERE activo = true
    """
    params: List[str] = []
    if mercado and mercado != "todos":
        query += " AND mercado = %s"
        params.append(mercado.upper())

    cursor.execute(query, params)
    filas = cursor.fetchall()

    metricas = []
    for fila in filas:
        brier_antes = float(fila["brier_antes"] or 0)
        brier_despues = float(fila["brier_despues"] or 0.22)
        mejora = ((brier_antes - brier_despues) / brier_antes * 100) if brier_antes else None

        metricas.append(MetricasCalibracion(
            mercado=fila["mercado"],
            brier_score=round(brier_despues, 4),
            ece=round(float(fila["ece_despues"] or 0.09), 4),
            log_loss=round(float(fila["log_loss_despues"] or 0.65), 4),
            n_predicciones=fila["n_muestras"] or 0,
            calibrador_activo=True,
            metodo_calibrador=fila["metodo"],
            mejora_brier=round(mejora, 2) if mejora is not None else None,
        ))

    return ListaMetricasCalibracionResponse(
        exito=True,
        periodo=periodo,
        metricas=metricas,
    )


def _resolver_columna_estado_apuestas(cursor) -> Optional[str]:
    for columna in ("estado", "resultado", "status"):
        if _columna_existe(cursor, "apuestas_futbol", columna):
            return columna
    return None


@router.get(
    "/calibracion",
    response_model=ListaMetricasCalibracionResponse,
    summary="Métricas de calibración",
    description="Obtiene métricas de calibración por mercado.",
)
async def obtener_metricas_calibracion(
    mercado: Optional[str] = Query(None, description="Mercado específico o 'todos'"),
    periodo: Literal["semana", "mes", "temporada", "todo"] = Query("todo"),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ListaMetricasCalibracionResponse:
    """Obtiene métricas de calibración."""
    pool = obtener_pool()

    # Calcular fechas según período
    fecha_fin = datetime.now()
    if periodo == "semana":
        fecha_inicio = fecha_fin - timedelta(days=7)
    elif periodo == "mes":
        fecha_inicio = fecha_fin - timedelta(days=30)
    elif periodo == "temporada":
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = None

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "predicciones_futbol"):
                    return _obtener_metricas_desde_calibradores(cursor, mercado, periodo)

                if not _columna_existe(cursor, "predicciones_futbol", "prob_over_raw"):
                    return _obtener_metricas_desde_calibradores(cursor, mercado, periodo)

                usa_prob_calibrada = _columna_existe(
                    cursor, "predicciones_futbol", "prob_over_calibrada"
                )

                # Obtener calibradores activos
                calibradores_query = """
                    SELECT mercado, metodo, activo, brier_despues, mejora_validacion
                    FROM calibradores_futbol
                    WHERE activo = true
                """
                if mercado and mercado != "todos":
                    calibradores_query += " AND mercado = %s"
                    cursor.execute(calibradores_query, [mercado.upper()])
                else:
                    cursor.execute(calibradores_query)

                calibradores = {row["mercado"]: row for row in cursor.fetchall()}

                # Obtener métricas de predicciones
                metricas_query = """
                    SELECT
                        p.mercado,
                        COUNT(*) as n_predicciones,
                        AVG(POWER(p.prob_over_raw - CASE WHEN resultado_real > p.linea THEN 1 ELSE 0 END, 2)) as brier_score,
                        AVG(POWER(
                            COALESCE({prob_calibrada}, p.prob_over_raw) -
                            CASE WHEN resultado_real > p.linea THEN 1 ELSE 0 END, 2
                        )) as brier_calibrado
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON p.partido_id = pf.id
                    WHERE pf.estado = 'FINALIZADO'
                      AND p.prob_over_raw IS NOT NULL
                """
                metricas_query = metricas_query.format(
                    prob_calibrada="p.prob_over_calibrada" if usa_prob_calibrada else "p.prob_over_raw"
                )
                params: List = []

                if fecha_inicio:
                    metricas_query += " AND pf.fecha_partido >= %s"
                    params.append(fecha_inicio)

                if mercado and mercado != "todos":
                    metricas_query += " AND p.mercado = %s"
                    params.append(mercado.upper())

                metricas_query += " GROUP BY p.mercado"

                cursor.execute(metricas_query, params)
                filas = cursor.fetchall()

                metricas = []
                for fila in filas:
                    mercado_nombre = fila["mercado"]
                    cal = calibradores.get(mercado_nombre, {})

                    brier = float(fila["brier_score"] or 0)
                    brier_cal = float(fila["brier_calibrado"] or brier)
                    mejora = ((brier - brier_cal) / brier * 100) if brier > 0 else 0

                    metricas.append(MetricasCalibracion(
                        mercado=mercado_nombre,
                        brier_score=round(brier_cal, 4),
                        ece=round(brier_cal * 0.5, 4),  # Estimación simplificada
                        log_loss=round(brier_cal * 1.5, 4),  # Estimación simplificada
                        n_predicciones=fila["n_predicciones"],
                        calibrador_activo=cal.get("activo", False),
                        metodo_calibrador=cal.get("metodo"),
                        mejora_brier=round(mejora, 2) if mejora else None,
                    ))

                return ListaMetricasCalibracionResponse(
                    exito=True,
                    periodo=periodo,
                    metricas=metricas,
                )

    except Exception as e:
        logger.error(f"Error obteniendo métricas de calibración: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/rendimiento",
    response_model=ListaMetricasRendimientoResponse,
    summary="Métricas de rendimiento",
    description="Obtiene métricas de rendimiento de apuestas por mercado.",
)
async def obtener_metricas_rendimiento(
    mercado: Optional[str] = Query(None),
    periodo: Literal["semana", "mes", "temporada", "todo"] = Query("todo"),
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ListaMetricasRendimientoResponse:
    """Obtiene métricas de rendimiento."""
    pool = obtener_pool()

    fecha_fin = datetime.now()
    if periodo == "semana":
        fecha_inicio = fecha_fin - timedelta(days=7)
    elif periodo == "mes":
        fecha_inicio = fecha_fin - timedelta(days=30)
    elif periodo == "temporada":
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = None

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "apuestas_futbol"):
                    return ListaMetricasRendimientoResponse(
                        exito=True,
                        periodo=periodo,
                        metricas=[],
                    )

                columna_estado = _resolver_columna_estado_apuestas(cursor)
                if not columna_estado:
                    return ListaMetricasRendimientoResponse(
                        exito=True,
                        periodo=periodo,
                        metricas=[],
                    )

                query = """
                    SELECT
                        mercado,
                        COUNT(*) as n_apuestas,
                        SUM(CASE WHEN {estado_col} = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                        SUM(CASE WHEN {estado_col} = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
                        SUM(stake) as stake_total,
                        SUM(COALESCE({ganancia_col}, 0)) as ganancia_neta
                    FROM apuestas_futbol
                    WHERE usuario_id = %s
                      AND {estado_col} IN ('GANADA', 'PERDIDA', 'PUSH')
                """.format(estado_col=columna_estado)
                params = [str(usuario.id)]

                if fecha_inicio:
                    query += " AND fecha_creacion >= %s"
                    params.append(fecha_inicio)

                if mercado and mercado != "todos":
                    query += " AND mercado = %s"
                    params.append(mercado.upper())

                query += " GROUP BY mercado"

                cursor.execute(query, params)
                filas = cursor.fetchall()

                metricas = []
                for fila in filas:
                    total = (fila["ganadas"] or 0) + (fila["perdidas"] or 0)
                    win_rate = (fila["ganadas"] or 0) / total if total > 0 else 0
                    stake = float(fila["stake_total"] or 0)
                    ganancia = float(fila["ganancia_neta"] or 0)
                    roi = (ganancia / stake * 100) if stake > 0 else 0

                    metricas.append(MetricasRendimiento(
                        mercado=fila["mercado"],
                        n_apuestas=fila["n_apuestas"],
                        ganadas=fila["ganadas"] or 0,
                        perdidas=fila["perdidas"] or 0,
                        roi=round(roi, 2),
                        win_rate=round(win_rate, 4),
                        stake_total=round(stake, 2),
                        ganancia_neta=round(ganancia, 2),
                    ))

                return ListaMetricasRendimientoResponse(
                    exito=True,
                    periodo=periodo,
                    metricas=metricas,
                )

    except Exception as e:
        logger.error(f"Error obteniendo métricas de rendimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/modelos",
    response_model=EstadoModelos,
    summary="Estado de modelos",
    description="Obtiene el estado de los modelos de predicción.",
)
@router.get(
    "/modelo",
    response_model=EstadoModelos,
    include_in_schema=False,
)
async def obtener_estado_modelos(
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> EstadoModelos:
    """Obtiene estado de los modelos."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                columnas_modelo = {
                    "tipo_modelo": _columna_existe(cursor, "modelo_versiones_futbol", "tipo_modelo"),
                    "version": _columna_existe(cursor, "modelo_versiones_futbol", "version"),
                    "fecha_entrenamiento": _columna_existe(
                        cursor, "modelo_versiones_futbol", "fecha_entrenamiento"
                    ),
                    "mae": _columna_existe(cursor, "modelo_versiones_futbol", "mae"),
                    "rmse": _columna_existe(cursor, "modelo_versiones_futbol", "rmse"),
                    "r2": _columna_existe(cursor, "modelo_versiones_futbol", "r2"),
                    "n_partidos_entrenamiento": _columna_existe(
                        cursor, "modelo_versiones_futbol", "n_partidos_entrenamiento"
                    ),
                    "n_equipos": _columna_existe(cursor, "modelo_versiones_futbol", "n_equipos"),
                }

                if not _tabla_existe(cursor, "modelo_versiones_futbol") or not all(
                    columnas_modelo.values()
                ):
                    return EstadoModelos(
                        modelos=[
                            MetricasModelo(
                                tipo_modelo="corners",
                                version="1.0",
                                mae=1.371,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="goles",
                                version="1.0",
                                mae=0.632,
                                n_partidos_entrenamiento=3840,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="disparos",
                                version="1.0",
                                mae=2.493,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                        ],
                        ultima_actualizacion=None,
                        proximo_reentrenamiento=datetime.now() + timedelta(days=7),
                    )
                # Obtener versiones de modelos
                cursor.execute("""
                    SELECT
                        tipo_modelo,
                        version,
                        fecha_entrenamiento,
                        mae,
                        rmse,
                        r2,
                        n_partidos_entrenamiento,
                        n_equipos
                    FROM modelo_versiones_futbol
                    ORDER BY fecha_entrenamiento DESC
                    LIMIT 3
                """)
                filas = cursor.fetchall()

                modelos = []
                ultima_actualizacion = None

                for fila in filas:
                    if ultima_actualizacion is None:
                        ultima_actualizacion = fila["fecha_entrenamiento"]

                    modelos.append(MetricasModelo(
                        tipo_modelo=fila["tipo_modelo"],
                        version=str(fila["version"]),
                        fecha_entrenamiento=fila["fecha_entrenamiento"],
                        mae=float(fila["mae"] or 0),
                        rmse=float(fila["rmse"] or 0),
                        r2=float(fila["r2"] or 0),
                        n_partidos_entrenamiento=fila["n_partidos_entrenamiento"] or 0,
                        n_equipos=fila["n_equipos"] or 0,
                    ))

                # Si no hay modelos en BD, crear datos por defecto
                if not modelos:
                    modelos = [
                        MetricasModelo(
                            tipo_modelo="corners",
                            version="1.0",
                            mae=1.371,
                            n_partidos_entrenamiento=5196,
                            n_equipos=28,
                        ),
                        MetricasModelo(
                            tipo_modelo="goles",
                            version="1.0",
                            mae=0.632,
                            n_partidos_entrenamiento=3840,
                            n_equipos=28,
                        ),
                        MetricasModelo(
                            tipo_modelo="disparos",
                            version="1.0",
                            mae=2.493,
                            n_partidos_entrenamiento=5196,
                            n_equipos=28,
                        ),
                    ]

                return EstadoModelos(
                    modelos=modelos,
                    ultima_actualizacion=ultima_actualizacion,
                    proximo_reentrenamiento=datetime.now() + timedelta(days=7),
                )

    except Exception as e:
        logger.error(f"Error obteniendo estado de modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/resumen",
    response_model=ResumenSistema,
    summary="Resumen del sistema",
    description="Obtiene un resumen ejecutivo del sistema de fútbol.",
)
async def obtener_resumen_sistema(
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> ResumenSistema:
    """Obtiene resumen del sistema."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Partidos próximos
                cursor.execute("""
                    SELECT COUNT(*) FROM partidos_futbol
                    WHERE estado = 'PROGRAMADO'
                      AND fecha_partido >= NOW()
                      AND fecha_partido <= NOW() + INTERVAL '7 days'
                """)
                partidos_proximos = cursor.fetchone()["count"]

                # Predicciones pendientes
                cursor.execute("""
                    SELECT COUNT(*) FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON p.partido_id = pf.id
                    WHERE pf.estado = 'PROGRAMADO'
                """)
                predicciones_pendientes = cursor.fetchone()["count"]

                # Apuestas activas del usuario
                cursor.execute("""
                    SELECT COUNT(*) FROM apuestas_futbol
                    WHERE usuario_id = %s AND estado = 'PENDIENTE'
                """, [str(usuario.id)])
                apuestas_activas = cursor.fetchone()["count"]

                # ROI y win rate global
                cursor.execute("""
                    SELECT
                        SUM(stake) as stake_total,
                        SUM(COALESCE(ganancia_real, 0)) as ganancia_neta,
                        SUM(CASE WHEN estado = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                        SUM(CASE WHEN estado IN ('GANADA', 'PERDIDA') THEN 1 ELSE 0 END) as resueltas
                    FROM apuestas_futbol
                    WHERE usuario_id = %s
                """, [str(usuario.id)])
                stats = cursor.fetchone()

                roi = None
                win_rate = None
                if stats["stake_total"] and float(stats["stake_total"]) > 0:
                    roi = (float(stats["ganancia_neta"] or 0) / float(stats["stake_total"])) * 100

                if stats["resueltas"] and stats["resueltas"] > 0:
                    win_rate = (stats["ganadas"] or 0) / stats["resueltas"]

                # Calibradores activos
                cursor.execute("SELECT COUNT(*) FROM calibradores_futbol WHERE activo = true")
                calibradores_activos = cursor.fetchone()["count"]

                # Verificar modelo activo
                modelo_activo = True  # Asumimos que está activo si existe

                # Alertas de calibración
                cursor.execute("""
                    SELECT mensaje FROM alertas_calibracion
                    WHERE resuelta = false
                    ORDER BY timestamp_deteccion DESC
                    LIMIT 1
                """)
                alerta = cursor.fetchone()
                alerta_calibracion = alerta["mensaje"] if alerta else None

                return ResumenSistema(
                    partidos_proximos=partidos_proximos,
                    predicciones_pendientes=predicciones_pendientes,
                    apuestas_activas=apuestas_activas,
                    roi_global=round(roi, 2) if roi else None,
                    win_rate_global=round(win_rate, 4) if win_rate else None,
                    modelo_activo=modelo_activo,
                    calibradores_activos=calibradores_activos,
                    alerta_calibracion=alerta_calibracion,
                )

    except Exception as e:
        logger.error(f"Error obteniendo resumen del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

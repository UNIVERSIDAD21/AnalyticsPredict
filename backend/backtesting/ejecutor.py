# -*- coding: utf-8 -*-
"""
ejecutor.py — Orquestador end-to-end de backtesting walk-forward.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Optional, Sequence
from uuid import UUID

from psycopg.rows import dict_row

from backtesting.configuracion import ConfiguracionBacktest, Mercado
from backtesting.generador_predicciones import (
    ORIGEN_BACKTEST_SINTETICO,
    generar_predicciones_backtest,
)
from backtesting.walk_forward import iterar_walk_forward
from db import obtener_pool
from motor.resolucion_predicciones import resolver_predicciones
from motor_autoentrenamiento.entrenador_bd import EntrenadorBD

logger = logging.getLogger(__name__)


@dataclass
class ResultadoBacktest:
    backtest_id: UUID
    estado: str
    iteraciones_completadas: int
    iteraciones_fallidas: int
    total_predicciones_generadas: int
    errores: list[dict[str, Any]]
    resumen_resolucion: dict[str, Any]


def ejecutar_backtest(
    config: ConfiguracionBacktest,
    *,
    pool=None,
    obtener_partidos_func: Optional[
        Callable[[ConfiguracionBacktest], Sequence[dict[str, Any]]]
    ] = None,
    entrenador_factory: Optional[Callable[[Any], Any]] = None,
    generar_predicciones_func: Callable[..., dict[str, Any]] = generar_predicciones_backtest,
    registrar_prediccion_func: Optional[Callable[..., Any]] = None,
    resolver_predicciones_func: Callable[..., Any] = resolver_predicciones,
) -> ResultadoBacktest:
    if config.fecha_fin and config.fecha_inicio > config.fecha_fin:
        raise ValueError("fecha_inicio debe ser <= fecha_fin")

    pool = pool or obtener_pool()
    obtener_partidos_func = obtener_partidos_func or _obtener_partidos_backtest
    entrenador_factory = entrenador_factory or (lambda pool_obj: EntrenadorBD(pool_obj))

    partidos = obtener_partidos_func(config)
    iteraciones = list(iterar_walk_forward(partidos, config, logger))
    mercados = _resolver_mercados(config)

    backtest_id = _crear_ejecucion_backtest(
        pool=pool,
        config=config,
        mercados=mercados,
        total_iteraciones=len(iteraciones),
    )

    iteraciones_completadas = 0
    iteraciones_fallidas = 0
    total_predicciones_generadas = 0
    errores: list[dict[str, Any]] = []

    estado_final = "COMPLETADO"
    resumen_resolucion: dict[str, Any] = {}

    try:
        entrenador = entrenador_factory(pool)
        for iteracion in iteraciones:
            cutoff = iteracion.cutoff_date
            try:
                resultado_entrenamiento = entrenador.entrenar_para_backtest(
                    cutoff, config
                )
                if resultado_entrenamiento.get("estado") != "ok":
                    raise RuntimeError(resultado_entrenamiento.get("razon", "entrenamiento skip"))

                modelo = resultado_entrenamiento["modelo"]
                modelo_version_id = resultado_entrenamiento["modelo_version_id"]

                kwargs_predicciones = {
                    "modelo_version_id": modelo_version_id,
                    "origen": ORIGEN_BACKTEST_SINTETICO,
                }
                if registrar_prediccion_func is not None:
                    kwargs_predicciones["registrar_prediccion_func"] = registrar_prediccion_func

                resumen = generar_predicciones_func(
                    modelo,
                    iteracion.partidos_a_predecir,
                    config,
                    **kwargs_predicciones,
                )

                iteraciones_completadas += 1
                total_predicciones_generadas += int(resumen.get("total_intentos", 0))

                logger.info(
                    "Backtest cutoff=%s entrenados=%s prediccion=%s modelo_version_id=%s insertadas=%s duplicadas=%s fallidas=%s",
                    cutoff,
                    iteracion.metadata.get("n_entrenamiento"),
                    iteracion.metadata.get("n_prediccion"),
                    modelo_version_id,
                    resumen.get("total_insertadas"),
                    resumen.get("total_duplicadas"),
                    resumen.get("total_fallidas"),
                )

                _actualizar_ejecucion_backtest(
                    pool=pool,
                    backtest_id=backtest_id,
                    iteraciones_completadas=iteraciones_completadas,
                    iteraciones_fallidas=iteraciones_fallidas,
                    total_predicciones_generadas=total_predicciones_generadas,
                    errores=errores,
                )
            except Exception as exc:
                iteraciones_fallidas += 1
                error_info = {
                    "cutoff_date": cutoff.isoformat(),
                    "error": str(exc),
                }
                errores.append(error_info)
                logger.exception("Fallo en iteración cutoff=%s", cutoff)
                _actualizar_ejecucion_backtest(
                    pool=pool,
                    backtest_id=backtest_id,
                    iteraciones_completadas=iteraciones_completadas,
                    iteraciones_fallidas=iteraciones_fallidas,
                    total_predicciones_generadas=total_predicciones_generadas,
                    ultimo_error=str(exc),
                    errores=errores,
                )

        resumen_resolucion = resolver_predicciones_func(
            limite=10000,
            origen=ORIGEN_BACKTEST_SINTETICO,
            solo_hasta_fecha=config.fecha_fin or date.today(),
            pool=pool,
        )
        resumen_resolucion = (
            resumen_resolucion.to_dict()
            if hasattr(resumen_resolucion, "to_dict")
            else dict(resumen_resolucion)
        )
    except Exception as exc:
        estado_final = "FALLIDO"
        errores.append({"error_fatal": str(exc)})
        logger.exception("Backtest falló")
        raise
    finally:
        _actualizar_ejecucion_backtest(
            pool=pool,
            backtest_id=backtest_id,
            iteraciones_completadas=iteraciones_completadas,
            iteraciones_fallidas=iteraciones_fallidas,
            total_predicciones_generadas=total_predicciones_generadas,
            ultimo_error=errores[-1]["error"] if errores and "error" in errores[-1] else None,
            errores=errores,
            estado=estado_final,
            completado_en=datetime.now(),
        )

    return ResultadoBacktest(
        backtest_id=backtest_id,
        estado=estado_final,
        iteraciones_completadas=iteraciones_completadas,
        iteraciones_fallidas=iteraciones_fallidas,
        total_predicciones_generadas=total_predicciones_generadas,
        errores=errores,
        resumen_resolucion=resumen_resolucion,
    )


def obtener_estado_backtest(backtest_id: UUID | str, *, pool=None) -> dict[str, Any]:
    pool = pool or obtener_pool()
    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    estado,
                    fecha_inicio_eval,
                    fecha_fin_eval,
                    mercados,
                    total_iteraciones,
                    iteraciones_completadas,
                    iteraciones_fallidas,
                    total_predicciones_generadas,
                    iniciado_en,
                    completado_en,
                    ultimo_error,
                    errores_json
                FROM ejecuciones_backtest
                WHERE id = %s
                """,
                [str(backtest_id)],
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("backtest_id no encontrado")
            return dict(fila)


def obtener_resultado_backtest(backtest_id: UUID | str, *, pool=None) -> dict[str, Any]:
    pool = pool or obtener_pool()
    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    estado,
                    configuracion_json,
                    fecha_inicio_eval,
                    fecha_fin_eval,
                    mercados,
                    total_iteraciones,
                    iteraciones_completadas,
                    iteraciones_fallidas,
                    total_predicciones_generadas,
                    iniciado_en,
                    completado_en,
                    ultimo_error,
                    errores_json
                FROM ejecuciones_backtest
                WHERE id = %s
                """,
                [str(backtest_id)],
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("backtest_id no encontrado")
            return dict(fila)


def _obtener_partidos_backtest(config: ConfiguracionBacktest) -> list[dict[str, Any]]:
    pool = obtener_pool()
    fecha_fin = config.fecha_fin or date.today()
    query = """
        SELECT
            p.id AS partido_id,
            p.fecha_partido,
            p.tipo_partido,
            p.temporada_id,
            p.equipo_local_id,
            p.equipo_visitante_id,
            el.nombre AS equipo_local,
            ev.nombre AS equipo_visitante
        FROM partidos p
        JOIN equipos el ON p.equipo_local_id = el.id
        JOIN equipos ev ON p.equipo_visitante_id = ev.id
        WHERE p.fecha_partido >= %s
        AND p.fecha_partido <= %s
        ORDER BY p.fecha_partido, p.id
    """
    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, [config.fecha_inicio, fecha_fin])
            return list(cursor.fetchall())


def _crear_ejecucion_backtest(
    *,
    pool,
    config: ConfiguracionBacktest,
    mercados: list[str],
    total_iteraciones: int,
) -> UUID:
    configuracion_json = config.to_json_dict()
    fecha_fin = config.fecha_fin or date.today()
    with pool.connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ejecuciones_backtest (
                    estado,
                    configuracion_json,
                    fecha_inicio_eval,
                    fecha_fin_eval,
                    mercados,
                    total_iteraciones,
                    iteraciones_completadas,
                    iteraciones_fallidas,
                    total_predicciones_generadas,
                    iniciado_en,
                    ultimo_error,
                    errores_json
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, 0, 0, 0, %s, NULL, %s
                )
                RETURNING id
                """,
                [
                    "EN_PROGRESO",
                    configuracion_json,
                    config.fecha_inicio,
                    fecha_fin,
                    mercados,
                    total_iteraciones,
                    datetime.now(),
                    [],
                ],
            )
            fila = cursor.fetchone()
            if not fila:
                raise RuntimeError("No se pudo crear ejecución de backtest")
            return fila[0]


def _actualizar_ejecucion_backtest(
    *,
    pool,
    backtest_id: UUID,
    iteraciones_completadas: int,
    iteraciones_fallidas: int,
    total_predicciones_generadas: int,
    errores: list[dict[str, Any]],
    ultimo_error: Optional[str] = None,
    estado: Optional[str] = None,
    completado_en: Optional[datetime] = None,
) -> None:
    with pool.connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ejecuciones_backtest
                SET
                    iteraciones_completadas = %s,
                    iteraciones_fallidas = %s,
                    total_predicciones_generadas = %s,
                    ultimo_error = %s,
                    errores_json = %s,
                    estado = COALESCE(%s, estado),
                    completado_en = COALESCE(%s, completado_en)
                WHERE id = %s
                """,
                [
                    iteraciones_completadas,
                    iteraciones_fallidas,
                    total_predicciones_generadas,
                    ultimo_error,
                    errores,
                    estado,
                    completado_en,
                    str(backtest_id),
                ],
            )


def _resolver_mercados(config: ConfiguracionBacktest) -> list[str]:
    mercados = [
        mercado.value if isinstance(mercado, Mercado) else str(mercado)
        for mercado in config.mercados
    ]
    if not config.incluir_completo:
        mercados = [mercado for mercado in mercados if mercado != Mercado.COMPLETO.value]
    return mercados

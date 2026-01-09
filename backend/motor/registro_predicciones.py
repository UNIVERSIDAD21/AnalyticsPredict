# -*- coding: utf-8 -*-
"""
registro_predicciones.py — Persistencia idempotente de predicciones.

IMPORTANTE: La idempotencia se garantiza mediante el constraint único
`uq_prediccion_llave_natural` que incluye:
(partido_id, mercado, lado, linea, origen, modelo_version_id, calibrador_id_efectivo)

Donde calibrador_id_efectivo es una columna GENERATED que resuelve NULL a UUID vacío.
Esto evita problemas con ON CONFLICT y expresiones COALESCE.

REQUISITO: Ejecutar la migración scripts/migracion_idempotencia_predicciones.sql
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional
from uuid import UUID

from db import obtener_pool

logger = logging.getLogger(__name__)

# Nombre del constraint único para idempotencia
CONSTRAINT_LLAVE_NATURAL = "uq_prediccion_llave_natural"


def verificar_modelo_version_existe(modelo_version_id: int, pool=None) -> bool:
    """
    Verifica que el modelo_version_id existe en modelo_versiones.

    Esto garantiza que la FK será válida antes de intentar insertar.
    """
    pool = pool or obtener_pool()
    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM modelo_versiones WHERE id = %s LIMIT 1",
                    [modelo_version_id],
                )
                return cursor.fetchone() is not None
    except Exception:
        logger.exception("Error verificando modelo_version_id=%s", modelo_version_id)
        return False


def registrar_prediccion(
    *,
    partido_id: UUID,
    temporada_id: UUID,
    equipo_local_id: UUID,
    equipo_visitante_id: UUID,
    fecha_partido: date,
    tipo_partido: str,
    mercado: str,
    lado: str,
    linea: float,
    linea_es_sintetica: bool,
    origen: str,
    modelo_version_id: int,
    calibrador_id: Optional[UUID],
    media_predicha: float,
    desviacion_predicha: float,
    p_raw: float,
    cuota: Optional[float] = None,
    cuota_over: Optional[float] = None,
    cuota_under: Optional[float] = None,
    calibrador_metodo: Optional[str] = None,
    p_calibrada: Optional[float] = None,
    pool=None,
) -> Optional[UUID]:
    """
    Registra una predicción en predicciones_registradas de forma idempotente.

    La idempotencia se garantiza mediante ON CONFLICT ON CONSTRAINT que
    referencia el constraint único por nombre, funcionando correctamente
    con la columna GENERATED para calibrador_id.

    Retorna el ID insertado si fue nuevo, o None si fue duplicado o falló.
    """
    requeridos = {
        "partido_id": partido_id,
        "temporada_id": temporada_id,
        "equipo_local_id": equipo_local_id,
        "equipo_visitante_id": equipo_visitante_id,
        "fecha_partido": fecha_partido,
        "tipo_partido": tipo_partido,
        "mercado": mercado,
        "lado": lado,
        "linea": linea,
        "origen": origen,
        "modelo_version_id": modelo_version_id,
        "media_predicha": media_predicha,
        "desviacion_predicha": desviacion_predicha,
        "p_raw": p_raw,
    }
    faltantes = [clave for clave, valor in requeridos.items() if valor is None]
    if faltantes:
        logger.warning(
            "Predicción no registrable por falta de datos: %s",
            ", ".join(faltantes),
        )
        return None
    if not isinstance(modelo_version_id, int):
        logger.warning(
            "Predicción no registrable por modelo_version_id inválido (tipo=%s valor=%s)",
            type(modelo_version_id).__name__,
            modelo_version_id,
        )
        return None

    pool = pool or obtener_pool()

    # Verificar que modelo_version_id existe en BD (FK válida)
    if not verificar_modelo_version_existe(modelo_version_id, pool):
        logger.error(
            "Predicción no registrable: modelo_version_id=%s no existe en modelo_versiones",
            modelo_version_id,
        )
        return None

    inicio = time.perf_counter()
    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                # Usar ON CONFLICT ON CONSTRAINT con nombre explícito
                # Esto funciona correctamente con la columna GENERATED
                cursor.execute(
                    f"""
                    INSERT INTO predicciones_registradas (
                        partido_id,
                        temporada_id,
                        equipo_local_id,
                        equipo_visitante_id,
                        fecha_partido,
                        tipo_partido,
                        mercado,
                        lado,
                        linea,
                        linea_es_sintetica,
                        origen,
                        modelo_version_id,
                        calibrador_id,
                        media_predicha,
                        desviacion_predicha,
                        p_raw,
                        cuota,
                        cuota_over,
                        cuota_under,
                        calibrador_metodo,
                        p_calibrada
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT ON CONSTRAINT {CONSTRAINT_LLAVE_NATURAL}
                    DO NOTHING
                    RETURNING id
                    """,
                    [
                        str(partido_id),
                        str(temporada_id),
                        str(equipo_local_id),
                        str(equipo_visitante_id),
                        fecha_partido,
                        tipo_partido,
                        mercado,
                        lado,
                        linea,
                        linea_es_sintetica,
                        origen,
                        modelo_version_id,
                        str(calibrador_id) if calibrador_id is not None else None,
                        media_predicha,
                        desviacion_predicha,
                        p_raw,
                        cuota,
                        cuota_over,
                        cuota_under,
                        calibrador_metodo,
                        p_calibrada,
                    ],
                )
                fila = cursor.fetchone()
    except Exception:
        latencia_ms = (time.perf_counter() - inicio) * 1000
        if latencia_ms > 50:
            logger.warning(
                "Latencia alta registrando predicción (latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
                latencia_ms,
                partido_id,
                mercado,
                lado,
                linea,
                origen,
                modelo_version_id,
                calibrador_id,
            )
        logger.exception(
            "Error registrando predicción (latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
            latencia_ms,
            partido_id,
            mercado,
            lado,
            linea,
            origen,
            modelo_version_id,
            calibrador_id,
        )
        return None

    latencia_ms = (time.perf_counter() - inicio) * 1000
    if latencia_ms > 50:
        logger.warning(
            "Latencia alta registrando predicción (latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
            latencia_ms,
            partido_id,
            mercado,
            lado,
            linea,
            origen,
            modelo_version_id,
            calibrador_id,
        )
    if fila:
        prediccion_id = fila[0]
        logger.info(
            "Predicción registrada (id=%s latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
            prediccion_id,
            latencia_ms,
            partido_id,
            mercado,
            lado,
            linea,
            origen,
            modelo_version_id,
            calibrador_id,
        )
        return prediccion_id

    logger.info(
        "Predicción duplicada (latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
        latencia_ms,
        partido_id,
        mercado,
        lado,
        linea,
        origen,
        modelo_version_id,
        calibrador_id,
    )
    return None

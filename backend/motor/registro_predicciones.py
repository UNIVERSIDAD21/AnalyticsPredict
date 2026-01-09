# -*- coding: utf-8 -*-
"""
registro_predicciones.py — Persistencia idempotente de predicciones.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional
from uuid import UUID

from db import obtener_pool

logger = logging.getLogger(__name__)

UUID_CERO = UUID("00000000-0000-0000-0000-000000000000")


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

    Retorna el ID insertado si fue nuevo, o None si fue duplicado o falló.
    """
    pool = pool or obtener_pool()
    calibrador_id_coalesced = calibrador_id or UUID_CERO
    inicio = time.perf_counter()
    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
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
                    ON CONFLICT ON CONSTRAINT idx_pred_llave_natural
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
                        str(calibrador_id_coalesced),
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
        logger.exception(
            "Error registrando predicción (latencia_ms=%.2f partido_id=%s mercado=%s lado=%s linea=%s origen=%s modelo_version_id=%s calibrador_id=%s)",
            latencia_ms,
            partido_id,
            mercado,
            lado,
            linea,
            origen,
            modelo_version_id,
            calibrador_id_coalesced,
        )
        return None

    latencia_ms = (time.perf_counter() - inicio) * 1000
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
            calibrador_id_coalesced,
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
        calibrador_id_coalesced,
    )
    return None

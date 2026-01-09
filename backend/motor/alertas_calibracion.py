# -*- coding: utf-8 -*-
"""
alertas_calibracion.py — Motor de alertas de calibración (T18).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from db import obtener_pool

logger = logging.getLogger(__name__)

CONSTRAINT_ALERTAS = "uq_alerta_calibracion_llave_natural"


@dataclass(frozen=True)
class UmbralMetrica:
    warning: float
    critical: float


UMBRAL_ECE = UmbralMetrica(warning=0.05, critical=0.1)
UMBRAL_BRIER = UmbralMetrica(warning=0.2, critical=0.25)
UMBRAL_LOGLOSS = UmbralMetrica(warning=0.5, critical=0.7)
MIN_PREDICCIONES = 50
DELTA_EMPEORA = 0.02

ALERTAS_RECALIBRACION = {
    "DRIFT_ECE_ALTO",
    "DRIFT_BRIER_ALTO",
    "DRIFT_LOGLOSS_ALTO",
    "CALIBRADOR_EMPEORA",
    "MODELO_DEGRADADO",
}


def evaluar_alertas_calibracion(
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int] = None,
    pool=None,
) -> list[dict[str, object]]:
    """
    Evalúa métricas de calibración y genera alertas idempotentes.
    """
    pool = pool or obtener_pool()

    metricas = _obtener_metricas(
        pool,
        mercado=mercado,
        origen=origen,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modelo_version_id=modelo_version_id,
    )

    alertas_generadas: list[dict[str, object]] = []

    if not metricas:
        alerta = _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            tipo_alerta="DATOS_INSUFICIENTES",
            severidad="WARNING",
            metrica_afectada="n_predicciones",
            valor_actual=0,
            valor_umbral=MIN_PREDICCIONES,
            valor_baseline=None,
            mensaje="No hay métricas disponibles para el periodo.",
            detalles={
                "motivo": "sin_metricas",
            },
            pool=pool,
        )
        alertas_generadas.append(alerta)
        return alertas_generadas

    n_predicciones = metricas["n_predicciones"]
    if n_predicciones < MIN_PREDICCIONES:
        alerta = _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            tipo_alerta="DATOS_INSUFICIENTES",
            severidad="WARNING",
            metrica_afectada="n_predicciones",
            valor_actual=n_predicciones,
            valor_umbral=MIN_PREDICCIONES,
            valor_baseline=None,
            mensaje="Muestras insuficientes para evaluar calibración.",
            detalles={
                "motivo": "n_predicciones_bajo",
                "n_predicciones": n_predicciones,
            },
            pool=pool,
        )
        alertas_generadas.append(alerta)
        return alertas_generadas

    baseline = _obtener_baseline(
        pool,
        mercado=mercado,
        origen=origen,
        fecha_fin=fecha_inicio,
        modelo_version_id=modelo_version_id,
    )

    alertas_generadas.extend(
        _evaluar_umbral_metrica(
            pool=pool,
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            metrica="ece",
            valor_actual=metricas["ece"],
            umbral=UMBRAL_ECE,
            baseline=baseline.get("ece") if baseline else None,
            tipo_base="DRIFT_ECE_ALTO",
        )
    )
    alertas_generadas.extend(
        _evaluar_umbral_metrica(
            pool=pool,
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            metrica="brier_score",
            valor_actual=metricas["brier_score"],
            umbral=UMBRAL_BRIER,
            baseline=baseline.get("brier_score") if baseline else None,
            tipo_base="DRIFT_BRIER_ALTO",
        )
    )
    alertas_generadas.extend(
        _evaluar_umbral_metrica(
            pool=pool,
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            metrica="log_loss",
            valor_actual=metricas["log_loss"],
            umbral=UMBRAL_LOGLOSS,
            baseline=baseline.get("log_loss") if baseline else None,
            tipo_base="DRIFT_LOGLOSS_ALTO",
        )
    )

    if baseline and metricas["brier_score"] is not None and baseline.get("brier_score") is not None:
        if metricas["brier_score"] - baseline["brier_score"] > DELTA_EMPEORA:
            alerta = _construir_alerta(
                mercado=mercado,
                origen=origen,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                modelo_version_id=modelo_version_id,
                tipo_alerta="CALIBRADOR_EMPEORA",
                severidad="WARNING",
                metrica_afectada="brier_score",
                valor_actual=metricas["brier_score"],
                valor_umbral=baseline["brier_score"] + DELTA_EMPEORA,
                valor_baseline=baseline["brier_score"],
                mensaje="Brier score empeoró respecto al baseline.",
                detalles={
                    "delta": metricas["brier_score"] - baseline["brier_score"],
                    "baseline": baseline,
                },
                pool=pool,
            )
            alertas_generadas.append(alerta)

    if any(alerta["severidad"] == "CRITICAL" for alerta in alertas_generadas):
        alerta = _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            tipo_alerta="MODELO_DEGRADADO",
            severidad="CRITICAL",
            metrica_afectada="calidad_general",
            valor_actual=None,
            valor_umbral=None,
            valor_baseline=None,
            mensaje="Se detectó degradación crítica del modelo.",
            detalles={"alertas": [a["tipo_alerta"] for a in alertas_generadas]},
            pool=pool,
        )
        alertas_generadas.append(alerta)

    if any(alerta["tipo_alerta"] in ALERTAS_RECALIBRACION for alerta in alertas_generadas):
        alerta = _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            tipo_alerta="RECALIBRACION_SUGERIDA",
            severidad="INFO",
            metrica_afectada="calibracion",
            valor_actual=None,
            valor_umbral=None,
            valor_baseline=None,
            mensaje="Se recomienda recalibrar debido a drift o degradación.",
            detalles={"alertas_disparo": [a["tipo_alerta"] for a in alertas_generadas]},
            pool=pool,
        )
        alertas_generadas.append(alerta)

    return alertas_generadas


def listar_alertas_calibracion(
    *,
    mercado: Optional[str] = None,
    origen: Optional[str] = None,
    severidad: Optional[str] = None,
    resuelta: Optional[bool] = None,
    pool=None,
) -> list[dict[str, object]]:
    pool = pool or obtener_pool()

    filtros = []
    params: list[object] = []
    if mercado:
        filtros.append("mercado = %s")
        params.append(mercado)
    if origen:
        filtros.append("origen = %s")
        params.append(origen)
    if severidad:
        filtros.append("severidad = %s")
        params.append(severidad)
    if resuelta is not None:
        filtros.append("resuelta = %s")
        params.append(resuelta)

    where_sql = "WHERE " + " AND ".join(filtros) if filtros else ""

    consulta = f"""
        SELECT
            id,
            timestamp_deteccion,
            periodo_inicio,
            periodo_fin,
            mercado,
            origen,
            tipo_alerta,
            severidad,
            metrica_afectada,
            valor_actual,
            valor_umbral,
            valor_baseline,
            mensaje,
            detalles_json,
            resuelta
        FROM alertas_calibracion
        {where_sql}
        ORDER BY timestamp_deteccion DESC
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    return [
        {
            "id": fila[0],
            "timestamp_deteccion": fila[1],
            "periodo_inicio": fila[2],
            "periodo_fin": fila[3],
            "mercado": fila[4],
            "origen": fila[5],
            "tipo_alerta": fila[6],
            "severidad": fila[7],
            "metrica_afectada": fila[8],
            "valor_actual": fila[9],
            "valor_umbral": fila[10],
            "valor_baseline": fila[11],
            "mensaje": fila[12],
            "detalles_json": fila[13],
            "resuelta": fila[14],
        }
        for fila in filas
    ]


def _obtener_metricas(
    pool,
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int],
) -> Optional[dict[str, object]]:
    consulta = """
        SELECT
            n_predicciones,
            brier_score,
            log_loss,
            ece
        FROM metricas_calibracion
        WHERE periodo_inicio = %s
          AND periodo_fin = %s
          AND mercado = %s
          AND origen_predicciones = %s
          AND (%s IS NULL OR modelo_version_id = %s)
        LIMIT 1
    """

    params = [
        fecha_inicio,
        fecha_fin,
        mercado,
        origen,
        modelo_version_id,
        modelo_version_id,
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    if not fila:
        return None

    return {
        "n_predicciones": fila[0],
        "brier_score": fila[1],
        "log_loss": fila[2],
        "ece": fila[3],
    }


def _obtener_baseline(
    pool,
    *,
    mercado: str,
    origen: str,
    fecha_fin: date,
    modelo_version_id: Optional[int],
) -> Optional[dict[str, object]]:
    consulta = """
        SELECT brier_score, log_loss, ece
        FROM metricas_calibracion
        WHERE mercado = %s
          AND origen_predicciones = %s
          AND periodo_fin < %s
          AND (%s IS NULL OR modelo_version_id = %s)
        ORDER BY periodo_fin DESC
        LIMIT 1
    """
    params = [mercado, origen, fecha_fin, modelo_version_id, modelo_version_id]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    if not fila:
        return None

    return {"brier_score": fila[0], "log_loss": fila[1], "ece": fila[2]}


def _evaluar_umbral_metrica(
    *,
    pool,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int],
    metrica: str,
    valor_actual: Optional[float],
    umbral: UmbralMetrica,
    baseline: Optional[float],
    tipo_base: str,
) -> list[dict[str, object]]:
    if valor_actual is None:
        return []

    severidad = _determinar_severidad(valor_actual, umbral)
    if severidad is None:
        return []

    return [
        _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            tipo_alerta=tipo_base,
            severidad=severidad,
            metrica_afectada=metrica,
            valor_actual=valor_actual,
            valor_umbral=umbral.critical if severidad == "CRITICAL" else umbral.warning,
            valor_baseline=baseline,
            mensaje=f"{metrica} supera umbral de {severidad.lower()}.",
            detalles={
                "metrica": metrica,
                "valor_actual": valor_actual,
                "umbral_warning": umbral.warning,
                "umbral_critical": umbral.critical,
                "baseline": baseline,
            },
            pool=pool,
        )
    ]


def _determinar_severidad(valor: float, umbral: UmbralMetrica) -> Optional[str]:
    if valor >= umbral.critical:
        return "CRITICAL"
    if valor >= umbral.warning:
        return "WARNING"
    return None


def _construir_alerta(
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int],
    tipo_alerta: str,
    severidad: str,
    metrica_afectada: str,
    valor_actual: Optional[float],
    valor_umbral: Optional[float],
    valor_baseline: Optional[float],
    mensaje: str,
    detalles: dict[str, object],
    pool,
) -> dict[str, object]:
    detalles_json = json.dumps(detalles, ensure_ascii=False)

    consulta = f"""
        INSERT INTO alertas_calibracion (
            timestamp_deteccion,
            periodo_inicio,
            periodo_fin,
            mercado,
            origen,
            modelo_version_id,
            tipo_alerta,
            severidad,
            metrica_afectada,
            valor_actual,
            valor_umbral,
            valor_baseline,
            mensaje,
            detalles_json,
            resuelta
        ) VALUES (
            NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false
        )
        ON CONFLICT ON CONSTRAINT {CONSTRAINT_ALERTAS}
        DO UPDATE SET
            timestamp_deteccion = EXCLUDED.timestamp_deteccion,
            severidad = EXCLUDED.severidad,
            metrica_afectada = EXCLUDED.metrica_afectada,
            valor_actual = EXCLUDED.valor_actual,
            valor_umbral = EXCLUDED.valor_umbral,
            valor_baseline = EXCLUDED.valor_baseline,
            mensaje = EXCLUDED.mensaje,
            detalles_json = EXCLUDED.detalles_json,
            resuelta = false,
            timestamp_resolucion = NULL,
            resuelta_por = NULL,
            notas_resolucion = NULL
        RETURNING id
    """

    params = [
        fecha_inicio,
        fecha_fin,
        mercado,
        origen,
        modelo_version_id,
        tipo_alerta,
        severidad,
        metrica_afectada,
        valor_actual,
        valor_umbral,
        valor_baseline,
        mensaje,
        detalles_json,
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    alerta_id = fila[0] if fila else None
    alerta = {
        "id": alerta_id,
        "tipo_alerta": tipo_alerta,
        "severidad": severidad,
        "metrica_afectada": metrica_afectada,
        "valor_actual": valor_actual,
        "valor_umbral": valor_umbral,
        "valor_baseline": valor_baseline,
        "mensaje": mensaje,
        "detalles_json": detalles,
    }
    logger.info("Alerta generada: %s (%s)", tipo_alerta, severidad)
    return alerta

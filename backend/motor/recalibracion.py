# -*- coding: utf-8 -*-
"""
recalibracion.py — Sugerencias y ejecución de recalibración (T19).
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from backtesting.metricas.brier import calcular_brier_score
from backtesting.metricas.log_loss import calcular_log_loss
from db import obtener_pool
from motor.alertas_calibracion import _construir_alerta

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoRecalibracion:
    calibrador_id: Optional[UUID]
    creado: bool
    mensaje: str
    detalle: dict[str, object]


def sugerir_recalibracion(
    *,
    mercado: str,
    origen: str,
    periodo_fin: date,
    modelo_version_id: Optional[int] = None,
    pool=None,
) -> dict[str, object]:
    pool = pool or obtener_pool()

    consulta = """
        SELECT tipo_alerta, severidad
        FROM alertas_calibracion
        WHERE mercado = %s
          AND origen = %s
          AND periodo_fin = %s
          AND resuelta = false
          AND (%s::int IS NULL OR modelo_version_id = %s::int)
    """
    params = [mercado, origen, periodo_fin, modelo_version_id, modelo_version_id]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            alertas = cursor.fetchall()

    if not alertas:
        return {
            "sugerida": False,
            "motivo": "Sin alertas activas para el periodo.",
            "alertas": [],
        }

    tipos = {fila[0] for fila in alertas}
    severidades = {fila[1] for fila in alertas}
    sugerida = "RECALIBRACION_SUGERIDA" in tipos or "CRITICAL" in severidades

    return {
        "sugerida": sugerida,
        "motivo": "Alertas activas detectadas." if sugerida else "Alertas no requieren recalibración.",
        "alertas": list(tipos),
    }


def recalibrar_mercado(
    *,
    mercado: str,
    origen: str,
    cutoff_datos: date,
    modelo_version_id: Optional[int] = None,
    metodo: str = "platt",
    min_muestras: int = 100,
    pool=None,
) -> ResultadoRecalibracion:
    """
    Ejecuta recalibración con Platt scaling usando datos hasta cutoff_datos.
    """
    pool = pool or obtener_pool()

    probabilidades, resultados = _cargar_datos_entrenamiento(
        pool,
        mercado=mercado,
        origen=origen,
        cutoff_datos=cutoff_datos,
        modelo_version_id=modelo_version_id,
    )

    n_muestras = len(resultados)
    if n_muestras < min_muestras:
        _construir_alerta(
            mercado=mercado,
            origen=origen,
            fecha_inicio=cutoff_datos,
            fecha_fin=cutoff_datos,
            modelo_version_id=modelo_version_id,
            tipo_alerta="DATOS_INSUFICIENTES",
            severidad="WARNING",
            metrica_afectada="n_muestras",
            valor_actual=n_muestras,
            valor_umbral=min_muestras,
            valor_baseline=None,
            mensaje="Recalibración bloqueada por datos insuficientes.",
            detalles={
                "motivo": "min_muestras",
                "n_muestras": n_muestras,
                "min_muestras": min_muestras,
            },
            pool=pool,
        )
        return ResultadoRecalibracion(
            calibrador_id=None,
            creado=False,
            mensaje="Recalibración bloqueada por datos insuficientes.",
            detalle={"n_muestras": n_muestras, "min_muestras": min_muestras},
        )

    a, b = _ajustar_platt(probabilidades, resultados)
    probabilidades_cal = [_aplicar_platt(p, a, b) for p in probabilidades]

    predicciones_raw = list(zip(probabilidades, resultados))
    predicciones_cal = list(zip(probabilidades_cal, resultados))

    brier_raw = calcular_brier_score(predicciones_raw)["brier_score"]
    brier_cal = calcular_brier_score(predicciones_cal)["brier_score"]
    log_loss_raw = calcular_log_loss(predicciones_raw)["log_loss"]
    log_loss_cal = calcular_log_loss(predicciones_cal)["log_loss"]

    mejora = brier_raw - brier_cal if brier_raw is not None and brier_cal is not None else None

    existente_id = _buscar_calibrador_existente(
        pool,
        mercado=mercado,
        origen=origen,
        cutoff_datos=cutoff_datos,
        metodo=metodo,
    )

    if existente_id:
        _activar_calibrador(pool, mercado=mercado, calibrador_id=existente_id)
        return ResultadoRecalibracion(
            calibrador_id=existente_id,
            creado=False,
            mensaje="Calibrador existente reactivado.",
            detalle={
                "metodo": metodo,
                "n_muestras": n_muestras,
                "brier_antes": brier_raw,
                "brier_despues": brier_cal,
                "log_loss_antes": log_loss_raw,
                "log_loss_despues": log_loss_cal,
            },
        )

    calibrador_id = uuid4()
    parametros_json = {
        "metodo": metodo,
        "a": a,
        "b": b,
        "cutoff_datos": cutoff_datos.isoformat(),
    }

    _insertar_calibrador(
        pool,
        calibrador_id=calibrador_id,
        mercado=mercado,
        metodo=metodo,
        cutoff_datos=cutoff_datos,
        n_muestras=n_muestras,
        origen=origen,
        parametros=parametros_json,
        brier_antes=brier_raw,
        brier_despues=brier_cal,
        log_loss_antes=log_loss_raw,
        log_loss_despues=log_loss_cal,
        mejora_validacion=mejora,
    )

    _activar_calibrador(pool, mercado=mercado, calibrador_id=calibrador_id)

    return ResultadoRecalibracion(
        calibrador_id=calibrador_id,
        creado=True,
        mensaje="Recalibración completada.",
        detalle={
            "metodo": metodo,
            "n_muestras": n_muestras,
            "brier_antes": brier_raw,
            "brier_despues": brier_cal,
            "log_loss_antes": log_loss_raw,
            "log_loss_despues": log_loss_cal,
            "mejora_validacion": mejora,
            "parametros": parametros_json,
        },
    )


def listar_calibradores(
    *,
    mercado: Optional[str] = None,
    activo: Optional[bool] = None,
    pool=None,
) -> list[dict[str, object]]:
    pool = pool or obtener_pool()
    filtros = []
    params: list[object] = []
    if mercado:
        filtros.append("mercado = %s")
        params.append(mercado)
    if activo is not None:
        filtros.append("activo = %s")
        params.append(activo)

    where_sql = "WHERE " + " AND ".join(filtros) if filtros else ""
    consulta = f"""
        SELECT
            id,
            mercado,
            metodo,
            fecha_entrenamiento,
            cutoff_datos,
            n_muestras_entrenamiento,
            origen_datos,
            parametros_json,
            activo,
            brier_antes,
            brier_despues,
            log_loss_antes,
            log_loss_despues,
            mejora_validacion,
            notas
        FROM calibradores
        {where_sql}
        ORDER BY fecha_entrenamiento DESC
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    return [
        {
            "id": fila[0],
            "mercado": fila[1],
            "metodo": fila[2],
            "fecha_entrenamiento": fila[3],
            "cutoff_datos": fila[4],
            "n_muestras_entrenamiento": fila[5],
            "origen_datos": fila[6],
            "parametros_json": fila[7],
            "activo": fila[8],
            "brier_antes": fila[9],
            "brier_despues": fila[10],
            "log_loss_antes": fila[11],
            "log_loss_despues": fila[12],
            "mejora_validacion": fila[13],
            "notas": fila[14],
        }
        for fila in filas
    ]


def _cargar_datos_entrenamiento(
    pool,
    *,
    mercado: str,
    origen: str,
    cutoff_datos: date,
    modelo_version_id: Optional[int],
) -> tuple[list[float], list[bool]]:
    consulta = """
        SELECT p_raw, outcome_binario
        FROM predicciones_registradas
        WHERE mercado = %s
          AND origen = %s
          AND fecha_partido < %s
          AND p_raw IS NOT NULL
          AND outcome_binario IS NOT NULL
          AND (%s::int IS NULL OR modelo_version_id = %s::int)
    """
    params = [mercado, origen, cutoff_datos, modelo_version_id, modelo_version_id]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    probabilidades = [float(fila[0]) for fila in filas]
    resultados = [bool(fila[1]) for fila in filas]
    return probabilidades, resultados


def _buscar_calibrador_existente(
    pool,
    *,
    mercado: str,
    origen: str,
    cutoff_datos: date,
    metodo: str,
) -> Optional[UUID]:
    consulta = """
        SELECT id
        FROM calibradores
        WHERE mercado = %s
          AND origen_datos = %s
          AND cutoff_datos = %s
          AND metodo = %s
        LIMIT 1
    """
    params = [mercado, origen, cutoff_datos, metodo]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    if not fila:
        return None
    valor = fila[0]
    return valor if isinstance(valor, UUID) else UUID(str(valor))


def _insertar_calibrador(
    pool,
    *,
    calibrador_id: UUID,
    mercado: str,
    metodo: str,
    cutoff_datos: date,
    n_muestras: int,
    origen: str,
    parametros: dict[str, object],
    brier_antes: Optional[float],
    brier_despues: Optional[float],
    log_loss_antes: Optional[float],
    log_loss_despues: Optional[float],
    mejora_validacion: Optional[float],
) -> None:
    consulta = """
        INSERT INTO calibradores (
            id,
            mercado,
            metodo,
            fecha_entrenamiento,
            cutoff_datos,
            n_muestras_entrenamiento,
            origen_datos,
            parametros_json,
            activo,
            brier_antes,
            brier_despues,
            log_loss_antes,
            log_loss_despues,
            mejora_validacion,
            notas
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = [
        str(calibrador_id),
        mercado,
        metodo,
        datetime.utcnow(),
        cutoff_datos,
        n_muestras,
        origen,
        json.dumps(parametros, ensure_ascii=False),
        True,
        brier_antes,
        brier_despues,
        log_loss_antes,
        log_loss_despues,
        mejora_validacion,
        "Recalibración automática",
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)


def _activar_calibrador(pool, *, mercado: str, calibrador_id: UUID) -> None:
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE calibradores SET activo = false WHERE mercado = %s AND id <> %s",
                [mercado, str(calibrador_id)],
            )
            cursor.execute(
                "UPDATE calibradores SET activo = true WHERE id = %s",
                [str(calibrador_id)],
            )


def _ajustar_platt(probabilidades: list[float], resultados: list[bool]) -> tuple[float, float]:
    eps = 1e-6
    x_vals = [_logit(_clip(p, eps, 1 - eps)) for p in probabilidades]
    y_vals = [1.0 if r else 0.0 for r in resultados]

    a, b = 1.0, 0.0
    for _ in range(50):
        grad_a = 0.0
        grad_b = 0.0
        h_aa = 0.0
        h_bb = 0.0
        h_ab = 0.0
        for x, y in zip(x_vals, y_vals):
            z = a * x + b
            p = _sigmoid(z)
            diff = p - y
            grad_a += diff * x
            grad_b += diff
            w = p * (1.0 - p)
            h_aa += w * x * x
            h_bb += w
            h_ab += w * x

        h_aa += 1e-6
        h_bb += 1e-6
        det = h_aa * h_bb - h_ab * h_ab
        if det == 0:
            break

        delta_a = (h_bb * grad_a - h_ab * grad_b) / det
        delta_b = (-h_ab * grad_a + h_aa * grad_b) / det
        a -= delta_a
        b -= delta_b

        if abs(delta_a) < 1e-6 and abs(delta_b) < 1e-6:
            break

    return a, b


def _aplicar_platt(p: float, a: float, b: float) -> float:
    p = _clip(p, 1e-6, 1 - 1e-6)
    x = _logit(p)
    return _sigmoid(a * x + b)


def _sigmoid(z: float) -> float:
    # Versión numéricamente estable para evitar overflow en exp() con |z| alto.
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _clip(valor: float, minimo: float, maximo: float) -> float:
    return max(min(valor, maximo), minimo)

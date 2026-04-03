# -*- coding: utf-8 -*-
"""
calibradores.py — Aplicación de calibradores activos en producción (T21).
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from db import obtener_pool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalibradorActivo:
    id: UUID
    mercado: str
    metodo: str
    cutoff_datos: Optional[date]
    origen_datos: Optional[str]
    parametros: dict[str, object]

    def calibrar(self, p_raw: float) -> float:
        if self.metodo == "platt":
            return _aplicar_platt(p_raw, self.parametros)
        if self.metodo == "isotonic":
            return _aplicar_isotonic(p_raw, self.parametros)
        return _clip(float(p_raw), 0.0, 1.0)


def obtener_calibrador_activo(
    *,
    mercado: str,
    origen: Optional[str] = None,
    fecha_partido: Optional[date] = None,
    pool=None,
) -> Optional[CalibradorActivo]:
    pool = pool or obtener_pool()
    filtros = ["mercado = %s", "activo = true"]
    params: list[object] = [mercado]
    if origen:
        filtros.append("origen_datos = %s")
        params.append(origen)

    where_sql = " AND ".join(filtros)
    consulta = f"""
        SELECT id, mercado, metodo, cutoff_datos, origen_datos, parametros_json, fecha_entrenamiento
        FROM calibradores
        WHERE {where_sql}
        ORDER BY fecha_entrenamiento DESC
        LIMIT 2
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    if not filas:
        return None

    if len(filas) > 1:
        ids = [str(fila[0]) for fila in filas]
        logger.error(
            "VIOLACIÓN DE INTEGRIDAD: múltiples calibradores activos para mercado=%s (origen=%s). IDs=%s",
            mercado,
            origen,
            ids,
        )
        raise RuntimeError(
            f"Múltiples calibradores activos para mercado={mercado} (origen={origen})."
        )

    fila = filas[0]
    valor_id = fila[0]
    calibrador_id = valor_id if isinstance(valor_id, UUID) else UUID(str(valor_id))
    cutoff_datos = fila[3]
    origen_datos = fila[4]
    parametros = _parsear_parametros(fila[5])

    if fecha_partido and cutoff_datos and fecha_partido < cutoff_datos:
        logger.warning(
            "Calibrador activo omitido por cutoff incompatible (mercado=%s fecha_partido=%s cutoff=%s).",
            mercado,
            fecha_partido,
            cutoff_datos,
        )
        return None

    return CalibradorActivo(
        id=calibrador_id,
        mercado=fila[1],
        metodo=str(fila[2]).lower(),
        cutoff_datos=cutoff_datos,
        origen_datos=origen_datos,
        parametros=parametros,
    )


def _parsear_parametros(parametros: object) -> dict[str, object]:
    if parametros is None:
        return {}
    if isinstance(parametros, dict):
        return parametros
    if isinstance(parametros, str):
        try:
            return json.loads(parametros)
        except json.JSONDecodeError:
            logger.warning("parametros_json inválido, se ignora.")
            return {}
    return {}


def _aplicar_platt(p_raw: float, parametros: dict[str, object]) -> float:
    a = parametros.get("a")
    b = parametros.get("b")
    if a is None or b is None:
        return _clip(float(p_raw), 0.0, 1.0)
    p = _clip(float(p_raw), 1e-6, 1 - 1e-6)
    x = math.log(p / (1 - p))
    z = (float(a) * x) + float(b)
    return _clip(_sigmoid_estable(z), 0.0, 1.0)


def _sigmoid_estable(z: float) -> float:
    """Sigmoid numéricamente estable para evitar overflow en exp()."""
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _aplicar_isotonic(p_raw: float, parametros: dict[str, object]) -> float:
    x_max = parametros.get("x_max") or parametros.get("x")
    y = parametros.get("y")
    if not isinstance(x_max, list) or not isinstance(y, list) or not x_max or not y:
        return _clip(float(p_raw), 0.0, 1.0)
    p = float(p_raw)
    idx = 0
    while idx < len(x_max) and p > float(x_max[idx]):
        idx += 1
    idx = min(idx, len(y) - 1)
    return _clip(float(y[idx]), 0.0, 1.0)


def _clip(valor: float, minimo: float, maximo: float) -> float:
    return max(min(valor, maximo), minimo)

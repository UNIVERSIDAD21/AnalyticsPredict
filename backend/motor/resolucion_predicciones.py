# -*- coding: utf-8 -*-
"""
resolucion_predicciones.py — Resolvedor de outcomes para predicciones registradas.

TAREA 6: Convierte predicciones pendientes en datos calibrables.

Este módulo toma predicciones de `predicciones_registradas` donde `resuelto=false`
y las resuelve usando los datos reales de la tabla `partidos`.

REGLAS DE CÁLCULO:
- valor_real según mercado:
  - Q1: local_q1 + visitante_q1
  - Q2: local_q2 + visitante_q2
  - Q3: local_q3 + visitante_q3
  - Q4: local_q4 + visitante_q4
  - COMPLETO: local_total + visitante_total

- outcome_binario según lado:
  - OVER + valor_real > linea → True
  - OVER + valor_real < linea → False
  - UNDER + valor_real < linea → True
  - UNDER + valor_real > linea → False
  - valor_real == linea → NULL (PUSH, pero resuelto=True)

GARANTÍAS:
- Idempotencia: correr N veces produce el mismo resultado
- No data leakage: no resuelve si el partido no tiene datos completos
- Transacciones por lotes: no bloquea la BD
- Logging operativo: cuántas resolvió, cuántas no pudo y por qué
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from db import obtener_pool

logger = logging.getLogger(__name__)


@dataclass
class ResumenResolucion:
    """Resumen del proceso de resolución."""

    resueltas: int = 0
    pendientes: int = 0
    push: int = 0
    errores: int = 0
    sin_datos_partido: int = 0
    ya_resueltas: int = 0
    detalles_errores: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resueltas": self.resueltas,
            "pendientes": self.pendientes,
            "push": self.push,
            "errores": self.errores,
            "sin_datos_partido": self.sin_datos_partido,
            "ya_resueltas": self.ya_resueltas,
            "detalles_errores": self.detalles_errores[:10],  # Limitar a 10 errores
        }


def _calcular_valor_real(
    mercado: str,
    local_q1: Optional[int],
    local_q2: Optional[int],
    local_q3: Optional[int],
    local_q4: Optional[int],
    local_total: Optional[int],
    visitante_q1: Optional[int],
    visitante_q2: Optional[int],
    visitante_q3: Optional[int],
    visitante_q4: Optional[int],
    visitante_total: Optional[int],
) -> Optional[int]:
    """
    Calcula el valor real según el mercado.

    Retorna None si faltan datos necesarios para el mercado.
    """
    if mercado == "Q1":
        if local_q1 is None or visitante_q1 is None:
            return None
        return local_q1 + visitante_q1

    if mercado == "Q2":
        if local_q2 is None or visitante_q2 is None:
            return None
        return local_q2 + visitante_q2

    if mercado == "Q3":
        if local_q3 is None or visitante_q3 is None:
            return None
        return local_q3 + visitante_q3

    if mercado == "Q4":
        if local_q4 is None or visitante_q4 is None:
            return None
        return local_q4 + visitante_q4

    if mercado == "COMPLETO":
        if local_total is None or visitante_total is None:
            return None
        return local_total + visitante_total

    # Mercado no reconocido
    return None


def _calcular_outcome_binario(
    lado: str,
    valor_real: int,
    linea: float,
) -> Optional[bool]:
    """
    Calcula el outcome binario comparando valor_real con línea.

    - OVER + valor_real > linea → True
    - OVER + valor_real < linea → False
    - UNDER + valor_real < linea → True
    - UNDER + valor_real > linea → False
    - valor_real == linea → None (PUSH)
    """
    # Comparación con tolerancia para floats
    if abs(valor_real - linea) < 0.001:
        # PUSH: empate exacto con la línea
        return None

    if lado == "OVER":
        return valor_real > linea

    if lado == "UNDER":
        return valor_real < linea

    # Lado no reconocido - no debería pasar
    return None


def _partido_tiene_datos_completos(
    mercado: str,
    local_q1: Optional[int],
    local_q2: Optional[int],
    local_q3: Optional[int],
    local_q4: Optional[int],
    local_total: Optional[int],
    visitante_q1: Optional[int],
    visitante_q2: Optional[int],
    visitante_q3: Optional[int],
    visitante_q4: Optional[int],
    visitante_total: Optional[int],
) -> bool:
    """Verifica que el partido tiene los datos necesarios para resolver el mercado."""
    if mercado == "Q1":
        return local_q1 is not None and visitante_q1 is not None

    if mercado == "Q2":
        return local_q2 is not None and visitante_q2 is not None

    if mercado == "Q3":
        return local_q3 is not None and visitante_q3 is not None

    if mercado == "Q4":
        return local_q4 is not None and visitante_q4 is not None

    if mercado == "COMPLETO":
        return local_total is not None and visitante_total is not None

    return False


def resolver_predicciones(
    *,
    limite: int = 1000,
    mercado: Optional[str] = None,
    origen: Optional[str] = None,
    solo_hasta_fecha: Optional[date] = None,
    force: bool = False,
    pool=None,
) -> ResumenResolucion:
    """
    Resuelve predicciones pendientes actualizando valor_real, outcome_binario.

    Parámetros:
    - limite: Batch size máximo (default 1000)
    - mercado: Filtrar por mercado específico (Q1, Q2, Q3, Q4, COMPLETO)
    - origen: Filtrar por origen (API_USUARIO, BACKTEST_BATCH, etc.)
    - solo_hasta_fecha: Solo resolver predicciones hasta esta fecha
    - force: Si True, re-resuelve predicciones ya resueltas (peligroso)
    - pool: Pool de conexiones a usar

    Retorna:
    - ResumenResolucion con estadísticas del proceso

    IDEMPOTENCIA: Correr múltiples veces produce el mismo resultado.
    Predicciones ya resueltas no se tocan (a menos que force=True).
    """
    pool = pool or obtener_pool()
    resumen = ResumenResolucion()

    # Construir query con filtros
    condiciones = ["pr.resuelto = false"] if not force else []
    parametros: List[Any] = []

    if mercado:
        condiciones.append("pr.mercado = %s")
        parametros.append(mercado)

    if origen:
        condiciones.append("pr.origen = %s")
        parametros.append(origen)

    if solo_hasta_fecha:
        condiciones.append("pr.fecha_partido <= %s")
        parametros.append(solo_hasta_fecha)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"
    parametros.append(limite)

    query_select = f"""
        SELECT
            pr.id AS prediccion_id,
            pr.partido_id,
            pr.mercado,
            pr.lado,
            pr.linea,
            pr.resuelto,
            p.local_q1,
            p.local_q2,
            p.local_q3,
            p.local_q4,
            p.local_total,
            p.visitante_q1,
            p.visitante_q2,
            p.visitante_q3,
            p.visitante_q4,
            p.visitante_total
        FROM predicciones_registradas pr
        JOIN partidos_baloncesto p ON pr.partido_id = p.id
        WHERE {where_clause}
        ORDER BY pr.fecha_partido ASC
        LIMIT %s
        FOR UPDATE SKIP LOCKED
    """

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query_select, parametros)
                filas = cursor.fetchall()

                if not filas:
                    logger.info("No hay predicciones pendientes para resolver")
                    return resumen

                logger.info(
                    "Procesando %d predicciones (limite=%d mercado=%s origen=%s hasta=%s force=%s)",
                    len(filas),
                    limite,
                    mercado,
                    origen,
                    solo_hasta_fecha,
                    force,
                )

                for fila in filas:
                    (
                        prediccion_id,
                        partido_id,
                        pred_mercado,
                        lado,
                        linea,
                        ya_resuelto,
                        local_q1,
                        local_q2,
                        local_q3,
                        local_q4,
                        local_total,
                        visitante_q1,
                        visitante_q2,
                        visitante_q3,
                        visitante_q4,
                        visitante_total,
                    ) = fila

                    # Si ya está resuelta y no es force, saltar
                    if ya_resuelto and not force:
                        resumen.ya_resueltas += 1
                        continue

                    # Verificar que el partido existe y tiene datos
                    if partido_id is None:
                        resumen.sin_datos_partido += 1
                        resumen.detalles_errores.append(
                            f"prediccion_id={prediccion_id}: partido_id es NULL"
                        )
                        continue

                    # Verificar datos completos para el mercado
                    if not _partido_tiene_datos_completos(
                        pred_mercado,
                        local_q1,
                        local_q2,
                        local_q3,
                        local_q4,
                        local_total,
                        visitante_q1,
                        visitante_q2,
                        visitante_q3,
                        visitante_q4,
                        visitante_total,
                    ):
                        resumen.sin_datos_partido += 1
                        resumen.pendientes += 1
                        logger.debug(
                            "Predicción pendiente: partido_id=%s mercado=%s - datos incompletos",
                            partido_id,
                            pred_mercado,
                        )
                        continue

                    # Calcular valor_real
                    valor_real = _calcular_valor_real(
                        pred_mercado,
                        local_q1,
                        local_q2,
                        local_q3,
                        local_q4,
                        local_total,
                        visitante_q1,
                        visitante_q2,
                        visitante_q3,
                        visitante_q4,
                        visitante_total,
                    )

                    if valor_real is None:
                        resumen.errores += 1
                        resumen.detalles_errores.append(
                            f"prediccion_id={prediccion_id}: error calculando valor_real (mercado={pred_mercado})"
                        )
                        continue

                    # Calcular outcome_binario
                    outcome = _calcular_outcome_binario(lado, valor_real, float(linea))

                    # Actualizar predicción
                    try:
                        cursor.execute(
                            """
                            UPDATE predicciones_registradas
                            SET
                                valor_real = %s,
                                outcome_binario = %s,
                                resuelto = true,
                                timestamp_resolucion = %s
                            WHERE id = %s
                            """,
                            [
                                valor_real,
                                outcome,
                                datetime.utcnow(),
                                str(prediccion_id),
                            ],
                        )

                        resumen.resueltas += 1
                        if outcome is None:
                            resumen.push += 1
                            logger.debug(
                                "PUSH: prediccion_id=%s valor_real=%d linea=%s",
                                prediccion_id,
                                valor_real,
                                linea,
                            )
                        else:
                            logger.debug(
                                "Resuelta: prediccion_id=%s valor_real=%d linea=%s lado=%s outcome=%s",
                                prediccion_id,
                                valor_real,
                                linea,
                                lado,
                                outcome,
                            )

                    except Exception as e:
                        resumen.errores += 1
                        resumen.detalles_errores.append(
                            f"prediccion_id={prediccion_id}: error UPDATE - {str(e)}"
                        )
                        logger.exception(
                            "Error actualizando prediccion_id=%s", prediccion_id
                        )

                # Commit de todos los cambios
                conexion.commit()

    except Exception as e:
        resumen.errores += 1
        resumen.detalles_errores.append(f"Error general: {str(e)}")
        logger.exception("Error en resolver_predicciones")

    logger.info(
        "Resolución completada: resueltas=%d push=%d pendientes=%d sin_datos=%d errores=%d ya_resueltas=%d",
        resumen.resueltas,
        resumen.push,
        resumen.pendientes,
        resumen.sin_datos_partido,
        resumen.errores,
        resumen.ya_resueltas,
    )

    return resumen


def obtener_estadisticas_predicciones(pool=None) -> Dict[str, Any]:
    """
    Obtiene estadísticas actuales de predicciones registradas.

    Útil para monitoreo y debugging.
    """
    pool = pool or obtener_pool()

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resuelto = true) AS resueltas,
                        COUNT(*) FILTER (WHERE resuelto = false) AS pendientes,
                        COUNT(*) FILTER (WHERE outcome_binario IS NULL AND resuelto = true) AS push,
                        COUNT(*) FILTER (WHERE outcome_binario = true) AS aciertos,
                        COUNT(*) FILTER (WHERE outcome_binario = false) AS fallos
                    FROM predicciones_registradas
                    """
                )
                fila = cursor.fetchone()
                if fila:
                    total, resueltas, pendientes, push, aciertos, fallos = fila
                    return {
                        "total": total,
                        "resueltas": resueltas,
                        "pendientes": pendientes,
                        "push": push,
                        "aciertos": aciertos,
                        "fallos": fallos,
                        "tasa_aciertos": (
                            round(aciertos / (aciertos + fallos), 4)
                            if (aciertos + fallos) > 0
                            else None
                        ),
                    }
                return {}
    except Exception:
        logger.exception("Error obteniendo estadísticas de predicciones")
        return {}


def obtener_predicciones_pendientes_por_mercado(pool=None) -> Dict[str, int]:
    """
    Obtiene conteo de predicciones pendientes agrupadas por mercado.
    """
    pool = pool or obtener_pool()

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT mercado, COUNT(*)
                    FROM predicciones_registradas
                    WHERE resuelto = false
                    GROUP BY mercado
                    ORDER BY mercado
                    """
                )
                return {fila[0]: fila[1] for fila in cursor.fetchall()}
    except Exception:
        logger.exception("Error obteniendo predicciones pendientes por mercado")
        return {}


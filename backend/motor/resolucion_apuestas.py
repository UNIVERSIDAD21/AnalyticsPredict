# -*- coding: utf-8 -*-
"""
resolucion_apuestas.py — Resolvedor de outcomes para apuestas de bitacora.

TAREA: Convierte apuestas PENDIENTE en GANADA/PERDIDA/PUSH.

Este modulo toma apuestas de la tabla `apuestas` donde `resultado='PENDIENTE'`
y las resuelve usando los datos reales de la tabla `partidos`.

REGLAS DE CALCULO:
- valor_real segun mercado:
  - Q1: local_q1 + visitante_q1
  - Q2: local_q2 + visitante_q2
  - Q3: local_q3 + visitante_q3
  - Q4: local_q4 + visitante_q4
  - COMPLETO: local_total + visitante_total

- resultado segun lado:
  - OVER + valor_real > linea -> GANADA
  - OVER + valor_real < linea -> PERDIDA
  - UNDER + valor_real < linea -> GANADA
  - UNDER + valor_real > linea -> PERDIDA
  - valor_real == linea -> PUSH

GARANTIAS:
- Idempotencia: correr N veces produce el mismo resultado
- No data leakage: no resuelve si el partido no tiene datos completos
- Transacciones por lotes: no bloquea la BD
- Logging operativo: cuantas resolvio, cuantas no pudo y por que
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from zoneinfo import ZoneInfo
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from db import obtener_pool

logger = logging.getLogger(__name__)


@dataclass
class ResumenResolucionApuestas:
    """Resumen del proceso de resolucion de apuestas."""

    resueltas: int = 0
    ganadas: int = 0
    perdidas: int = 0
    push: int = 0
    pendientes: int = 0
    errores: int = 0
    sin_partido_id: int = 0
    sin_datos_partido: int = 0
    ya_resueltas: int = 0
    detalles_errores: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resueltas": self.resueltas,
            "ganadas": self.ganadas,
            "perdidas": self.perdidas,
            "push": self.push,
            "pendientes": self.pendientes,
            "errores": self.errores,
            "sin_partido_id": self.sin_partido_id,
            "sin_datos_partido": self.sin_datos_partido,
            "ya_resueltas": self.ya_resueltas,
            "detalles_errores": self.detalles_errores[:10],
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
    Calcula el valor real segun el mercado.

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

    return None


def _calcular_resultado(
    lado: str,
    valor_real: int,
    linea: float,
) -> str:
    """
    Calcula el resultado comparando valor_real con linea.

    - OVER + valor_real > linea -> GANADA
    - OVER + valor_real < linea -> PERDIDA
    - UNDER + valor_real < linea -> GANADA
    - UNDER + valor_real > linea -> PERDIDA
    - valor_real == linea -> PUSH
    """
    # Comparacion con tolerancia para floats
    if abs(valor_real - linea) < 0.001:
        return "PUSH"

    if lado == "OVER":
        return "GANADA" if valor_real > linea else "PERDIDA"

    if lado == "UNDER":
        return "GANADA" if valor_real < linea else "PERDIDA"

    return "PERDIDA"


def _calcular_ganancia(
    resultado: str,
    stake: float,
    cuota: float,
) -> float:
    """Calcula la ganancia/perdida de la apuesta."""
    if resultado == "GANADA":
        return stake * (cuota - 1)
    if resultado == "PERDIDA":
        return -stake
    # PUSH o ANULADA
    return 0.0


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


def resolver_apuestas(
    *,
    usuario_id: Optional[str] = None,
    limite: int = 1000,
    mercado: Optional[str] = None,
    solo_hasta_fecha: Optional[date] = None,
    force: bool = False,
    pool=None,
) -> ResumenResolucionApuestas:
    """
    Resuelve apuestas pendientes actualizando resultado, puntos_reales, ganancia.

    Parametros:
    - usuario_id: Filtrar por usuario especifico (None = todos)
    - limite: Batch size maximo (default 1000)
    - mercado: Filtrar por mercado especifico (Q1, Q2, Q3, Q4, COMPLETO)
    - solo_hasta_fecha: Solo resolver apuestas hasta esta fecha
    - force: Si True, re-resuelve apuestas ya resueltas (peligroso)
    - pool: Pool de conexiones a usar

    Retorna:
    - ResumenResolucionApuestas con estadisticas del proceso

    IDEMPOTENCIA: Correr multiples veces produce el mismo resultado.
    Apuestas ya resueltas no se tocan (a menos que force=True).
    """
    pool = pool or obtener_pool()
    resumen = ResumenResolucionApuestas()

    # Construir query con filtros
    condiciones = ["a.resultado = 'PENDIENTE'"] if not force else []
    parametros: List[Any] = []

    if usuario_id:
        condiciones.append("a.usuario_id = %s")
        parametros.append(usuario_id)

    if mercado:
        condiciones.append("a.mercado = %s")
        parametros.append(mercado)

    if solo_hasta_fecha:
        condiciones.append("a.fecha_partido <= %s")
        parametros.append(solo_hasta_fecha)

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"
    parametros.append(limite)

    query_select = f"""
        SELECT
            a.id AS apuesta_id,
            a.partido_id,
            a.fecha_partido,
            a.mercado,
            a.lado,
            a.linea,
            a.cuota,
            a.stake,
            a.resultado,
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
        FROM apuestas a
        LEFT JOIN partidos_baloncesto p ON a.partido_id::uuid = p.id
        WHERE {where_clause}
        ORDER BY a.fecha_partido ASC NULLS LAST
        LIMIT %s
        FOR UPDATE OF a SKIP LOCKED
    """

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                # Saneamiento preventivo: si alguna apuesta quedó resuelta antes de tiempo,
                # se devuelve a PENDIENTE para evitar inconsistencias en bitácora.
                hoy_bogota = datetime.now(ZoneInfo("America/Bogota")).date()
                revert_params: List[Any] = [hoy_bogota]
                revert_where = [
                    "resultado IN ('GANADA','PERDIDA','PUSH')",
                    "fecha_partido >= %s",
                ]
                if usuario_id:
                    revert_where.append("usuario_id = %s")
                    revert_params.append(usuario_id)

                cursor.execute(
                    f"""
                    UPDATE apuestas
                    SET
                        resultado = 'PENDIENTE',
                        puntos_reales = NULL,
                        ganancia = 0,
                        fecha_resolucion = NULL,
                        actualizado_en = NOW()
                    WHERE {' AND '.join(revert_where)}
                    """,
                    revert_params,
                )

                cursor.execute(query_select, parametros)
                filas = cursor.fetchall()

                if not filas:
                    logger.info("No hay apuestas pendientes para resolver")
                    return resumen

                logger.info(
                    "Procesando %d apuestas (limite=%d usuario=%s mercado=%s hasta=%s force=%s)",
                    len(filas),
                    limite,
                    usuario_id,
                    mercado,
                    solo_hasta_fecha,
                    force,
                )

                for fila in filas:
                    (
                        apuesta_id,
                        partido_id,
                        fecha_partido,
                        ap_mercado,
                        lado,
                        linea,
                        cuota,
                        stake,
                        resultado_actual,
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

                    # Si ya esta resuelta y no es force, saltar
                    if resultado_actual != "PENDIENTE" and not force:
                        resumen.ya_resueltas += 1
                        continue

                    # Verificar que tiene partido_id
                    if partido_id is None:
                        resumen.sin_partido_id += 1
                        resumen.pendientes += 1
                        resumen.detalles_errores.append(
                            f"apuesta_id={apuesta_id}: partido_id es NULL"
                        )
                        continue

                    # Guard-rail temporal: no resolver apuestas de fecha actual/futura
                    # para evitar cierres prematuros por diferencias de zona horaria/carga parcial.
                    hoy_bogota = datetime.now(ZoneInfo("America/Bogota")).date()
                    if fecha_partido is not None and fecha_partido >= hoy_bogota:
                        resumen.pendientes += 1
                        logger.debug(
                            "Apuesta pendiente: partido_id=%s fecha_partido=%s >= hoy_bogota=%s",
                            partido_id,
                            fecha_partido,
                            hoy_bogota,
                        )
                        continue

                    # Verificar datos completos para el mercado
                    if not _partido_tiene_datos_completos(
                        ap_mercado,
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
                            "Apuesta pendiente: partido_id=%s mercado=%s - datos incompletos",
                            partido_id,
                            ap_mercado,
                        )
                        continue

                    # Calcular valor_real
                    valor_real = _calcular_valor_real(
                        ap_mercado,
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
                            f"apuesta_id={apuesta_id}: error calculando valor_real (mercado={ap_mercado})"
                        )
                        continue

                    # Calcular resultado
                    nuevo_resultado = _calcular_resultado(lado, valor_real, float(linea))

                    # Calcular ganancia
                    ganancia = _calcular_ganancia(
                        nuevo_resultado,
                        float(stake),
                        float(cuota),
                    )

                    # Actualizar apuesta
                    try:
                        cursor.execute(
                            """
                            UPDATE apuestas
                            SET
                                resultado = %s,
                                puntos_reales = %s,
                                ganancia = %s,
                                fecha_resolucion = %s,
                                actualizado_en = %s
                            WHERE id = %s
                            """,
                            [
                                nuevo_resultado,
                                valor_real,
                                ganancia,
                                datetime.utcnow(),
                                datetime.utcnow(),
                                str(apuesta_id),
                            ],
                        )

                        resumen.resueltas += 1
                        if nuevo_resultado == "GANADA":
                            resumen.ganadas += 1
                        elif nuevo_resultado == "PERDIDA":
                            resumen.perdidas += 1
                        else:
                            resumen.push += 1

                        logger.debug(
                            "Resuelta: apuesta_id=%s valor_real=%d linea=%s lado=%s resultado=%s ganancia=%.2f",
                            apuesta_id,
                            valor_real,
                            linea,
                            lado,
                            nuevo_resultado,
                            ganancia,
                        )

                    except Exception as e:
                        resumen.errores += 1
                        resumen.detalles_errores.append(
                            f"apuesta_id={apuesta_id}: error UPDATE - {str(e)}"
                        )
                        logger.exception(
                            "Error actualizando apuesta_id=%s", apuesta_id
                        )

                # Commit de todos los cambios
                conexion.commit()

    except Exception as e:
        resumen.errores += 1
        resumen.detalles_errores.append(f"Error general: {str(e)}")
        logger.exception("Error en resolver_apuestas")

    logger.info(
        "Resolucion completada: resueltas=%d ganadas=%d perdidas=%d push=%d pendientes=%d sin_partido=%d sin_datos=%d errores=%d",
        resumen.resueltas,
        resumen.ganadas,
        resumen.perdidas,
        resumen.push,
        resumen.pendientes,
        resumen.sin_partido_id,
        resumen.sin_datos_partido,
        resumen.errores,
    )

    return resumen


def obtener_estadisticas_apuestas(
    *,
    usuario_id: Optional[str] = None,
    pool=None,
) -> Dict[str, Any]:
    """
    Obtiene estadisticas actuales de apuestas.

    Util para monitoreo y debugging.
    """
    pool = pool or obtener_pool()

    where_clause = "WHERE usuario_id = %s" if usuario_id else ""
    params = [usuario_id] if usuario_id else []

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE resultado = 'PENDIENTE') AS pendientes,
                        COUNT(*) FILTER (WHERE resultado = 'GANADA') AS ganadas,
                        COUNT(*) FILTER (WHERE resultado = 'PERDIDA') AS perdidas,
                        COUNT(*) FILTER (WHERE resultado = 'PUSH') AS push,
                        COUNT(*) FILTER (WHERE resultado = 'ANULADA') AS anuladas,
                        COUNT(*) FILTER (WHERE partido_id IS NULL) AS sin_partido_id,
                        COALESCE(SUM(ganancia), 0) AS ganancia_total,
                        COALESCE(SUM(stake), 0) AS stake_total
                    FROM apuestas
                    {where_clause}
                    """,
                    params,
                )
                fila = cursor.fetchone()
                if fila:
                    (
                        total,
                        pendientes,
                        ganadas,
                        perdidas,
                        push,
                        anuladas,
                        sin_partido_id,
                        ganancia_total,
                        stake_total,
                    ) = fila
                    resueltas = ganadas + perdidas + push
                    return {
                        "total": total,
                        "pendientes": pendientes,
                        "ganadas": ganadas,
                        "perdidas": perdidas,
                        "push": push,
                        "anuladas": anuladas,
                        "resueltas": resueltas,
                        "sin_partido_id": sin_partido_id,
                        "win_rate": (
                            round(ganadas / (ganadas + perdidas), 4)
                            if (ganadas + perdidas) > 0
                            else None
                        ),
                        "ganancia_total": float(ganancia_total),
                        "stake_total": float(stake_total),
                        "roi": (
                            round(float(ganancia_total) / float(stake_total), 4)
                            if float(stake_total) > 0
                            else None
                        ),
                    }
                return {}
    except Exception:
        logger.exception("Error obteniendo estadisticas de apuestas")
        return {}


def obtener_apuestas_pendientes_por_mercado(
    *,
    usuario_id: Optional[str] = None,
    pool=None,
) -> Dict[str, int]:
    """
    Obtiene conteo de apuestas pendientes agrupadas por mercado.
    """
    pool = pool or obtener_pool()

    where_clause = "resultado = 'PENDIENTE'"
    params: List[Any] = []
    if usuario_id:
        where_clause += " AND usuario_id = %s"
        params.append(usuario_id)

    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT mercado, COUNT(*)
                    FROM apuestas
                    WHERE {where_clause}
                    GROUP BY mercado
                    ORDER BY mercado
                    """,
                    params,
                )
                return {fila[0]: fila[1] for fila in cursor.fetchall()}
    except Exception:
        logger.exception("Error obteniendo apuestas pendientes por mercado")
        return {}


# -*- coding: utf-8 -*-
"""
resolucion_combinadas.py — Resolución automática de combinadas.

Convierte selecciones pendientes en GANADA/PERDIDA/PUSH y actualiza el
estado global de la combinada.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from db import obtener_pool
from motor.resolucion_apuestas import _calcular_valor_real, _calcular_resultado

logger = logging.getLogger(__name__)


@dataclass
class ResumenResolucionCombinadas:
    """Resumen del proceso de resolución de combinadas."""

    selecciones_resueltas: int = 0
    combinadas_ganadas: int = 0
    combinadas_perdidas: int = 0
    combinadas_pendientes: int = 0
    selecciones_push: int = 0
    selecciones_pendientes: int = 0
    errores: int = 0
    detalles_errores: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selecciones_resueltas": self.selecciones_resueltas,
            "combinadas_ganadas": self.combinadas_ganadas,
            "combinadas_perdidas": self.combinadas_perdidas,
            "combinadas_pendientes": self.combinadas_pendientes,
            "selecciones_push": self.selecciones_push,
            "selecciones_pendientes": self.selecciones_pendientes,
            "errores": self.errores,
            "detalles_errores": self.detalles_errores[:10],
        }


def _actualizar_estado_combinada(combinada_id: str) -> None:
    """Recalcula el estado global de la combinada y actualiza la ganancia."""
    with obtener_pool().connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT resultado, cuota
                FROM selecciones_combinada
                WHERE combinada_id = %s
                """,
                (combinada_id,),
            )
            selecciones = cursor.fetchall()

            if not selecciones:
                return

            total = len(selecciones)
            ganadas = sum(1 for fila in selecciones if fila[0] == "GANADA")
            perdidas = sum(1 for fila in selecciones if fila[0] == "PERDIDA")
            push = sum(1 for fila in selecciones if fila[0] == "PUSH")
            pendientes = sum(1 for fila in selecciones if fila[0] == "PENDIENTE")

            if perdidas > 0:
                resultado = "PERDIDA"
            elif pendientes > 0:
                resultado = "PENDIENTE"
            else:
                resultado = "GANADA"

            cuota_efectiva = 1.0
            for resultado_sel, cuota in selecciones:
                if resultado_sel == "PUSH":
                    continue
                cuota_efectiva *= float(cuota or 1.0)

            cursor.execute(
                """
                SELECT stake
                FROM apuestas_combinadas
                WHERE id = %s
                """,
                (combinada_id,),
            )
            fila_stake = cursor.fetchone()
            stake = float(fila_stake[0]) if fila_stake else 0.0

            if resultado == "GANADA":
                ganancia = stake * (cuota_efectiva - 1)
            elif resultado == "PERDIDA":
                ganancia = -stake
            else:
                ganancia = 0.0

            fecha_resolucion = datetime.utcnow() if resultado != "PENDIENTE" else None

            cursor.execute(
                """
                UPDATE apuestas_combinadas
                SET resultado = %s,
                    ganancia = %s,
                    selecciones_ganadas = %s,
                    selecciones_perdidas = %s,
                    selecciones_push = %s,
                    selecciones_pendientes = %s,
                    fecha_resolucion = %s,
                    actualizado_en = NOW()
                WHERE id = %s
                """,
                (
                    resultado,
                    ganancia,
                    ganadas,
                    perdidas,
                    push,
                    pendientes,
                    fecha_resolucion,
                    combinada_id,
                ),
            )


def resolver_combinadas(
    *,
    usuario_id: Optional[str] = None,
    limite: int = 1000,
    solo_hasta_fecha: Optional[date] = None,
) -> Dict[str, Any]:
    """Resuelve selecciones pendientes de combinadas."""
    resumen = ResumenResolucionCombinadas()

    query = """
        SELECT
            sc.id,
            sc.combinada_id,
            sc.partido_id,
            sc.mercado,
            sc.lado,
            sc.linea,
            p.local_q1,
            p.local_q2,
            p.local_q3,
            p.local_q4,
            p.local_total,
            p.visitante_q1,
            p.visitante_q2,
            p.visitante_q3,
            p.visitante_q4,
            p.visitante_total,
            p.fecha_partido
        FROM selecciones_combinada sc
        JOIN apuestas_combinadas ac ON ac.id = sc.combinada_id
        LEFT JOIN partidos p ON p.id = sc.partido_id
        WHERE sc.resultado = 'PENDIENTE'
          AND ac.resultado = 'PENDIENTE'
    """

    parametros: List[Any] = []
    if usuario_id:
        query += " AND ac.usuario_id = %s"
        parametros.append(usuario_id)

    if solo_hasta_fecha:
        query += " AND p.fecha_partido <= %s"
        parametros.append(solo_hasta_fecha)

    query += " ORDER BY p.fecha_partido DESC NULLS LAST LIMIT %s"
    parametros.append(limite)

    with obtener_pool().connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(query, parametros)
            pendientes = cursor.fetchall()

            for (
                seleccion_id,
                combinada_id,
                _partido_id,
                mercado,
                lado,
                linea,
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
                _fecha_partido,
            ) in pendientes:
                try:
                    valor_real = _calcular_valor_real(
                        mercado,
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
                        resumen.selecciones_pendientes += 1
                        continue

                    resultado = _calcular_resultado(lado, valor_real, float(linea))
                    fecha_resolucion = datetime.utcnow()

                    cursor.execute(
                        """
                        UPDATE selecciones_combinada
                        SET resultado = %s,
                            puntos_reales = %s,
                            fecha_resolucion = %s
                        WHERE id = %s
                        """,
                        (resultado, valor_real, fecha_resolucion, seleccion_id),
                    )

                    resumen.selecciones_resueltas += 1
                    if resultado == "PUSH":
                        resumen.selecciones_push += 1

                    _actualizar_estado_combinada(str(combinada_id))
                except Exception as exc:
                    resumen.errores += 1
                    resumen.detalles_errores.append(str(exc))

    return resumen.to_dict()

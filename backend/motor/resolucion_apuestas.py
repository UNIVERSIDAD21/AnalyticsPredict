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
from servicios.politica_pnl import publicar_pnl

logger = logging.getLogger(__name__)

_NBA_COMPETENCIA_SQL = "(a.competicion_id IS NULL OR EXISTS ("
_NBA_COMPETENCIA_SQL += "SELECT 1 FROM competiciones_baloncesto cb "
_NBA_COMPETENCIA_SQL += "WHERE cb.id = a.competicion_id AND cb.codigo = 'nba'))"


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
    # Un marcador total 0–0 no acredita outcome NBA, incluso con Q1–Q4 en cero.
    if local_total == 0 and visitante_total == 0:
        return False
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
    limite: int = 1000,
    mercado: Optional[str] = None,
    solo_hasta_fecha: Optional[date] = None,
    force: bool = False,
    pool=None,
) -> ResumenResolucionApuestas:
    """Entrada legacy NBA. Nunca reabre ni recalcula registros ya completados.

    force se conserva en firma por compatibilidad, no habilita re-liquidación.
    """
    from motor.resolucion_bitacora import resolver_bitacora
    r = resolver_bitacora(pool=pool, deportes=('baloncesto',), solo_liga='nba',
                         limite=limite, mercado=mercado, hasta=solo_hasta_fecha)
    return ResumenResolucionApuestas(
        resueltas=r['resueltas'], ganadas=r['ganadas'], perdidas=r['perdidas'],
        push=r['push'], pendientes=r['pendientes'], errores=r['errores'],
        sin_partido_id=r['motivos_pendientes'].get('sin_partido', 0),
        sin_datos_partido=r['motivos_pendientes'].get('sin_datos_mercado', 0),
        detalles_errores=r['detalles_errores'])


def obtener_estadisticas_apuestas(
    *,
    pool=None,
) -> Dict[str, Any]:
    """
    Obtiene estadisticas actuales de apuestas.

    Util para monitoreo y debugging.
    """
    pool = pool or obtener_pool()

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
                    FROM apuestas a
                    WHERE {_NBA_COMPETENCIA_SQL}
                    """,
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
                    return publicar_pnl({
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
                        # La suma histórica no tiene procedencia completa de
                        # stake/cuota/outcome. Este GET no publica ROI bruto.
                        "roi": None,
                    })
                return {}
    except Exception:
        raise


def obtener_apuestas_pendientes_por_mercado(
    *,
    pool=None,
) -> Dict[str, int]:
    """
    Obtiene conteo de apuestas pendientes agrupadas por mercado.
    """
    pool = pool or obtener_pool()

    where_clause = f"a.resultado = 'PENDIENTE' AND {_NBA_COMPETENCIA_SQL}"
    try:
        with pool.connection() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT a.mercado, COUNT(*)
                    FROM apuestas a
                    WHERE {where_clause}
                    GROUP BY a.mercado
                    ORDER BY a.mercado
                    """,
                )
                return {fila[0]: fila[1] for fila in cursor.fetchall()}
    except Exception:
        raise

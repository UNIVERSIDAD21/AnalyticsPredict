# -*- coding: utf-8 -*-
"""Resolver predicciones de fútbol en tabla predicciones_futbol."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Any

from db import obtener_pool

logger = logging.getLogger(__name__)


@dataclass
class ResumenResolucionFutbol:
    resueltas: int = 0
    push: int = 0
    pendientes: int = 0
    sin_datos_partido: int = 0
    errores: int = 0
    detalles_errores: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resueltas": self.resueltas,
            "push": self.push,
            "pendientes": self.pendientes,
            "sin_datos_partido": self.sin_datos_partido,
            "errores": self.errores,
            "detalles_errores": self.detalles_errores[:10],
        }


def _valor_real_futbol(mercado: str, fila_partido: Dict[str, Any]) -> Optional[float]:
    m = (mercado or "").upper()

    if m.startswith("GOLES"):
        if "_1T" in m:
            loc, vis = fila_partido.get("local_goles_1t"), fila_partido.get("visitante_goles_1t")
        elif "_2T" in m:
            loc, vis = fila_partido.get("local_goles_2t"), fila_partido.get("visitante_goles_2t")
        else:
            loc, vis = fila_partido.get("local_goles_total"), fila_partido.get("visitante_goles_total")
    elif m.startswith("CORNERS"):
        if "_1T" in m:
            loc, vis = fila_partido.get("local_corners_1t"), fila_partido.get("visitante_corners_1t")
        elif "_2T" in m:
            loc, vis = fila_partido.get("local_corners_2t"), fila_partido.get("visitante_corners_2t")
        else:
            loc, vis = fila_partido.get("local_corners_total"), fila_partido.get("visitante_corners_total")
    elif m.startswith("DISPAROS_ARCO"):
        loc, vis = fila_partido.get("local_disparos_arco"), fila_partido.get("visitante_disparos_arco")
    elif m.startswith("DISPAROS"):
        loc, vis = fila_partido.get("local_disparos_total"), fila_partido.get("visitante_disparos_total")
    else:
        return None

    if "_LOCAL_" in m:
        return float(loc) if loc is not None else None
    if "_VISITANTE_" in m:
        return float(vis) if vis is not None else None

    if loc is None or vis is None:
        return None
    return float(loc) + float(vis)


def resolver_predicciones_futbol(
    *,
    limite: int = 2000,
    mercado: Optional[str] = None,
    solo_hasta_fecha: Optional[date] = None,
    force: bool = False,
    pool=None,
) -> ResumenResolucionFutbol:
    pool = pool or obtener_pool()
    resumen = ResumenResolucionFutbol()

    condiciones = [] if force else ["(pfu.resuelto = false OR pfu.resuelto IS NULL)"]
    params: List[Any] = []

    if mercado:
        condiciones.append("pfu.mercado::text = %s")
        params.append(mercado.upper())

    if solo_hasta_fecha:
        condiciones.append("pfu.fecha_partido <= %s")
        params.append(solo_hasta_fecha)

    where_sql = " AND ".join(condiciones) if condiciones else "1=1"
    params.append(limite)

    query = f"""
        SELECT
            pfu.id,
            pfu.partido_id,
            pfu.mercado::text,
            pfu.linea,
            pf.estado::text as estado_partido,
            pf.local_goles_1t,
            pf.local_goles_2t,
            pf.local_goles_total,
            pf.visitante_goles_1t,
            pf.visitante_goles_2t,
            pf.visitante_goles_total,
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.local_corners_total,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.visitante_corners_total,
            pf.local_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_total,
            pf.visitante_disparos_arco
        FROM predicciones_futbol pfu
        JOIN partidos_futbol pf ON pfu.partido_id = pf.id
        WHERE {where_sql}
        ORDER BY pfu.fecha_partido ASC
        LIMIT %s
        FOR UPDATE SKIP LOCKED
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            filas = cursor.fetchall()

            if not filas:
                return resumen

            for fila in filas:
                try:
                    (
                        pred_id,
                        _partido_id,
                        mercado_row,
                        linea,
                        estado_partido,
                        local_goles_1t,
                        local_goles_2t,
                        local_goles_total,
                        visitante_goles_1t,
                        visitante_goles_2t,
                        visitante_goles_total,
                        local_corners_1t,
                        local_corners_2t,
                        local_corners_total,
                        visitante_corners_1t,
                        visitante_corners_2t,
                        visitante_corners_total,
                        local_disparos_total,
                        local_disparos_arco,
                        visitante_disparos_total,
                        visitante_disparos_arco,
                    ) = fila

                    if estado_partido != "FINALIZADO":
                        resumen.pendientes += 1
                        continue

                    valor_real = _valor_real_futbol(
                        mercado_row,
                        {
                            "local_goles_1t": local_goles_1t,
                            "local_goles_2t": local_goles_2t,
                            "local_goles_total": local_goles_total,
                            "visitante_goles_1t": visitante_goles_1t,
                            "visitante_goles_2t": visitante_goles_2t,
                            "visitante_goles_total": visitante_goles_total,
                            "local_corners_1t": local_corners_1t,
                            "local_corners_2t": local_corners_2t,
                            "local_corners_total": local_corners_total,
                            "visitante_corners_1t": visitante_corners_1t,
                            "visitante_corners_2t": visitante_corners_2t,
                            "visitante_corners_total": visitante_corners_total,
                            "local_disparos_total": local_disparos_total,
                            "local_disparos_arco": local_disparos_arco,
                            "visitante_disparos_total": visitante_disparos_total,
                            "visitante_disparos_arco": visitante_disparos_arco,
                        },
                    )

                    if valor_real is None:
                        resumen.sin_datos_partido += 1
                        continue

                    if abs(valor_real - float(linea)) < 1e-9:
                        outcome = None
                        resultado = "PUSH"
                        resumen.push += 1
                    elif valor_real > float(linea):
                        outcome = True
                        resultado = "OVER"
                    else:
                        outcome = False
                        resultado = "UNDER"

                    cursor.execute(
                        """
                        UPDATE predicciones_futbol
                        SET valor_real = %s,
                            outcome_binario = %s,
                            resultado = %s,
                            resuelto = true,
                            timestamp_resolucion = NOW(),
                            actualizado_en = NOW()
                        WHERE id = %s
                        """,
                        [valor_real, outcome, resultado, pred_id],
                    )
                    resumen.resueltas += 1
                except Exception as exc:
                    resumen.errores += 1
                    detalle = f"prediccion_id={fila[0]} error={exc}"
                    resumen.detalles_errores.append(detalle)
                    logger.exception("Error resolviendo predicción fútbol")

    return resumen

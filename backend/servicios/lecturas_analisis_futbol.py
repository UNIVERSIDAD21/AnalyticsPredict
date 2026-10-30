"""Lecturas acotadas de contexto de fútbol mediante un cursor recibido.

No abre conexiones/pools, no confirma transacciones ni entrena. El llamador
conserva la transacción de solo lectura y el corte exclusivo. Se mantienen SQL,
parámetros, orden, NULLs y filtros previos exactamente; sin caché nueva.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional



def _obtener_partidos_equipo(
    cursor,
    equipo_id: str,
    fecha_corte: datetime,
    limite: int,
    solo_local: Optional[bool] = None,
    temporada_ids: Optional[List[str]] = None,
    fecha_minima: Optional[datetime] = None,
    competicion_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Obtiene partidos recientes de un equipo (hasta limite)."""
    query = """
        SELECT
            pf.id, pf.valido, pf.estado, pf.hubo_tiempo_extra,
            pf.local_goles_et, pf.visitante_goles_et,
            pf.equipo_local_id,
            pf.equipo_visitante_id,
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
            pf.visitante_disparos_arco,
            pf.temporada_id,
            pf.competicion_id,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
          AND pf.estado = 'FINALIZADO'
          AND pf.fecha_partido < %s
    """
    params: List[Any] = [equipo_id, equipo_id, fecha_corte]

    if competicion_id:
        query += " AND pf.competicion_id::text = %s"
        params.append(str(competicion_id))

    if temporada_ids:
        query += " AND pf.temporada_id::text = ANY(%s)"
        params.append(temporada_ids)
    elif fecha_minima is not None:
        query += " AND pf.fecha_partido >= %s"
        params.append(fecha_minima)

    if solo_local is True:
        query += " AND pf.equipo_local_id = %s"
        params.append(equipo_id)
    elif solo_local is False:
        query += " AND pf.equipo_visitante_id = %s"
        params.append(equipo_id)

    query += " ORDER BY pf.fecha_partido DESC,pf.id DESC LIMIT %s"
    params.append(limite)

    cursor.execute(query, params)
    return cursor.fetchall()

def _obtener_partidos_liga(
    cursor,
    competicion_id: str,
    fecha_corte: datetime,
    limite: int,
    temporada_ids: Optional[List[str]] = None,
    fecha_minima: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Obtiene partidos recientes de una liga (hasta limite)."""
    query = """
        SELECT
            pf.id, pf.valido, pf.estado, pf.hubo_tiempo_extra,
            pf.local_goles_et, pf.visitante_goles_et,
            pf.equipo_local_id,
            pf.equipo_visitante_id,
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
            pf.visitante_disparos_arco,
            pf.temporada_id,
            pf.competicion_id,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE pf.competicion_id = %s
          AND pf.estado = 'FINALIZADO'
          AND pf.fecha_partido < %s
    """
    params: List[Any] = [competicion_id, fecha_corte]
    if temporada_ids:
        query += " AND pf.temporada_id::text = ANY(%s)"
        params.append(temporada_ids)
    elif fecha_minima is not None:
        query += " AND pf.fecha_partido >= %s"
        params.append(fecha_minima)

    query += " ORDER BY pf.fecha_partido DESC,pf.id DESC LIMIT %s"
    params.append(limite)
    cursor.execute(query, params)
    return cursor.fetchall()

def _obtener_partidos_h2h(
    cursor,
    equipo_local_id: str,
    equipo_visitante_id: str,
    fecha_corte: datetime,
    limite: int,
    temporada_ids: Optional[List[str]] = None,
    fecha_minima: Optional[datetime] = None,
    competicion_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Obtiene partidos H2H recientes entre dos equipos."""
    query = """
        SELECT
            pf.id, pf.valido, pf.estado, pf.hubo_tiempo_extra,
            pf.local_goles_et, pf.visitante_goles_et,
            pf.equipo_local_id,
            pf.equipo_visitante_id,
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
            pf.visitante_disparos_arco,
            pf.temporada_id,
            pf.competicion_id,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE pf.estado = 'FINALIZADO'
          AND (
            (pf.equipo_local_id = %s AND pf.equipo_visitante_id = %s)
            OR (pf.equipo_local_id = %s AND pf.equipo_visitante_id = %s)
          )
          AND pf.fecha_partido < %s
    """
    params = [
        equipo_local_id,
        equipo_visitante_id,
        equipo_visitante_id,
        equipo_local_id,
        fecha_corte,
    ]

    if competicion_id:
        query += " AND pf.competicion_id::text = %s"
        params.append(str(competicion_id))

    if temporada_ids:
        query += " AND pf.temporada_id::text = ANY(%s)"
        params.append(temporada_ids)
    elif fecha_minima is not None:
        query += " AND pf.fecha_partido >= %s"
        params.append(fecha_minima)

    query += " ORDER BY pf.fecha_partido DESC,pf.id DESC LIMIT %s"
    params.append(limite)
    cursor.execute(query, params)
    return cursor.fetchall()

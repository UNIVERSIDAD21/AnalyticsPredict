# -*- coding: utf-8 -*-
"""calculador_descanso.py — Cálculo de descanso y back-to-back."""

from __future__ import annotations

from datetime import date
from typing import Optional, Dict, Any

from psycopg.rows import dict_row

from .tipos_contexto import ContextoDescanso


def calcular_descanso(
    pool,
    equipo_id: str,
    fecha_partido: date,
) -> ContextoDescanso:
    """Calcula días de descanso y último partido antes de la fecha indicada."""
    ultimo_partido: Optional[Dict[str, Any]] = None
    dias_descanso = 0

    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    p.fecha_partido,
                    p.equipo_local_id,
                    p.equipo_visitante_id,
                    p.local_total,
                    p.visitante_total
                FROM partidos p
                WHERE p.tipo_partido = 'REG'
                  AND (p.equipo_local_id = %s OR p.equipo_visitante_id = %s)
                  AND p.fecha_partido < %s
                ORDER BY p.fecha_partido DESC
                LIMIT 1
                """,
                [equipo_id, equipo_id, fecha_partido],
            )
            fila = cursor.fetchone()

    if fila:
        fecha_ultimo = fila["fecha_partido"]
        dias_descanso = max((fecha_partido - fecha_ultimo).days - 1, 0)
        es_local = fila["equipo_local_id"] == equipo_id
        puntos_equipo = float(fila["local_total"] if es_local else fila["visitante_total"])
        puntos_rival = float(fila["visitante_total"] if es_local else fila["local_total"])
        ultimo_partido = {
            "fecha": fecha_ultimo.isoformat() if fecha_ultimo else None,
            "puntos_equipo": puntos_equipo,
            "puntos_rival": puntos_rival,
            "ubicacion": "LOCAL" if es_local else "VISITANTE",
        }

    return ContextoDescanso(
        dias_descanso=int(dias_descanso),
        es_back_to_back=dias_descanso == 0 and ultimo_partido is not None,
        ultimo_partido=ultimo_partido,
        distancia_viaje_km=None,
    )

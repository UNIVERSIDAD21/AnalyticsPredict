# -*- coding: utf-8 -*-
"""calculador_h2h.py — Cálculos de enfrentamientos directos."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from psycopg.rows import dict_row

from .tipos_contexto import ContextoH2H


def calcular_h2h(
    pool,
    equipo_id: str,
    rival_id: str,
    limite: int = 10,
    min_partidos: int = 3,
) -> Optional[ContextoH2H]:
    """Calcula métricas head-to-head para los últimos enfrentamientos."""
    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    p.fecha_partido,
                    p.equipo_local_id,
                    p.equipo_visitante_id,
                    p.local_total,
                    p.visitante_total,
                    p.ganador_id,
                    p.diferencia_puntos
                FROM partidos_baloncesto p
                WHERE p.tipo_partido = 'REG'
                  AND p.local_total IS NOT NULL
                  AND p.visitante_total IS NOT NULL
                  AND NOT (p.local_total = 0 AND p.visitante_total = 0)
                  AND (
                        (p.equipo_local_id = %s AND p.equipo_visitante_id = %s)
                        OR (p.equipo_local_id = %s AND p.equipo_visitante_id = %s)
                  )
                ORDER BY p.fecha_partido DESC
                LIMIT %s
                """,
                [equipo_id, rival_id, rival_id, equipo_id, limite],
            )
            filas = cursor.fetchall()

    total_partidos = len(filas)
    if total_partidos < min_partidos:
        return None

    victorias_equipo = 0
    victorias_rival = 0
    total_sum = 0.0
    total_equipo = 0.0
    total_rival = 0.0

    partidos: List[Dict[str, Any]] = []
    for fila in filas:
        equipo_es_local = fila["equipo_local_id"] == equipo_id
        puntos_equipo = float(fila["local_total"] if equipo_es_local else fila["visitante_total"])
        puntos_rival = float(fila["visitante_total"] if equipo_es_local else fila["local_total"])
        total = puntos_equipo + puntos_rival
        total_sum += total
        total_equipo += puntos_equipo
        total_rival += puntos_rival

        ganador_id = fila.get("ganador_id")
        if ganador_id == equipo_id:
            victorias_equipo += 1
        elif ganador_id == rival_id:
            victorias_rival += 1

        partidos.append(
            {
                "fecha": fila["fecha_partido"].isoformat() if fila["fecha_partido"] else None,
                "puntos_equipo": puntos_equipo,
                "puntos_rival": puntos_rival,
                "total": total,
                "ganador_id": ganador_id,
                "diferencia_puntos": fila.get("diferencia_puntos"),
            }
        )

    promedio_total = total_sum / total_partidos
    promedio_equipo = total_equipo / total_partidos
    promedio_rival = total_rival / total_partidos
    tendencia_over = sum(1 for partido in partidos if partido["total"] > promedio_total) / total_partidos

    ultimo = partidos[0] if partidos else None

    return ContextoH2H(
        total_partidos=total_partidos,
        victorias_equipo=victorias_equipo,
        victorias_rival=victorias_rival,
        promedio_total=round(promedio_total, 2),
        promedio_equipo=round(promedio_equipo, 2),
        promedio_rival=round(promedio_rival, 2),
        tendencia_over=round(tendencia_over, 3),
        ultimo_enfrentamiento=ultimo,
        partidos=partidos,
    )


# -*- coding: utf-8 -*-
"""calculador_forma.py — Cálculo de forma reciente por equipo."""

from __future__ import annotations

from typing import List

from psycopg.rows import dict_row

from .tipos_contexto import ContextoForma


def _construir_racha(resultados: List[bool], max_segmentos: int = 5) -> str:
    if not resultados:
        return ""
    segmentos: List[str] = []
    actual = resultados[0]
    contador = 0
    for res in resultados:
        if res == actual:
            contador += 1
        else:
            segmentos.append(f"{'W' if actual else 'L'}{contador}")
            actual = res
            contador = 1
        if len(segmentos) >= max_segmentos:
            break
    if len(segmentos) < max_segmentos:
        segmentos.append(f"{'W' if actual else 'L'}{contador}")
    return "".join(segmentos)


def calcular_forma_reciente(
    pool,
    equipo_id: str,
    ultimos_n: int = 10,
    ppg_temporada: float = 0.0,
) -> ContextoForma:
    """Calcula la forma reciente de un equipo basado en últimos N partidos."""
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
                    p.ganador_id
                FROM partidos p
                WHERE p.tipo_partido = 'REG'
                  AND (p.equipo_local_id = %s OR p.equipo_visitante_id = %s)
                ORDER BY p.fecha_partido DESC
                LIMIT %s
                """,
                [equipo_id, equipo_id, ultimos_n],
            )
            filas = cursor.fetchall()

    puntos_a_favor = 0.0
    puntos_en_contra = 0.0
    victorias = 0
    derrotas = 0
    resultados: List[bool] = []

    for fila in filas:
        es_local = fila["equipo_local_id"] == equipo_id
        puntos_equipo = float(fila["local_total"] if es_local else fila["visitante_total"])
        puntos_rival = float(fila["visitante_total"] if es_local else fila["local_total"])
        puntos_a_favor += puntos_equipo
        puntos_en_contra += puntos_rival
        gano = fila.get("ganador_id") == equipo_id
        resultados.append(gano)
        if gano:
            victorias += 1
        else:
            derrotas += 1

    total_juegos = max(len(filas), 1)
    ppg = puntos_a_favor / total_juegos
    opp_ppg = puntos_en_contra / total_juegos
    diferencia = ppg - (ppg_temporada or 0.0)

    if diferencia > 1.0:
        tendencia = "MEJORANDO"
    elif diferencia < -1.0:
        tendencia = "EMPEORANDO"
    else:
        tendencia = "ESTABLE"

    return ContextoForma(
        ultimos_n=len(filas),
        victorias=victorias,
        derrotas=derrotas,
        racha=_construir_racha(resultados),
        ppg=round(ppg, 2),
        opp_ppg=round(opp_ppg, 2),
        net_rating=round(ppg - opp_ppg, 2),
        ppg_temporada=round(ppg_temporada or 0.0, 2),
        diferencia_vs_temporada=round(diferencia, 2),
        tendencia=tendencia,
    )

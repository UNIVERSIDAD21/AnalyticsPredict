# -*- coding: utf-8 -*-
"""
calculadores.py — Funciones de cálculo de estadísticas.

Este módulo contiene funciones auxiliares para calcular estadísticas
específicas usadas en la generación de features.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

import numpy as np


def calcular_estadisticas_temporada(
    conn,
    equipo_id: UUID,
    temporada_id: UUID,
    fecha_corte: datetime,
) -> Dict[str, float]:
    """
    Calcula estadísticas de temporada para un equipo.

    IMPORTANTE: Solo considera partidos ANTERIORES a fecha_corte.

    Args:
        conn: Conexión a la base de datos
        equipo_id: ID del equipo
        temporada_id: ID de la temporada
        fecha_corte: Fecha límite para datos históricos

    Returns:
        Dict con estadísticas promediadas
    """
    query = """
        SELECT
            COUNT(*) as partidos_jugados,
            AVG(CASE
                WHEN equipo_local_id = %s THEN local_goles_total
                ELSE visitante_goles_total
            END) as goles_favor,
            AVG(CASE
                WHEN equipo_local_id = %s THEN visitante_goles_total
                ELSE local_goles_total
            END) as goles_contra,
            AVG(CASE
                WHEN equipo_local_id = %s THEN local_corners_total
                ELSE visitante_corners_total
            END) as corners_favor,
            AVG(CASE
                WHEN equipo_local_id = %s THEN visitante_corners_total
                ELSE local_corners_total
            END) as corners_contra,
            AVG(CASE
                WHEN equipo_local_id = %s THEN local_posesion
                ELSE visitante_posesion
            END) as posesion
        FROM partidos_futbol
        WHERE (equipo_local_id = %s OR equipo_visitante_id = %s)
          AND temporada_id = %s
          AND estado = 'FINALIZADO'
          AND fecha_partido < %s
    """

    equipo_str = str(equipo_id)
    parametros = [equipo_str] * 7 + [str(temporada_id), fecha_corte]

    with conn.cursor() as cursor:
        cursor.execute(query, parametros)
        fila = cursor.fetchone()

        if not fila or fila[0] == 0:
            return {}

        columnas = [desc[0] for desc in cursor.description]
        resultado = {}
        for i, col in enumerate(columnas):
            valor = fila[i]
            if valor is not None:
                resultado[col] = float(valor) if col != "partidos_jugados" else int(valor)

        return resultado


def calcular_estadisticas_ubicacion(
    conn,
    equipo_id: UUID,
    temporada_id: UUID,
    fecha_corte: datetime,
    es_local: bool,
) -> Dict[str, float]:
    """
    Calcula estadísticas cuando el equipo juega como local o visitante.

    Args:
        conn: Conexión a la base de datos
        equipo_id: ID del equipo
        temporada_id: ID de la temporada
        fecha_corte: Fecha límite
        es_local: True para estadísticas como local, False como visitante

    Returns:
        Dict con estadísticas
    """
    if es_local:
        query = """
            SELECT
                COUNT(*) as partidos_jugados,
                AVG(local_goles_total) as goles_favor,
                AVG(visitante_goles_total) as goles_contra,
                AVG(local_corners_total) as corners_favor,
                AVG(visitante_corners_total) as corners_contra,
                AVG(local_posesion) as posesion
            FROM partidos_futbol
            WHERE equipo_local_id = %s
              AND temporada_id = %s
              AND estado = 'FINALIZADO'
              AND fecha_partido < %s
        """
    else:
        query = """
            SELECT
                COUNT(*) as partidos_jugados,
                AVG(visitante_goles_total) as goles_favor,
                AVG(local_goles_total) as goles_contra,
                AVG(visitante_corners_total) as corners_favor,
                AVG(local_corners_total) as corners_contra,
                AVG(visitante_posesion) as posesion
            FROM partidos_futbol
            WHERE equipo_visitante_id = %s
              AND temporada_id = %s
              AND estado = 'FINALIZADO'
              AND fecha_partido < %s
        """

    parametros = [str(equipo_id), str(temporada_id), fecha_corte]

    with conn.cursor() as cursor:
        cursor.execute(query, parametros)
        fila = cursor.fetchone()

        if not fila or fila[0] == 0:
            return {}

        columnas = [desc[0] for desc in cursor.description]
        resultado = {}
        for i, col in enumerate(columnas):
            valor = fila[i]
            if valor is not None:
                resultado[col] = float(valor) if col != "partidos_jugados" else int(valor)

        return resultado


def calcular_forma_reciente(
    conn,
    equipo_id: UUID,
    fecha_corte: datetime,
    n_partidos: int = 5,
) -> Dict[str, float]:
    """
    Calcula estadísticas de los últimos N partidos.

    Args:
        conn: Conexión a la base de datos
        equipo_id: ID del equipo
        fecha_corte: Fecha límite
        n_partidos: Número de partidos a considerar

    Returns:
        Dict con promedios de forma reciente
    """
    query = """
        SELECT
            CASE
                WHEN equipo_local_id = %s THEN local_goles_total
                ELSE visitante_goles_total
            END as goles,
            CASE
                WHEN equipo_local_id = %s THEN local_corners_total
                ELSE visitante_corners_total
            END as corners,
            CASE
                WHEN equipo_local_id = %s THEN local_disparos_total
                ELSE visitante_disparos_total
            END as disparos
        FROM partidos_futbol
        WHERE (equipo_local_id = %s OR equipo_visitante_id = %s)
          AND estado = 'FINALIZADO'
          AND fecha_partido < %s
        ORDER BY fecha_partido DESC
        LIMIT %s
    """

    equipo_str = str(equipo_id)
    parametros = [equipo_str] * 5 + [fecha_corte, n_partidos]

    with conn.cursor() as cursor:
        cursor.execute(query, parametros)
        filas = cursor.fetchall()

        if not filas:
            return {}

        goles = [f[0] for f in filas if f[0] is not None]
        corners = [f[1] for f in filas if f[1] is not None]
        disparos = [f[2] for f in filas if f[2] is not None]

        resultado = {}

        if goles:
            resultado["goles_promedio"] = sum(goles) / len(goles)
        if corners:
            resultado["corners_promedio"] = sum(corners) / len(corners)
            resultado["tendencia_corners"] = calcular_tendencia(corners)
        if disparos:
            resultado["disparos_promedio"] = sum(disparos) / len(disparos)

        return resultado


def calcular_tendencia(valores: List[float]) -> float:
    """
    Calcula la pendiente de regresión lineal de una serie de valores.

    Una pendiente positiva indica tendencia al alza.
    Una pendiente negativa indica tendencia a la baja.

    Args:
        valores: Lista de valores ordenados cronológicamente (más reciente primero)

    Returns:
        Pendiente de la regresión lineal
    """
    if not valores or len(valores) < 2:
        return 0.0

    # Invertir para que esté en orden cronológico (más antiguo primero)
    valores_cronologicos = list(reversed(valores))

    n = len(valores_cronologicos)
    x = np.arange(n, dtype=float)
    y = np.array(valores_cronologicos, dtype=float)

    # Calcular pendiente con mínimos cuadrados
    x_mean = x.mean()
    y_mean = y.mean()

    numerador = np.sum((x - x_mean) * (y - y_mean))
    denominador = np.sum((x - x_mean) ** 2)

    if denominador == 0:
        return 0.0

    pendiente = numerador / denominador
    return float(pendiente)


def calcular_head_to_head(
    conn,
    equipo_id: UUID,
    rival_id: UUID,
    fecha_corte: datetime,
    n_partidos: int = 5,
) -> Dict[str, float]:
    """
    Calcula estadísticas de enfrentamientos directos.

    Args:
        conn: Conexión a la base de datos
        equipo_id: ID del equipo
        rival_id: ID del rival
        fecha_corte: Fecha límite
        n_partidos: Número de enfrentamientos a considerar

    Returns:
        Dict con estadísticas de H2H
    """
    query = """
        SELECT
            CASE WHEN equipo_local_id = %s THEN local_corners_total + visitante_corners_total
                 ELSE local_corners_total + visitante_corners_total
            END as corners_total,
            CASE WHEN equipo_local_id = %s THEN local_goles_total + visitante_goles_total
                 ELSE local_goles_total + visitante_goles_total
            END as goles_total,
            CASE WHEN equipo_local_id = %s THEN local_goles_total - visitante_goles_total
                 ELSE visitante_goles_total - local_goles_total
            END as diferencia_goles
        FROM partidos_futbol
        WHERE ((equipo_local_id = %s AND equipo_visitante_id = %s)
            OR (equipo_local_id = %s AND equipo_visitante_id = %s))
          AND estado = 'FINALIZADO'
          AND fecha_partido < %s
        ORDER BY fecha_partido DESC
        LIMIT %s
    """

    equipo_str = str(equipo_id)
    rival_str = str(rival_id)
    parametros = [equipo_str] * 3 + [equipo_str, rival_str, rival_str, equipo_str, fecha_corte, n_partidos]

    with conn.cursor() as cursor:
        cursor.execute(query, parametros)
        filas = cursor.fetchall()

        if not filas or len(filas) < 3:  # Mínimo 3 enfrentamientos
            return {}

        corners = [f[0] for f in filas if f[0] is not None]
        goles = [f[1] for f in filas if f[1] is not None]
        diferencias = [f[2] for f in filas if f[2] is not None]

        resultado = {}

        if corners:
            resultado["corners_h2h"] = sum(corners) / len(corners)
        if goles:
            resultado["goles_h2h"] = sum(goles) / len(goles)
        if diferencias:
            resultado["ventaja_h2h"] = sum(diferencias) / len(diferencias)

        return resultado


def valor_o_default(
    valor: Optional[float],
    default: float,
) -> float:
    """
    Retorna el valor si no es None, sino el default.

    Args:
        valor: Valor a verificar
        default: Valor por defecto

    Returns:
        El valor original o el default
    """
    return valor if valor is not None else default

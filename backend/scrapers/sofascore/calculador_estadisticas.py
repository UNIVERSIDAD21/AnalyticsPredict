# -*- coding: utf-8 -*-
"""
Calculador de estadísticas agregadas por equipo.

Este módulo implementa el cálculo de estadísticas agregadas para la
tabla estadisticas_equipos_futbol, incluyendo promedios de goles,
corners, disparos y xG como local y visitante.

Funciones principales:
- calcular_estadisticas_equipo: Calcula estadísticas de un equipo
- actualizar_estadisticas_equipo: Actualiza/inserta en BD
- actualizar_estadisticas_todos_equipos: Procesa todos los equipos

Ejemplo de uso:
    from scrapers.sofascore.calculador_estadisticas import (
        actualizar_estadisticas_todos_equipos
    )

    with obtener_pool().connection() as conn:
        resultado = actualizar_estadisticas_todos_equipos(
            conn, competicion_id=1, temporada_id=5
        )
        print(f"Equipos actualizados: {resultado['actualizados']}")
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .excepciones import ErrorBaseDatos

# Configuración del logger
logger = logging.getLogger(__name__)


def calcular_estadisticas_equipo(
    conexion,
    equipo_id: int,
    competicion_id: int,
    temporada_id: int
) -> Optional[Dict[str, Any]]:
    """
    Calcula estadísticas agregadas de un equipo para una competición/temporada.

    Ejecuta consultas para calcular promedios y totales de:
    - Goles a favor y en contra (por tiempo y totales)
    - Corners a favor y en contra (por tiempo y totales)
    - Disparos realizados y recibidos
    - Posesión promedio
    - xG promedio
    - Victorias, empates y derrotas (como local y visitante)
    - Porcentajes de Over (goles, corners, disparos)

    Args:
        conexion: Conexión a la base de datos.
        equipo_id: ID del equipo en la BD.
        competicion_id: ID de la competición.
        temporada_id: ID de la temporada.

    Returns:
        Diccionario con todas las estadísticas calculadas, o None si
        no hay partidos del equipo.

    Ejemplo:
        stats = calcular_estadisticas_equipo(conn, 15, 1, 5)
        if stats:
            print(f"Goles por partido: {stats['goles_favor_total_promedio']:.2f}")
    """
    try:
        with conexion.cursor() as cursor:
            # Estadísticas como LOCAL
            cursor.execute(
                """
                SELECT
                    COUNT(*) as partidos_local,
                    SUM(CASE WHEN ganador_id = equipo_local_id THEN 1 ELSE 0 END) as victorias_local,
                    SUM(CASE WHEN ganador_id IS NULL AND estado = 'finished' THEN 1 ELSE 0 END) as empates_local,
                    SUM(CASE WHEN ganador_id = equipo_visitante_id THEN 1 ELSE 0 END) as derrotas_local,

                    -- Goles
                    COALESCE(AVG(local_goles_1t), 0) as goles_favor_1t_local,
                    COALESCE(AVG(local_goles_2t), 0) as goles_favor_2t_local,
                    COALESCE(AVG(local_goles_total), 0) as goles_favor_total_local,
                    COALESCE(AVG(visitante_goles_1t), 0) as goles_contra_1t_local,
                    COALESCE(AVG(visitante_goles_2t), 0) as goles_contra_2t_local,
                    COALESCE(AVG(visitante_goles_total), 0) as goles_contra_total_local,

                    -- Corners (como local, corners_local son a favor)
                    COALESCE(AVG(corners_local_1t), 0) as corners_favor_1t_local,
                    COALESCE(AVG(corners_local_2t), 0) as corners_favor_2t_local,
                    COALESCE(AVG(corners_local_total), 0) as corners_favor_total_local,
                    COALESCE(AVG(corners_visitante_1t), 0) as corners_contra_1t_local,
                    COALESCE(AVG(corners_visitante_2t), 0) as corners_contra_2t_local,
                    COALESCE(AVG(corners_visitante_total), 0) as corners_contra_total_local,

                    -- Disparos
                    COALESCE(AVG(disparos_local_total), 0) as disparos_favor_local,
                    COALESCE(AVG(disparos_local_arco), 0) as disparos_arco_favor_local,
                    COALESCE(AVG(disparos_visitante_total), 0) as disparos_contra_local,
                    COALESCE(AVG(disparos_visitante_arco), 0) as disparos_arco_contra_local,

                    -- Posesión y xG
                    COALESCE(AVG(posesion_local), 0) as posesion_local,
                    COALESCE(AVG(xg_local), 0) as xg_favor_local,
                    COALESCE(AVG(xg_visitante), 0) as xg_contra_local,

                    -- Over/Under (como local)
                    COALESCE(AVG(CASE WHEN local_goles_total + visitante_goles_total > 2.5 THEN 1 ELSE 0 END), 0) as over_25_goles_local,
                    COALESCE(AVG(CASE WHEN COALESCE(corners_local_total, 0) + COALESCE(corners_visitante_total, 0) > 8.5 THEN 1 ELSE 0 END), 0) as over_85_corners_local

                FROM partidos_futbol
                WHERE equipo_local_id = %s
                  AND competicion_id = %s
                  AND temporada_id = %s
                  AND estado = 'finished'
                """,
                (equipo_id, competicion_id, temporada_id)
            )
            stats_local = cursor.fetchone()

            # Estadísticas como VISITANTE
            cursor.execute(
                """
                SELECT
                    COUNT(*) as partidos_visitante,
                    SUM(CASE WHEN ganador_id = equipo_visitante_id THEN 1 ELSE 0 END) as victorias_visitante,
                    SUM(CASE WHEN ganador_id IS NULL AND estado = 'finished' THEN 1 ELSE 0 END) as empates_visitante,
                    SUM(CASE WHEN ganador_id = equipo_local_id THEN 1 ELSE 0 END) as derrotas_visitante,

                    -- Goles (como visitante, visitante_goles son a favor)
                    COALESCE(AVG(visitante_goles_1t), 0) as goles_favor_1t_visitante,
                    COALESCE(AVG(visitante_goles_2t), 0) as goles_favor_2t_visitante,
                    COALESCE(AVG(visitante_goles_total), 0) as goles_favor_total_visitante,
                    COALESCE(AVG(local_goles_1t), 0) as goles_contra_1t_visitante,
                    COALESCE(AVG(local_goles_2t), 0) as goles_contra_2t_visitante,
                    COALESCE(AVG(local_goles_total), 0) as goles_contra_total_visitante,

                    -- Corners (como visitante, corners_visitante son a favor)
                    COALESCE(AVG(corners_visitante_1t), 0) as corners_favor_1t_visitante,
                    COALESCE(AVG(corners_visitante_2t), 0) as corners_favor_2t_visitante,
                    COALESCE(AVG(corners_visitante_total), 0) as corners_favor_total_visitante,
                    COALESCE(AVG(corners_local_1t), 0) as corners_contra_1t_visitante,
                    COALESCE(AVG(corners_local_2t), 0) as corners_contra_2t_visitante,
                    COALESCE(AVG(corners_local_total), 0) as corners_contra_total_visitante,

                    -- Disparos
                    COALESCE(AVG(disparos_visitante_total), 0) as disparos_favor_visitante,
                    COALESCE(AVG(disparos_visitante_arco), 0) as disparos_arco_favor_visitante,
                    COALESCE(AVG(disparos_local_total), 0) as disparos_contra_visitante,
                    COALESCE(AVG(disparos_local_arco), 0) as disparos_arco_contra_visitante,

                    -- Posesión y xG
                    COALESCE(AVG(posesion_visitante), 0) as posesion_visitante,
                    COALESCE(AVG(xg_visitante), 0) as xg_favor_visitante,
                    COALESCE(AVG(xg_local), 0) as xg_contra_visitante,

                    -- Over/Under (como visitante)
                    COALESCE(AVG(CASE WHEN local_goles_total + visitante_goles_total > 2.5 THEN 1 ELSE 0 END), 0) as over_25_goles_visitante,
                    COALESCE(AVG(CASE WHEN COALESCE(corners_local_total, 0) + COALESCE(corners_visitante_total, 0) > 8.5 THEN 1 ELSE 0 END), 0) as over_85_corners_visitante

                FROM partidos_futbol
                WHERE equipo_visitante_id = %s
                  AND competicion_id = %s
                  AND temporada_id = %s
                  AND estado = 'finished'
                """,
                (equipo_id, competicion_id, temporada_id)
            )
            stats_visitante = cursor.fetchone()

        # Verificar si hay datos
        partidos_local = stats_local[0] if stats_local else 0
        partidos_visitante = stats_visitante[0] if stats_visitante else 0
        partidos_totales = partidos_local + partidos_visitante

        if partidos_totales == 0:
            logger.debug(f"No hay partidos para equipo {equipo_id} en la competición/temporada")
            return None

        # Combinar estadísticas
        resultado = _combinar_estadisticas(
            stats_local, stats_visitante,
            partidos_local, partidos_visitante
        )

        resultado['equipo_id'] = equipo_id
        resultado['competicion_id'] = competicion_id
        resultado['temporada_id'] = temporada_id
        resultado['partidos_jugados'] = partidos_totales
        resultado['partidos_local'] = partidos_local
        resultado['partidos_visitante'] = partidos_visitante

        return resultado

    except Exception as e:
        logger.error(f"Error calculando estadísticas de equipo {equipo_id}: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error calculando estadísticas de equipo {equipo_id}",
            operacion="SELECT",
            tabla="partidos_futbol",
            excepcion_original=e
        )


def _combinar_estadisticas(
    stats_local: tuple,
    stats_visitante: tuple,
    partidos_local: int,
    partidos_visitante: int
) -> Dict[str, Any]:
    """
    Combina estadísticas de local y visitante en totales.

    Calcula promedios ponderados por número de partidos.
    """
    total = partidos_local + partidos_visitante

    def promedio_ponderado(val_local: float, val_visitante: float) -> float:
        if total == 0:
            return 0.0
        return (val_local * partidos_local + val_visitante * partidos_visitante) / total

    # Índices de stats_local (después del count):
    # 1: victorias_local, 2: empates_local, 3: derrotas_local
    # 4: goles_favor_1t, 5: goles_favor_2t, 6: goles_favor_total
    # 7: goles_contra_1t, 8: goles_contra_2t, 9: goles_contra_total
    # 10: corners_favor_1t, 11: corners_favor_2t, 12: corners_favor_total
    # 13: corners_contra_1t, 14: corners_contra_2t, 15: corners_contra_total
    # 16: disparos_favor, 17: disparos_arco_favor, 18: disparos_contra, 19: disparos_arco_contra
    # 20: posesion, 21: xg_favor, 22: xg_contra
    # 23: over_25_goles, 24: over_85_corners

    def safe_float(val) -> float:
        return float(val) if val is not None else 0.0

    return {
        # Victorias, empates, derrotas
        'victorias': int(stats_local[1] or 0) + int(stats_visitante[1] or 0),
        'empates': int(stats_local[2] or 0) + int(stats_visitante[2] or 0),
        'derrotas': int(stats_local[3] or 0) + int(stats_visitante[3] or 0),
        'victorias_local': int(stats_local[1] or 0),
        'empates_local': int(stats_local[2] or 0),
        'derrotas_local': int(stats_local[3] or 0),
        'victorias_visitante': int(stats_visitante[1] or 0),
        'empates_visitante': int(stats_visitante[2] or 0),
        'derrotas_visitante': int(stats_visitante[3] or 0),

        # Goles - Local
        'goles_favor_1t_local': safe_float(stats_local[4]),
        'goles_favor_2t_local': safe_float(stats_local[5]),
        'goles_favor_total_local': safe_float(stats_local[6]),
        'goles_contra_1t_local': safe_float(stats_local[7]),
        'goles_contra_2t_local': safe_float(stats_local[8]),
        'goles_contra_total_local': safe_float(stats_local[9]),

        # Goles - Visitante
        'goles_favor_1t_visitante': safe_float(stats_visitante[4]),
        'goles_favor_2t_visitante': safe_float(stats_visitante[5]),
        'goles_favor_total_visitante': safe_float(stats_visitante[6]),
        'goles_contra_1t_visitante': safe_float(stats_visitante[7]),
        'goles_contra_2t_visitante': safe_float(stats_visitante[8]),
        'goles_contra_total_visitante': safe_float(stats_visitante[9]),

        # Goles - Totales (promedio ponderado)
        'goles_favor_1t_promedio': promedio_ponderado(
            safe_float(stats_local[4]), safe_float(stats_visitante[4])
        ),
        'goles_favor_2t_promedio': promedio_ponderado(
            safe_float(stats_local[5]), safe_float(stats_visitante[5])
        ),
        'goles_favor_total_promedio': promedio_ponderado(
            safe_float(stats_local[6]), safe_float(stats_visitante[6])
        ),
        'goles_contra_1t_promedio': promedio_ponderado(
            safe_float(stats_local[7]), safe_float(stats_visitante[7])
        ),
        'goles_contra_2t_promedio': promedio_ponderado(
            safe_float(stats_local[8]), safe_float(stats_visitante[8])
        ),
        'goles_contra_total_promedio': promedio_ponderado(
            safe_float(stats_local[9]), safe_float(stats_visitante[9])
        ),

        # Corners - Local
        'corners_favor_1t_local': safe_float(stats_local[10]),
        'corners_favor_2t_local': safe_float(stats_local[11]),
        'corners_favor_total_local': safe_float(stats_local[12]),
        'corners_contra_1t_local': safe_float(stats_local[13]),
        'corners_contra_2t_local': safe_float(stats_local[14]),
        'corners_contra_total_local': safe_float(stats_local[15]),

        # Corners - Visitante
        'corners_favor_1t_visitante': safe_float(stats_visitante[10]),
        'corners_favor_2t_visitante': safe_float(stats_visitante[11]),
        'corners_favor_total_visitante': safe_float(stats_visitante[12]),
        'corners_contra_1t_visitante': safe_float(stats_visitante[13]),
        'corners_contra_2t_visitante': safe_float(stats_visitante[14]),
        'corners_contra_total_visitante': safe_float(stats_visitante[15]),

        # Corners - Totales
        'corners_favor_total_promedio': promedio_ponderado(
            safe_float(stats_local[12]), safe_float(stats_visitante[12])
        ),
        'corners_contra_total_promedio': promedio_ponderado(
            safe_float(stats_local[15]), safe_float(stats_visitante[15])
        ),

        # Disparos - Local
        'disparos_favor_local': safe_float(stats_local[16]),
        'disparos_arco_favor_local': safe_float(stats_local[17]),
        'disparos_contra_local': safe_float(stats_local[18]),
        'disparos_arco_contra_local': safe_float(stats_local[19]),

        # Disparos - Visitante
        'disparos_favor_visitante': safe_float(stats_visitante[16]),
        'disparos_arco_favor_visitante': safe_float(stats_visitante[17]),
        'disparos_contra_visitante': safe_float(stats_visitante[18]),
        'disparos_arco_contra_visitante': safe_float(stats_visitante[19]),

        # Disparos - Totales
        'disparos_favor_promedio': promedio_ponderado(
            safe_float(stats_local[16]), safe_float(stats_visitante[16])
        ),
        'disparos_arco_favor_promedio': promedio_ponderado(
            safe_float(stats_local[17]), safe_float(stats_visitante[17])
        ),

        # Posesión
        'posesion_local': safe_float(stats_local[20]),
        'posesion_visitante': safe_float(stats_visitante[20]),
        'posesion_promedio': promedio_ponderado(
            safe_float(stats_local[20]), safe_float(stats_visitante[20])
        ),

        # xG
        'xg_favor_local': safe_float(stats_local[21]),
        'xg_contra_local': safe_float(stats_local[22]),
        'xg_favor_visitante': safe_float(stats_visitante[21]),
        'xg_contra_visitante': safe_float(stats_visitante[22]),
        'xg_favor_promedio': promedio_ponderado(
            safe_float(stats_local[21]), safe_float(stats_visitante[21])
        ),
        'xg_contra_promedio': promedio_ponderado(
            safe_float(stats_local[22]), safe_float(stats_visitante[22])
        ),

        # Over/Under
        'over_25_goles_local': safe_float(stats_local[23]) * 100,  # Porcentaje
        'over_25_goles_visitante': safe_float(stats_visitante[23]) * 100,
        'over_25_goles_total': promedio_ponderado(
            safe_float(stats_local[23]), safe_float(stats_visitante[23])
        ) * 100,
        'over_85_corners_local': safe_float(stats_local[24]) * 100,
        'over_85_corners_visitante': safe_float(stats_visitante[24]) * 100,
        'over_85_corners_total': promedio_ponderado(
            safe_float(stats_local[24]), safe_float(stats_visitante[24])
        ) * 100,
    }


def actualizar_estadisticas_equipo(
    conexion,
    equipo_id: int,
    competicion_id: int,
    temporada_id: int
) -> bool:
    """
    Calcula y guarda estadísticas de un equipo en la base de datos.

    Hace upsert en la tabla estadisticas_equipos_futbol.

    Args:
        conexion: Conexión a la base de datos.
        equipo_id: ID del equipo.
        competicion_id: ID de la competición.
        temporada_id: ID de la temporada.

    Returns:
        True si se guardaron las estadísticas, False si no hay datos.
    """
    # Calcular estadísticas
    stats = calcular_estadisticas_equipo(
        conexion, equipo_id, competicion_id, temporada_id
    )

    if stats is None:
        return False

    try:
        with conexion.cursor() as cursor:
            # Upsert de estadísticas
            cursor.execute(
                """
                INSERT INTO estadisticas_equipos_futbol (
                    equipo_id, competicion_id, temporada_id,
                    partidos_jugados, partidos_local, partidos_visitante,
                    victorias, empates, derrotas,
                    victorias_local, empates_local, derrotas_local,
                    victorias_visitante, empates_visitante, derrotas_visitante,
                    goles_favor_promedio, goles_contra_promedio,
                    goles_favor_local, goles_contra_local,
                    goles_favor_visitante, goles_contra_visitante,
                    corners_favor_promedio, corners_contra_promedio,
                    corners_favor_local, corners_contra_local,
                    corners_favor_visitante, corners_contra_visitante,
                    disparos_favor_promedio, disparos_arco_favor_promedio,
                    posesion_promedio,
                    xg_favor_promedio, xg_contra_promedio,
                    over_25_goles_porcentaje, over_85_corners_porcentaje,
                    ultima_actualizacion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, NOW()
                )
                ON CONFLICT (equipo_id, competicion_id, temporada_id)
                DO UPDATE SET
                    partidos_jugados = EXCLUDED.partidos_jugados,
                    partidos_local = EXCLUDED.partidos_local,
                    partidos_visitante = EXCLUDED.partidos_visitante,
                    victorias = EXCLUDED.victorias,
                    empates = EXCLUDED.empates,
                    derrotas = EXCLUDED.derrotas,
                    victorias_local = EXCLUDED.victorias_local,
                    empates_local = EXCLUDED.empates_local,
                    derrotas_local = EXCLUDED.derrotas_local,
                    victorias_visitante = EXCLUDED.victorias_visitante,
                    empates_visitante = EXCLUDED.empates_visitante,
                    derrotas_visitante = EXCLUDED.derrotas_visitante,
                    goles_favor_promedio = EXCLUDED.goles_favor_promedio,
                    goles_contra_promedio = EXCLUDED.goles_contra_promedio,
                    goles_favor_local = EXCLUDED.goles_favor_local,
                    goles_contra_local = EXCLUDED.goles_contra_local,
                    goles_favor_visitante = EXCLUDED.goles_favor_visitante,
                    goles_contra_visitante = EXCLUDED.goles_contra_visitante,
                    corners_favor_promedio = EXCLUDED.corners_favor_promedio,
                    corners_contra_promedio = EXCLUDED.corners_contra_promedio,
                    corners_favor_local = EXCLUDED.corners_favor_local,
                    corners_contra_local = EXCLUDED.corners_contra_local,
                    corners_favor_visitante = EXCLUDED.corners_favor_visitante,
                    corners_contra_visitante = EXCLUDED.corners_contra_visitante,
                    disparos_favor_promedio = EXCLUDED.disparos_favor_promedio,
                    disparos_arco_favor_promedio = EXCLUDED.disparos_arco_favor_promedio,
                    posesion_promedio = EXCLUDED.posesion_promedio,
                    xg_favor_promedio = EXCLUDED.xg_favor_promedio,
                    xg_contra_promedio = EXCLUDED.xg_contra_promedio,
                    over_25_goles_porcentaje = EXCLUDED.over_25_goles_porcentaje,
                    over_85_corners_porcentaje = EXCLUDED.over_85_corners_porcentaje,
                    ultima_actualizacion = NOW()
                """,
                (
                    equipo_id, competicion_id, temporada_id,
                    stats['partidos_jugados'],
                    stats['partidos_local'],
                    stats['partidos_visitante'],
                    stats['victorias'],
                    stats['empates'],
                    stats['derrotas'],
                    stats['victorias_local'],
                    stats['empates_local'],
                    stats['derrotas_local'],
                    stats['victorias_visitante'],
                    stats['empates_visitante'],
                    stats['derrotas_visitante'],
                    stats['goles_favor_total_promedio'],
                    stats['goles_contra_total_promedio'],
                    stats['goles_favor_total_local'],
                    stats['goles_contra_total_local'],
                    stats['goles_favor_total_visitante'],
                    stats['goles_contra_total_visitante'],
                    stats['corners_favor_total_promedio'],
                    stats['corners_contra_total_promedio'],
                    stats['corners_favor_total_local'],
                    stats['corners_contra_total_local'],
                    stats['corners_favor_total_visitante'],
                    stats['corners_contra_total_visitante'],
                    stats['disparos_favor_promedio'],
                    stats['disparos_arco_favor_promedio'],
                    stats['posesion_promedio'],
                    stats['xg_favor_promedio'],
                    stats['xg_contra_promedio'],
                    stats['over_25_goles_total'],
                    stats['over_85_corners_total'],
                )
            )

            conexion.commit()
            logger.debug(f"Estadísticas actualizadas para equipo {equipo_id}")
            return True

    except Exception as e:
        conexion.rollback()
        logger.error(f"Error guardando estadísticas de equipo {equipo_id}: {e}")
        raise ErrorBaseDatos(
            mensaje=f"Error guardando estadísticas de equipo {equipo_id}",
            operacion="UPSERT",
            tabla="estadisticas_equipos_futbol",
            excepcion_original=e
        )


def actualizar_estadisticas_todos_equipos(
    conexion,
    competicion_id: int,
    temporada_id: int,
    callback_progreso=None
) -> Dict[str, Any]:
    """
    Actualiza estadísticas de todos los equipos de una competición/temporada.

    Obtiene la lista de equipos con partidos y calcula estadísticas
    para cada uno.

    Args:
        conexion: Conexión a la base de datos.
        competicion_id: ID de la competición.
        temporada_id: ID de la temporada.
        callback_progreso: Función opcional para reportar progreso.

    Returns:
        Diccionario con resumen:
        - total_equipos: Número de equipos procesados
        - actualizados: Número con estadísticas actualizadas
        - sin_datos: Número sin partidos suficientes
        - errores: Número de errores
        - detalles_errores: Lista de errores

    Ejemplo:
        resultado = actualizar_estadisticas_todos_equipos(conn, 1, 5)
        print(f"Equipos actualizados: {resultado['actualizados']}")
    """
    resultado = {
        'total_equipos': 0,
        'actualizados': 0,
        'sin_datos': 0,
        'errores': 0,
        'detalles_errores': [],
    }

    try:
        # Obtener lista de equipos con partidos en la competición/temporada
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT equipo_id FROM (
                    SELECT equipo_local_id as equipo_id
                    FROM partidos_futbol
                    WHERE competicion_id = %s AND temporada_id = %s
                      AND estado = 'finished'
                    UNION
                    SELECT equipo_visitante_id as equipo_id
                    FROM partidos_futbol
                    WHERE competicion_id = %s AND temporada_id = %s
                      AND estado = 'finished'
                ) equipos
                """,
                (competicion_id, temporada_id, competicion_id, temporada_id)
            )
            equipos = [row[0] for row in cursor.fetchall()]

        resultado['total_equipos'] = len(equipos)
        logger.info(
            f"Actualizando estadísticas de {len(equipos)} equipos "
            f"para competición {competicion_id}, temporada {temporada_id}"
        )

        for i, equipo_id in enumerate(equipos):
            try:
                exito = actualizar_estadisticas_equipo(
                    conexion, equipo_id, competicion_id, temporada_id
                )

                if exito:
                    resultado['actualizados'] += 1
                else:
                    resultado['sin_datos'] += 1

                if callback_progreso:
                    callback_progreso(i + 1, len(equipos), equipo_id)

            except Exception as e:
                resultado['errores'] += 1
                resultado['detalles_errores'].append(
                    f"Equipo {equipo_id}: {str(e)}"
                )
                logger.error(f"Error actualizando estadísticas de equipo {equipo_id}: {e}")

        logger.info(
            f"Actualización completada: "
            f"{resultado['actualizados']} actualizados, "
            f"{resultado['sin_datos']} sin datos, "
            f"{resultado['errores']} errores"
        )

        return resultado

    except Exception as e:
        logger.error(f"Error obteniendo lista de equipos: {e}")
        raise ErrorBaseDatos(
            mensaje="Error obteniendo lista de equipos",
            operacion="SELECT",
            tabla="partidos_futbol",
            excepcion_original=e
        )


def obtener_estadisticas_equipo_bd(
    conexion,
    equipo_id: int,
    competicion_id: int,
    temporada_id: int
) -> Optional[Dict[str, Any]]:
    """
    Obtiene las estadísticas guardadas de un equipo.

    Args:
        conexion: Conexión a la base de datos.
        equipo_id: ID del equipo.
        competicion_id: ID de la competición.
        temporada_id: ID de la temporada.

    Returns:
        Diccionario con estadísticas o None si no existe.
    """
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM estadisticas_equipos_futbol
                WHERE equipo_id = %s
                  AND competicion_id = %s
                  AND temporada_id = %s
                """,
                (equipo_id, competicion_id, temporada_id)
            )
            resultado = cursor.fetchone()

            if resultado:
                # Convertir a diccionario (asumiendo que tenemos los nombres de columnas)
                columnas = [desc[0] for desc in cursor.description]
                return dict(zip(columnas, resultado))

            return None

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de equipo {equipo_id}: {e}")
        return None

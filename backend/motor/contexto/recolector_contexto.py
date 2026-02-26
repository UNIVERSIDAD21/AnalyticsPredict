# -*- coding: utf-8 -*-
"""recolector_contexto.py — Recolecta contexto de BD para ajustes."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple

from psycopg.rows import dict_row

from db import obtener_pool

from .calculador_descanso import calcular_descanso
from .calculador_forma import calcular_forma_reciente
from .calculador_h2h import calcular_h2h
from .tipos_contexto import ContextoCompleto


def _obtener_equipo_id(pool, nombre_equipo: str) -> Tuple[str, str]:
    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, nombre
                FROM equipos
                WHERE LOWER(nombre) = LOWER(%s)
                LIMIT 1
                """,
                [nombre_equipo],
            )
            fila = cursor.fetchone()
    if not fila:
        raise ValueError(f"Equipo no encontrado en BD: {nombre_equipo}")
    return str(fila["id"]), str(fila["nombre"])


def _obtener_stats_temporada(pool, equipo_id: str) -> Dict[str, Any]:
    """Obtiene stats de temporada con fallback seguro si la tabla legacy no existe."""
    consultas = (
        """
        SELECT
            ppg_total,
            opp_total,
            victorias,
            derrotas,
            victorias_local,
            derrotas_local,
            victorias_visitante,
            derrotas_visitante
        FROM estadisticas_equipos
        WHERE equipo_id = %s
        ORDER BY temporada_id DESC
        LIMIT 1
        """,
        """
        SELECT
            ppg_total,
            opp_total,
            victorias,
            derrotas,
            victorias_local,
            derrotas_local,
            victorias_visitante,
            derrotas_visitante
        FROM estadisticas_equipos_baloncesto
        WHERE equipo_id = %s
        ORDER BY temporada_id DESC
        LIMIT 1
        """,
    )

    with pool.connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            for query in consultas:
                try:
                    cursor.execute(query, [equipo_id])
                    fila = cursor.fetchone()
                    if fila:
                        return dict(fila)
                except Exception:
                    # Si la tabla no existe u otro error estructural, intentar fallback.
                    conexion.rollback()
                    continue

    return {}


def _recolectar_contexto_ids(
    equipo_id: str,
    rival_id: str,
    fecha_partido: date,
    limite_h2h: int,
    ultimos_n_forma: int,
) -> ContextoCompleto:
    pool = obtener_pool()

    stats_equipo = _obtener_stats_temporada(pool, equipo_id)
    stats_rival = _obtener_stats_temporada(pool, rival_id)
    ppg_equipo = float(stats_equipo.get("ppg_total") or 0.0)
    ppg_rival = float(stats_rival.get("ppg_total") or 0.0)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futuro_h2h = executor.submit(calcular_h2h, pool, equipo_id, rival_id, limite_h2h)
        futuro_forma_equipo = executor.submit(
            calcular_forma_reciente,
            pool,
            equipo_id,
            ultimos_n_forma,
            ppg_equipo,
        )
        futuro_forma_rival = executor.submit(
            calcular_forma_reciente,
            pool,
            rival_id,
            ultimos_n_forma,
            ppg_rival,
        )
        futuro_descanso_equipo = executor.submit(calcular_descanso, pool, equipo_id, fecha_partido)
        futuro_descanso_rival = executor.submit(calcular_descanso, pool, rival_id, fecha_partido)

        h2h = futuro_h2h.result()
        forma_equipo = futuro_forma_equipo.result()
        forma_rival = futuro_forma_rival.result()
        descanso_equipo = futuro_descanso_equipo.result()
        descanso_rival = futuro_descanso_rival.result()

    return ContextoCompleto(
        h2h=h2h,
        forma_equipo=forma_equipo,
        forma_rival=forma_rival,
        descanso_equipo=descanso_equipo,
        descanso_rival=descanso_rival,
        stats_temporada_equipo=stats_equipo,
        stats_temporada_rival=stats_rival,
    )


@lru_cache(maxsize=256)
def _contexto_cache(
    equipo_id: str,
    rival_id: str,
    fecha_partido_iso: str,
    limite_h2h: int,
    ultimos_n_forma: int,
) -> ContextoCompleto:
    fecha = date.fromisoformat(fecha_partido_iso)
    return _recolectar_contexto_ids(equipo_id, rival_id, fecha, limite_h2h, ultimos_n_forma)


def recolectar_contexto(
    equipo: str,
    rival: str,
    fecha_partido: Optional[date] = None,
    limite_h2h: int = 10,
    ultimos_n_forma: int = 10,
) -> ContextoCompleto:
    """Recolecta contexto del partido con cache simple."""
    pool = obtener_pool()
    equipo_id, _ = _obtener_equipo_id(pool, equipo)
    rival_id, _ = _obtener_equipo_id(pool, rival)
    fecha = fecha_partido or date.today()
    return _contexto_cache(
        equipo_id,
        rival_id,
        fecha.isoformat(),
        limite_h2h,
        ultimos_n_forma,
    )

"""Persistencia neutral de partidos de fútbol para consultar más tarde."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from psycopg.rows import dict_row

from db import obtener_pool


ESTADO_PARTIDO_GUARDADO = "PARTIDO_GUARDADO"
ESTADO_PARTIDO_ARCHIVADO = "PARTIDO_ARCHIVADO"

_SELECT_PARTIDO = """
    SELECT
        pf.id AS partido_id,
        c.nombre AS competicion,
        pf.fecha_partido,
        pf.estado::text AS estado_partido,
        pf.jornada,
        el.nombre AS equipo_local,
        ev.nombre AS equipo_visitante,
        pf.local_goles_total AS goles_local,
        pf.visitante_goles_total AS goles_visitante,
        a.creado_en,
        a.actualizado_en
    FROM apuestas_analizadas a
    JOIN partidos_futbol pf ON pf.id = a.partido_id
    JOIN competiciones_futbol c ON c.id = pf.competicion_id
    JOIN equipos_futbol el ON el.id = pf.equipo_local_id
    JOIN equipos_futbol ev ON ev.id = pf.equipo_visitante_id
    WHERE a.deporte = 'futbol'
      AND a.estado = %s
"""


def _armar_item(fila: dict[str, Any]) -> dict[str, Any]:
    fecha = fila.get("fecha_partido")
    partido = {
        "id": str(fila["partido_id"]),
        "competicion": fila.get("competicion"),
        "fecha_partido": fecha.isoformat() if fecha is not None else None,
        "estado": fila.get("estado_partido"),
        "jornada": fila.get("jornada"),
        "equipo_local": fila.get("equipo_local"),
        "equipo_visitante": fila.get("equipo_visitante"),
        "goles_local": fila.get("goles_local"),
        "goles_visitante": fila.get("goles_visitante"),
    }
    return {
        "deporte": "futbol",
        "partido_id": partido["id"],
        "estado": ESTADO_PARTIDO_GUARDADO,
        "partido": partido,
        "creado_en": fila.get("creado_en"),
        "actualizado_en": fila.get("actualizado_en"),
    }


def guardar_partido_futbol(partido_id: UUID | str, *, pool=None) -> dict[str, Any]:
    """Guarda un partido canónico sin mercado, pick, probabilidad ni stake.

    Reutiliza columnas existentes. El estado específico evita interpretarlo como
    apuesta y el detalle se vuelve a leer del calendario canónico al consultarlo.
    No ejecuta DDL ni depende de la columna JSON `payload`.
    """
    pool = pool or obtener_pool()
    partido_uuid = str(partido_id)
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id
                FROM partidos_futbol
                WHERE id = %s
                """,
                [partido_uuid],
            )
            if not cur.fetchone():
                raise ValueError("El partido de fútbol no existe en el calendario canónico")

            cur.execute(
                """
                SELECT id
                FROM apuestas_analizadas
                WHERE deporte = 'futbol'
                  AND partido_id = %s
                  AND estado IN (%s, %s)
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
                """,
                [partido_uuid, ESTADO_PARTIDO_GUARDADO, ESTADO_PARTIDO_ARCHIVADO],
            )
            existente = cur.fetchone()
            if existente:
                cur.execute(
                    """
                    UPDATE apuestas_analizadas
                    SET estado = %s, actualizado_en = now()
                    WHERE id = %s
                    RETURNING creado_en, actualizado_en
                    """,
                    [ESTADO_PARTIDO_GUARDADO, existente["id"]],
                )
                timestamps = cur.fetchone() or {}
            else:
                cur.execute(
                    """
                    INSERT INTO apuestas_analizadas
                        (deporte, partido_id, mercado, lado, linea, probabilidad_sistema,
                         confianza, estado)
                    VALUES ('futbol', %s, NULL, NULL, NULL, NULL, NULL, %s)
                    RETURNING creado_en, actualizado_en
                    """,
                    [partido_uuid, ESTADO_PARTIDO_GUARDADO],
                )
                timestamps = cur.fetchone() or {}

            cur.execute(
                _SELECT_PARTIDO + " AND a.partido_id = %s ORDER BY a.id DESC LIMIT 1",
                [ESTADO_PARTIDO_GUARDADO, partido_uuid],
            )
            fila = cur.fetchone() or {}
            fila.update(timestamps)
            return _armar_item(fila)


def listar_partidos_futbol_guardados(
    *, partido_id: Optional[UUID | str] = None, limite: int = 500, pool=None
) -> list[dict[str, Any]]:
    pool = pool or obtener_pool()
    limite_n = max(1, min(int(limite), 1000))
    consulta = _SELECT_PARTIDO
    parametros: list[Any] = [ESTADO_PARTIDO_GUARDADO]
    if partido_id is not None:
        consulta += " AND a.partido_id = %s"
        parametros.append(str(partido_id))
    consulta += " ORDER BY a.actualizado_en DESC, a.id DESC LIMIT %s"
    parametros.append(limite_n)

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(consulta, parametros)
            return [_armar_item(fila) for fila in (cur.fetchall() or [])]


def archivar_partido_futbol_guardado(partido_id: UUID | str, *, pool=None) -> bool:
    """Retira el partido de la lista sin borrar ningún registro."""
    pool = pool or obtener_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE apuestas_analizadas
                SET estado = %s, actualizado_en = now()
                WHERE deporte = 'futbol'
                  AND partido_id = %s
                  AND estado = %s
                RETURNING id
                """,
                [ESTADO_PARTIDO_ARCHIVADO, str(partido_id), ESTADO_PARTIDO_GUARDADO],
            )
            return cur.fetchone() is not None

# -*- coding: utf-8 -*-
"""Persistencia y resolución de apuestas analizadas."""

from __future__ import annotations

from typing import Optional

from db import obtener_pool


def asegurar_tabla_apuestas_analizadas(pool=None) -> None:
    pool = pool or obtener_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS apuestas_analizadas (
                    id BIGSERIAL PRIMARY KEY,
                    deporte TEXT NOT NULL,
                    partido_id UUID NOT NULL,
                    mercado TEXT,
                    lado TEXT,
                    linea NUMERIC,
                    probabilidad_sistema NUMERIC,
                    confianza TEXT,
                    estado TEXT NOT NULL DEFAULT 'PENDIENTE',
                    resultado_outcome TEXT,
                    valor_real NUMERIC,
                    resultado_resumen TEXT,
                    payload JSONB,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
                    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS resultado_outcome TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS valor_real NUMERIC;")
            # Historial completo: NO deduplicar por clave natural.
            # Antes existía un índice único que sobreescribía análisis repetidos.
            # Para bitácora completa por evento, se elimina esa restricción.
            cur.execute("DROP INDEX IF EXISTS uq_apuestas_analizadas_natural;")
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_lookup
                ON apuestas_analizadas (deporte, partido_id, mercado, lado, linea);
                """
            )


def registrar_apuesta_analizada(
    *,
    deporte: str,
    partido_id: str,
    mercado: Optional[str],
    lado: Optional[str],
    linea: Optional[float],
    probabilidad_sistema: Optional[float],
    confianza: Optional[str],
    payload_json: str,
    pool=None,
) -> None:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO apuestas_analizadas
                (deporte, partido_id, mercado, lado, linea, probabilidad_sistema, confianza, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                [
                    deporte,
                    partido_id,
                    mercado,
                    lado,
                    linea,
                    probabilidad_sistema,
                    confianza,
                    payload_json,
                ],
            )


def resolver_apuestas_analizadas(pool=None) -> dict:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Baloncesto: soporte Q1-Q4/COMPLETO con outcome over-under
            cur.execute(
                """
                UPDATE apuestas_analizadas a
                SET estado = 'FINALIZADA',
                    valor_real = CASE
                        WHEN UPPER(COALESCE(a.mercado, '')) = 'Q1' THEN COALESCE(pb.local_q1, 0) + COALESCE(pb.visitante_q1, 0)
                        WHEN UPPER(COALESCE(a.mercado, '')) = 'Q2' THEN COALESCE(pb.local_q2, 0) + COALESCE(pb.visitante_q2, 0)
                        WHEN UPPER(COALESCE(a.mercado, '')) = 'Q3' THEN COALESCE(pb.local_q3, 0) + COALESCE(pb.visitante_q3, 0)
                        WHEN UPPER(COALESCE(a.mercado, '')) = 'Q4' THEN COALESCE(pb.local_q4, 0) + COALESCE(pb.visitante_q4, 0)
                        ELSE COALESCE(pb.local_total, 0) + COALESCE(pb.visitante_total, 0)
                    END,
                    resultado_outcome = CASE
                        WHEN a.lado IS NULL OR a.linea IS NULL THEN NULL
                        WHEN (
                            CASE
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q1' THEN COALESCE(pb.local_q1, 0) + COALESCE(pb.visitante_q1, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q2' THEN COALESCE(pb.local_q2, 0) + COALESCE(pb.visitante_q2, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q3' THEN COALESCE(pb.local_q3, 0) + COALESCE(pb.visitante_q3, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q4' THEN COALESCE(pb.local_q4, 0) + COALESCE(pb.visitante_q4, 0)
                                ELSE COALESCE(pb.local_total, 0) + COALESCE(pb.visitante_total, 0)
                            END
                        ) = a.linea THEN 'PUSH'
                        WHEN UPPER(COALESCE(a.lado, '')) = 'OVER' AND (
                            CASE
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q1' THEN COALESCE(pb.local_q1, 0) + COALESCE(pb.visitante_q1, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q2' THEN COALESCE(pb.local_q2, 0) + COALESCE(pb.visitante_q2, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q3' THEN COALESCE(pb.local_q3, 0) + COALESCE(pb.visitante_q3, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q4' THEN COALESCE(pb.local_q4, 0) + COALESCE(pb.visitante_q4, 0)
                                ELSE COALESCE(pb.local_total, 0) + COALESCE(pb.visitante_total, 0)
                            END
                        ) > a.linea THEN 'GANADA'
                        WHEN UPPER(COALESCE(a.lado, '')) = 'UNDER' AND (
                            CASE
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q1' THEN COALESCE(pb.local_q1, 0) + COALESCE(pb.visitante_q1, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q2' THEN COALESCE(pb.local_q2, 0) + COALESCE(pb.visitante_q2, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q3' THEN COALESCE(pb.local_q3, 0) + COALESCE(pb.visitante_q3, 0)
                                WHEN UPPER(COALESCE(a.mercado, '')) = 'Q4' THEN COALESCE(pb.local_q4, 0) + COALESCE(pb.visitante_q4, 0)
                                ELSE COALESCE(pb.local_total, 0) + COALESCE(pb.visitante_total, 0)
                            END
                        ) < a.linea THEN 'GANADA'
                        ELSE 'PERDIDA'
                    END,
                    resultado_resumen = CONCAT('Resultado final: ', pb.local_total, '-', pb.visitante_total),
                    actualizado_en = now()
                FROM partidos_baloncesto pb
                WHERE a.deporte = 'baloncesto'
                  AND a.estado = 'PENDIENTE'
                  AND pb.id = a.partido_id
                  AND pb.local_total IS NOT NULL
                  AND pb.visitante_total IS NOT NULL;
                """
            )
            res_b = cur.rowcount

            # Fútbol: default sobre total goles FT
            cur.execute(
                """
                UPDATE apuestas_analizadas a
                SET estado = 'FINALIZADA',
                    valor_real = COALESCE(pf.local_goles_total, 0) + COALESCE(pf.visitante_goles_total, 0),
                    resultado_outcome = CASE
                        WHEN a.lado IS NULL OR a.linea IS NULL THEN NULL
                        WHEN (COALESCE(pf.local_goles_total, 0) + COALESCE(pf.visitante_goles_total, 0)) = a.linea THEN 'PUSH'
                        WHEN UPPER(COALESCE(a.lado, '')) = 'OVER' AND (COALESCE(pf.local_goles_total, 0) + COALESCE(pf.visitante_goles_total, 0)) > a.linea THEN 'GANADA'
                        WHEN UPPER(COALESCE(a.lado, '')) = 'UNDER' AND (COALESCE(pf.local_goles_total, 0) + COALESCE(pf.visitante_goles_total, 0)) < a.linea THEN 'GANADA'
                        ELSE 'PERDIDA'
                    END,
                    resultado_resumen = CONCAT('Resultado final: ', pf.local_goles_total, '-', pf.visitante_goles_total),
                    actualizado_en = now()
                FROM partidos_futbol pf
                WHERE a.deporte = 'futbol'
                  AND a.estado = 'PENDIENTE'
                  AND pf.id = a.partido_id
                  AND pf.estado = 'FINALIZADO';
                """
            )
            res_f = cur.rowcount
    return {"baloncesto": res_b, "futbol": res_f, "total": res_b + res_f}


def resumen_apuestas_analizadas(pool=None) -> dict:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE estado = 'PENDIENTE') AS pendientes,
                    COUNT(*) FILTER (WHERE resultado_outcome = 'GANADA') AS ganadas,
                    COUNT(*) FILTER (WHERE resultado_outcome = 'PERDIDA') AS perdidas,
                    COUNT(*) FILTER (WHERE resultado_outcome = 'PUSH') AS push
                FROM apuestas_analizadas
            """)
            row = cur.fetchone()
            return {
                'total': int(row[0] or 0),
                'pendientes': int(row[1] or 0),
                'ganadas': int(row[2] or 0),
                'perdidas': int(row[3] or 0),
                'push': int(row[4] or 0),
            }

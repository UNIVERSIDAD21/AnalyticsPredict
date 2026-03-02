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
                    resultado_resumen TEXT,
                    payload JSONB,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
                    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_apuestas_analizadas_natural
                ON apuestas_analizadas (deporte, partido_id, COALESCE(mercado,''), COALESCE(lado,''), COALESCE(linea, -1));
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
                ON CONFLICT (deporte, partido_id, COALESCE(mercado,''), COALESCE(lado,''), COALESCE(linea, -1))
                DO UPDATE SET
                    probabilidad_sistema = EXCLUDED.probabilidad_sistema,
                    confianza = EXCLUDED.confianza,
                    payload = EXCLUDED.payload,
                    actualizado_en = now();
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
            cur.execute(
                """
                UPDATE apuestas_analizadas a
                SET estado = 'FINALIZADA',
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
            cur.execute(
                """
                UPDATE apuestas_analizadas a
                SET estado = 'FINALIZADA',
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

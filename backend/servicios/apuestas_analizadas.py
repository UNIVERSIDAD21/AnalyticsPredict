# -*- coding: utf-8 -*-
"""Persistencia y resolución de apuestas analizadas."""

from __future__ import annotations

from typing import Optional, Any

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
                    decision_p_raw NUMERIC,
                    decision_p_calibrada NUMERIC,
                    decision_edge_real NUMERIC,
                    decision_score NUMERIC,
                    decision_sizing NUMERIC,
                    decision_valor_esperado NUMERIC,
                    decision_calibrador_id TEXT,
                    decision_modelo_version_id TEXT,
                    decision_fuente TEXT,
                    decision_devig_metodo TEXT,
                    decision_devig_overround NUMERIC,
                    decision_devig_p_mkt_fair NUMERIC,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
                    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS resultado_outcome TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS valor_real NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_p_raw NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_p_calibrada NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_edge_real NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_score NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_sizing NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_valor_esperado NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_calibrador_id TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_modelo_version_id TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_fuente TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_metodo TEXT;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_overround NUMERIC;")
            cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_p_mkt_fair NUMERIC;")
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
    decision_p_raw: Optional[float] = None,
    decision_p_calibrada: Optional[float] = None,
    decision_edge_real: Optional[float] = None,
    decision_score: Optional[float] = None,
    decision_sizing: Optional[float] = None,
    decision_valor_esperado: Optional[float] = None,
    decision_calibrador_id: Optional[str] = None,
    decision_modelo_version_id: Optional[str] = None,
    decision_fuente: Optional[str] = None,
    decision_devig_metodo: Optional[str] = None,
    decision_devig_overround: Optional[float] = None,
    decision_devig_p_mkt_fair: Optional[float] = None,
    pool=None,
) -> None:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO apuestas_analizadas
                (
                    deporte, partido_id, mercado, lado, linea, probabilidad_sistema, confianza, payload,
                    decision_p_raw, decision_p_calibrada, decision_edge_real, decision_score,
                    decision_sizing, decision_valor_esperado, decision_calibrador_id,
                    decision_modelo_version_id, decision_fuente, decision_devig_metodo,
                    decision_devig_overround, decision_devig_p_mkt_fair
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
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
                    decision_p_raw,
                    decision_p_calibrada,
                    decision_edge_real,
                    decision_score,
                    decision_sizing,
                    decision_valor_esperado,
                    decision_calibrador_id,
                    decision_modelo_version_id,
                    decision_fuente,
                    decision_devig_metodo,
                    decision_devig_overround,
                    decision_devig_p_mkt_fair,
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


def _armar_where_auditoria_futbol(
    mercado: Optional[str] = None,
    fuente: Optional[str] = None,
    devig_metodo: Optional[str] = None,
) -> tuple[str, list[Any]]:
    condiciones = ["deporte = 'futbol'"]
    params: list[Any] = []

    if mercado:
        condiciones.append("mercado = %s")
        params.append(mercado)
    if fuente:
        condiciones.append("decision_fuente = %s")
        params.append(fuente)
    if devig_metodo:
        condiciones.append("decision_devig_metodo = %s")
        params.append(devig_metodo)

    return (" AND ".join(condiciones), params)


def obtener_auditoria_decisiones_futbol(
    *,
    limite: int = 200,
    offset: int = 0,
    mercado: Optional[str] = None,
    fuente: Optional[str] = None,
    devig_metodo: Optional[str] = None,
    pool=None,
) -> dict:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    where_sql, params = _armar_where_auditoria_futbol(mercado, fuente, devig_metodo)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    id, partido_id, mercado, lado, linea,
                    probabilidad_sistema, confianza, estado, resultado_outcome,
                    decision_p_raw, decision_p_calibrada, decision_edge_real,
                    decision_score, decision_sizing, decision_valor_esperado,
                    decision_calibrador_id, decision_modelo_version_id,
                    decision_fuente, decision_devig_metodo,
                    decision_devig_overround, decision_devig_p_mkt_fair,
                    creado_en, actualizado_en
                FROM apuestas_analizadas
                WHERE {where_sql}
                ORDER BY actualizado_en DESC
                LIMIT %s OFFSET %s
                """,
                params + [max(1, min(limite, 2000)), max(0, offset)],
            )
            filas = cur.fetchall() or []

            cur.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE decision_fuente = 'ML') AS total_ml,
                    COUNT(*) FILTER (WHERE decision_fuente = 'HEURISTICO') AS total_heuristico,
                    COUNT(*) FILTER (WHERE decision_fuente = 'ENSEMBLE') AS total_ensemble,
                    AVG(decision_edge_real) AS edge_promedio,
                    AVG(decision_score) AS score_promedio,
                    AVG(decision_sizing) AS sizing_promedio,
                    AVG(decision_valor_esperado) AS ev_promedio
                FROM apuestas_analizadas
                WHERE {where_sql}
                """,
                params,
            )
            resumen = cur.fetchone()

            cur.execute(
                f"""
                SELECT
                    COALESCE(mercado, 'N/A') AS mercado,
                    COALESCE(decision_fuente, 'N/A') AS fuente,
                    COALESCE(decision_devig_metodo, 'N/A') AS devig_metodo,
                    COUNT(*) AS total,
                    AVG(decision_edge_real) AS edge_promedio,
                    AVG(decision_score) AS score_promedio,
                    AVG(decision_sizing) AS sizing_promedio,
                    AVG(decision_valor_esperado) AS ev_promedio
                FROM apuestas_analizadas
                WHERE {where_sql}
                GROUP BY 1,2,3
                ORDER BY total DESC, mercado ASC
                LIMIT 200
                """,
                params,
            )
            cortes = cur.fetchall() or []

    return {
        "total": int(resumen[0] or 0),
        "totales": {
            "ml": int(resumen[1] or 0),
            "heuristico": int(resumen[2] or 0),
            "ensemble": int(resumen[3] or 0),
        },
        "promedios": {
            "edge_real": float(resumen[4]) if resumen[4] is not None else None,
            "score": float(resumen[5]) if resumen[5] is not None else None,
            "sizing": float(resumen[6]) if resumen[6] is not None else None,
            "valor_esperado": float(resumen[7]) if resumen[7] is not None else None,
        },
        "cortes": [
            {
                "mercado": c[0],
                "fuente": c[1],
                "devig_metodo": c[2],
                "total": int(c[3] or 0),
                "edge_promedio": float(c[4]) if c[4] is not None else None,
                "score_promedio": float(c[5]) if c[5] is not None else None,
                "sizing_promedio": float(c[6]) if c[6] is not None else None,
                "ev_promedio": float(c[7]) if c[7] is not None else None,
            }
            for c in cortes
        ],
        "items": filas,
    }

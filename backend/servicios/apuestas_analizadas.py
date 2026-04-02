# -*- coding: utf-8 -*-
"""Persistencia y resolución de apuestas analizadas."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Any

from psycopg.rows import dict_row

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
                    decision_cuota NUMERIC,
                    decision_cuota_over NUMERIC,
                    decision_cuota_under NUMERIC,
                    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
                    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            # Política de esquema: migraciones formales primero.
            # Runtime DDL solo cuando se habilita explícitamente para bootstrap/emergencia.
            allow_runtime_ddl = os.getenv("APUESTAS_ANALIZADAS_RUNTIME_DDL", "0") == "1"
            if allow_runtime_ddl:
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
                cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota NUMERIC;")
                cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota_over NUMERIC;")
                cur.execute("ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota_under NUMERIC;")
                cur.execute("DROP INDEX IF EXISTS uq_apuestas_analizadas_natural;")
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_lookup
                    ON apuestas_analizadas (deporte, partido_id, mercado, lado, linea);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_actualizado
                    ON apuestas_analizadas (deporte, actualizado_en DESC);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_cortes
                    ON apuestas_analizadas (deporte, mercado, decision_fuente, decision_devig_metodo);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_modelo
                    ON apuestas_analizadas (deporte, decision_modelo_version_id);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_calibrador
                    ON apuestas_analizadas (deporte, decision_calibrador_id);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_estado_outcome
                    ON apuestas_analizadas (deporte, estado, resultado_outcome);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS ix_apuestas_analizadas_futbol_creado
                    ON apuestas_analizadas (deporte, creado_en DESC);
                """)

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
    decision_cuota: Optional[float] = None,
    decision_cuota_over: Optional[float] = None,
    decision_cuota_under: Optional[float] = None,
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
                    decision_devig_overround, decision_devig_p_mkt_fair,
                    decision_cuota, decision_cuota_over, decision_cuota_under
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
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
                    decision_cuota,
                    decision_cuota_over,
                    decision_cuota_under,
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
    creado_desde: Optional[datetime] = None,
    creado_hasta: Optional[datetime] = None,
    actualizado_desde: Optional[datetime] = None,
    actualizado_hasta: Optional[datetime] = None,
    fecha_partido_desde: Optional[datetime] = None,
    fecha_partido_hasta: Optional[datetime] = None,
    partido_id: Optional[str] = None,
    modelo_version_id: Optional[str] = None,
    calibrador_id: Optional[str] = None,
    estado: Optional[str] = None,
    resultado_outcome: Optional[str] = None,
) -> tuple[str, list[Any]]:
    # La vista ya está filtrada a deporte='futbol'
    condiciones = ["1=1"]
    params: list[Any] = []

    if mercado:
        condiciones.append("v.mercado = %s")
        params.append(mercado)
    if fuente:
        condiciones.append("v.decision_fuente = %s")
        params.append(fuente)
    if devig_metodo:
        condiciones.append("v.decision_devig_metodo = %s")
        params.append(devig_metodo)
    if creado_desde:
        condiciones.append("v.creado_en >= %s")
        params.append(creado_desde)
    if creado_hasta:
        condiciones.append("v.creado_en <= %s")
        params.append(creado_hasta)
    if actualizado_desde:
        condiciones.append("v.actualizado_en >= %s")
        params.append(actualizado_desde)
    if actualizado_hasta:
        condiciones.append("v.actualizado_en <= %s")
        params.append(actualizado_hasta)
    if fecha_partido_desde:
        condiciones.append("v.fecha_partido >= %s")
        params.append(fecha_partido_desde)
    if fecha_partido_hasta:
        condiciones.append("v.fecha_partido <= %s")
        params.append(fecha_partido_hasta)
    if partido_id:
        condiciones.append("v.partido_id = %s")
        params.append(partido_id)
    if modelo_version_id:
        condiciones.append("v.decision_modelo_version_id = %s")
        params.append(modelo_version_id)
    if calibrador_id:
        condiciones.append("v.decision_calibrador_id = %s")
        params.append(calibrador_id)
    if estado:
        condiciones.append("v.estado = %s")
        params.append(estado)
    if resultado_outcome:
        condiciones.append("v.resultado_outcome = %s")
        params.append(resultado_outcome)

    return (" AND ".join(condiciones), params)


def obtener_auditoria_decisiones_futbol(
    *,
    limite: int = 200,
    offset: int = 0,
    mercado: Optional[str] = None,
    fuente: Optional[str] = None,
    devig_metodo: Optional[str] = None,
    creado_desde: Optional[datetime] = None,
    creado_hasta: Optional[datetime] = None,
    actualizado_desde: Optional[datetime] = None,
    actualizado_hasta: Optional[datetime] = None,
    fecha_partido_desde: Optional[datetime] = None,
    fecha_partido_hasta: Optional[datetime] = None,
    partido_id: Optional[str] = None,
    modelo_version_id: Optional[str] = None,
    calibrador_id: Optional[str] = None,
    estado: Optional[str] = None,
    resultado_outcome: Optional[str] = None,
    pool=None,
) -> dict:
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)
    where_sql, params = _armar_where_auditoria_futbol(
        mercado=mercado,
        fuente=fuente,
        devig_metodo=devig_metodo,
        creado_desde=creado_desde,
        creado_hasta=creado_hasta,
        actualizado_desde=actualizado_desde,
        actualizado_hasta=actualizado_hasta,
        fecha_partido_desde=fecha_partido_desde,
        fecha_partido_hasta=fecha_partido_hasta,
        partido_id=partido_id,
        modelo_version_id=modelo_version_id,
        calibrador_id=calibrador_id,
        estado=estado,
        resultado_outcome=resultado_outcome,
    )

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT
                    v.id, v.partido_id, v.mercado, v.lado, v.linea,
                    v.probabilidad_sistema, v.confianza, v.estado, v.resultado_outcome,
                    v.decision_p_raw, v.decision_p_calibrada, v.decision_edge_real,
                    v.decision_score, v.decision_sizing, v.decision_valor_esperado,
                    v.decision_calibrador_id, v.decision_modelo_version_id,
                    v.decision_fuente, v.decision_devig_metodo,
                    v.decision_devig_overround, v.decision_devig_p_mkt_fair,
                    v.decision_cuota, v.decision_cuota_over, v.decision_cuota_under,
                    v.fecha_partido,
                    v.creado_en, v.actualizado_en
                FROM vw_auditoria_decisiones_futbol v
                WHERE {where_sql}
                ORDER BY v.actualizado_en DESC
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
                    COUNT(*) FILTER (WHERE resultado_outcome IN ('GANADA','PERDIDA')) AS total_resueltas,
                    COUNT(*) FILTER (WHERE resultado_outcome IS NULL OR resultado_outcome IN ('PUSH','ANULADA')) AS total_no_resueltas,
                    AVG(decision_edge_real) AS edge_promedio,
                    AVG(decision_score) AS score_promedio,
                    AVG(decision_sizing) AS sizing_promedio,
                    AVG(decision_valor_esperado) AS ev_promedio,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            POWER(
                                COALESCE(decision_p_calibrada, probabilidad_sistema)
                                - CASE WHEN resultado_outcome = 'GANADA' THEN 1 ELSE 0 END,
                                2
                            )
                        END
                    ) AS brier_score,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            -(
                                CASE WHEN resultado_outcome = 'GANADA'
                                    THEN LN(GREATEST(LEAST(COALESCE(decision_p_calibrada, probabilidad_sistema), 0.999999), 0.000001))
                                    ELSE LN(GREATEST(LEAST(1 - COALESCE(decision_p_calibrada, probabilidad_sistema), 0.999999), 0.000001))
                                END
                            )
                        END
                    ) AS log_loss,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            ABS(
                                COALESCE(decision_p_calibrada, probabilidad_sistema)
                                - CASE WHEN resultado_outcome = 'GANADA' THEN 1 ELSE 0 END
                            )
                        END
                    ) AS calibration_gap,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            CASE WHEN resultado_outcome = 'GANADA' THEN 1.0 ELSE 0.0 END
                        END
                    ) AS hit_rate
                FROM vw_auditoria_decisiones_futbol v
                WHERE {where_sql}
                """,
                params,
            )
            resumen = cur.fetchone() or {}

            cur.execute(
                f"""
                SELECT
                    COALESCE(v.mercado, 'N/A') AS mercado,
                    COALESCE(v.decision_fuente, 'N/A') AS fuente,
                    COALESCE(v.decision_devig_metodo, 'N/A') AS devig_metodo,
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE resultado_outcome IN ('GANADA','PERDIDA')) AS resueltas,
                    AVG(decision_edge_real) AS edge_promedio,
                    AVG(decision_score) AS score_promedio,
                    AVG(decision_sizing) AS sizing_promedio,
                    AVG(decision_valor_esperado) AS ev_promedio,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            POWER(
                                COALESCE(decision_p_calibrada, probabilidad_sistema)
                                - CASE WHEN resultado_outcome = 'GANADA' THEN 1 ELSE 0 END,
                                2
                            )
                        END
                    ) AS brier_score,
                    AVG(
                        CASE WHEN resultado_outcome IN ('GANADA','PERDIDA') THEN
                            CASE WHEN resultado_outcome = 'GANADA' THEN 1.0 ELSE 0.0 END
                        END
                    ) AS hit_rate
                FROM vw_auditoria_decisiones_futbol v
                WHERE {where_sql}
                GROUP BY 1,2,3
                ORDER BY total DESC, mercado ASC
                LIMIT 200
                """,
                params,
            )
            cortes = cur.fetchall() or []

    items = [
        {
            "id": row["id"],
            "partido_id": row["partido_id"],
            "mercado": row["mercado"],
            "lado": row["lado"],
            "linea": row["linea"],
            "probabilidad_sistema": row["probabilidad_sistema"],
            "confianza": row["confianza"],
            "estado": row["estado"],
            "resultado_outcome": row["resultado_outcome"],
            "decision_p_raw": row["decision_p_raw"],
            "decision_p_calibrada": row["decision_p_calibrada"],
            "decision_edge_real": row["decision_edge_real"],
            "decision_score": row["decision_score"],
            "decision_sizing": row["decision_sizing"],
            "decision_valor_esperado": row["decision_valor_esperado"],
            "decision_calibrador_id": row["decision_calibrador_id"],
            "decision_modelo_version_id": row["decision_modelo_version_id"],
            "decision_fuente": row["decision_fuente"],
            "decision_devig_metodo": row["decision_devig_metodo"],
            "decision_devig_overround": row["decision_devig_overround"],
            "decision_devig_p_mkt_fair": row["decision_devig_p_mkt_fair"],
            "decision_cuota": row["decision_cuota"],
            "decision_cuota_over": row["decision_cuota_over"],
            "decision_cuota_under": row["decision_cuota_under"],
            "fecha_partido": row.get("fecha_partido"),
            "creado_en": row["creado_en"],
            "actualizado_en": row["actualizado_en"],
        }
        for row in filas
    ]

    return {
        "total": int(resumen.get("total") or 0),
        "totales": {
            "ml": int(resumen.get("total_ml") or 0),
            "heuristico": int(resumen.get("total_heuristico") or 0),
            "ensemble": int(resumen.get("total_ensemble") or 0),
            "resueltas": int(resumen.get("total_resueltas") or 0),
            "no_resueltas": int(resumen.get("total_no_resueltas") or 0),
        },
        "promedios": {
            "edge_real": float(resumen["edge_promedio"]) if resumen.get("edge_promedio") is not None else None,
            "score": float(resumen["score_promedio"]) if resumen.get("score_promedio") is not None else None,
            "sizing": float(resumen["sizing_promedio"]) if resumen.get("sizing_promedio") is not None else None,
            "valor_esperado": float(resumen["ev_promedio"]) if resumen.get("ev_promedio") is not None else None,
            "brier_score": float(resumen["brier_score"]) if resumen.get("brier_score") is not None else None,
            "log_loss": float(resumen["log_loss"]) if resumen.get("log_loss") is not None else None,
            "calibration_gap": float(resumen["calibration_gap"]) if resumen.get("calibration_gap") is not None else None,
            "hit_rate": float(resumen["hit_rate"]) if resumen.get("hit_rate") is not None else None,
        },
        "cortes": [
            {
                "mercado": c["mercado"],
                "fuente": c["fuente"],
                "devig_metodo": c["devig_metodo"],
                "total": int(c["total"] or 0),
                "resueltas": int(c.get("resueltas") or 0),
                "edge_promedio": float(c["edge_promedio"]) if c.get("edge_promedio") is not None else None,
                "score_promedio": float(c["score_promedio"]) if c.get("score_promedio") is not None else None,
                "sizing_promedio": float(c["sizing_promedio"]) if c.get("sizing_promedio") is not None else None,
                "ev_promedio": float(c["ev_promedio"]) if c.get("ev_promedio") is not None else None,
                "brier_score": float(c["brier_score"]) if c.get("brier_score") is not None else None,
                "hit_rate": float(c["hit_rate"]) if c.get("hit_rate") is not None else None,
            }
            for c in cortes
        ],
        "items": items,
        "filtros_aplicados": {
            "mercado": mercado,
            "fuente": fuente,
            "devig_metodo": devig_metodo,
            "creado_desde": creado_desde,
            "creado_hasta": creado_hasta,
            "actualizado_desde": actualizado_desde,
            "actualizado_hasta": actualizado_hasta,
            "fecha_partido_desde": fecha_partido_desde,
            "fecha_partido_hasta": fecha_partido_hasta,
            "partido_id": partido_id,
            "modelo_version_id": modelo_version_id,
            "calibrador_id": calibrador_id,
            "estado": estado,
            "resultado_outcome": resultado_outcome,
        },
        "paginacion": {
            "limite": max(1, min(limite, 2000)),
            "offset": max(0, offset),
            "items": len(items),
        },
    }


def backfill_decisiones_desde_payload_futbol(
    *,
    limite: int = 5000,
    batch_size: int = 500,
    checkpoint_id: Optional[int] = None,
    dry_run: bool = False,
    pool=None,
) -> dict:
    """Backfill idempotente de columnas canónicas desde payload JSON cuando sea posible."""
    pool = pool or obtener_pool()
    asegurar_tabla_apuestas_analizadas(pool)

    limite_n = max(1, min(limite, 50000))
    batch_n = max(1, min(batch_size, 5000))

    coverage = {
        "decision_p_raw": 0,
        "decision_p_calibrada": 0,
        "decision_edge_real": 0,
        "decision_score": 0,
        "decision_sizing": 0,
        "decision_valor_esperado": 0,
        "decision_calibrador_id": 0,
        "decision_modelo_version_id": 0,
        "decision_fuente": 0,
        "decision_devig_metodo": 0,
        "decision_devig_overround": 0,
        "decision_devig_p_mkt_fair": 0,
        "decision_cuota": 0,
        "decision_cuota_over": 0,
        "decision_cuota_under": 0,
    }

    candidatas = 0
    actualizadas = 0
    sin_datos = 0
    ultimo_id = checkpoint_id
    procesadas = 0

    while procesadas < limite_n:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                restantes = limite_n - procesadas
                chunk = min(batch_n, restantes)
                cur.execute(
                    """
                    SELECT id, payload
                    FROM apuestas_analizadas
                    WHERE deporte = 'futbol'
                      AND (%s IS NULL OR id > %s)
                      AND (
                        decision_p_raw IS NULL
                        OR decision_p_calibrada IS NULL
                        OR decision_fuente IS NULL
                        OR decision_devig_metodo IS NULL
                      )
                    ORDER BY id ASC
                    LIMIT %s
                    """,
                    [ultimo_id, ultimo_id, chunk],
                )
                filas = cur.fetchall() or []

                if not filas:
                    break

                for row in filas:
                    candidatas += 1
                    procesadas += 1
                    ultimo_id = int(row["id"])
                    payload = row.get("payload") or {}
                    decision = payload.get("decision") if isinstance(payload, dict) else None
                    if not isinstance(decision, dict):
                        sin_datos += 1
                        continue

                    for field, source_key in [
                        ("decision_p_raw", "p_raw"),
                        ("decision_p_calibrada", "p_calibrada"),
                        ("decision_edge_real", "edge_real"),
                        ("decision_score", "score"),
                        ("decision_sizing", "sizing"),
                        ("decision_valor_esperado", "valor_esperado"),
                        ("decision_calibrador_id", "calibrador_id"),
                        ("decision_modelo_version_id", "modelo_version_id"),
                        ("decision_fuente", "fuente"),
                        ("decision_devig_metodo", "devig_metodo"),
                        ("decision_devig_overround", "devig_overround"),
                        ("decision_devig_p_mkt_fair", "devig_p_mkt_fair"),
                        ("decision_cuota", "cuota"),
                        ("decision_cuota_over", "cuota_over"),
                        ("decision_cuota_under", "cuota_under"),
                    ]:
                        if decision.get(source_key) is not None:
                            coverage[field] += 1

                    if dry_run:
                        continue

                    cur.execute(
                        """
                        UPDATE apuestas_analizadas
                        SET
                            decision_p_raw = COALESCE(decision_p_raw, %s),
                            decision_p_calibrada = COALESCE(decision_p_calibrada, %s),
                            decision_edge_real = COALESCE(decision_edge_real, %s),
                            decision_score = COALESCE(decision_score, %s),
                            decision_sizing = COALESCE(decision_sizing, %s),
                            decision_valor_esperado = COALESCE(decision_valor_esperado, %s),
                            decision_calibrador_id = COALESCE(decision_calibrador_id, %s),
                            decision_modelo_version_id = COALESCE(decision_modelo_version_id, %s),
                            decision_fuente = COALESCE(decision_fuente, %s),
                            decision_devig_metodo = COALESCE(decision_devig_metodo, %s),
                            decision_devig_overround = COALESCE(decision_devig_overround, %s),
                            decision_devig_p_mkt_fair = COALESCE(decision_devig_p_mkt_fair, %s),
                            decision_cuota = COALESCE(decision_cuota, %s),
                            decision_cuota_over = COALESCE(decision_cuota_over, %s),
                            decision_cuota_under = COALESCE(decision_cuota_under, %s)
                        WHERE id = %s
                        """,
                        [
                            decision.get("p_raw"),
                            decision.get("p_calibrada"),
                            decision.get("edge_real"),
                            decision.get("score"),
                            decision.get("sizing"),
                            decision.get("valor_esperado"),
                            decision.get("calibrador_id"),
                            decision.get("modelo_version_id"),
                            decision.get("fuente"),
                            decision.get("devig_metodo"),
                            decision.get("devig_overround"),
                            decision.get("devig_p_mkt_fair"),
                            decision.get("cuota"),
                            decision.get("cuota_over"),
                            decision.get("cuota_under"),
                            row["id"],
                        ],
                    )
                    actualizadas += cur.rowcount

    return {
        "dry_run": dry_run,
        "candidatas": candidatas,
        "actualizadas": actualizadas,
        "sin_datos_decision": sin_datos,
        "checkpoint_inicial": checkpoint_id,
        "checkpoint_final": ultimo_id,
        "batch_size": batch_n,
        "coverage_por_campo": coverage,
        "idempotencia": "usa COALESCE en UPDATE: re-ejecutar no sobrescribe campos ya poblados",
    }

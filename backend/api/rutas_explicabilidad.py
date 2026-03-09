# -*- coding: utf-8 -*-
"""Endpoints de explicabilidad de predicciones."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import logging

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from psycopg import OperationalError

from db import obtener_pool
from calidad.scorecard import obtener_scorecard_actual
from calidad.alertas import obtener_alertas_activas
from feature_flags import FEATURE_CONTRATO_EXPLICACION_V1, flag_activo
from explicabilidad.contrato import (
    ContratoExplicacion,
    QualityCoherenceError,
    adaptar_legacy,
    construir_contrato,
)

router = APIRouter(prefix="/api/prediccion", tags=["Explicabilidad"])
logger = logging.getLogger(__name__)
SUNSET_MAX_DATE = datetime(2026, 12, 31, tzinfo=timezone.utc)


def _fetch_prediccion(cursor: Any, prediction_id: str) -> Optional[Dict[str, Any]]:
    try:
        cursor.execute(
            """
            SELECT
              pr.id::text AS prediction_id,
              'NBA'::text AS sport,
              el.nombre AS home_team,
              ev.nombre AS away_team,
              p.fecha_partido::timestamp AS game_date,
              'NBA'::text AS league,
              COALESCE(pr.linea, 0)::numeric AS line,
              COALESCE(pr.linea, 0)::numeric AS value,
              CASE WHEN UPPER(COALESCE(pr.lado,'')) LIKE 'OVER%%' THEN 'over' ELSE 'under' END AS recommendation,
              COALESCE(pr.p_calibrada, pr.p_raw, 0.5) * 100.0 AS confidence_numeric,
              CASE WHEN pr.p_calibrada IS NULL THEN 'p_raw' ELSE 'p_calibrada' END AS calibration_source,
              TRUE AS market_valid,
              GREATEST(COALESCE(pr.linea,0) - 3, 0)::numeric AS interval_lower,
              (COALESCE(pr.linea,0) + 3)::numeric AS interval_upper,
              'points'::text AS unit,
              COALESCE(pr.origen, 'ridge_nba_v3')::text AS model_version,
              'api-2.x'::text AS backend_version
            FROM predicciones_registradas pr
            JOIN partidos_baloncesto p ON p.id = pr.partido_id
            JOIN equipos el ON el.id = p.equipo_local_id
            JOIN equipos ev ON ev.id = p.equipo_visitante_id
            WHERE pr.id::text = %s
            LIMIT 1
            """,
            (prediction_id,),
        )
        row = cursor.fetchone()
        if row:
            return row
    except (KeyError, AttributeError) as e:
        logger.warning("Inconsistencia de atributos en fetch NBA", extra={"error": str(e)})
    except OperationalError:
        raise
    except Exception:
        pass

    try:
        cursor.execute(
            """
            SELECT
              pf.id::text AS prediction_id,
              'FOOTBALL'::text AS sport,
              'LOCAL'::text AS home_team,
              'VISITANTE'::text AS away_team,
              COALESCE(pf.fecha_partido, NOW())::timestamp AS game_date,
              'FOOTBALL'::text AS league,
              COALESCE(pf.linea, 2.5)::numeric AS line,
              COALESCE(pf.linea, 2.5)::numeric AS value,
              CASE WHEN COALESCE(pf.prob_over_calibrada, pf.prob_over, 0.5) >= 0.5 THEN 'over' ELSE 'under' END AS recommendation,
              COALESCE(pf.prob_over_calibrada, pf.prob_over, 0.5) * 100.0 AS confidence_numeric,
              CASE WHEN pf.prob_over_calibrada IS NULL THEN 'p_raw' ELSE 'p_calibrada' END AS calibration_source,
              TRUE AS market_valid,
              GREATEST(COALESCE(pf.linea,2.5) - 0.5, 0)::numeric AS interval_lower,
              (COALESCE(pf.linea,2.5) + 0.5)::numeric AS interval_upper,
              'goals'::text AS unit,
              'football_beta_v1'::text AS model_version,
              'api-2.x'::text AS backend_version
            FROM predicciones_futbol pf
            WHERE pf.id::text = %s
            LIMIT 1
            """,
            (prediction_id,),
        )
        row = cursor.fetchone()
        return row
    except (KeyError, AttributeError) as e:
        logger.warning("Inconsistencia de atributos en fetch FUT", extra={"error": str(e)})
        return None
    except OperationalError:
        raise
    except Exception:
        return None


def _registrar_uso_contrato(conn: Any, domain: str, es_legacy: bool) -> None:
    """Persistencia de telemetría por dominio/día para contrato v1/legacy."""
    sql = """
    INSERT INTO analytics.contrato_uso_log (fecha, domain, total_llamadas_v1, total_llamadas_legacy)
    VALUES (CURRENT_DATE, %s, %s, %s)
    ON CONFLICT (fecha, domain)
    DO UPDATE SET
      total_llamadas_v1 = analytics.contrato_uso_log.total_llamadas_v1 + EXCLUDED.total_llamadas_v1,
      total_llamadas_legacy = analytics.contrato_uso_log.total_llamadas_legacy + EXCLUDED.total_llamadas_legacy,
      updated_at = NOW()
    """
    inc_v1 = 0 if es_legacy else 1
    inc_legacy = 1 if es_legacy else 0
    try:
      with conn.cursor() as cur:
          cur.execute(sql, (domain, inc_v1, inc_legacy))
      conn.commit()
    except Exception:
      conn.rollback()
      logger.warning("No fue posible registrar telemetría de contrato", extra={"domain": domain, "legacy": es_legacy})


def _calcular_sunset(conn: Any, domain: str) -> str:
    """Sunset = hoy+30d si legacy<5% por 7 días, si no fecha tope bloque 10."""
    sql = """
    SELECT fecha, total_llamadas_v1, total_llamadas_legacy
    FROM analytics.contrato_uso_log
    WHERE domain = %s
      AND fecha >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY fecha DESC
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (domain,))
            rows = cur.fetchall() or []
    except Exception:
        rows = []

    if len(rows) >= 7:
        ok = True
        for _fecha, v1, legacy in rows[:7]:
            total = float((v1 or 0) + (legacy or 0))
            ratio = (float(legacy or 0) / total) if total > 0 else 0.0
            if ratio >= 0.05:
                ok = False
                break
        if ok:
            target = datetime.now(timezone.utc) + timedelta(days=30)
            return min(target, SUNSET_MAX_DATE).date().isoformat()
    return SUNSET_MAX_DATE.date().isoformat()


@router.get(
    "/{prediction_id}/explicacion",
    response_model=ContratoExplicacion,
    summary="Explicación de predicción",
    description="Retorna explicación quality-aware de una predicción en contrato canónico v1 o formato legacy.",
    responses={
        200: {"description": "Contrato de explicación válido"},
        422: {"description": "Predicción no encontrada o inconsistencia de calidad"},
    },
)
async def get_explicacion_prediccion(
    prediction_id: str,
    version: str = Query(default="v1", pattern="^(v1|legacy)$"),
    accept: Optional[str] = Header(default=None),
):
    accept_legacy = bool(accept and "version=legacy" in accept)
    contrato_v1_activo = flag_activo(FEATURE_CONTRATO_EXPLICACION_V1)

    if not contrato_v1_activo and not (version == "legacy" or accept_legacy):
        return JSONResponse(
            status_code=404,
            content={
                "exito": False,
                "error": {
                    "code": "FEATURE_DISABLED",
                    "message": "Contrato de explicación v1 desactivado por feature flag",
                    "detail": {"feature": FEATURE_CONTRATO_EXPLICACION_V1},
                    "trace_id": None,
                },
            },
        )

    try:
        pool = obtener_pool()
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                pred = _fetch_prediccion(cursor, prediction_id)
                if not pred:
                    return JSONResponse(
                        status_code=404,
                        content={
                            "exito": False,
                            "error": {
                                "code": "PREDICTION_NOT_FOUND",
                                "message": "No existe la predicción solicitada",
                                "detail": {"prediction_id": prediction_id},
                                "trace_id": None,
                            },
                        },
                    )

                domain = "NBA" if pred["sport"] == "NBA" else "FUTBOL"
                scorecard = obtener_scorecard_actual(conn, domain)
                alertas = obtener_alertas_activas(conn, domain=domain, severidad_min="MEDIA", ventana_dias=14)
    except OperationalError:
        return JSONResponse(
            status_code=503,
            content={
                "exito": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Base de datos no disponible temporalmente",
                    "detail": None,
                    "trace_id": None,
                },
            },
        )

    factores = [
        {
            "factor_name": "form_recent",
            "contribution": 18.0,
            "value": 1.0,
            "description": "Tendencia reciente relevante",
        },
        {
            "factor_name": "matchup_context",
            "contribution": 12.0,
            "value": 1.0,
            "description": "Contexto del enfrentamiento",
        },
    ]

    historico = {
        "similar_predictions": 100,
        "accuracy_rate": 0.7,
        "sample_size": 100,
    }

    try:
        contrato = construir_contrato(pred, scorecard, alertas, factores, historico)
    except QualityCoherenceError as e:
        return JSONResponse(
            status_code=422,
            content={
                "exito": False,
                "error": {
                    "code": "QUALITY_COHERENCE_ERROR",
                    "message": str(e),
                    "detail": {"prediction_id": prediction_id},
                    "trace_id": None,
                },
            },
        )

    es_legacy = version == "legacy" or accept_legacy

    with pool.connection() as conn2:
        _registrar_uso_contrato(conn2, domain, es_legacy)
        sunset_date = _calcular_sunset(conn2, domain)

    logger.info(
        "explicacion_contrato_entregado",
        extra={
            "prediction_id": prediction_id,
            "domain": domain,
            "is_legacy_contract": es_legacy,
            "contract_version": "legacy" if es_legacy else "v1.0.0",
        },
    )

    if es_legacy:
        legacy = adaptar_legacy(contrato)
        headers = {
            "Deprecation": "true",
            "Sunset": sunset_date,
            "Link": f"</api/prediccion/{prediction_id}/explicacion?version=v1>; rel=\"successor-version\"",
        }
        return JSONResponse(content={"exito": True, "contrato": legacy}, headers=headers)

    return contrato

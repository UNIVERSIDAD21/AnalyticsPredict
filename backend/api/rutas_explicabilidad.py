# -*- coding: utf-8 -*-
"""Endpoints de explicabilidad de predicciones."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from db import obtener_pool
from calidad.scorecard import obtener_scorecard_actual
from calidad.alertas import obtener_alertas_activas
from explicabilidad.contrato import (
    ContratoExplicacion,
    QualityCoherenceError,
    adaptar_legacy,
    construir_contrato,
)

router = APIRouter(prefix="/api/prediccion", tags=["Explicabilidad"])


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
        return cursor.fetchone()
    except Exception:
        return None


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
    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            pred = _fetch_prediccion(cursor, prediction_id)
            if not pred:
                return JSONResponse(
                    status_code=422,
                    content={
                        "exito": False,
                        "error": {
                            "code": "PREDICCION_NO_EXISTE",
                            "message": "No existe la predicción solicitada",
                            "detail": {"prediction_id": prediction_id},
                            "trace_id": None,
                        },
                    },
                )

            domain = "NBA" if pred["sport"] == "NBA" else "FUTBOL"
            scorecard = obtener_scorecard_actual(conn, domain) or {
                "score_final": 60.0,
                "nivel": "C",
                "criticas_activas": 1,
                "drift_penalty": 0.0,
                "partial_penalty": 0.0,
                "componentes": {},
                "overrides": {},
                "periodo": datetime.utcnow().date().isoformat(),
            }

            alertas = obtener_alertas_activas(conn, domain=domain, severidad_min="MEDIA", ventana_dias=14)

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

    accept_legacy = bool(accept and "version=legacy" in accept)
    if version == "legacy" or accept_legacy:
        legacy = adaptar_legacy(contrato)
        return {"exito": True, "contrato": legacy}

    return contrato

# -*- coding: utf-8 -*-
"""Endpoints de calidad de datos."""

from __future__ import annotations

from fastapi import APIRouter, Query
from psycopg.rows import dict_row

from db import obtener_pool
from calidad.alertas import obtener_alertas_activas
from calidad.scorecard import obtener_scorecard_actual
from feature_flags import estado_flags, FEATURE_CONTRATO_EXPLICACION_V1, flag_activo

router = APIRouter(prefix="/api/calidad", tags=["Calidad"])


@router.get(
    "/alertas",
    summary="Obtener alertas activas de calidad",
    description="Retorna alertas activas con filtro opcional por dominio y severidad mínima.",
)
async def get_alertas_activas(
    domain: str | None = Query(default=None, description="NBA o FUTBOL"),
    severidad_min: str = Query(default="MEDIA", description="MEDIA|ALTA|CRITICA"),
    ventana_dias: int = Query(default=14, ge=1, le=90),
):
    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row):
            alertas = obtener_alertas_activas(
                conn,
                domain=domain,
                severidad_min=severidad_min,
                ventana_dias=ventana_dias,
            )

    resumen = {
        "total": len(alertas),
        "criticas": sum(1 for a in alertas if a["severity"] == "CRITICA"),
        "altas": sum(1 for a in alertas if a["severity"] == "ALTA"),
        "medias": sum(1 for a in alertas if a["severity"] == "MEDIA"),
    }

    return {
        "exito": True,
        "alertas": alertas,
        "resumen": resumen,
    }


@router.get(
    "/estado-sistema",
    summary="Estado integral del sistema de calidad/explicabilidad",
    description="Retorna flags activos, scorecards por dominio, alertas críticas y deuda residual bloque 05.",
)
async def get_estado_sistema():
    flags = estado_flags()

    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row):
            score_nba = obtener_scorecard_actual(conn, "NBA")
            score_fut = obtener_scorecard_actual(conn, "FUTBOL")
            alertas_crit_nba = obtener_alertas_activas(conn, domain="NBA", severidad_min="CRITICA")
            alertas_crit_fut = obtener_alertas_activas(conn, domain="FUTBOL", severidad_min="CRITICA")

    deuda_residual_b05 = {
        "confidence_parcial": True,
        "contratos_legacy_coexistentes": True,
        "drift_futbol_parcial_alto": True,
    }

    return {
        "exito": True,
        "feature_flags": flags,
        "scorecard_actual": {
            "NBA": score_nba,
            "FUTBOL": score_fut,
        },
        "alertas_criticas_activas": {
            "NBA": len(alertas_crit_nba),
            "FUTBOL": len(alertas_crit_fut),
        },
        "version_contrato": "1.0.0" if flag_activo(FEATURE_CONTRATO_EXPLICACION_V1) else "legacy",
        "deuda_residual_b05": deuda_residual_b05,
    }

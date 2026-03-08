# -*- coding: utf-8 -*-
"""Endpoints de calidad de datos."""

from __future__ import annotations

from fastapi import APIRouter, Query
from psycopg.rows import dict_row

from db import obtener_pool
from calidad.alertas import obtener_alertas_activas

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

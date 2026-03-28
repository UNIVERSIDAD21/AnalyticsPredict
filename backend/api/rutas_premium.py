# -*- coding: utf-8 -*-
"""Rutas premium con enforcement backend de tier (Fase E)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.pagos_store import PagosStore, obtener_pagos_store
from servicios.access_tiers import exigir_premium, resolver_tier, usuario_actual

router = APIRouter(prefix="/api/premium", tags=["Premium"])


@router.get("/capas-depth")
def obtener_capas_depth(
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = usuario_actual(authorization, auth_store)
    exigir_premium(user["id"], pagos_store)

    return {
        "ok": True,
        "data": {
            "tier": "PREMIUM",
            "depth_layers": [
                "comparativas_multi_mercado",
                "contexto_historico_extendido",
                "priorizacion_operativa_avanzada",
            ],
            "message": "Capas premium activas",
        },
    }


@router.get("/estado-tier")
def estado_tier(
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = usuario_actual(authorization, auth_store)
    tier = resolver_tier(user["id"], pagos_store)
    return {
        "ok": True,
        "data": {
            "tier": tier,
            "premium_active": tier == "PREMIUM",
        },
    }

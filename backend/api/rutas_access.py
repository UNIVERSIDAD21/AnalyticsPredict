# -*- coding: utf-8 -*-
"""Rutas de verificación de capacidad por tier (Fase E hardening extendido)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.pagos_store import PagosStore, obtener_pagos_store
from servicios.access_tiers import resolver_tier, usuario_actual

router = APIRouter(prefix="/api/access", tags=["Access"])

CAPABILITY_MIN_TIER = {
    "public.shell": "INVITADO",
    "public.center": "INVITADO",
    "public.governance": "INVITADO",
    "dashboard.personal": "BASE",
    "bitacora.personal": "BASE",
    "configuracion.base": "BASE",
    "analisis.nba.base": "BASE",
    "futbol.base": "BASE",
    "premium.depth": "PREMIUM",
    "chat.contextual": "BLOCKED",
}

RANK = {"INVITADO": 0, "BASE": 1, "PREMIUM": 2}


def _enabled_for_tier(capability: str, tier: str) -> bool:
    requerido = CAPABILITY_MIN_TIER.get(capability)
    if requerido is None:
        return False
    if requerido == "BLOCKED":
        return False
    return RANK[tier] >= RANK[requerido]


@router.get("/capability-check")
def capability_check(
    capability: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    user = usuario_actual(authorization, auth_store)
    tier = resolver_tier(user["id"], pagos_store)
    enabled = _enabled_for_tier(capability, tier)

    return {
        "ok": True,
        "data": {
            "capability": capability,
            "tier": tier,
            "enabled": enabled,
        },
    }

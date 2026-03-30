# -*- coding: utf-8 -*-
"""Rutas de verificación de capacidad por tier."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from servicios.auth_store import AuthStore, obtener_auth_store
from servicios.pagos_store import PagosStore, obtener_pagos_store
from servicios.access_tiers import resolver_tier, usuario_actual
from servicios.access_policy import CAPABILITY_MIN_TIER, CAPABILITIES_DESHABILITADAS, capability_existe, evaluar_capability

router = APIRouter(prefix="/api/access", tags=["Access"])


@router.get("/capability-check")
def capability_check(
    capability: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    auth_store: AuthStore = Depends(obtener_auth_store),
    pagos_store: PagosStore = Depends(obtener_pagos_store),
):
    if not capability_existe(capability):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAPABILITY_NOT_FOUND", "capability": capability},
        )

    user = usuario_actual(authorization, auth_store)
    tier = resolver_tier(user["id"], pagos_store)
    resultado = evaluar_capability(capability, tier)

    return {
        "ok": True,
        "data": {
            "capability": resultado.capability,
            "tier": resultado.tier_actual,
            "required_tier": resultado.tier_requerido,
            "enabled": resultado.enabled,
            "gate": resultado.gate.value if resultado.gate else None,
        },
    }


@router.get("/policy")
def access_policy():
    return {
        "ok": True,
        "data": {
            "capabilities": {
                capability: {
                    "required_tier": required_tier,
                    "disabled": False,
                }
                for capability, required_tier in CAPABILITY_MIN_TIER.items()
            }
            | {
                capability: {
                    "required_tier": None,
                    "disabled": True,
                }
                for capability in CAPABILITIES_DESHABILITADAS
            }
        },
    }

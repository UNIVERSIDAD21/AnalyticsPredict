# -*- coding: utf-8 -*-
"""Política central de capabilities y tiers para enforcement backend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

Tier = str  # INVITADO | BASE | PREMIUM


class TipoGate(str, Enum):
    BASE_REQUIRED = "BASE_REQUIRED"
    PREMIUM_REQUIRED = "PREMIUM_REQUIRED"
    DISABLED = "DISABLED"


RANK_TIER: dict[Tier, int] = {"INVITADO": 0, "BASE": 1, "PREMIUM": 2}


CAPABILITY_MIN_TIER: dict[str, Tier] = {
    "public.shell": "INVITADO",
    "public.center": "INVITADO",
    "public.governance": "INVITADO",
    "dashboard.personal": "BASE",
    "bitacora.personal": "BASE",
    "configuracion.base": "BASE",
    "analisis.nba.base": "BASE",
    "futbol.base": "BASE",
    "premium.depth": "PREMIUM",
}

CAPABILITIES_DESHABILITADAS: set[str] = {
    "chat.contextual",
}


@dataclass(frozen=True)
class ResultadoCapability:
    capability: str
    tier_actual: Tier
    tier_requerido: Tier | None
    enabled: bool
    gate: TipoGate | None


def capability_existe(capability: str) -> bool:
    return capability in CAPABILITY_MIN_TIER or capability in CAPABILITIES_DESHABILITADAS


def tier_requerido_capability(capability: str) -> Tier | None:
    return CAPABILITY_MIN_TIER.get(capability)


def capability_habilitada(capability: str, tier_actual: Tier) -> bool:
    requerido = tier_requerido_capability(capability)
    if not requerido:
        return False
    return RANK_TIER[tier_actual] >= RANK_TIER[requerido]


def tipo_gate(capability: str, tier_actual: Tier) -> TipoGate | None:
    if capability in CAPABILITIES_DESHABILITADAS:
        return TipoGate.DISABLED

    requerido = tier_requerido_capability(capability)
    if not requerido:
        return TipoGate.DISABLED

    if capability_habilitada(capability, tier_actual):
        return None

    if requerido == "BASE":
        return TipoGate.BASE_REQUIRED
    if requerido == "PREMIUM":
        return TipoGate.PREMIUM_REQUIRED

    return TipoGate.DISABLED


def evaluar_capability(capability: str, tier_actual: Tier) -> ResultadoCapability:
    requerido = tier_requerido_capability(capability)
    enabled = capability_habilitada(capability, tier_actual)
    gate = tipo_gate(capability, tier_actual)

    return ResultadoCapability(
        capability=capability,
        tier_actual=tier_actual,
        tier_requerido=requerido,
        enabled=enabled,
        gate=gate,
    )

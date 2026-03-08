# -*- coding: utf-8 -*-
"""Feature flags de rollout gradual para bloque 08."""

from __future__ import annotations

import os
from typing import Dict


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


FEATURE_CALIDAD_SCORECARD = "FEATURE_CALIDAD_SCORECARD"
FEATURE_ALERTAS_CALIDAD = "FEATURE_ALERTAS_CALIDAD"
FEATURE_CONTRATO_EXPLICACION_V1 = "FEATURE_CONTRATO_EXPLICACION_V1"
FEATURE_EXPLICABILIDAD_UI = "FEATURE_EXPLICABILIDAD_UI"

_ALL_FLAGS = {
    FEATURE_CALIDAD_SCORECARD: False,
    FEATURE_ALERTAS_CALIDAD: False,
    FEATURE_CONTRATO_EXPLICACION_V1: False,
    FEATURE_EXPLICABILIDAD_UI: False,
}


def flag_activo(nombre: str) -> bool:
    """Retorna estado de un flag (default false)."""
    if nombre not in _ALL_FLAGS:
        return False
    return _to_bool(os.getenv(nombre), default=_ALL_FLAGS[nombre])


def estado_flags() -> Dict[str, bool]:
    """Retorna todos los flags y su estado actual."""
    return {name: flag_activo(name) for name in _ALL_FLAGS}

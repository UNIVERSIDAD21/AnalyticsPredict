from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import math
import numpy as np


@dataclass(frozen=True)
class OutlierPolicy:
    enabled: bool = True
    min_n: int = 25
    p_low: float = 0.02
    p_high: float = 0.98


# Configuración estadística central del módulo fútbol
STATS_TEMPORAL_CONFIG: Dict[str, float] = {
    "fallback_window_days": 540,
    "recency_half_life_days": 180,
}

STATS_MIN_SAMPLE_CONFIG: Dict[str, int] = {
    "h2h_objetivo": 5,
    "local_home_objetivo": 25,
    "visitante_away_objetivo": 25,
}

STATS_OUTLIER_POLICY = OutlierPolicy(
    enabled=True,
    min_n=25,
    p_low=0.02,
    p_high=0.98,
)

# Distribución por familia de mercado (evita hardcodes dispersos)
DISTRIBUCION_POR_BASE: Dict[str, str] = {
    "corners": "nbinom",
    "goles": "poisson",
    "disparos": "nbinom",
    "disparos_arco": "nbinom",
}

# Partición temporal para disparos/tiros a puerta
STATS_PROB_CONFIG: Dict[str, float] = {
    "std_threshold_alto": 5.0,
    "std_threshold_medio": 3.0,
    "factor_conservador_alto": 0.85,
    "factor_conservador_medio": 0.92,
}

STATS_SHOTS_SPLIT_CONFIG: Dict[str, float] = {
    "default_ratio_1t": 0.45,
    "min_ratio_1t": 0.25,
    "max_ratio_1t": 0.75,
    "peso_corners": 0.65,
    "peso_goles": 0.35,
    "min_std_factor": 0.5,
}


def distribucion_para_mercado(mercado: str) -> str:
    mercado_u = str(mercado or "").upper()
    if mercado_u.startswith("CORNERS"):
        return DISTRIBUCION_POR_BASE["corners"]
    if mercado_u.startswith("GOLES"):
        return DISTRIBUCION_POR_BASE["goles"]
    if mercado_u.startswith("DISPAROS_ARCO"):
        return DISTRIBUCION_POR_BASE["disparos_arco"]
    if mercado_u.startswith("DISPAROS"):
        return DISTRIBUCION_POR_BASE["disparos"]
    return "normal"


def winsorizar_valores(
    valores: List[float],
    policy: OutlierPolicy = STATS_OUTLIER_POLICY,
) -> Tuple[List[float], Optional[float], Optional[float], bool]:
    if not policy.enabled or len(valores) < policy.min_n:
        return list(valores), None, None, False

    arr = np.array(valores, dtype=float)
    if arr.size == 0:
        return list(valores), None, None, False

    low = float(np.quantile(arr, policy.p_low))
    high = float(np.quantile(arr, policy.p_high))
    if not math.isfinite(low) or not math.isfinite(high) or low > high:
        return list(valores), None, None, False

    clipped = np.clip(arr, low, high)
    applied = bool(np.any(clipped != arr))
    return clipped.tolist(), low, high, applied


def estimar_ratio_tiempo_disparos(
    *,
    corners_1t_total: float,
    corners_2t_total: float,
    goles_1t_total: float,
    goles_2t_total: float,
) -> Dict[str, float]:
    cfg = STATS_SHOTS_SPLIT_CONFIG

    ratio_default = float(cfg["default_ratio_1t"])
    ratio_corners = ratio_default
    ratio_goles = ratio_default

    total_corners = max(float(corners_1t_total) + float(corners_2t_total), 0.0)
    if total_corners > 0:
        ratio_corners = float(corners_1t_total) / total_corners

    total_goles = max(float(goles_1t_total) + float(goles_2t_total), 0.0)
    if total_goles > 0:
        ratio_goles = float(goles_1t_total) / total_goles

    ratio_1t = (
        float(cfg["peso_corners"]) * ratio_corners
        + float(cfg["peso_goles"]) * ratio_goles
    )

    ratio_1t = float(max(cfg["min_ratio_1t"], min(cfg["max_ratio_1t"], ratio_1t)))
    ratio_2t = 1.0 - ratio_1t

    std_factor_1t = max(float(cfg["min_std_factor"]), math.sqrt(ratio_1t))
    std_factor_2t = max(float(cfg["min_std_factor"]), math.sqrt(ratio_2t))

    return {
        "ratio_1t": ratio_1t,
        "ratio_2t": ratio_2t,
        "std_factor_1t": float(std_factor_1t),
        "std_factor_2t": float(std_factor_2t),
    }

# -*- coding: utf-8 -*-
"""
log_loss.py — Log Loss estable para probabilidades binarias.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional


def calcular_log_loss(
    predicciones: Iterable[tuple[float, Optional[bool]]],
    *,
    eps: float = 1e-15,
) -> dict[str, float | int]:
    """
    Calcula el Log Loss para predicciones binarias.

    Reglas:
    - Excluye outcomes None (PUSH).
    - Valida que p esté en [0, 1].
    - Aplica clipping p = clip(p, eps, 1 - eps).

    Retorna:
    - log_loss: float
    - n: int
    - eps: float
    - p_min: float (post-clip)
    - p_max: float (post-clip)
    """
    if eps <= 0 or eps >= 0.5:
        raise ValueError("eps debe estar en (0, 0.5)")

    valores = []
    p_min = 1.0
    p_max = 0.0
    for p, outcome in predicciones:
        if outcome is None:
            continue
        if not 0.0 <= p <= 1.0:
            raise ValueError("p debe estar en el rango [0, 1]")
        p_clip = min(max(p, eps), 1.0 - eps)
        p_min = min(p_min, p_clip)
        p_max = max(p_max, p_clip)
        y = 1.0 if bool(outcome) else 0.0
        loss = -(y * math.log(p_clip) + (1.0 - y) * math.log(1.0 - p_clip))
        valores.append(loss)

    n = len(valores)
    log_loss = sum(valores) / n if n else 0.0
    if n == 0:
        p_min = 0.0
        p_max = 0.0
    return {
        "log_loss": log_loss,
        "n": n,
        "eps": float(eps),
        "p_min": p_min,
        "p_max": p_max,
    }

"""Definición canónica de Brier, Log Loss y ECE para outcomes binarios.

Escala de probabilidad [0, 1], ECE con diez bins fijos [0,.1), …, [.9,1],
Log Loss en nats con clipping numérico 1e-15. Sin pares válidos: None.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

EPS_LOG_LOSS = 1e-15
N_BINS_ECE = 10


def resumir_pares_binarios(
    pares: Iterable[tuple[Any, Any]], *, n_bins: int = N_BINS_ECE,
    eps_log_loss: float = EPS_LOG_LOSS,
) -> dict[str, float | int | None]:
    """Excluye pares incompletos/inválidos; informa n y exclusiones."""
    if n_bins < 1:
        raise ValueError("n_bins debe ser positivo")
    if not 0 < eps_log_loss < 0.5:
        raise ValueError("eps_log_loss debe estar en (0, 0.5)")

    validos: list[tuple[float, int]] = []
    excluidos = 0
    for probabilidad, outcome in pares:
        if probabilidad is None or outcome is None or outcome not in (0, 1, False, True):
            excluidos += 1
            continue
        try:
            p = float(probabilidad)
        except (TypeError, ValueError):
            excluidos += 1
            continue
        if not math.isfinite(p) or not 0 <= p <= 1:
            excluidos += 1
            continue
        validos.append((p, int(outcome)))

    n = len(validos)
    if n == 0:
        return {"n": 0, "n_excluidas": excluidos, "brier": None,
                "log_loss": None, "ece": None}

    brier = sum((p - y) ** 2 for p, y in validos) / n
    log_loss = -sum(
        y * math.log(min(1 - eps_log_loss, max(eps_log_loss, p)))
        + (1 - y) * math.log(min(1 - eps_log_loss, max(eps_log_loss, 1 - p)))
        for p, y in validos
    ) / n
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in validos:
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    ece = sum(
        len(bin_) / n * abs(
            sum(p for p, _ in bin_) / len(bin_) - sum(y for _, y in bin_) / len(bin_)
        )
        for bin_ in bins if bin_
    )
    return {"n": n, "n_excluidas": excluidos, "brier": brier,
            "log_loss": log_loss, "ece": ece}

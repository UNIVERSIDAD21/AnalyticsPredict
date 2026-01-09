# -*- coding: utf-8 -*-
"""
brier.py — Cálculo formal del Brier Score para probabilidades binarias.
"""

from __future__ import annotations

from typing import Iterable, Optional


def calcular_brier_score(
    predicciones: Iterable[tuple[float, Optional[bool]]],
) -> dict[str, float | int | str]:
    """
    Calcula el Brier Score para predicciones binarias.

    Reglas:
    - Excluye outcomes None (PUSH).
    - Valida que p esté en [0, 1].

    Retorna:
    - brier_score: float
    - n: int
    - interpretacion: str (opcional)
    """
    valores = []
    for p, outcome in predicciones:
        if outcome is None:
            continue
        if not 0.0 <= p <= 1.0:
            raise ValueError("p debe estar en el rango [0, 1]")
        y = 1.0 if bool(outcome) else 0.0
        valores.append((p - y) ** 2)

    n = len(valores)
    brier = sum(valores) / n if n else 0.0
    return {
        "brier_score": brier,
        "n": n,
        "interpretacion": _interpretar_brier(brier),
    }


def _interpretar_brier(brier_score: float) -> str:
    if brier_score < 0.1:
        return "excelente"
    if brier_score < 0.2:
        return "buena"
    if brier_score < 0.3:
        return "aceptable"
    return "pobre"

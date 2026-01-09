# -*- coding: utf-8 -*-
"""
ece.py — Expected Calibration Error (ECE) y Maximum Calibration Error (MCE).
"""

from __future__ import annotations

import math
from typing import Iterable, Optional


def calcular_ece(
    predicciones: Iterable[tuple[float, Optional[bool]]],
    *,
    n_bins: int = 10,
    tipo_bins: str = "fijos",
    min_por_bin: int = 10,
) -> dict[str, object]:
    """
    Calcula ECE/MCE para predicciones binarias.

    - Excluye outcomes None (PUSH).
    - Valida que p esté en [0, 1].
    - tipo_bins: "fijos" o "cuantiles".
    """
    if n_bins <= 0:
        raise ValueError("n_bins debe ser mayor que 0")
    if min_por_bin < 0:
        raise ValueError("min_por_bin no puede ser negativo")

    datos = []
    for p, outcome in predicciones:
        if outcome is None:
            continue
        if not 0.0 <= p <= 1.0:
            raise ValueError("p debe estar en el rango [0, 1]")
        y = 1.0 if bool(outcome) else 0.0
        datos.append((p, y))

    if tipo_bins == "fijos":
        bins = _bins_fijos(datos, n_bins=n_bins, min_por_bin=min_por_bin)
        metadatos = {"n_bins_solicitados": n_bins, "min_por_bin": min_por_bin}
    elif tipo_bins == "cuantiles":
        bins, bins_efectivos = _bins_cuantiles(
            datos, n_bins=n_bins, min_por_bin=min_por_bin
        )
        metadatos = {
            "n_bins_solicitados": n_bins,
            "bins_efectivos": bins_efectivos,
            "min_por_bin": min_por_bin,
        }
    else:
        raise ValueError("tipo_bins debe ser 'fijos' o 'cuantiles'")

    ece, mce, mce_suficiente, n_total = _resumen_bins(bins)

    return {
        "ece": ece,
        "mce": mce,
        "mce_suficiente": mce_suficiente,
        "n": n_total,
        "tipo_bins": tipo_bins,
        "n_bins": n_bins,
        "bins": bins,
        "metadatos": metadatos,
    }


def _bins_fijos(
    datos: list[tuple[float, float]],
    *,
    n_bins: int,
    min_por_bin: int,
) -> list[dict[str, object]]:
    bins = [
        {
            "bin_inicio": i / n_bins,
            "bin_fin": (i + 1) / n_bins,
            "n": 0,
            "avg_predicha": None,
            "frecuencia_real": None,
            "gap": None,
            "suficiente_data": False,
            "_p_suma": 0.0,
            "_y_suma": 0.0,
        }
        for i in range(n_bins)
    ]

    for p, y in datos:
        indice = min(int(p * n_bins), n_bins - 1)
        bins[indice]["n"] += 1
        bins[indice]["_p_suma"] += p
        bins[indice]["_y_suma"] += y

    for bin_info in bins:
        n = bin_info["n"]
        if n > 0:
            avg_predicha = bin_info["_p_suma"] / n
            frecuencia_real = bin_info["_y_suma"] / n
            gap = abs(avg_predicha - frecuencia_real)
            bin_info["avg_predicha"] = avg_predicha
            bin_info["frecuencia_real"] = frecuencia_real
            bin_info["gap"] = gap
            bin_info["suficiente_data"] = n >= min_por_bin
        del bin_info["_p_suma"]
        del bin_info["_y_suma"]

    return bins


def _bins_cuantiles(
    datos: list[tuple[float, float]],
    *,
    n_bins: int,
    min_por_bin: int,
) -> tuple[list[dict[str, object]], int]:
    if not datos:
        return [], 0

    ordenados = sorted(datos, key=lambda item: item[0])
    total = len(ordenados)
    objetivo = max(1, math.ceil(total / n_bins))
    bins = []
    inicio = 0
    while inicio < total:
        fin = min(inicio + objetivo, total)
        while fin < total and ordenados[fin - 1][0] == ordenados[fin][0]:
            fin += 1
        segmento = ordenados[inicio:fin]
        p_vals = [p for p, _ in segmento]
        y_vals = [y for _, y in segmento]
        n = len(segmento)
        avg_predicha = sum(p_vals) / n
        frecuencia_real = sum(y_vals) / n
        gap = abs(avg_predicha - frecuencia_real)
        bins.append(
            {
                "bin_inicio": min(p_vals),
                "bin_fin": max(p_vals),
                "n": n,
                "avg_predicha": avg_predicha,
                "frecuencia_real": frecuencia_real,
                "gap": gap,
                "suficiente_data": n >= min_por_bin,
            }
        )
        inicio = fin

    return bins, len(bins)


def _resumen_bins(
    bins: list[dict[str, object]],
) -> tuple[float, float, float, int]:
    n_total = sum(bin_info["n"] for bin_info in bins)
    if n_total == 0:
        return 0.0, 0.0, 0.0, 0

    ece = 0.0
    gaps = []
    gaps_suficientes = []
    for bin_info in bins:
        n = bin_info["n"]
        gap = bin_info["gap"]
        if n == 0 or gap is None:
            continue
        ece += (n / n_total) * gap
        gaps.append(gap)
        if bin_info["suficiente_data"]:
            gaps_suficientes.append(gap)

    mce = max(gaps) if gaps else 0.0
    mce_suficiente = max(gaps_suficientes) if gaps_suficientes else 0.0
    return ece, mce, mce_suficiente, n_total

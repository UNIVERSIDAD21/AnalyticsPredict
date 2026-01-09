# -*- coding: utf-8 -*-
"""
curva_calibracion.py — Cálculo de curva de calibración con bins.

Soporta dos modos:
- Bins fijos: rangos uniformes (0.0-0.1, 0.1-0.2, ...)
- Bins por cuantiles: cada bin con ~mismo número de muestras
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BinCalibracion:
    """Un bin de la curva de calibración."""

    rango_inicio: float
    rango_fin: float
    n: int
    probabilidad_promedio: float
    frecuencia_real: float
    gap: float
    gap_con_signo: float
    suficiente_data: bool
    advertencia: Optional[str] = None


@dataclass(frozen=True)
class ResultadoCurva:
    """Resultado completo del cálculo de curva."""

    bins: List[BinCalibracion]
    ece: float
    mce: float
    n_total: int
    bin_peor: Optional[str]


def calcular_curva_bins_fijos(
    predicciones: Sequence[Tuple[float, bool]],
    *,
    n_bins: int = 10,
    min_por_bin: int = 30,
) -> ResultadoCurva:
    """
    Calcula curva de calibración con bins de tamaño fijo.

    Args:
        predicciones: Lista de (p_predicha, outcome_binario).
        n_bins: Número de bins.
        min_por_bin: Mínimo de muestras para considerar bin confiable.
    """
    if n_bins <= 0:
        raise ValueError("n_bins debe ser mayor a 0")
    if min_por_bin < 0:
        raise ValueError("min_por_bin no puede ser negativo")

    if not predicciones:
        return ResultadoCurva(bins=[], ece=0.0, mce=0.0, n_total=0, bin_peor=None)

    step = 1.0 / n_bins
    bins_data: dict[int, list[Tuple[float, float]]] = {i: [] for i in range(n_bins)}

    for p, outcome in predicciones:
        p_clipped = max(0.0, min(1.0 - 1e-12, float(p)))
        bin_idx = min(int(p_clipped / step), n_bins - 1)
        bins_data[bin_idx].append((float(p), 1.0 if outcome else 0.0))

    bins_resultado: list[BinCalibracion] = []
    gaps_ponderados: list[float] = []
    max_gap = 0.0
    bin_peor = None

    for i in range(n_bins):
        rango_inicio = i * step
        rango_fin = (i + 1) * step
        datos_bin = bins_data[i]
        n = len(datos_bin)

        if n == 0:
            bins_resultado.append(
                BinCalibracion(
                    rango_inicio=rango_inicio,
                    rango_fin=rango_fin,
                    n=0,
                    probabilidad_promedio=0.0,
                    frecuencia_real=0.0,
                    gap=0.0,
                    gap_con_signo=0.0,
                    suficiente_data=False,
                    advertencia="Bin vacío",
                )
            )
            continue

        prob_promedio = sum(p for p, _ in datos_bin) / n
        freq_real = sum(o for _, o in datos_bin) / n
        gap = abs(prob_promedio - freq_real)
        gap_con_signo = prob_promedio - freq_real

        suficiente = n >= min_por_bin
        advertencia = None if suficiente else f"Solo {n} muestras (mínimo: {min_por_bin})"

        bins_resultado.append(
            BinCalibracion(
                rango_inicio=rango_inicio,
                rango_fin=rango_fin,
                n=n,
                probabilidad_promedio=prob_promedio,
                frecuencia_real=freq_real,
                gap=gap,
                gap_con_signo=gap_con_signo,
                suficiente_data=suficiente,
                advertencia=advertencia,
            )
        )

        gaps_ponderados.append(n * gap)
        if gap > max_gap:
            max_gap = gap
            bin_peor = f"{rango_inicio:.1f}-{rango_fin:.1f}"

    n_total = len(predicciones)
    ece = sum(gaps_ponderados) / n_total if n_total > 0 else 0.0

    return ResultadoCurva(
        bins=bins_resultado,
        ece=ece,
        mce=max_gap,
        n_total=n_total,
        bin_peor=bin_peor,
    )


def calcular_curva_bins_cuantiles(
    predicciones: Sequence[Tuple[float, bool]],
    *,
    n_bins: int = 10,
    min_por_bin: int = 30,
) -> ResultadoCurva:
    """
    Calcula curva de calibración con bins por cuantiles.

    Cada bin tiene aproximadamente el mismo número de predicciones.
    Útil cuando las probabilidades están concentradas.
    """
    if n_bins <= 0:
        raise ValueError("n_bins debe ser mayor a 0")
    if min_por_bin < 0:
        raise ValueError("min_por_bin no puede ser negativo")

    if not predicciones:
        return ResultadoCurva(bins=[], ece=0.0, mce=0.0, n_total=0, bin_peor=None)

    sorted_preds = sorted(predicciones, key=lambda x: x[0])
    n_total = len(sorted_preds)
    chunk_size = n_total // n_bins
    remainder = n_total % n_bins

    bins_resultado: list[BinCalibracion] = []
    gaps_ponderados: list[float] = []
    max_gap = 0.0
    bin_peor = None
    idx = 0

    for i in range(n_bins):
        current_size = chunk_size + (1 if i < remainder else 0)
        if current_size == 0:
            continue
        chunk = sorted_preds[idx : idx + current_size]
        idx += current_size

        probabilidades = [p for p, _ in chunk]
        outcomes = [1.0 if o else 0.0 for _, o in chunk]

        rango_inicio = min(probabilidades)
        rango_fin = max(probabilidades)
        n = len(chunk)
        prob_promedio = sum(probabilidades) / n
        freq_real = sum(outcomes) / n
        gap = abs(prob_promedio - freq_real)
        gap_con_signo = prob_promedio - freq_real

        suficiente = n >= min_por_bin
        advertencia = None if suficiente else f"Solo {n} muestras (mínimo: {min_por_bin})"

        bins_resultado.append(
            BinCalibracion(
                rango_inicio=rango_inicio,
                rango_fin=rango_fin,
                n=n,
                probabilidad_promedio=prob_promedio,
                frecuencia_real=freq_real,
                gap=gap,
                gap_con_signo=gap_con_signo,
                suficiente_data=suficiente,
                advertencia=advertencia,
            )
        )

        gaps_ponderados.append(n * gap)
        if gap > max_gap:
            max_gap = gap
            bin_peor = f"{rango_inicio:.2f}-{rango_fin:.2f}"

    ece = sum(gaps_ponderados) / n_total if n_total > 0 else 0.0

    return ResultadoCurva(
        bins=bins_resultado,
        ece=ece,
        mce=max_gap,
        n_total=n_total,
        bin_peor=bin_peor,
    )

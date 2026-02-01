# -*- coding: utf-8 -*-
"""
metricas_calibracion.py — Métricas para evaluar calidad de calibración.

Este módulo contiene funciones para calcular métricas de calibración
como Brier Score, Log Loss, ECE, MCE y datos para reliability diagrams.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple, Optional

import numpy as np

from ..tipos import DatosReliabilityDiagram


def calcular_brier_score(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
) -> float:
    """
    Calcula el Brier Score.

    El Brier Score mide la precisión de predicciones probabilísticas.

    Fórmula:
        BS = mean((prob - outcome)²)

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)

    Returns:
        Brier Score (0 = perfecto, 1 = peor)

    Raises:
        ValueError: Si los arrays tienen longitudes diferentes o valores inválidos
    """
    prob = np.asarray(probabilidades, dtype=float)
    out = np.asarray(outcomes, dtype=float)

    if len(prob) != len(out):
        raise ValueError(
            f"Los arrays deben tener la misma longitud: "
            f"probabilidades={len(prob)}, outcomes={len(out)}"
        )

    if len(prob) == 0:
        return 0.0

    # Validar rangos
    if np.any(prob < 0) or np.any(prob > 1):
        raise ValueError("Las probabilidades deben estar entre 0 y 1")

    if not np.all(np.isin(out, [0, 1])):
        raise ValueError("Los outcomes deben ser 0 o 1")

    return float(np.mean((prob - out) ** 2))


def calcular_log_loss(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
    epsilon: float = 1e-15,
) -> float:
    """
    Calcula el Log Loss (Logarithmic Loss / Cross-Entropy Loss).

    El Log Loss penaliza más fuertemente las predicciones muy equivocadas.

    Fórmula:
        LL = -mean(outcome * log(prob) + (1-outcome) * log(1-prob))

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)
        epsilon: Valor mínimo para evitar log(0)

    Returns:
        Log Loss (menor es mejor, 0 = perfecto)

    Raises:
        ValueError: Si los arrays tienen longitudes diferentes o valores inválidos
    """
    prob = np.asarray(probabilidades, dtype=float)
    out = np.asarray(outcomes, dtype=float)

    if len(prob) != len(out):
        raise ValueError(
            f"Los arrays deben tener la misma longitud: "
            f"probabilidades={len(prob)}, outcomes={len(out)}"
        )

    if len(prob) == 0:
        return 0.0

    # Clip para evitar log(0)
    prob_clipped = np.clip(prob, epsilon, 1 - epsilon)

    # Calcular log loss
    log_loss = -np.mean(
        out * np.log(prob_clipped) + (1 - out) * np.log(1 - prob_clipped)
    )

    return float(log_loss)


def calcular_ece(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Calcula el Expected Calibration Error (ECE).

    El ECE mide la diferencia promedio entre la confianza del modelo
    y la precisión real, ponderado por el tamaño de cada bin.

    Proceso:
        1. Dividir probabilidades en n_bins (ej: 0-0.1, 0.1-0.2, ...)
        2. Para cada bin: calcular |promedio_prob - frecuencia_real|
        3. ECE = promedio ponderado por tamaño de bin

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)
        n_bins: Número de bins para discretizar las probabilidades

    Returns:
        ECE (0 = calibración perfecta)

    Raises:
        ValueError: Si los arrays tienen longitudes diferentes
    """
    prob = np.asarray(probabilidades, dtype=float)
    out = np.asarray(outcomes, dtype=float)

    if len(prob) != len(out):
        raise ValueError(
            f"Los arrays deben tener la misma longitud: "
            f"probabilidades={len(prob)}, outcomes={len(out)}"
        )

    if len(prob) == 0:
        return 0.0

    n_total = len(prob)
    ece = 0.0

    # Definir bordes de bins
    bin_edges = np.linspace(0, 1, n_bins + 1)

    for i in range(n_bins):
        # Encontrar muestras en este bin
        in_bin = (prob > bin_edges[i]) & (prob <= bin_edges[i + 1])

        # Caso especial para el primer bin (incluir 0)
        if i == 0:
            in_bin = (prob >= bin_edges[i]) & (prob <= bin_edges[i + 1])

        n_in_bin = np.sum(in_bin)

        if n_in_bin > 0:
            # Promedio de probabilidades en el bin
            avg_prob = np.mean(prob[in_bin])
            # Frecuencia real de outcomes positivos en el bin
            avg_outcome = np.mean(out[in_bin])
            # Contribución al ECE ponderada por tamaño del bin
            ece += (n_in_bin / n_total) * abs(avg_prob - avg_outcome)

    return float(ece)


def calcular_mce(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> float:
    """
    Calcula el Maximum Calibration Error (MCE).

    El MCE es el máximo error de calibración sobre todos los bins.

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)
        n_bins: Número de bins para discretizar las probabilidades

    Returns:
        MCE (0 = calibración perfecta)

    Raises:
        ValueError: Si los arrays tienen longitudes diferentes
    """
    prob = np.asarray(probabilidades, dtype=float)
    out = np.asarray(outcomes, dtype=float)

    if len(prob) != len(out):
        raise ValueError(
            f"Los arrays deben tener la misma longitud: "
            f"probabilidades={len(prob)}, outcomes={len(out)}"
        )

    if len(prob) == 0:
        return 0.0

    mce = 0.0

    # Definir bordes de bins
    bin_edges = np.linspace(0, 1, n_bins + 1)

    for i in range(n_bins):
        # Encontrar muestras en este bin
        in_bin = (prob > bin_edges[i]) & (prob <= bin_edges[i + 1])

        # Caso especial para el primer bin (incluir 0)
        if i == 0:
            in_bin = (prob >= bin_edges[i]) & (prob <= bin_edges[i + 1])

        n_in_bin = np.sum(in_bin)

        if n_in_bin > 0:
            # Promedio de probabilidades en el bin
            avg_prob = np.mean(prob[in_bin])
            # Frecuencia real de outcomes positivos en el bin
            avg_outcome = np.mean(out[in_bin])
            # Actualizar máximo error
            mce = max(mce, abs(avg_prob - avg_outcome))

    return float(mce)


def generar_reliability_diagram(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> DatosReliabilityDiagram:
    """
    Genera datos para un diagrama de confiabilidad (reliability diagram).

    Un reliability diagram compara las probabilidades predichas contra
    la frecuencia real de ocurrencia del evento.

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)
        n_bins: Número de bins para discretizar las probabilidades

    Returns:
        DatosReliabilityDiagram con información de cada bin

    Raises:
        ValueError: Si los arrays tienen longitudes diferentes
    """
    prob = np.asarray(probabilidades, dtype=float)
    out = np.asarray(outcomes, dtype=float)

    if len(prob) != len(out):
        raise ValueError(
            f"Los arrays deben tener la misma longitud: "
            f"probabilidades={len(prob)}, outcomes={len(out)}"
        )

    bins: List[Tuple[float, float]] = []
    frecuencia_predicha: List[float] = []
    frecuencia_real: List[float] = []
    conteo: List[int] = []

    # Definir bordes de bins
    bin_edges = np.linspace(0, 1, n_bins + 1)

    for i in range(n_bins):
        inicio = bin_edges[i]
        fin = bin_edges[i + 1]
        bins.append((float(inicio), float(fin)))

        # Encontrar muestras en este bin
        in_bin = (prob > inicio) & (prob <= fin)

        # Caso especial para el primer bin (incluir 0)
        if i == 0:
            in_bin = (prob >= inicio) & (prob <= fin)

        n_in_bin = int(np.sum(in_bin))
        conteo.append(n_in_bin)

        if n_in_bin > 0:
            frecuencia_predicha.append(float(np.mean(prob[in_bin])))
            frecuencia_real.append(float(np.mean(out[in_bin])))
        else:
            # Para bins vacíos, usar el centro del bin
            frecuencia_predicha.append((inicio + fin) / 2)
            frecuencia_real.append(0.0)

    return DatosReliabilityDiagram(
        bins=bins,
        frecuencia_predicha=frecuencia_predicha,
        frecuencia_real=frecuencia_real,
        conteo=conteo,
    )


def calcular_metricas_completas(
    probabilidades: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, float]:
    """
    Calcula todas las métricas de calibración.

    Args:
        probabilidades: Array de probabilidades predichas (0 a 1)
        outcomes: Array de resultados reales (0 o 1)
        n_bins: Número de bins para ECE y MCE

    Returns:
        Diccionario con todas las métricas:
        - brier_score
        - log_loss
        - ece
        - mce
        - n_muestras
    """
    return {
        "brier_score": calcular_brier_score(probabilidades, outcomes),
        "log_loss": calcular_log_loss(probabilidades, outcomes),
        "ece": calcular_ece(probabilidades, outcomes, n_bins),
        "mce": calcular_mce(probabilidades, outcomes, n_bins),
        "n_muestras": len(probabilidades),
    }


def comparar_calibracion(
    prob_antes: np.ndarray,
    prob_despues: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, Dict[str, float]]:
    """
    Compara métricas de calibración antes y después de calibrar.

    Args:
        prob_antes: Probabilidades sin calibrar
        prob_despues: Probabilidades calibradas
        outcomes: Resultados reales

    Returns:
        Diccionario con métricas 'antes', 'despues' y 'mejora_porcentual'
    """
    metricas_antes = calcular_metricas_completas(prob_antes, outcomes, n_bins)
    metricas_despues = calcular_metricas_completas(prob_despues, outcomes, n_bins)

    mejora = {}
    for metrica in ["brier_score", "log_loss", "ece", "mce"]:
        antes = metricas_antes[metrica]
        despues = metricas_despues[metrica]
        if antes > 0:
            mejora[metrica] = (antes - despues) / antes * 100
        else:
            mejora[metrica] = 0.0

    return {
        "antes": metricas_antes,
        "despues": metricas_despues,
        "mejora_porcentual": mejora,
    }

"""Matemática legacy del análisis contextual, separada de HTTP y acceso a datos.

Extracción sin cambio numérico de normal/Poisson/NB y 1X2 Dixon-Coles. Estos
estimadores ya existían: no son un nuevo modelo ni una mejora de eficacia.
Conserva sus aproximaciones, truncamientos y límites; no corrige automáticamente
push, calibración, parámetros por competición o soporte de las colas.
"""
from __future__ import annotations

import numpy as np
from scipy import stats



def _tau_dixon_coles(x: int, y: int, lambda_local: float, lambda_visitante: float, rho: float) -> float:
    """Factor tau de Dixon-Coles para corregir correlación en marcadores bajos."""
    if x == 0 and y == 0:
        return max(0.01, 1.0 - (lambda_local * lambda_visitante * rho))
    if x == 0 and y == 1:
        return max(0.01, 1.0 + (lambda_local * rho))
    if x == 1 and y == 0:
        return max(0.01, 1.0 + (lambda_visitante * rho))
    if x == 1 and y == 1:
        return max(0.01, 1.0 - rho)
    return 1.0

def _calcular_1x2_dixon_coles(
    goles_local: float,
    goles_visitante: float,
    max_goles: int = 10,
    rho: float = -0.06,
) -> tuple[float, float, float, str]:
    """Calcula probabilidades 1X2 con Poisson corregido por Dixon-Coles."""
    lambda_local = max(goles_local, 0.05)
    lambda_visitante = max(goles_visitante, 0.05)

    pl = np.array([stats.poisson.pmf(i, lambda_local) for i in range(max_goles + 1)])
    pv = np.array([stats.poisson.pmf(i, lambda_visitante) for i in range(max_goles + 1)])
    matriz = np.outer(pl, pv)

    # Corrección Dixon-Coles en marcadores bajos
    for x in range(min(2, max_goles + 1)):
        for y in range(min(2, max_goles + 1)):
            matriz[x, y] *= _tau_dixon_coles(x, y, lambda_local, lambda_visitante, rho)

    # Renormalizar
    total_prob = float(matriz.sum())
    if total_prob > 0:
        matriz = matriz / total_prob

    prob_local = float(np.tril(matriz, -1).sum())
    prob_empate = float(np.trace(matriz))
    prob_visitante = float(np.triu(matriz, 1).sum())

    total = prob_local + prob_empate + prob_visitante
    if total > 0:
        prob_local, prob_empate, prob_visitante = prob_local / total, prob_empate / total, prob_visitante / total

    score_idx = np.unravel_index(np.argmax(matriz), matriz.shape)
    marcador = f"{score_idx[0]}-{score_idx[1]}"
    return prob_local, prob_empate, prob_visitante, marcador

def _calcular_probabilidad_over_normal(media: float, std: float, linea: float) -> float:
    """Calcula P(over) usando distribución normal."""
    if std <= 0:
        std = 1.0
    z = (linea - media) / std
    return 1.0 - stats.norm.cdf(z)

def _calcular_probabilidad_over_poisson(media: float, linea: float) -> float:
    """Calcula P(over) para conteos discretos usando Poisson."""
    lam = max(float(media), 0.05)
    k = int(np.floor(linea))
    return float(1.0 - stats.poisson.cdf(k, lam))

def _calcular_probabilidad_over_nbinom(media: float, std: float, linea: float) -> float:
    """Calcula P(over) usando Negative Binomial ajustada por media y varianza."""
    mu = max(float(media), 0.05)
    var = max(float(std) ** 2, mu + 1e-6)

    # Si no hay sobredispersión suficiente, volver a Poisson
    if var <= mu + 1e-6:
        return _calcular_probabilidad_over_poisson(mu, linea)

    r = (mu ** 2) / (var - mu)
    r = max(r, 1e-3)
    p = r / (r + mu)
    p = float(min(max(p, 1e-6), 1.0 - 1e-6))
    k = int(np.floor(linea))
    return float(1.0 - stats.nbinom.cdf(k, r, p))

def _calcular_probabilidad_over(
    media: float,
    std: float,
    linea: float,
    distribucion: str = "normal",
) -> float:
    """Calcula P(over) según la distribución configurada para el mercado."""
    dist = str(distribucion or "normal").lower()
    if dist == "poisson":
        return _calcular_probabilidad_over_poisson(media, linea)
    if dist in {"nbinom", "negative_binomial", "neg_binomial"}:
        return _calcular_probabilidad_over_nbinom(media, std, linea)
    return _calcular_probabilidad_over_normal(media, std, linea)

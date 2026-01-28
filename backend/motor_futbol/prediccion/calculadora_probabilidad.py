# -*- coding: utf-8 -*-
"""
calculadora_probabilidad.py — Funciones matemáticas para cálculos probabilísticos.

Este módulo contiene funciones para convertir predicciones de media/std
en probabilidades y calcular métricas relacionadas.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple, Optional


class CalculadoraProbabilidad:
    """
    Calculadora de probabilidades para apuestas deportivas.

    Contiene métodos estáticos para:
    - Calcular P(X > línea) usando distribución normal
    - Calcular intervalos de confianza
    - Calcular valor esperado y criterio de Kelly
    """

    @staticmethod
    def cdf_normal(z: float) -> float:
        """
        Función de distribución acumulativa de la normal estándar.

        Args:
            z: Valor z-score

        Returns:
            P(Z ≤ z)
        """
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    @staticmethod
    def prob_over(media: float, std: float, linea: float) -> float:
        """
        Calcula P(X > línea) asumiendo distribución normal.

        Fórmula:
        P(X > línea) = 1 - Φ((línea - μ) / σ)

        Args:
            media: Media predicha
            std: Desviación estándar
            linea: Valor de la línea de apuesta

        Returns:
            Probabilidad de superar la línea
        """
        std = max(float(std), 1e-9)  # Evitar división por cero
        z = (linea - media) / std
        return 1.0 - CalculadoraProbabilidad.cdf_normal(z)

    @staticmethod
    def prob_under(media: float, std: float, linea: float) -> float:
        """
        Calcula P(X < línea).

        Args:
            media: Media predicha
            std: Desviación estándar
            linea: Valor de la línea

        Returns:
            Probabilidad de estar bajo la línea
        """
        std = max(float(std), 1e-9)
        z = (linea - media) / std
        return CalculadoraProbabilidad.cdf_normal(z)

    @staticmethod
    def intervalo_confianza(
        media: float,
        std: float,
        nivel: float = 0.90,
    ) -> Tuple[float, float]:
        """
        Calcula intervalo de confianza bilateral.

        Fórmula:
        IC = [μ - z_{α/2} × σ, μ + z_{α/2} × σ]

        Args:
            media: Media de la predicción
            std: Desviación estándar
            nivel: Nivel de confianza (0.90 = 90%)

        Returns:
            Tupla (límite_inferior, límite_superior)
        """
        # Valores z para niveles comunes
        z_valores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576,
            0.80: 1.28,
        }

        z = z_valores.get(nivel, 1.645)
        margen = z * std

        return (media - margen, media + margen)

    @staticmethod
    def probabilidades_lineas(
        media: float,
        std: float,
        lineas: List[float],
    ) -> Dict[str, float]:
        """
        Calcula probabilidades para múltiples líneas.

        Args:
            media: Media predicha
            std: Desviación estándar
            lineas: Lista de líneas a calcular

        Returns:
            Dict con {"over_X.X": prob, "under_X.X": prob, ...}
        """
        resultado = {}

        for linea in lineas:
            prob_over = CalculadoraProbabilidad.prob_over(media, std, linea)
            prob_under = 1.0 - prob_over

            resultado[f"over_{linea}"] = round(prob_over, 4)
            resultado[f"under_{linea}"] = round(prob_under, 4)

        return resultado

    @staticmethod
    def cuota_justa(probabilidad: float) -> float:
        """
        Calcula cuota justa (sin margen) para una probabilidad.

        Args:
            probabilidad: Probabilidad del evento

        Returns:
            Cuota decimal justa
        """
        if probabilidad <= 0:
            return float("inf")
        if probabilidad >= 1:
            return 1.0
        return 1.0 / probabilidad

    @staticmethod
    def probabilidad_implicita(cuota: float) -> float:
        """
        Calcula probabilidad implícita de una cuota.

        Args:
            cuota: Cuota decimal

        Returns:
            Probabilidad implícita
        """
        if cuota <= 0:
            return 0.0
        return 1.0 / cuota

    @staticmethod
    def valor_esperado(
        probabilidad: float,
        cuota_ofrecida: float,
    ) -> float:
        """
        Calcula valor esperado de una apuesta.

        Fórmula:
        EV = (prob × cuota) - 1

        Args:
            probabilidad: Probabilidad estimada del sistema
            cuota_ofrecida: Cuota ofrecida por la casa

        Returns:
            Valor esperado (-1 a infinito)
        """
        return (probabilidad * cuota_ofrecida) - 1.0

    @staticmethod
    def edge(
        probabilidad_modelo: float,
        cuota_ofrecida: float,
    ) -> float:
        """
        Calcula el edge (ventaja) sobre la casa.

        Args:
            probabilidad_modelo: Probabilidad estimada
            cuota_ofrecida: Cuota ofrecida

        Returns:
            Edge como diferencia de probabilidades
        """
        prob_implicita = CalculadoraProbabilidad.probabilidad_implicita(cuota_ofrecida)
        return probabilidad_modelo - prob_implicita

    @staticmethod
    def kelly_criterion(
        probabilidad: float,
        cuota: float,
        fraccion: float = 0.25,
    ) -> float:
        """
        Calcula fracción de Kelly para sizing de apuesta.

        Fórmula Kelly completa:
        f* = (p × (cuota-1) - (1-p)) / (cuota-1)

        Kelly fraccional = f* × fracción

        Args:
            probabilidad: Probabilidad estimada
            cuota: Cuota decimal
            fraccion: Fracción de Kelly (0.25 = quarter Kelly)

        Returns:
            Fracción del bankroll a apostar
        """
        if cuota <= 1.0 or probabilidad <= 0 or probabilidad >= 1:
            return 0.0

        b = cuota - 1.0  # Odds to 1
        p = probabilidad
        q = 1.0 - p

        kelly_full = (b * p - q) / b

        if kelly_full <= 0:
            return 0.0

        return kelly_full * fraccion

    @staticmethod
    def distancia_z(media: float, std: float, linea: float) -> float:
        """
        Calcula la distancia en desviaciones estándar de la media a la línea.

        Args:
            media: Media predicha
            std: Desviación estándar
            linea: Línea a evaluar

        Returns:
            Número de desviaciones estándar
        """
        std = max(float(std), 1e-9)
        return abs(media - linea) / std

    @staticmethod
    def percentil(media: float, std: float, valor: float) -> float:
        """
        Calcula en qué percentil cae un valor dado.

        Args:
            media: Media de la distribución
            std: Desviación estándar
            valor: Valor a evaluar

        Returns:
            Percentil (0 a 1)
        """
        std = max(float(std), 1e-9)
        z = (valor - media) / std
        return CalculadoraProbabilidad.cdf_normal(z)

    @staticmethod
    def valor_en_percentil(media: float, std: float, percentil: float) -> float:
        """
        Calcula el valor correspondiente a un percentil dado.

        Usa aproximación inversa de la CDF normal.

        Args:
            media: Media de la distribución
            std: Desviación estándar
            percentil: Percentil deseado (0 a 1)

        Returns:
            Valor correspondiente
        """
        # Aproximación de la función inversa de la CDF normal
        # Usando la aproximación de Abramowitz and Stegun
        if percentil <= 0:
            return media - 5 * std
        if percentil >= 1:
            return media + 5 * std

        # Transformar a z-score
        t = math.sqrt(-2.0 * math.log(1.0 - percentil if percentil < 0.5 else percentil))

        c0 = 2.515517
        c1 = 0.802853
        c2 = 0.010328
        d1 = 1.432788
        d2 = 0.189269
        d3 = 0.001308

        z = t - (c0 + c1*t + c2*t*t) / (1.0 + d1*t + d2*t*t + d3*t*t*t)

        if percentil < 0.5:
            z = -z

        return media + z * std

    @staticmethod
    def calcular_overround(cuota_over: float, cuota_under: float) -> float:
        """
        Calcula el overround (vig) de un mercado.

        Args:
            cuota_over: Cuota para over
            cuota_under: Cuota para under

        Returns:
            Overround (>1.0 indica margen de la casa)
        """
        if cuota_over <= 0 or cuota_under <= 0:
            return 0.0

        prob_over = 1.0 / cuota_over
        prob_under = 1.0 / cuota_under

        return prob_over + prob_under

    @staticmethod
    def cuotas_justas(
        cuota_over: float,
        cuota_under: float,
    ) -> Tuple[float, float]:
        """
        Elimina el vig y calcula cuotas justas.

        Args:
            cuota_over: Cuota original para over
            cuota_under: Cuota original para under

        Returns:
            Tupla (cuota_justa_over, cuota_justa_under)
        """
        overround = CalculadoraProbabilidad.calcular_overround(cuota_over, cuota_under)

        if overround <= 0:
            return (cuota_over, cuota_under)

        prob_over = (1.0 / cuota_over) / overround
        prob_under = (1.0 / cuota_under) / overround

        cuota_justa_over = 1.0 / prob_over if prob_over > 0 else cuota_over
        cuota_justa_under = 1.0 / prob_under if prob_under > 0 else cuota_under

        return (cuota_justa_over, cuota_justa_under)

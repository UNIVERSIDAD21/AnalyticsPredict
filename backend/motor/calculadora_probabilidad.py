# -*- coding: utf-8 -*-
"""
calculadora_probabilidad.py — Funciones matemáticas para el motor.
"""

from __future__ import annotations

import math
from typing import Tuple, Optional, List

from motor.tipos import DatosDeVig


def cdf_normal(z: float) -> float:
    """Función de distribución acumulativa de la normal estándar."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def calcular_probabilidad_over(media: float, desviacion: float, linea: float) -> float:
    """Calcula la probabilidad de que el total supere la línea."""
    desviacion = max(float(desviacion), 1e-9)
    z = (linea - media) / desviacion
    return 1.0 - cdf_normal(z)


def calcular_probabilidad_victoria(
    media_equipo: float,
    desviacion_equipo: float,
    media_rival: float,
    desviacion_rival: float,
) -> float:
    """Calcula la probabilidad de victoria del equipo en el cuarto."""
    diferencia_media = float(media_equipo) - float(media_rival)
    desviacion_diferencia = math.sqrt(float(desviacion_equipo) ** 2 + float(desviacion_rival) ** 2)
    desviacion_diferencia = max(desviacion_diferencia, 1e-9)
    return cdf_normal(diferencia_media / desviacion_diferencia)


def calcular_intervalo_confianza(
    media: float,
    desviacion: float,
    z: float = 1.0
) -> Tuple[float, float]:
    """Calcula un intervalo de confianza simétrico."""
    margen = z * desviacion
    return media - margen, media + margen


def calcular_devig(
    cuota_lado_a: float,
    cuota_lado_b: Optional[float] = None,
    modo_estimado: bool = False,
    overround_estimado: float = 1.045,
) -> DatosDeVig:
    """Calcula probabilidades de mercado ajustadas por vig."""
    if cuota_lado_a <= 0:
        raise ValueError("cuota_lado_a debe ser mayor a 0.")

    p_mkt_raw = 1.0 / float(cuota_lado_a)
    advertencias: List[str] = []

    if cuota_lado_b is not None:
        if cuota_lado_b <= 0:
            raise ValueError("cuota_lado_b debe ser mayor a 0.")

        p_raw_b = 1.0 / float(cuota_lado_b)
        overround = p_mkt_raw + p_raw_b
        p_mkt_fair = p_mkt_raw / overround

        if overround < 1.0:
            advertencias.append(
                "Overround < 1.0: posible arbitraje o datos erróneos."
            )
        elif overround > 1.10:
            advertencias.append(
                "Overround > 1.10: cuotas atípicas o error de captura."
            )

        return DatosDeVig(
            metodo="exacto",
            overround=overround,
            p_mkt_raw=p_mkt_raw,
            p_mkt_fair=p_mkt_fair,
            advertencias=advertencias,
        )

    if modo_estimado:
        if overround_estimado <= 0:
            raise ValueError("overround_estimado debe ser mayor a 0.")

        p_mkt_fair = p_mkt_raw / overround_estimado
        advertencias.extend(
            [
                "De-vig estimado: falta cuota del otro lado.",
                "Penalizar sizing/score porque es una aproximación.",
            ]
        )

        return DatosDeVig(
            metodo="estimado",
            overround=overround_estimado,
            p_mkt_raw=p_mkt_raw,
            p_mkt_fair=p_mkt_fair,
            advertencias=advertencias,
        )

    advertencias.append(
        "Falta cuota del otro lado, no se puede de-vig exacto."
    )
    return DatosDeVig(
        metodo="no_aplicado",
        overround=None,
        p_mkt_raw=p_mkt_raw,
        p_mkt_fair=p_mkt_raw,
        advertencias=advertencias,
    )

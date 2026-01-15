# -*- coding: utf-8 -*-
"""
calculadora_probabilidad.py — Funciones matemáticas para el motor.
"""

from __future__ import annotations

import math
from typing import Tuple, Optional, List

from motor.tipos import ConfiguracionSizing, DatosDeVig, ResultadoSizing


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


def calcular_kelly(
    probabilidad: float,
    cuota: float,
    config: ConfiguracionSizing,
    datos_devig: DatosDeVig,
    riesgo_alto: bool = False,
) -> ResultadoSizing:
    """Calcula sizing con Kelly fraccional, penalizaciones y caps."""
    if cuota <= 1.0:
        raise ValueError("cuota debe ser mayor a 1.0 para calcular Kelly.")
    if not (0.0 <= probabilidad <= 1.0):
        raise ValueError("probabilidad debe estar entre 0 y 1.")

    advertencias = list(config.advertencias)
    penalizaciones: dict[str, float] = {}

    b = float(cuota) - 1.0
    p = float(probabilidad)
    q = 1.0 - p
    kelly_full = (b * p - q) / b

    bankroll = config.bankroll
    perfil_riesgo = config.perfil_riesgo

    if kelly_full <= 0:
        advertencias.append("Kelly <= 0: no apostar.")
        penalizaciones["kelly_negativo"] = 1.0
        stake_monto = 0.0 if bankroll is not None else None
        return ResultadoSizing(
            kelly_full=kelly_full,
            kelly_fraccional=0.0,
            fraccion_kelly=0.0,
            stake=stake_monto,
            stake_porcentaje=0.0,
            bankroll_momento=bankroll,
            perfil_riesgo_usado=perfil_riesgo,
            advertencias=advertencias,
            penalizaciones=penalizaciones,
            aplicaron_caps=False,
        )

    if perfil_riesgo.value == "CONSERVADOR":
        fraccion_base = config.fraccion_kelly_conservador
    elif perfil_riesgo.value == "MEDIO":
        fraccion_base = config.fraccion_kelly_medio
    else:
        fraccion_base = config.fraccion_kelly_agresivo

    multiplicador = 1.0
    if datos_devig.metodo == "estimado":
        multiplicador *= 0.5
        penalizaciones["devig_estimado"] = 0.5
        advertencias.append("De-vig estimado: stake penalizado.")
    elif datos_devig.metodo == "no_aplicado":
        multiplicador *= 0.3
        penalizaciones["devig_no_aplicado"] = 0.3
        advertencias.append("Sin devig: stake penalizado.")

    if riesgo_alto:
        multiplicador *= 0.7
        penalizaciones["riesgo_alto"] = 0.7
        advertencias.append("Riesgo alto: desviación alta.")

    kelly_pre_cap = kelly_full * fraccion_base * multiplicador
    aplicaron_caps = False

    kelly_fraccional = kelly_pre_cap
    if config.cap_diario and kelly_fraccional > config.cap_diario:
        kelly_fraccional = config.cap_diario
        aplicaron_caps = True
        advertencias.append("Cap diario aplicado.")

    if config.cap_por_apuesta and kelly_fraccional > config.cap_por_apuesta:
        kelly_fraccional = config.cap_por_apuesta
        aplicaron_caps = True
        advertencias.append("Cap por apuesta aplicado.")

    stake_porcentaje = kelly_fraccional * 100.0
    stake_monto = None
    if bankroll is not None:
        stake_monto = bankroll * kelly_fraccional
        if 0 < stake_monto < config.stake_minimo:
            advertencias.append("Stake por debajo del mínimo configurado.")

    fraccion_kelly = kelly_fraccional / kelly_full if kelly_full > 0 else 0.0

    return ResultadoSizing(
        kelly_full=kelly_full,
        kelly_fraccional=kelly_fraccional,
        fraccion_kelly=fraccion_kelly,
        stake=stake_monto,
        stake_porcentaje=stake_porcentaje,
        bankroll_momento=bankroll,
        perfil_riesgo_usado=perfil_riesgo,
        advertencias=advertencias,
        penalizaciones=penalizaciones,
        aplicaron_caps=aplicaron_caps,
    )

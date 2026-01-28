# -*- coding: utf-8 -*-
"""
goles.py — Modelo de predicción de goles.

Este módulo implementa el modelo específico para predicción de goles,
incluyendo el cálculo de mercados derivados.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Tuple, Any

from .base import ModeloPrediccionBase
from ..tipos import TipoModelo, TipoMercadoFutbol, PrediccionMercado
from ..constantes import TARGETS_GOLES, LINEAS_GOLES
from ..excepciones import ModeloNoEntrenado

logger = logging.getLogger(__name__)


class ModeloGoles(ModeloPrediccionBase):
    """
    Modelo de predicción de goles.

    Predice 4 targets básicos:
    - goles_local_1t
    - goles_local_2t
    - goles_visitante_1t
    - goles_visitante_2t

    Y calcula 5 mercados derivados:
    - GOLES_1T (local_1t + visitante_1t)
    - GOLES_2T (local_2t + visitante_2t)
    - GOLES_LOCAL_FT (local_1t + local_2t)
    - GOLES_VISITANTE_FT (visitante_1t + visitante_2t)
    - GOLES_FT (suma de los 4)
    """

    def __init__(self):
        """Inicializa el modelo de goles."""
        super().__init__(
            tipo=TipoModelo.GOLES,
            targets=TARGETS_GOLES,
        )

    def predecir_completo(
        self,
        equipo: str,
        rival: str,
        es_local: bool = True,
    ) -> Dict[str, PrediccionMercado]:
        """
        Genera predicciones para los 9 mercados de goles.

        Args:
            equipo: Nombre del equipo local
            rival: Nombre del equipo visitante
            es_local: True si equipo es local

        Returns:
            Dict con PrediccionMercado para cada mercado
        """
        if not self.entrenado:
            raise ModeloNoEntrenado(self.tipo.value)

        # Obtener predicciones base
        pred_targets = self.predecir_partido(equipo, rival, es_local)

        # Extraer predicciones de targets básicos
        local_1t = pred_targets.get("goles_local_1t", (0.6, 0.8))
        local_2t = pred_targets.get("goles_local_2t", (0.7, 0.9))
        visitante_1t = pred_targets.get("goles_visitante_1t", (0.5, 0.7))
        visitante_2t = pred_targets.get("goles_visitante_2t", (0.6, 0.8))

        # Calcular mercados derivados
        mercados_derivados = self._calcular_mercados_derivados(
            local_1t, local_2t, visitante_1t, visitante_2t
        )

        # Construir predicciones para todos los mercados
        resultados = {}

        # Mercados básicos
        resultados[TipoMercadoFutbol.GOLES_LOCAL_1T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.GOLES_LOCAL_1T, local_1t[0], local_1t[1]
        )
        resultados[TipoMercadoFutbol.GOLES_LOCAL_2T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.GOLES_LOCAL_2T, local_2t[0], local_2t[1]
        )
        resultados[TipoMercadoFutbol.GOLES_VISITANTE_1T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.GOLES_VISITANTE_1T, visitante_1t[0], visitante_1t[1]
        )
        resultados[TipoMercadoFutbol.GOLES_VISITANTE_2T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.GOLES_VISITANTE_2T, visitante_2t[0], visitante_2t[1]
        )

        # Mercados derivados
        for mercado, (media, std) in mercados_derivados.items():
            resultados[mercado.value] = self._crear_prediccion_mercado(mercado, media, std)

        return resultados

    def _calcular_mercados_derivados(
        self,
        local_1t: Tuple[float, float],
        local_2t: Tuple[float, float],
        visitante_1t: Tuple[float, float],
        visitante_2t: Tuple[float, float],
    ) -> Dict[TipoMercadoFutbol, Tuple[float, float]]:
        """Calcula mercados derivados a partir de los targets básicos."""
        derivados = {}

        # GOLES_1T = local_1t + visitante_1t
        media_1t = local_1t[0] + visitante_1t[0]
        std_1t = math.sqrt(local_1t[1]**2 + visitante_1t[1]**2)
        derivados[TipoMercadoFutbol.GOLES_1T] = (media_1t, std_1t)

        # GOLES_2T = local_2t + visitante_2t
        media_2t = local_2t[0] + visitante_2t[0]
        std_2t = math.sqrt(local_2t[1]**2 + visitante_2t[1]**2)
        derivados[TipoMercadoFutbol.GOLES_2T] = (media_2t, std_2t)

        # GOLES_LOCAL_FT = local_1t + local_2t
        media_local_ft = local_1t[0] + local_2t[0]
        std_local_ft = math.sqrt(local_1t[1]**2 + local_2t[1]**2)
        derivados[TipoMercadoFutbol.GOLES_LOCAL_FT] = (media_local_ft, std_local_ft)

        # GOLES_VISITANTE_FT = visitante_1t + visitante_2t
        media_visitante_ft = visitante_1t[0] + visitante_2t[0]
        std_visitante_ft = math.sqrt(visitante_1t[1]**2 + visitante_2t[1]**2)
        derivados[TipoMercadoFutbol.GOLES_VISITANTE_FT] = (media_visitante_ft, std_visitante_ft)

        # GOLES_FT = suma de los 4 targets
        media_ft = local_1t[0] + local_2t[0] + visitante_1t[0] + visitante_2t[0]
        std_ft = math.sqrt(
            local_1t[1]**2 + local_2t[1]**2 +
            visitante_1t[1]**2 + visitante_2t[1]**2
        )
        derivados[TipoMercadoFutbol.GOLES_FT] = (media_ft, std_ft)

        return derivados

    def _crear_prediccion_mercado(
        self,
        mercado: TipoMercadoFutbol,
        media: float,
        std: float,
    ) -> PrediccionMercado:
        """Crea un objeto PrediccionMercado con todas las probabilidades."""
        from ..prediccion.calculadora_probabilidad import CalculadoraProbabilidad

        # Obtener líneas para este mercado
        lineas = LINEAS_GOLES.get(mercado.value, [])

        # Calcular probabilidades
        probabilidades = {}
        for linea in lineas:
            prob_over = CalculadoraProbabilidad.prob_over(media, std, linea)
            prob_under = CalculadoraProbabilidad.prob_under(media, std, linea)
            probabilidades[f"over_{linea}"] = round(prob_over, 4)
            probabilidades[f"under_{linea}"] = round(prob_under, 4)

        # Intervalo de confianza 90%
        intervalo_90 = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.90)

        return PrediccionMercado(
            mercado=mercado,
            media=round(media, 2),
            std=round(std, 2),
            intervalo_90=(round(intervalo_90[0], 2), round(intervalo_90[1], 2)),
            probabilidades=probabilidades,
        )

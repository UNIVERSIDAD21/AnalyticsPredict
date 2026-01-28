# -*- coding: utf-8 -*-
"""
corners.py — Modelo de predicción de corners.

Este módulo implementa el modelo específico para predicción de corners,
incluyendo el cálculo de mercados derivados.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Tuple, Any

import numpy as np

from .base import ModeloPrediccionBase, construir_matriz_diseno
from ..tipos import TipoModelo, TipoMercadoFutbol, PrediccionMercado
from ..constantes import TARGETS_CORNERS, LINEAS_CORNERS
from ..excepciones import ModeloNoEntrenado

logger = logging.getLogger(__name__)


class ModeloCorners(ModeloPrediccionBase):
    """
    Modelo de predicción de corners.

    Predice 4 targets básicos:
    - corners_local_1t
    - corners_local_2t
    - corners_visitante_1t
    - corners_visitante_2t

    Y calcula 5 mercados derivados:
    - CORNERS_1T (local_1t + visitante_1t)
    - CORNERS_2T (local_2t + visitante_2t)
    - CORNERS_LOCAL_FT (local_1t + local_2t)
    - CORNERS_VISITANTE_FT (visitante_1t + visitante_2t)
    - CORNERS_FT (suma de los 4)
    """

    def __init__(self):
        """Inicializa el modelo de corners."""
        super().__init__(
            tipo=TipoModelo.CORNERS,
            targets=TARGETS_CORNERS,
        )

    def predecir_completo(
        self,
        equipo: str,
        rival: str,
        es_local: bool = True,
    ) -> Dict[str, PrediccionMercado]:
        """
        Genera predicciones para los 9 mercados de corners.

        Args:
            equipo: Nombre del equipo local
            rival: Nombre del equipo visitante
            es_local: True si equipo es local (siempre True para esta perspectiva)

        Returns:
            Dict con PrediccionMercado para cada mercado
        """
        if not self.entrenado:
            raise ModeloNoEntrenado(self.tipo.value)

        # Obtener predicciones base
        pred_targets = self.predecir_partido(equipo, rival, es_local)

        # Extraer predicciones de targets básicos
        local_1t = pred_targets.get("corners_local_1t", (2.5, 1.5))
        local_2t = pred_targets.get("corners_local_2t", (3.0, 1.6))
        visitante_1t = pred_targets.get("corners_visitante_1t", (2.2, 1.4))
        visitante_2t = pred_targets.get("corners_visitante_2t", (2.5, 1.5))

        # Calcular mercados derivados
        mercados_derivados = self._calcular_mercados_derivados(
            local_1t, local_2t, visitante_1t, visitante_2t
        )

        # Construir predicciones para todos los mercados
        resultados = {}

        # Mercados básicos
        resultados[TipoMercadoFutbol.CORNERS_LOCAL_1T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.CORNERS_LOCAL_1T, local_1t[0], local_1t[1]
        )
        resultados[TipoMercadoFutbol.CORNERS_LOCAL_2T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.CORNERS_LOCAL_2T, local_2t[0], local_2t[1]
        )
        resultados[TipoMercadoFutbol.CORNERS_VISITANTE_1T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.CORNERS_VISITANTE_1T, visitante_1t[0], visitante_1t[1]
        )
        resultados[TipoMercadoFutbol.CORNERS_VISITANTE_2T.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.CORNERS_VISITANTE_2T, visitante_2t[0], visitante_2t[1]
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
        """
        Calcula mercados derivados a partir de los targets básicos.

        Para sumas de variables independientes:
        - Media(X + Y) = Media(X) + Media(Y)
        - Var(X + Y) = Var(X) + Var(Y)
        - Std(X + Y) = sqrt(Std(X)² + Std(Y)²)
        """
        derivados = {}

        # CORNERS_1T = local_1t + visitante_1t
        media_1t = local_1t[0] + visitante_1t[0]
        std_1t = math.sqrt(local_1t[1]**2 + visitante_1t[1]**2)
        derivados[TipoMercadoFutbol.CORNERS_1T] = (media_1t, std_1t)

        # CORNERS_2T = local_2t + visitante_2t
        media_2t = local_2t[0] + visitante_2t[0]
        std_2t = math.sqrt(local_2t[1]**2 + visitante_2t[1]**2)
        derivados[TipoMercadoFutbol.CORNERS_2T] = (media_2t, std_2t)

        # CORNERS_LOCAL_FT = local_1t + local_2t
        media_local_ft = local_1t[0] + local_2t[0]
        std_local_ft = math.sqrt(local_1t[1]**2 + local_2t[1]**2)
        derivados[TipoMercadoFutbol.CORNERS_LOCAL_FT] = (media_local_ft, std_local_ft)

        # CORNERS_VISITANTE_FT = visitante_1t + visitante_2t
        media_visitante_ft = visitante_1t[0] + visitante_2t[0]
        std_visitante_ft = math.sqrt(visitante_1t[1]**2 + visitante_2t[1]**2)
        derivados[TipoMercadoFutbol.CORNERS_VISITANTE_FT] = (media_visitante_ft, std_visitante_ft)

        # CORNERS_FT = suma de los 4 targets
        media_ft = local_1t[0] + local_2t[0] + visitante_1t[0] + visitante_2t[0]
        std_ft = math.sqrt(
            local_1t[1]**2 + local_2t[1]**2 +
            visitante_1t[1]**2 + visitante_2t[1]**2
        )
        derivados[TipoMercadoFutbol.CORNERS_FT] = (media_ft, std_ft)

        return derivados

    def _crear_prediccion_mercado(
        self,
        mercado: TipoMercadoFutbol,
        media: float,
        std: float,
    ) -> PrediccionMercado:
        """
        Crea un objeto PrediccionMercado con todas las probabilidades.

        Args:
            mercado: Tipo de mercado
            media: Media predicha
            std: Desviación estándar

        Returns:
            PrediccionMercado completo
        """
        from ..prediccion.calculadora_probabilidad import CalculadoraProbabilidad

        # Obtener líneas para este mercado
        lineas = LINEAS_CORNERS.get(mercado.value, [])

        # Calcular probabilidades para cada línea
        probabilidades = {}
        for linea in lineas:
            prob_over = CalculadoraProbabilidad.prob_over(media, std, linea)
            prob_under = CalculadoraProbabilidad.prob_under(media, std, linea)
            probabilidades[f"over_{linea}"] = round(prob_over, 4)
            probabilidades[f"under_{linea}"] = round(prob_under, 4)

        # Calcular intervalo de confianza 90%
        intervalo_90 = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.90)

        return PrediccionMercado(
            mercado=mercado,
            media=round(media, 2),
            std=round(std, 2),
            intervalo_90=(round(intervalo_90[0], 2), round(intervalo_90[1], 2)),
            probabilidades=probabilidades,
        )

    def predecir_targets(
        self,
        equipo: str,
        rival: str,
        es_local: bool = True,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Predice solo los 4 targets básicos.

        Útil para entrenamiento y evaluación interna.

        Returns:
            Dict con {target: (media, std)}
        """
        return self.predecir_partido(equipo, rival, es_local)

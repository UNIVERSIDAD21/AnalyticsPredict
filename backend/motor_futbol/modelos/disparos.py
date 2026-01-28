# -*- coding: utf-8 -*-
"""
disparos.py — Modelo de predicción de disparos.

Este módulo implementa el modelo específico para predicción de disparos.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Tuple, Any

from .base import ModeloPrediccionBase
from ..tipos import TipoModelo, TipoMercadoFutbol, PrediccionMercado
from ..constantes import TARGETS_DISPAROS, LINEAS_DISPAROS
from ..excepciones import ModeloNoEntrenado

logger = logging.getLogger(__name__)


class ModeloDisparos(ModeloPrediccionBase):
    """
    Modelo de predicción de disparos.

    Predice 4 targets:
    - disparos_local_total
    - disparos_local_arco
    - disparos_visitante_total
    - disparos_visitante_arco

    Y calcula 2 mercados derivados:
    - DISPAROS_FT (local_total + visitante_total)
    - DISPAROS_ARCO_FT (local_arco + visitante_arco)

    Nota: No hay datos por tiempo para disparos.
    """

    def __init__(self):
        """Inicializa el modelo de disparos."""
        super().__init__(
            tipo=TipoModelo.DISPAROS,
            targets=TARGETS_DISPAROS,
        )

    def predecir_completo(
        self,
        equipo: str,
        rival: str,
        es_local: bool = True,
    ) -> Dict[str, PrediccionMercado]:
        """
        Genera predicciones para los 6 mercados de disparos.

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
        local_total = pred_targets.get("disparos_local_total", (12.0, 4.0))
        local_arco = pred_targets.get("disparos_local_arco", (4.5, 2.0))
        visitante_total = pred_targets.get("disparos_visitante_total", (11.0, 3.8))
        visitante_arco = pred_targets.get("disparos_visitante_arco", (4.0, 1.9))

        # Calcular mercados derivados
        mercados_derivados = self._calcular_mercados_derivados(
            local_total, local_arco, visitante_total, visitante_arco
        )

        # Construir predicciones para todos los mercados
        resultados = {}

        # Mercados por equipo
        resultados[TipoMercadoFutbol.DISPAROS_LOCAL_FT.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.DISPAROS_LOCAL_FT, local_total[0], local_total[1]
        )
        resultados[TipoMercadoFutbol.DISPAROS_LOCAL_ARCO_FT.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.DISPAROS_LOCAL_ARCO_FT, local_arco[0], local_arco[1]
        )
        resultados[TipoMercadoFutbol.DISPAROS_VISITANTE_FT.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.DISPAROS_VISITANTE_FT, visitante_total[0], visitante_total[1]
        )
        resultados[TipoMercadoFutbol.DISPAROS_VISITANTE_ARCO_FT.value] = self._crear_prediccion_mercado(
            TipoMercadoFutbol.DISPAROS_VISITANTE_ARCO_FT, visitante_arco[0], visitante_arco[1]
        )

        # Mercados derivados (totales)
        for mercado, (media, std) in mercados_derivados.items():
            resultados[mercado.value] = self._crear_prediccion_mercado(mercado, media, std)

        return resultados

    def _calcular_mercados_derivados(
        self,
        local_total: Tuple[float, float],
        local_arco: Tuple[float, float],
        visitante_total: Tuple[float, float],
        visitante_arco: Tuple[float, float],
    ) -> Dict[TipoMercadoFutbol, Tuple[float, float]]:
        """Calcula mercados derivados."""
        derivados = {}

        # DISPAROS_FT = local_total + visitante_total
        media_total = local_total[0] + visitante_total[0]
        std_total = math.sqrt(local_total[1]**2 + visitante_total[1]**2)
        derivados[TipoMercadoFutbol.DISPAROS_FT] = (media_total, std_total)

        # DISPAROS_ARCO_FT = local_arco + visitante_arco
        media_arco = local_arco[0] + visitante_arco[0]
        std_arco = math.sqrt(local_arco[1]**2 + visitante_arco[1]**2)
        derivados[TipoMercadoFutbol.DISPAROS_ARCO_FT] = (media_arco, std_arco)

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
        lineas = LINEAS_DISPAROS.get(mercado.value, [])

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

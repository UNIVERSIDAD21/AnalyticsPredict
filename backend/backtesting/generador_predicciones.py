# -*- coding: utf-8 -*-
"""
generador_predicciones.py — Generación de predicciones de backtest con líneas sintéticas.
"""

from __future__ import annotations

from collections import defaultdict
import logging
import time
from typing import Any, Callable, Sequence

import numpy as np

from backtesting.configuracion import ConfiguracionBacktest, Mercado
from motor.calculadora_probabilidad import calcular_probabilidad_over
from motor.nba_predictor_cuartos import predecir_cuartos
from motor.registro_predicciones import registrar_prediccion
from motor.tipos import ModeloRidge, Ubicacion


logger = logging.getLogger(__name__)

LADOS = ("OVER", "UNDER")
ORIGEN_BACKTEST_SINTETICO = "BACKTEST_SINTETICO"


def generar_predicciones_backtest(
    modelo: ModeloRidge | dict[str, Any],
    partidos: Sequence[dict[str, Any]],
    config: ConfiguracionBacktest,
    *,
    modelo_version_id: int,
    origen: str = ORIGEN_BACKTEST_SINTETICO,
    registrar_prediccion_func: Callable[..., Any] = registrar_prediccion,
) -> dict[str, Any]:
    inicio = time.perf_counter()
    modelo_ridge = _normalizar_modelo(modelo)
    offsets = _resolver_offsets(config)
    mercados = _resolver_mercados(config)

    resumen = {
        "total_intentos": 0,
        "total_insertadas": 0,
        "total_duplicadas": 0,
        "total_fallidas": 0,
        "por_mercado": defaultdict(_estructura_conteo),
        "por_offset": defaultdict(_estructura_conteo),
    }

    for partido in partidos:
        try:
            contexto = _extraer_contexto_partido(partido)
        except ValueError as exc:
            logger.warning("Partido inválido para predicción: %s", exc)
            resumen["total_fallidas"] += 1
            continue

        media_equipo, desviacion_equipo, media_rival, desviacion_rival = predecir_cuartos(
            modelo_ridge,
            contexto["equipo_local"],
            contexto["equipo_visitante"],
            Ubicacion.LOCAL,
        )

        for mercado in mercados:
            media_total, desviacion_total = _calcular_media_y_desviacion(
                mercado,
                media_equipo,
                media_rival,
                desviacion_equipo,
                desviacion_rival,
            )
            for offset in offsets:
                linea = float(media_total + offset)
                if origen == ORIGEN_BACKTEST_SINTETICO:
                    linea_es_sintetica = True
                else:
                    linea_es_sintetica = config.usar_lineas_sinteticas or offset != 0
                p_over = calcular_probabilidad_over(media_total, desviacion_total, linea)
                p_under = 1.0 - p_over

                for lado in LADOS:
                    resumen["total_intentos"] += 1
                    resumen["por_mercado"][mercado]["total_intentos"] += 1
                    resumen["por_offset"][offset]["total_intentos"] += 1
                    p_raw = p_over if lado == "OVER" else p_under
                    resultado = registrar_prediccion_func(
                        partido_id=contexto["partido_id"],
                        temporada_id=contexto["temporada_id"],
                        equipo_local_id=contexto["equipo_local_id"],
                        equipo_visitante_id=contexto["equipo_visitante_id"],
                        fecha_partido=contexto["fecha_partido"],
                        tipo_partido=contexto["tipo_partido"],
                        mercado=mercado,
                        lado=lado,
                        linea=linea,
                        linea_es_sintetica=linea_es_sintetica,
                        origen=origen,
                        modelo_version_id=modelo_version_id,
                        calibrador_id=None,
                        media_predicha=float(media_total),
                        desviacion_predicha=float(desviacion_total),
                        p_raw=float(p_raw),
                        cuota=None,
                        cuota_over=None,
                        cuota_under=None,
                        return_status=True,
                    )
                    _acumular_resultado(resumen, resultado, mercado, offset)

    duracion = time.perf_counter() - inicio
    resumen["duracion_segundos"] = duracion
    resumen["tiempo_promedio_ms"] = (
        duracion * 1000 / resumen["total_intentos"] if resumen["total_intentos"] else 0.0
    )
    resumen["por_mercado"] = dict(resumen["por_mercado"])
    resumen["por_offset"] = dict(resumen["por_offset"])
    return resumen


def _estructura_conteo() -> dict[str, int]:
    return {
        "total_intentos": 0,
        "total_insertadas": 0,
        "total_duplicadas": 0,
        "total_fallidas": 0,
    }


def _acumular_resultado(
    resumen: dict[str, Any],
    resultado: Any,
    mercado: str,
    offset: float,
) -> None:
    if isinstance(resultado, tuple):
        _, estado = resultado
    else:
        estado = "insertada" if resultado is not None else "fallida"

    if estado == "insertada":
        resumen["total_insertadas"] += 1
        resumen["por_mercado"][mercado]["total_insertadas"] += 1
        resumen["por_offset"][offset]["total_insertadas"] += 1
    elif estado == "duplicada":
        resumen["total_duplicadas"] += 1
        resumen["por_mercado"][mercado]["total_duplicadas"] += 1
        resumen["por_offset"][offset]["total_duplicadas"] += 1
    else:
        resumen["total_fallidas"] += 1
        resumen["por_mercado"][mercado]["total_fallidas"] += 1
        resumen["por_offset"][offset]["total_fallidas"] += 1


def _normalizar_modelo(modelo: ModeloRidge | dict[str, Any]) -> ModeloRidge:
    if isinstance(modelo, ModeloRidge):
        return modelo
    return ModeloRidge(
        alfa=float(modelo["alpha"]),
        entidad_a_indice=modelo["entidad_a_indice"],
        pesos_equipo=np.array(modelo["pesos_equipo"]),
        pesos_rival=np.array(modelo["pesos_rival"]),
        desviacion_equipo=np.array(modelo["desviacion_equipo"]),
        desviacion_rival=np.array(modelo["desviacion_rival"]),
    )


def _resolver_offsets(config: ConfiguracionBacktest) -> list[float]:
    if config.usar_lineas_sinteticas:
        return list(config.offsets_linea or [])
    return [0.0]


def _resolver_mercados(config: ConfiguracionBacktest) -> list[str]:
    mercados = [
        mercado.value if isinstance(mercado, Mercado) else str(mercado)
        for mercado in config.mercados
    ]
    if not config.incluir_completo:
        mercados = [
            mercado for mercado in mercados if mercado != Mercado.COMPLETO.value
        ]
    return mercados


def _calcular_media_y_desviacion(
    mercado: str,
    media_equipo: np.ndarray,
    media_rival: np.ndarray,
    desviacion_equipo: np.ndarray,
    desviacion_rival: np.ndarray,
) -> tuple[float, float]:
    if mercado == Mercado.COMPLETO.value:
        media_total = float(np.sum(media_equipo) + np.sum(media_rival))
        desviacion_total = float(
            np.sqrt(np.sum(desviacion_equipo ** 2) + np.sum(desviacion_rival ** 2))
        )
        return media_total, desviacion_total

    indice = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}[mercado]
    media_total = float(media_equipo[indice] + media_rival[indice])
    desviacion_total = float(
        np.sqrt(desviacion_equipo[indice] ** 2 + desviacion_rival[indice] ** 2)
    )
    return media_total, desviacion_total


def _extraer_contexto_partido(partido: dict[str, Any]) -> dict[str, Any]:
    partido_id = partido.get("partido_id", partido.get("id"))
    if partido_id is None:
        raise ValueError("partido_id es obligatorio")

    requeridos = {
        "temporada_id": partido.get("temporada_id"),
        "equipo_local_id": partido.get("equipo_local_id"),
        "equipo_visitante_id": partido.get("equipo_visitante_id"),
        "fecha_partido": partido.get("fecha_partido"),
        "tipo_partido": partido.get("tipo_partido"),
        "equipo_local": partido.get("equipo_local"),
        "equipo_visitante": partido.get("equipo_visitante"),
    }
    faltantes = [clave for clave, valor in requeridos.items() if valor is None]
    if faltantes:
        raise ValueError(f"faltan campos requeridos: {', '.join(faltantes)}")

    return {
        "partido_id": partido_id,
        **requeridos,
    }

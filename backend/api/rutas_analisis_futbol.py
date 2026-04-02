# -*- coding: utf-8 -*-
"""
rutas_analisis_futbol.py — Endpoint principal de análisis de partidos de fútbol.

Este es el endpoint más importante del sistema. Genera predicciones para los
24 mercados de fútbol utilizando los modelos Ridge entrenados.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from uuid import UUID

import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from psycopg.rows import dict_row
from scipy import stats

from db import obtener_pool
from servicios.apuestas_analizadas import registrar_apuesta_analizada
from servicios.b3_estabilizacion_futbol import (
    combinar_valor_cross_liga,
    ajustar_probabilidad_por_muestras,
    nivel_confianza_b3,
)
from .schemas_futbol import (
    AnalisisRequest,
    AnalisisResponse,
    PartidoResumen,
    PrediccionMercado,
    ProbabilidadLinea,
    RecomendacionApuesta,
    ErrorResponse,
    ProbabilidadesGanadorFutbol,
)
from .dependencias import obtener_usuario_actual, UsuarioActual

router = APIRouter(prefix="/api/futbol", tags=["Fútbol - Análisis"])
logger = logging.getLogger(__name__)

# Intentar importar el motor de predicción
try:
    from motor_futbol.prediccion.predictor import PredictorFutbol
    from motor_futbol.calibracion.gestor_calibradores import GestorCalibradores
    from motor_futbol.tipos import TipoMercadoFutbol
    MOTOR_DISPONIBLE = True
except ImportError:
    MOTOR_DISPONIBLE = False
    logger.warning("Motor de predicción de fútbol no disponible")


# Cache simple para estadísticas de equipos (TTL: 1 hora)
_cache_estadisticas: Dict[str, tuple] = {}
CACHE_TTL = 3600

# Instancia singleton del predictor ML de fútbol (P1)
_predictor_futbol_ml: Optional["PredictorFutbol"] = None
# Instancia singleton del gestor de calibradores (P2)
_gestor_calibradores_futbol: Optional["GestorCalibradores"] = None


def _obtener_predictor_futbol_ml(pool) -> Optional["PredictorFutbol"]:
    """Obtiene/crea el predictor ML de fútbol para usarlo como núcleo del endpoint."""
    global _predictor_futbol_ml
    if not MOTOR_DISPONIBLE:
        return None

    if _predictor_futbol_ml is None:
        try:
            _predictor_futbol_ml = PredictorFutbol(pool=pool, cargar_modelos=True)
            logger.info("PredictorFutbol ML inicializado para /api/futbol/analizar")
        except Exception:
            logger.exception("No se pudo inicializar PredictorFutbol ML")
            _predictor_futbol_ml = None

    return _predictor_futbol_ml


def _obtener_gestor_calibradores_futbol(pool) -> Optional["GestorCalibradores"]:
    """Obtiene/crea el gestor de calibradores de fútbol para calibrar probabilidades operativas."""
    global _gestor_calibradores_futbol
    if not MOTOR_DISPONIBLE:
        return None

    if _gestor_calibradores_futbol is None:
        try:
            _gestor_calibradores_futbol = GestorCalibradores(pool=pool)
            logger.info("GestorCalibradores inicializado para /api/futbol/analizar")
        except Exception:
            logger.exception("No se pudo inicializar GestorCalibradores de fútbol")
            _gestor_calibradores_futbol = None

    return _gestor_calibradores_futbol


def _inferir_lineas_desde_probabilidades(
    probabilidades: Dict[str, float],
    lineas_default: List[float],
) -> List[float]:
    """Extrae líneas desde keys over_X.X / under_X.X para respetar modelo activo."""
    lineas_detectadas: List[float] = []
    for clave in probabilidades.keys():
        if not (clave.startswith("over_") or clave.startswith("under_")):
            continue
        try:
            linea = float(clave.split("_", 1)[1])
            if linea not in lineas_detectadas:
                lineas_detectadas.append(linea)
        except Exception:
            continue

    if lineas_detectadas:
        lineas_detectadas.sort()
        return lineas_detectadas
    return lineas_default


def _convertir_mercado_ml_a_schema(
    prediccion_ml,
    lineas_default: List[float],
    gestor_calibradores: Optional["GestorCalibradores"] = None,
) -> PrediccionMercado:
    """Convierte PrediccionMercado del motor_futbol al schema API actual."""
    lineas: Dict[str, ProbabilidadLinea] = {}
    probabilidades = getattr(prediccion_ml, "probabilidades", {}) or {}
    mercado_txt = str(getattr(prediccion_ml.mercado, "value", prediccion_ml.mercado))

    tipo_mercado: Optional["TipoMercadoFutbol"] = None
    if gestor_calibradores is not None:
        try:
            tipo_mercado = TipoMercadoFutbol(mercado_txt)
        except Exception:
            tipo_mercado = None

    for linea in _inferir_lineas_desde_probabilidades(probabilidades, lineas_default):
        prob_over_raw = float(probabilidades.get(f"over_{linea}", 0.5))
        prob_under_raw = float(probabilidades.get(f"under_{linea}", 1.0 - prob_over_raw))

        prob_over_cal = prob_over_raw
        prob_under_cal = prob_under_raw

        if gestor_calibradores is not None and tipo_mercado is not None:
            try:
                prob_over_cal = float(
                    gestor_calibradores.calibrar_probabilidad(tipo_mercado, prob_over_raw)
                )
                prob_over_cal = float(max(0.0, min(1.0, prob_over_cal)))
                prob_under_cal = 1.0 - prob_over_cal
            except Exception:
                logger.exception(
                    "No se pudo calibrar probabilidad de fútbol (mercado=%s linea=%s)",
                    mercado_txt,
                    linea,
                )
                prob_over_cal = prob_over_raw
                prob_under_cal = prob_under_raw

        lineas[str(linea)] = ProbabilidadLinea(
            over_raw=round(prob_over_raw, 4),
            over_calibrada=round(prob_over_cal, 4),
            under_raw=round(prob_under_raw, 4),
            under_calibrada=round(prob_under_cal, 4),
            razones=None,
        )

    return PrediccionMercado(
        mercado=mercado_txt,
        media=round(float(prediccion_ml.media), 2),
        std=round(float(prediccion_ml.std), 2),
        lineas=lineas,
    )


def _nivel_confianza_ml_a_api(nivel: str) -> str:
    nivel_u = str(nivel or "MEDIA").upper()
    if nivel_u in {"MUY_ALTA", "ALTA", "MEDIA", "BAJA", "MUY_BAJA"}:
        return nivel_u
    if nivel_u == "ALTA":
        return "ALTA"
    if nivel_u == "BAJA":
        return "BAJA"
    return "MEDIA"


def _recomendaciones_ml_a_api(
    recomendaciones_ml: List[Dict[str, Any]],
    confianza_base: str,
) -> List[RecomendacionApuesta]:
    recomendaciones: List[RecomendacionApuesta] = []
    confianza_api = _nivel_confianza_ml_a_api(confianza_base)

    for rec in recomendaciones_ml or []:
        try:
            lado = str(rec.get("tipo", "OVER")).upper()
            if lado not in {"OVER", "UNDER"}:
                lado = "OVER"
            p_cal = float(rec.get("probabilidad_modelo", 0.5))
            p_raw = float(rec.get("p_raw", p_cal))
            edge_real = rec.get("edge_real")
            score = rec.get("score")
            sizing = rec.get("sizing")
            recomendaciones.append(
                RecomendacionApuesta(
                    mercado=str(rec.get("mercado", "")),
                    lado=lado,
                    linea=float(rec.get("linea", 0.0)),
                    probabilidad=p_cal,
                    confianza=confianza_api,
                    valor_esperado=rec.get("valor_esperado"),
                    p_raw=p_raw,
                    p_calibrada=p_cal,
                    modelo_version_id=str(rec.get("modelo_version_id")) if rec.get("modelo_version_id") else None,
                    calibrador_id=str(rec.get("calibrador_id")) if rec.get("calibrador_id") else None,
                    edge_real=float(edge_real) if edge_real is not None else None,
                    score=float(score) if score is not None else None,
                    sizing=float(sizing) if sizing is not None else None,
                    cuota=float(rec.get("cuota")) if rec.get("cuota") is not None else None,
                    cuota_over=float(rec.get("cuota_over")) if rec.get("cuota_over") is not None else None,
                    cuota_under=float(rec.get("cuota_under")) if rec.get("cuota_under") is not None else None,
                    devig_metodo=rec.get("devig_metodo"),
                    devig_overround=float(rec.get("devig_overround")) if rec.get("devig_overround") is not None else None,
                    devig_p_mkt_fair=float(rec.get("devig_p_mkt_fair")) if rec.get("devig_p_mkt_fair") is not None else None,
                    advertencias=rec.get("advertencias"),
                    fuente="ML",
                    metadata_ensemble={"motivo_arbitraje": "senal_ml"},
                )
            )
        except Exception:
            logger.exception("No se pudo convertir recomendación ML de fútbol")
            continue

    return recomendaciones[:10]


def _prediccion_ganador_desde_mercados_ml(
    mercados_goles_ml: Dict[str, Any],
) -> Optional[ProbabilidadesGanadorFutbol]:
    """Deriva 1X2 con Dixon-Coles usando GOLES_LOCAL_FT y GOLES_VISITANTE_FT del motor ML."""
    try:
        goles_local_ft = mercados_goles_ml.get("GOLES_LOCAL_FT")
        goles_visitante_ft = mercados_goles_ml.get("GOLES_VISITANTE_FT")
        if not goles_local_ft or not goles_visitante_ft:
            return None

        media_local = float(goles_local_ft.media)
        media_visitante = float(goles_visitante_ft.media)
        prob_local, prob_empate, prob_visitante, marcador_probable = _calcular_1x2_dixon_coles(
            media_local,
            media_visitante,
        )
        ganador_probable = (
            "LOCAL"
            if prob_local >= prob_empate and prob_local >= prob_visitante
            else ("VISITANTE" if prob_visitante >= prob_empate else "EMPATE")
        )

        return ProbabilidadesGanadorFutbol(
            prob_local=prob_local,
            prob_empate=prob_empate,
            prob_visitante=prob_visitante,
            ganador_probable=ganador_probable,
            marcador_probable=marcador_probable,
            razones=[
                f"Estimación ML de goles FT: local={media_local:.2f}, visitante={media_visitante:.2f}.",
                f"1X2 derivado con Dixon-Coles sobre medias ML. Marcador más probable: {marcador_probable}.",
            ],
        )
    except Exception:
        logger.exception("No se pudo derivar predicción 1X2 desde mercados ML")
        return None


def _ensamblar_mercados(
    mercados_ml: Dict[str, PrediccionMercado],
    mercados_heur: Dict[str, PrediccionMercado],
    peso_ml: float = 0.65,
) -> Dict[str, PrediccionMercado]:
    """Ensamble simple ML + heurístico para un conjunto de mercados."""
    peso_ml = float(max(0.0, min(1.0, peso_ml)))
    peso_heur = 1.0 - peso_ml
    resultado: Dict[str, PrediccionMercado] = {}

    for clave, heur in (mercados_heur or {}).items():
        ml = (mercados_ml or {}).get(clave)
        if ml is None:
            resultado[clave] = heur
            continue

        media = (peso_ml * float(ml.media)) + (peso_heur * float(heur.media))
        std = (peso_ml * float(ml.std)) + (peso_heur * float(heur.std))

        lineas_union = set((ml.lineas or {}).keys()) | set((heur.lineas or {}).keys())
        lineas_blend: Dict[str, ProbabilidadLinea] = {}
        for linea in lineas_union:
            l_ml = (ml.lineas or {}).get(linea)
            l_h = (heur.lineas or {}).get(linea)
            if l_ml and l_h:
                over_raw = (peso_ml * float(l_ml.over_raw)) + (peso_heur * float(l_h.over_raw))
                over_cal = (peso_ml * float(l_ml.over_calibrada)) + (peso_heur * float(l_h.over_calibrada))
                under_raw = 1.0 - over_raw
                under_cal = 1.0 - over_cal
                razones = (l_ml.razones or []) + (l_h.razones or []) if (l_ml.razones or l_h.razones) else None
                lineas_blend[linea] = ProbabilidadLinea(
                    over_raw=round(max(0.001, min(0.999, over_raw)), 4),
                    over_calibrada=round(max(0.001, min(0.999, over_cal)), 4),
                    under_raw=round(max(0.001, min(0.999, under_raw)), 4),
                    under_calibrada=round(max(0.001, min(0.999, under_cal)), 4),
                    razones=razones,
                )
            elif l_ml:
                lineas_blend[linea] = l_ml
            elif l_h:
                lineas_blend[linea] = l_h

        resultado[clave] = PrediccionMercado(
            mercado=heur.mercado,
            media=round(float(media), 2),
            std=round(float(std), 2),
            lineas=lineas_blend,
        )

    for clave, ml in (mercados_ml or {}).items():
        if clave not in resultado:
            resultado[clave] = ml

    return resultado


def _normalizar_linea_key(linea: float) -> str:
    return f"{float(linea):.2f}".rstrip("0").rstrip(".")


def _clave_recomendacion(mercado: str, lado: str, linea: float) -> str:
    return f"{str(mercado).upper()}|{str(lado).upper()}|{_normalizar_linea_key(linea)}"


def _obtener_cuotas_para_recomendacion(
    cuotas_por_linea: Optional[Dict[str, Dict[str, float]]],
    mercado: str,
    linea: float,
) -> Tuple[Optional[float], Optional[float]]:
    if not cuotas_por_linea:
        return (None, None)

    mercado_u = str(mercado).upper()
    linea_keys = {_normalizar_linea_key(linea), str(linea)}
    posibles = [
        f"{mercado_u}|{lk}" for lk in linea_keys
    ]

    for key in posibles:
        data = cuotas_por_linea.get(key)
        if not data:
            continue
        cuota_over = data.get("cuota_over")
        cuota_under = data.get("cuota_under")
        return (
            float(cuota_over) if cuota_over is not None else None,
            float(cuota_under) if cuota_under is not None else None,
        )

    return (None, None)


def _calcular_metricas_mercado(
    *,
    lado: str,
    prob_raw: float,
    prob_cal: float,
    cuota_over: Optional[float],
    cuota_under: Optional[float],
    std: float,
    mercado_estado: str,
) -> Dict[str, Any]:
    lado_u = str(lado).upper()
    cuota_lado = cuota_over if lado_u == "OVER" else cuota_under
    cuota_opuesta = cuota_under if lado_u == "OVER" else cuota_over

    advertencias: List[str] = []
    devig_metodo = "fallback_conservador_no_odds"
    devig_overround = None
    p_mkt_fair = None

    if cuota_lado is not None:
        p_mkt_raw = 1.0 / max(float(cuota_lado), 1e-9)
    else:
        p_mkt_raw = None

    if cuota_lado is not None and cuota_opuesta is not None:
        devig_metodo = "exacto"
        overround = (1.0 / max(float(cuota_over), 1e-9)) + (1.0 / max(float(cuota_under), 1e-9))
        devig_overround = float(overround)
        if overround > 0:
            p_over_fair = (1.0 / float(cuota_over)) / overround
            p_under_fair = (1.0 / float(cuota_under)) / overround
            p_mkt_fair = float(p_over_fair if lado_u == "OVER" else p_under_fair)
    elif cuota_lado is not None:
        devig_metodo = "implied_raw_single_side"
        p_mkt_fair = float(p_mkt_raw)
        advertencias.append("Solo una cuota disponible: se usa probabilidad implícita raw (sin de-vig real).")
        advertencias.append("Resultado en modo fallback conservador; priorizar confirmación con cuota opuesta.")
    else:
        advertencias.append("Sin cuotas de mercado: edge/EV/sizing en fallback conservador.")

    edge_real = float(prob_cal - p_mkt_fair) if p_mkt_fair is not None else float(prob_cal - 0.5)
    ev_real = None
    if cuota_lado is not None:
        ev_real = float((prob_cal * float(cuota_lado)) - 1.0)

    # Score: EV + edge + calidad mercado + calibración + riesgo
    base_score = 50.0
    if ev_real is not None:
        base_score += ev_real * 120.0
    base_score += edge_real * 80.0
    if mercado_estado == "verde":
        base_score += 6.0
    elif mercado_estado == "amarillo":
        base_score -= 6.0
    else:
        base_score -= 14.0
    # Penalización por varianza
    base_score -= min(18.0, max(0.0, float(std) * 1.8))
    score = float(max(0.0, min(100.0, base_score)))

    # Kelly fraccional comparable a NBA
    kelly_full = 0.0
    kelly_frac = 0.0
    sizing = 0.0
    if cuota_lado is not None and cuota_lado > 1.0:
        b = float(cuota_lado) - 1.0
        p = float(prob_cal)
        q = 1.0 - p
        kelly_full = ((b * p) - q) / b
        if kelly_full < 0:
            kelly_full = 0.0
        kelly_frac = 0.25 * kelly_full
        # Penalizaciones de riesgo
        risk_factor = 1.0
        if mercado_estado == "amarillo":
            risk_factor *= 0.8
        elif mercado_estado == "rojo":
            risk_factor *= 0.5
        if std > 4.0:
            risk_factor *= 0.75
            advertencias.append("Alta volatilidad del mercado; sizing penalizado.")
        sizing = float(max(0.0, min(0.05, kelly_frac * risk_factor)))

    return {
        "cuota_lado": cuota_lado,
        "cuota_over": cuota_over,
        "cuota_under": cuota_under,
        "devig_metodo": devig_metodo,
        "devig_overround": devig_overround,
        "devig_p_mkt_fair": p_mkt_fair,
        "edge_real": edge_real,
        "valor_esperado": ev_real,
        "score": score,
        "sizing": sizing,
        "advertencias": advertencias,
    }


def _calcular_peso_ml_dinamico(
    *,
    mercado: str,
    mercado_estado: str,
    partidos_relevantes: int,
    ml_calibrada: bool,
    heur_calibrada: bool,
) -> float:
    peso = 0.55
    mercado_u = str(mercado).upper()
    if mercado_u.startswith("GOLES"):
        peso += 0.08
    elif mercado_u.startswith("CORNERS"):
        peso += 0.04

    if ml_calibrada:
        peso += 0.07
    if heur_calibrada:
        peso -= 0.03

    if partidos_relevantes >= 80:
        peso += 0.05
    elif partidos_relevantes < 25:
        peso -= 0.08

    if mercado_estado == "amarillo":
        peso -= 0.08
    elif mercado_estado == "rojo":
        peso -= 0.15

    return float(max(0.25, min(0.80, peso)))


def _arbitrar_recomendaciones(
    recomendaciones_ml: List[RecomendacionApuesta],
    recomendaciones_heur: List[RecomendacionApuesta],
    *,
    estado_mercados: Dict[str, str],
    partidos_relevantes: int,
) -> List[RecomendacionApuesta]:
    """Dedupe + arbitraje fuerte por (mercado, lado, línea) con trazabilidad."""
    mapa_ml = {
        _clave_recomendacion(r.mercado, r.lado, r.linea): r for r in (recomendaciones_ml or [])
    }
    mapa_h = {
        _clave_recomendacion(r.mercado, r.lado, r.linea): r for r in (recomendaciones_heur or [])
    }

    claves = set(mapa_ml.keys()) | set(mapa_h.keys())
    salida: List[RecomendacionApuesta] = []

    for key in claves:
        r_ml = mapa_ml.get(key)
        r_h = mapa_h.get(key)
        base = r_ml or r_h
        mercado_estado = estado_mercados.get(str(base.mercado).upper(), "verde") if base else "verde"

        if r_ml and r_h:
            score_ml = float(r_ml.score or 0.0)
            score_h = float(r_h.score or 0.0)
            delta_score = score_ml - score_h
            ml_exacto = str(r_ml.devig_metodo or "") == "exacto"
            h_exacto = str(r_h.devig_metodo or "") == "exacto"

            # Selección dura por evidencia fuerte
            if ml_exacto and not h_exacto and delta_score >= -4.0:
                ganador = r_ml
                ganador.fuente = "ML"
                ganador.metadata_ensemble = {
                    "decision": "seleccion_dura",
                    "motivo_arbitraje": "ml_tiene_devig_exacto",
                    "delta_score": round(delta_score, 4),
                    "clave": key,
                }
                salida.append(ganador)
                continue
            if h_exacto and not ml_exacto and delta_score <= 4.0:
                ganador = r_h
                ganador.fuente = "HEURISTICO"
                ganador.metadata_ensemble = {
                    "decision": "seleccion_dura",
                    "motivo_arbitraje": "heuristico_tiene_devig_exacto",
                    "delta_score": round(delta_score, 4),
                    "clave": key,
                }
                salida.append(ganador)
                continue
            if abs(delta_score) >= 12.0:
                ganador = r_ml if delta_score > 0 else r_h
                ganador.fuente = "ML" if delta_score > 0 else "HEURISTICO"
                ganador.metadata_ensemble = {
                    "decision": "seleccion_dura",
                    "motivo_arbitraje": "diferencia_score_alta",
                    "delta_score": round(delta_score, 4),
                    "clave": key,
                }
                salida.append(ganador)
                continue

            # Blend sólo cuando no hay evidencia fuerte para selección dura
            ml_cal = r_ml.p_calibrada is not None
            h_cal = r_h.p_calibrada is not None
            peso_ml = _calcular_peso_ml_dinamico(
                mercado=str(base.mercado),
                mercado_estado=mercado_estado,
                partidos_relevantes=partidos_relevantes,
                ml_calibrada=ml_cal,
                heur_calibrada=h_cal,
            )
            peso_h = 1.0 - peso_ml
            p_raw = (peso_ml * float(r_ml.p_raw or r_ml.probabilidad)) + (peso_h * float(r_h.p_raw or r_h.probabilidad))
            p_cal = (peso_ml * float(r_ml.p_calibrada or r_ml.probabilidad)) + (peso_h * float(r_h.p_calibrada or r_h.probabilidad))
            prob = (peso_ml * float(r_ml.probabilidad)) + (peso_h * float(r_h.probabilidad))

            rec = RecomendacionApuesta(
                mercado=base.mercado,
                lado=base.lado,
                linea=base.linea,
                probabilidad=float(prob),
                confianza=base.confianza,
                valor_esperado=r_ml.valor_esperado if r_ml.valor_esperado is not None else r_h.valor_esperado,
                p_raw=float(p_raw),
                p_calibrada=float(p_cal),
                modelo_version_id=r_ml.modelo_version_id or r_h.modelo_version_id,
                calibrador_id=r_ml.calibrador_id or r_h.calibrador_id,
                edge_real=(peso_ml * float(r_ml.edge_real or 0.0)) + (peso_h * float(r_h.edge_real or 0.0)),
                score=(peso_ml * float(score_ml)) + (peso_h * float(score_h)),
                sizing=(peso_ml * float(r_ml.sizing or 0.0)) + (peso_h * float(r_h.sizing or 0.0)),
                cuota=r_ml.cuota or r_h.cuota,
                cuota_over=r_ml.cuota_over or r_h.cuota_over,
                cuota_under=r_ml.cuota_under or r_h.cuota_under,
                devig_metodo=r_ml.devig_metodo if ml_exacto else (r_h.devig_metodo if h_exacto else (r_ml.devig_metodo or r_h.devig_metodo)),
                devig_overround=r_ml.devig_overround if ml_exacto else (r_h.devig_overround if h_exacto else (r_ml.devig_overround or r_h.devig_overround)),
                devig_p_mkt_fair=r_ml.devig_p_mkt_fair if ml_exacto else (r_h.devig_p_mkt_fair if h_exacto else (r_ml.devig_p_mkt_fair or r_h.devig_p_mkt_fair)),
                advertencias=(r_ml.advertencias or []) + (r_h.advertencias or []),
                fuente="ENSEMBLE",
                metadata_ensemble={
                    "decision": "blend",
                    "peso_ml": round(peso_ml, 4),
                    "peso_heuristico": round(peso_h, 4),
                    "mercado_estado": mercado_estado,
                    "motivo_arbitraje": "sin_evidencia_fuerte_para_seleccion_dura",
                    "delta_score": round(delta_score, 4),
                    "clave": key,
                },
            )
            salida.append(rec)
        elif r_ml:
            r_ml.fuente = r_ml.fuente or "ML"
            r_ml.metadata_ensemble = {
                "decision": "seleccion_dura",
                "motivo_arbitraje": "solo_ml",
                "clave": key,
            }
            salida.append(r_ml)
        elif r_h:
            r_h.fuente = r_h.fuente or "HEURISTICO"
            r_h.metadata_ensemble = {
                "decision": "seleccion_dura",
                "motivo_arbitraje": "solo_heuristico",
                "clave": key,
            }
            salida.append(r_h)

    salida.sort(key=lambda x: float(x.score or 0.0), reverse=True)
    return salida[:10]


def _obtener_estadisticas_equipo_cached(cursor, equipo_id: str) -> Dict[str, float]:
    """Obtiene estadísticas de equipo con cache."""
    ahora = time.time()

    if equipo_id in _cache_estadisticas:
        stats, timestamp = _cache_estadisticas[equipo_id]
        if ahora - timestamp < CACHE_TTL:
            return stats

    query = """
        SELECT
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_goles_total ELSE pf.visitante_goles_total END) as goles_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_goles_total ELSE pf.local_goles_total END) as goles_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_corners_total ELSE pf.visitante_corners_total END) as corners_favor,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.visitante_corners_total ELSE pf.local_corners_total END) as corners_contra,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_total ELSE pf.visitante_disparos_total END) as disparos_total,
            AVG(CASE WHEN pf.equipo_local_id = %s THEN pf.local_disparos_arco ELSE pf.visitante_disparos_arco END) as disparos_arco,
            COUNT(*) as partidos
        FROM partidos_futbol pf
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
          AND pf.estado = 'FINALIZADO'
    """
    cursor.execute(query, [equipo_id] * 8)
    row = cursor.fetchone()

    stats = {
        "goles_favor": float(row["goles_favor"] or 0),
        "goles_contra": float(row["goles_contra"] or 0),
        "corners_favor": float(row["corners_favor"] or 0),
        "corners_contra": float(row["corners_contra"] or 0),
        "disparos_total": float(row["disparos_total"] or 0),
        "disparos_arco": float(row["disparos_arco"] or 0),
        "partidos": row["partidos"] or 0,
    }

    _cache_estadisticas[equipo_id] = (stats, ahora)
    return stats




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

# ============================================================================
# ANALISIS CONTEXTUAL PARA LINEAS (H2H + ESTADISTICAS INDIVIDUALES)
# ============================================================================

MAX_PARTIDOS_STATS = 100
MIN_PARTIDOS_H2H = 3
MIN_PARTIDOS_MUESTRA = 30
UMBRAL_ALINEACION = 0.05
UMBRAL_ALERTA = 0.20

METRIC_COLUMN_MAP: Dict[str, Tuple[str, str]] = {
    "corners_ft": ("local_corners_total", "visitante_corners_total"),
    "corners_1t": ("local_corners_1t", "visitante_corners_1t"),
    "corners_2t": ("local_corners_2t", "visitante_corners_2t"),
    "goles_ft": ("local_goles_total", "visitante_goles_total"),
    "goles_1t": ("local_goles_1t", "visitante_goles_1t"),
    "goles_2t": ("local_goles_2t", "visitante_goles_2t"),
    "disparos_ft": ("local_disparos_total", "visitante_disparos_total"),
    "disparos_arco_ft": ("local_disparos_arco", "visitante_disparos_arco"),
}

UNIDADES_MERCADO = {
    "corners": "corners",
    "goles": "goles",
    "disparos": "disparos",
    "disparos_arco": "disparos a puerta",
}

VOLATILIDAD_UMBRALES = {
    "corners": (1.5, 2.8),
    "goles": (0.7, 1.3),
    "disparos": (3.0, 5.5),
    "disparos_arco": (1.3, 2.6),
}


def _limitar_h2h_limite(limite: Optional[int]) -> int:
    """Asegura que el limite H2H este entre 5 y 20."""
    if limite is None:
        return 10
    return max(5, min(int(limite), 20))


def _parsear_mercado(mercado: str) -> Dict[str, str]:
    """Deriva base, periodo, alcance y metric_key desde el mercado."""
    mercado_upper = (mercado or "").upper()

    if mercado_upper.startswith("CORNERS"):
        base = "corners"
    elif mercado_upper.startswith("GOLES"):
        base = "goles"
    elif mercado_upper.startswith("DISPAROS_ARCO"):
        base = "disparos_arco"
    else:
        base = "disparos"

    if "_1T" in mercado_upper:
        periodo = "1t"
    elif "_2T" in mercado_upper:
        periodo = "2t"
    else:
        periodo = "ft"

    if base.startswith("disparos"):
        periodo = "ft"

    if "_LOCAL_" in mercado_upper:
        alcance = "local"
    elif "_VISITANTE_" in mercado_upper:
        alcance = "visitante"
    else:
        alcance = "total"

    metric_key = f"{base}_{periodo}"
    return {
        "base": base,
        "periodo": periodo,
        "alcance": alcance,
        "metric_key": metric_key,
        "unidad": UNIDADES_MERCADO.get(base, "valor"),
    }


def _extraer_valor_equipo(
    partido: Dict[str, Any],
    equipo_id: str,
    metric_key: str,
) -> Optional[float]:
    """Extrae el valor del equipo para una metrica dada."""
    columnas = METRIC_COLUMN_MAP.get(metric_key)
    if not columnas:
        return None
    col_local, col_visitante = columnas

    if str(partido.get("equipo_local_id")) == equipo_id:
        valor = partido.get(col_local)
    elif str(partido.get("equipo_visitante_id")) == equipo_id:
        valor = partido.get(col_visitante)
    else:
        return None

    return float(valor) if valor is not None else None


def _extraer_valor_total(
    partido: Dict[str, Any],
    metric_key: str,
) -> Optional[float]:
    """Extrae el total (local + visitante) para una metrica."""
    columnas = METRIC_COLUMN_MAP.get(metric_key)
    if not columnas:
        return None
    col_local, col_visitante = columnas
    valor_local = partido.get(col_local)
    valor_visitante = partido.get(col_visitante)
    if valor_local is None or valor_visitante is None:
        return None
    return float(valor_local) + float(valor_visitante)


def _resumen_valores(
    valores: List[float],
    incluir_std: bool = False,
    incluir_valores: bool = False,
) -> Dict[str, Any]:
    """Calcula promedio, std y rango para una lista de valores."""
    n = len(valores)
    if n == 0:
        resumen = {"n": 0, "promedio": None, "std": None, "min": None, "max": None}
        if incluir_valores:
            resumen["valores"] = []
        return resumen

    promedio = float(np.mean(valores))
    std = float(np.std(valores, ddof=1)) if incluir_std and n > 1 else None
    resumen = {
        "n": n,
        "promedio": promedio,
        "std": std,
        "min": float(min(valores)),
        "max": float(max(valores)),
    }
    if incluir_valores:
        resumen["valores"] = list(valores)
    return resumen


def _resumen_metricas_equipo(
    partidos: List[Dict[str, Any]],
    equipo_id: str,
) -> Dict[str, Dict[str, Any]]:
    """Calcula promedios por metrica para un equipo."""
    acumulados: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}

    for partido in partidos:
        for metric_key in METRIC_COLUMN_MAP:
            valor = _extraer_valor_equipo(partido, equipo_id, metric_key)
            if valor is not None:
                acumulados[metric_key].append(valor)

    return {
        metric_key: _resumen_valores(valores, incluir_std=True)
        for metric_key, valores in acumulados.items()
    }


def _resumen_metricas_liga(
    partidos: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Calcula promedios de liga por metrica (local, visitante, global y total)."""
    acumulados_local: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}
    acumulados_visitante: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}
    acumulados_total: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}
    acumulados_global: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}

    for partido in partidos:
        for metric_key, (col_local, col_visitante) in METRIC_COLUMN_MAP.items():
            valor_local = partido.get(col_local)
            valor_visitante = partido.get(col_visitante)
            if valor_local is not None:
                acumulados_local[metric_key].append(float(valor_local))
                acumulados_global[metric_key].append(float(valor_local))
            if valor_visitante is not None:
                acumulados_visitante[metric_key].append(float(valor_visitante))
                acumulados_global[metric_key].append(float(valor_visitante))
            if valor_local is not None and valor_visitante is not None:
                acumulados_total[metric_key].append(float(valor_local) + float(valor_visitante))

    return {
        "local": {
            metric_key: _resumen_valores(valores)
            for metric_key, valores in acumulados_local.items()
        },
        "visitante": {
            metric_key: _resumen_valores(valores)
            for metric_key, valores in acumulados_visitante.items()
        },
        "global": {
            metric_key: _resumen_valores(valores)
            for metric_key, valores in acumulados_global.items()
        },
        "total": {
            metric_key: _resumen_valores(valores)
            for metric_key, valores in acumulados_total.items()
        },
    }


def _resumen_metricas_h2h(
    partidos: List[Dict[str, Any]],
    equipo_local_id: str,
    equipo_visitante_id: str,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Calcula resumen H2H por metrica para local, visitante y total."""
    acumulados_local: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}
    acumulados_visitante: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}
    acumulados_total: Dict[str, List[float]] = {k: [] for k in METRIC_COLUMN_MAP}

    for partido in partidos:
        for metric_key in METRIC_COLUMN_MAP:
            valor_total = _extraer_valor_total(partido, metric_key)
            if valor_total is not None:
                acumulados_total[metric_key].append(valor_total)

            valor_local = _extraer_valor_equipo(partido, equipo_local_id, metric_key)
            if valor_local is not None:
                acumulados_local[metric_key].append(valor_local)

            valor_visitante = _extraer_valor_equipo(partido, equipo_visitante_id, metric_key)
            if valor_visitante is not None:
                acumulados_visitante[metric_key].append(valor_visitante)

    return {
        "local": {
            metric_key: _resumen_valores(valores, incluir_std=True, incluir_valores=True)
            for metric_key, valores in acumulados_local.items()
        },
        "visitante": {
            metric_key: _resumen_valores(valores, incluir_std=True, incluir_valores=True)
            for metric_key, valores in acumulados_visitante.items()
        },
        "total": {
            metric_key: _resumen_valores(valores, incluir_std=True, incluir_valores=True)
            for metric_key, valores in acumulados_total.items()
        },
    }


def _obtener_partidos_equipo(
    cursor,
    equipo_id: str,
    fecha_corte: datetime,
    limite: int,
    solo_local: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """Obtiene partidos recientes de un equipo (hasta limite)."""
    query = """
        SELECT
            pf.equipo_local_id,
            pf.equipo_visitante_id,
            pf.local_goles_1t,
            pf.local_goles_2t,
            pf.local_goles_total,
            pf.visitante_goles_1t,
            pf.visitante_goles_2t,
            pf.visitante_goles_total,
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.local_corners_total,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.visitante_corners_total,
            pf.local_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_total,
            pf.visitante_disparos_arco,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE (pf.equipo_local_id = %s OR pf.equipo_visitante_id = %s)
          AND pf.estado = 'FINALIZADO'
          AND pf.fecha_partido < %s
    """
    params: List[Any] = [equipo_id, equipo_id, fecha_corte]

    if solo_local is True:
        query += " AND pf.equipo_local_id = %s"
        params.append(equipo_id)
    elif solo_local is False:
        query += " AND pf.equipo_visitante_id = %s"
        params.append(equipo_id)

    query += " ORDER BY pf.fecha_partido DESC LIMIT %s"
    params.append(limite)

    cursor.execute(query, params)
    return cursor.fetchall()


def _obtener_partidos_liga(
    cursor,
    competicion_id: str,
    fecha_corte: datetime,
    limite: int,
) -> List[Dict[str, Any]]:
    """Obtiene partidos recientes de una liga (hasta limite)."""
    query = """
        SELECT
            pf.equipo_local_id,
            pf.equipo_visitante_id,
            pf.local_goles_1t,
            pf.local_goles_2t,
            pf.local_goles_total,
            pf.visitante_goles_1t,
            pf.visitante_goles_2t,
            pf.visitante_goles_total,
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.local_corners_total,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.visitante_corners_total,
            pf.local_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_total,
            pf.visitante_disparos_arco,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE pf.competicion_id = %s
          AND pf.estado = 'FINALIZADO'
          AND pf.fecha_partido < %s
        ORDER BY pf.fecha_partido DESC
        LIMIT %s
    """
    cursor.execute(query, [competicion_id, fecha_corte, limite])
    return cursor.fetchall()


def _obtener_partidos_h2h(
    cursor,
    equipo_local_id: str,
    equipo_visitante_id: str,
    fecha_corte: datetime,
    limite: int,
) -> List[Dict[str, Any]]:
    """Obtiene partidos H2H recientes entre dos equipos."""
    query = """
        SELECT
            pf.equipo_local_id,
            pf.equipo_visitante_id,
            pf.local_goles_1t,
            pf.local_goles_2t,
            pf.local_goles_total,
            pf.visitante_goles_1t,
            pf.visitante_goles_2t,
            pf.visitante_goles_total,
            pf.local_corners_1t,
            pf.local_corners_2t,
            pf.local_corners_total,
            pf.visitante_corners_1t,
            pf.visitante_corners_2t,
            pf.visitante_corners_total,
            pf.local_disparos_total,
            pf.local_disparos_arco,
            pf.visitante_disparos_total,
            pf.visitante_disparos_arco,
            pf.fecha_partido
        FROM partidos_futbol pf
        WHERE pf.estado = 'FINALIZADO'
          AND (
            (pf.equipo_local_id = %s AND pf.equipo_visitante_id = %s)
            OR (pf.equipo_local_id = %s AND pf.equipo_visitante_id = %s)
          )
          AND pf.fecha_partido < %s
        ORDER BY pf.fecha_partido DESC
        LIMIT %s
    """
    params = [
        equipo_local_id,
        equipo_visitante_id,
        equipo_visitante_id,
        equipo_local_id,
        fecha_corte,
        limite,
    ]
    cursor.execute(query, params)
    return cursor.fetchall()


def _calcular_pct_diferencia(valor: Optional[float], referencia: Optional[float]) -> Optional[float]:
    """Calcula porcentaje de diferencia entre valor y referencia."""
    if valor is None or referencia in (None, 0):
        return None
    return (valor - referencia) / referencia * 100.0


def _direccion_por_pct(pct: Optional[float], umbral: float = UMBRAL_ALINEACION) -> str:
    """Determina direccion segun porcentaje."""
    if pct is None:
        return "neutral"
    if pct > (umbral * 100):
        return "sube"
    if pct < -(umbral * 100):
        return "baja"
    return "neutral"


def _texto_pct_vs_liga(pct: Optional[float]) -> Optional[str]:
    """Texto de comparacion vs liga."""
    if pct is None:
        return None
    return f"{abs(pct):.0f}% {'superior' if pct > 0 else 'inferior'}"


def _clasificar_volatilidad(std: float, base: str) -> str:
    """Clasifica volatilidad segun std y base."""
    low, high = VOLATILIDAD_UMBRALES.get(base, (1.0, 2.0))
    if std <= low:
        return "baja"
    if std <= high:
        return "moderada"
    return "alta"


def _generar_razones_linea(
    mercado: str,
    linea: float,
    equipo_local: str,
    equipo_visitante: str,
    resumen_h2h: Dict[str, Dict[str, Dict[str, Any]]],
    stats_local_global: Dict[str, Dict[str, Any]],
    stats_local_home: Dict[str, Dict[str, Any]],
    stats_visitante_global: Dict[str, Dict[str, Any]],
    stats_visitante_away: Dict[str, Dict[str, Any]],
    promedios_liga: Dict[str, Dict[str, Dict[str, Any]]],
    pred_media: Optional[float] = None,
    pred_std: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Genera razones cuantitativas para una linea."""
    razones: List[Dict[str, Any]] = []
    config = _parsear_mercado(mercado)
    metric_key = config["metric_key"]
    base = config["base"]
    unidad = config["unidad"]
    alcance = config["alcance"]

    # H2H
    h2h_metric = resumen_h2h.get(alcance, {}).get(metric_key, {})
    h2h_n = h2h_metric.get("n", 0) or 0
    h2h_promedio = h2h_metric.get("promedio")
    h2h_min = h2h_metric.get("min")
    h2h_max = h2h_metric.get("max")
    h2h_std = h2h_metric.get("std")
    h2h_valores = h2h_metric.get("valores", [])

    if h2h_n > 0 and h2h_promedio is not None:
        diff_pct_h2h = _calcular_pct_diferencia(linea, h2h_promedio)
        direccion_h2h = "neutral"
        if h2h_promedio > linea:
            direccion_h2h = "sube"
        elif h2h_promedio < linea:
            direccion_h2h = "baja"

        rango_h2h = ""
        if h2h_min is not None and h2h_max is not None:
            rango_h2h = f" (rango: {h2h_min:.1f}-{h2h_max:.1f})"

        over_count = sum(1 for v in h2h_valores if v > linea)
        over_pct = (over_count / h2h_n * 100) if h2h_n else 0.0

        if h2h_n < MIN_PARTIDOS_H2H:
            razones.append(
                {
                    "factor": "Comparacion H2H",
                    "direccion": "neutral",
                    "impacto": 0.05,
                    "descripcion": (
                        f"Solo {h2h_n} H2H disponibles. Promedio H2H: "
                        f"{h2h_promedio:.1f} {unidad}{rango_h2h}. "
                        "Dato de referencia con baja robustez."
                    ),
                }
            )
        else:
            texto_diff = ""
            if diff_pct_h2h is not None:
                texto_diff = (
                    f"La linea de {linea:.1f} esta {abs(diff_pct_h2h):.0f}% "
                    f"{'por debajo' if diff_pct_h2h < 0 else 'por encima'} del promedio H2H, "
                )
            sugerencia = "OVER" if h2h_promedio > linea else "UNDER"
            descripcion = (
                f"En ultimos {h2h_n} H2H: promedio de {h2h_promedio:.1f} {unidad}{rango_h2h}. "
                f"{texto_diff}Over {linea:.1f} en {over_count}/{h2h_n} "
                f"({over_pct:.0f}%). Sugiere valor en {sugerencia}."
            )

            # Outliers
            outliers = 0
            if h2h_std and h2h_std > 0:
                outliers = sum(1 for v in h2h_valores if abs(v - h2h_promedio) > 3 * h2h_std)
            if outliers:
                descripcion += f" Se detecto {outliers} outlier (>3 sigma)."

            razones.append(
                {
                    "factor": "Comparacion H2H",
                    "direccion": direccion_h2h,
                    "impacto": 0.15,
                    "descripcion": descripcion,
                }
            )
    else:
        razones.append(
            {
                "factor": "Comparacion H2H",
                "direccion": "neutral",
                "impacto": 0.05,
                "descripcion": "Sin datos H2H suficientes para este mercado.",
            }
        )

    # Estadisticas equipo local
    local_home = stats_local_home.get(metric_key, {})
    local_global = stats_local_global.get(metric_key, {})
    local_home_avg = local_home.get("promedio")
    local_home_n = local_home.get("n", 0) or 0
    local_global_avg = local_global.get("promedio")
    local_global_n = local_global.get("n", 0) or 0

    liga_local_avg = promedios_liga.get("local", {}).get(metric_key, {}).get("promedio")
    liga_global_avg = promedios_liga.get("global", {}).get(metric_key, {}).get("promedio")

    pct_local_vs_liga = _calcular_pct_diferencia(local_home_avg, liga_local_avg)
    pct_global_vs_liga = _calcular_pct_diferencia(local_global_avg, liga_global_avg)

    texto_liga_local = _texto_pct_vs_liga(pct_local_vs_liga)
    texto_liga_global = _texto_pct_vs_liga(pct_global_vs_liga)

    if local_home_avg is not None or local_global_avg is not None:
        impacto_local = 0.12 if local_home_n >= MIN_PARTIDOS_MUESTRA else 0.08
        factor_local = "Estadisticas Local"
        if local_home_n < MIN_PARTIDOS_MUESTRA:
            factor_local += " (Muestra Limitada)"

        descripcion_local = []
        if local_home_avg is not None:
            descripcion_local.append(
                f"{equipo_local} promedia {local_home_avg:.1f} {unidad} como local "
                f"en ultimos {local_home_n} partidos."
            )
            if liga_local_avg is not None and texto_liga_local:
                descripcion_local.append(
                    f"Rendimiento {texto_liga_local} a la media de la liga "
                    f"({liga_local_avg:.1f})."
                )
        if local_global_avg is not None:
            texto_global = (
                f"Global: {local_global_avg:.1f} {unidad} en {local_global_n} partidos."
            )
            if liga_global_avg is not None and texto_liga_global:
                texto_global += f" ({texto_liga_global} vs liga {liga_global_avg:.1f})."
            descripcion_local.append(texto_global)

        direccion_local = _direccion_por_pct(pct_local_vs_liga)
        razones.append(
            {
                "factor": factor_local,
                "direccion": direccion_local,
                "impacto": impacto_local,
                "descripcion": " ".join(descripcion_local),
            }
        )
    else:
        razones.append(
            {
                "factor": "Estadisticas Local (Muestra Limitada)",
                "direccion": "neutral",
                "impacto": 0.05,
                "descripcion": (
                    f"Sin datos suficientes de {equipo_local} para {unidad} en los "
                    f"ultimos {MAX_PARTIDOS_STATS} partidos."
                ),
            }
        )

    # Estadisticas equipo visitante
    visitante_away = stats_visitante_away.get(metric_key, {})
    visitante_global = stats_visitante_global.get(metric_key, {})
    visitante_away_avg = visitante_away.get("promedio")
    visitante_away_n = visitante_away.get("n", 0) or 0
    visitante_global_avg = visitante_global.get("promedio")
    visitante_global_n = visitante_global.get("n", 0) or 0

    liga_visitante_avg = promedios_liga.get("visitante", {}).get(metric_key, {}).get("promedio")
    pct_visitante_vs_liga = _calcular_pct_diferencia(visitante_away_avg, liga_visitante_avg)
    texto_liga_visitante = _texto_pct_vs_liga(pct_visitante_vs_liga)

    if visitante_away_avg is not None or visitante_global_avg is not None:
        impacto_visitante = 0.10 if visitante_away_n >= MIN_PARTIDOS_MUESTRA else 0.07
        factor_visitante = "Estadisticas Visitante"
        if visitante_away_n < MIN_PARTIDOS_MUESTRA:
            factor_visitante += " (Muestra Limitada)"

        descripcion_visitante = []
        if visitante_away_avg is not None:
            descripcion_visitante.append(
                f"{equipo_visitante} promedia {visitante_away_avg:.1f} {unidad} como visitante "
                f"en ultimos {visitante_away_n} partidos."
            )
            if liga_visitante_avg is not None and texto_liga_visitante:
                descripcion_visitante.append(
                    f"Rendimiento {texto_liga_visitante} a la media de la liga "
                    f"como visitantes ({liga_visitante_avg:.1f})."
                )
        if visitante_global_avg is not None:
            texto_global = (
                f"Global: {visitante_global_avg:.1f} {unidad} en {visitante_global_n} partidos."
            )
            if liga_global_avg is not None and texto_liga_global:
                texto_global += f" ({texto_liga_global} vs liga {liga_global_avg:.1f})."
            descripcion_visitante.append(texto_global)

        direccion_visitante = _direccion_por_pct(pct_visitante_vs_liga)
        razones.append(
            {
                "factor": factor_visitante,
                "direccion": direccion_visitante,
                "impacto": impacto_visitante,
                "descripcion": " ".join(descripcion_visitante),
            }
        )
    else:
        razones.append(
            {
                "factor": "Estadisticas Visitante (Muestra Limitada)",
                "direccion": "neutral",
                "impacto": 0.05,
                "descripcion": (
                    f"Sin datos suficientes de {equipo_visitante} para {unidad} en los "
                    f"ultimos {MAX_PARTIDOS_STATS} partidos."
                ),
            }
        )

    # Total esperado vs linea
    esperado_local = local_home_avg if local_home_avg is not None else local_global_avg
    esperado_visitante = (
        visitante_away_avg if visitante_away_avg is not None else visitante_global_avg
    )

    esperado: Optional[float] = None
    detalle_esperado = ""
    if alcance == "total":
        if esperado_local is not None and esperado_visitante is not None:
            esperado = esperado_local + esperado_visitante
            detalle_esperado = (
                f"{esperado_local:.1f} ({equipo_local} local) + "
                f"{esperado_visitante:.1f} ({equipo_visitante} visitante)"
            )
    elif alcance == "local":
        if esperado_local is not None:
            esperado = esperado_local
            detalle_esperado = f"{esperado_local:.1f} ({equipo_local} local)"
    else:
        if esperado_visitante is not None:
            esperado = esperado_visitante
            detalle_esperado = f"{esperado_visitante:.1f} ({equipo_visitante} visitante)"

    if esperado is None and pred_media is not None:
        esperado = pred_media
        detalle_esperado = f"{pred_media:.1f} (media modelo)"

    if esperado is not None and esperado > 0:
        diff_pct_esperado = _calcular_pct_diferencia(linea, esperado)
        alineada = diff_pct_esperado is not None and abs(diff_pct_esperado) <= (UMBRAL_ALINEACION * 100)
        sugerencia = "OVER" if esperado > linea else "UNDER"
        texto_diff = ""
        if diff_pct_esperado is not None:
            texto_diff = (
                f"La linea de {linea:.1f} esta {abs(diff_pct_esperado):.0f}% "
                f"{'por debajo' if diff_pct_esperado < 0 else 'por encima'} del esperado, "
            )
        etiqueta_esperado = "Total esperado" if alcance == "total" else "Esperado del equipo"
        referencia_esperado = etiqueta_esperado.lower()
        descripcion_total = (
            f"{etiqueta_esperado} basado en estadisticas individuales: {detalle_esperado} = "
            f"{esperado:.1f} {unidad}. {texto_diff}"
            f"linea {'alineada' if alineada else 'desalineada'} "
            f"con el {referencia_esperado}. Indica oportunidad potencial en {sugerencia}."
        )

        direccion_total = "sube" if esperado > linea else "baja"
        if alineada:
            direccion_total = "neutral"

        razones.append(
            {
                "factor": "Alineacion Historica",
                "direccion": direccion_total,
                "impacto": 0.12,
                "descripcion": descripcion_total,
            }
        )

        # Alerta por linea anomala
        if diff_pct_esperado is not None and abs(diff_pct_esperado) >= (UMBRAL_ALERTA * 100):
            referencia_alerta = "total esperado" if alcance == "total" else "esperado del equipo"
            razones.append(
                {
                    "factor": "ALERTA: Linea Anomala",
                    "direccion": "neutral",
                    "impacto": 0.15,
                    "descripcion": (
                        f"La linea de {linea:.1f} esta {abs(diff_pct_esperado):.0f}% "
                        f"{'por debajo' if diff_pct_esperado < 0 else 'por encima'} "
                        f"del {referencia_alerta} ({esperado:.1f} {unidad}). "
                        "Diferencia inusualmente alta. Podria indicar informacion del mercado "
                        "sobre lesiones/alineaciones, error en la linea o trampa del bookmaker. "
                        "Recomendacion: revisar noticias recientes antes de apostar."
                    ),
                }
            )

    # Volatilidad
    if h2h_std is not None and h2h_std > 0:
        margen_95 = 1.96 * h2h_std
        nivel_vol = _clasificar_volatilidad(h2h_std, base)
        razones.append(
            {
                "factor": "Volatilidad del Mercado",
                "direccion": "neutral",
                "impacto": 0.05,
                "descripcion": (
                    f"Desviacion estandar H2H: {h2h_std:.1f} {unidad}. "
                    f"Volatilidad {nivel_vol} sugiere margen de +/-{margen_95:.1f} "
                    f"{unidad} (95% de los casos)."
                ),
            }
        )
    elif pred_std is not None and pred_std > 0:
        razones.append(
            {
                "factor": "Volatilidad del Mercado",
                "direccion": "neutral",
                "impacto": 0.05,
                "descripcion": (
                    f"Desviacion estandar del modelo: {pred_std:.1f} {unidad}. "
                    "Volatilidad estimada ante H2H insuficiente."
                ),
            }
        )

    return razones


def _agregar_razones_a_mercados(
    mercados: Dict[str, PrediccionMercado],
    equipo_local: str,
    equipo_visitante: str,
    resumen_h2h: Dict[str, Dict[str, Dict[str, Any]]],
    stats_local_global: Dict[str, Dict[str, Any]],
    stats_local_home: Dict[str, Dict[str, Any]],
    stats_visitante_global: Dict[str, Dict[str, Any]],
    stats_visitante_away: Dict[str, Dict[str, Any]],
    promedios_liga: Dict[str, Dict[str, Dict[str, Any]]],
) -> None:
    """Enriquece cada linea con razones."""
    for prediccion in mercados.values():
        for linea_str, prob in prediccion.lineas.items():
            try:
                linea = float(linea_str)
            except (TypeError, ValueError):
                continue
            razones = _generar_razones_linea(
                mercado=prediccion.mercado,
                linea=linea,
                equipo_local=equipo_local,
                equipo_visitante=equipo_visitante,
                resumen_h2h=resumen_h2h,
                stats_local_global=stats_local_global,
                stats_local_home=stats_local_home,
                stats_visitante_global=stats_visitante_global,
                stats_visitante_away=stats_visitante_away,
                promedios_liga=promedios_liga,
                pred_media=prediccion.media,
                pred_std=prediccion.std,
            )
            prob.razones = razones

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


def _determinar_confianza(
    prob: float,
    partidos_local: int,
    partidos_visitante: int,
    partidos_relevantes: int,
) -> str:
    """Determina confianza usando muestra total y muestra relevante (B3)."""
    n_total = max(0, min(int(partidos_local or 0), int(partidos_visitante or 0)))
    n_relevante = max(0, int(partidos_relevantes or 0))

    confianza = nivel_confianza_b3(prob=prob, n_total=n_total, n_relevante=n_relevante)
    if confianza == "ALTA" and (prob >= 0.88 or prob <= 0.12):
        return "MUY_ALTA"
    return confianza


def _generar_predicciones_mercado(
    tipo_base: str,
    media: float,
    std: float,
    lineas: List[float],
    calibrador: Optional[Any] = None,
    distribucion: str = "normal",
) -> PrediccionMercado:
    """Genera predicciones para un mercado específico."""
    lineas_dict = {}

    # Penalización conservadora de confianza cuando la varianza es alta
    factor_conservador = 1.0
    if std > 5.0:
        factor_conservador = 0.85
    elif std > 3.0:
        factor_conservador = 0.92

    for linea in lineas:
        prob_over_raw = _calcular_probabilidad_over(media, std, linea, distribucion=distribucion)
        prob_over_raw = 0.5 + (prob_over_raw - 0.5) * factor_conservador
        prob_over_raw = float(max(0.02, min(0.98, prob_over_raw)))
        prob_under_raw = 1.0 - prob_over_raw

        # Aplicar calibración si está disponible
        if calibrador is not None:
            try:
                prob_over_cal = float(calibrador.transform([[prob_over_raw]])[0])
                prob_over_cal = float(max(0.02, min(0.98, prob_over_cal)))
                prob_under_cal = 1.0 - prob_over_cal
            except Exception:
                prob_over_cal = prob_over_raw
                prob_under_cal = prob_under_raw
        else:
            prob_over_cal = prob_over_raw
            prob_under_cal = prob_under_raw

        lineas_dict[str(linea)] = ProbabilidadLinea(
            over_raw=round(prob_over_raw, 4),
            over_calibrada=round(prob_over_cal, 4),
            under_raw=round(prob_under_raw, 4),
            under_calibrada=round(prob_under_cal, 4),
        )

    return PrediccionMercado(
        mercado=tipo_base,
        media=round(media, 2),
        std=round(std, 2),
        lineas=lineas_dict,
    )


def _obtener_resumen_seguro(
    contenedor: Dict[str, Dict[str, Any]],
    clave: str,
) -> Dict[str, Any]:
    return contenedor.get(clave, {}) if contenedor else {}


def _valor_robusto(
    *,
    valor_ctx: Optional[float],
    n_ctx: int,
    valor_global: Optional[float],
    n_global: int,
    valor_liga: Optional[float],
) -> float:
    """Combina contexto local/visitante + global + liga con pesos por muestra."""
    piezas: List[Tuple[float, float]] = []

    if valor_ctx is not None and n_ctx > 0:
        peso_ctx = min(0.65, 0.2 + (n_ctx / 40.0))
        piezas.append((valor_ctx, peso_ctx))

    if valor_global is not None and n_global > 0:
        peso_global = min(0.45, 0.15 + (n_global / 120.0))
        piezas.append((valor_global, peso_global))

    if valor_liga is not None:
        piezas.append((valor_liga, 0.25))

    if not piezas:
        return 0.0

    suma_pesos = sum(p for _, p in piezas)
    if suma_pesos <= 0:
        return float(piezas[0][0])

    return float(sum(v * p for v, p in piezas) / suma_pesos)


def _std_robusta(
    *,
    std_ctx: Optional[float],
    std_global: Optional[float],
    default_std: float,
) -> float:
    base = std_ctx or std_global or default_std
    return float(max(base, default_std * 0.55))


def _media_reciente_metrica(
    partidos: List[Dict[str, Any]],
    equipo_id: str,
    metric_key: str,
    limite: int = 5,
) -> Optional[float]:
    """Calcula media reciente para capturar forma (últimos N partidos)."""
    if not partidos:
        return None
    valores: List[float] = []
    for partido in partidos[:limite]:
        v = _extraer_valor_equipo(partido, equipo_id, metric_key)
        if v is not None:
            valores.append(v)
    if not valores:
        return None
    return float(np.mean(valores))


def _aplicar_ajuste_forma(
    valor_base: float,
    reciente: Optional[float],
    referencia: Optional[float],
    cap_pct: float = 0.12,
) -> float:
    """Ajuste de forma reciente con tope para evitar sobreajuste."""
    if reciente is None or referencia in (None, 0):
        return valor_base
    delta_pct = (reciente - referencia) / referencia
    delta_pct = max(-cap_pct, min(cap_pct, delta_pct))
    return float(valor_base * (1.0 + delta_pct * 0.35))


def _home_advantage_liga(
    promedios_liga: Dict[str, Dict[str, Dict[str, Any]]],
    metric_key: str,
) -> float:
    """Factor de ventaja local por mercado basado en liga (profesional, pero conservador)."""
    local_avg = _obtener_resumen_seguro(promedios_liga.get("local", {}), metric_key).get("promedio")
    vis_avg = _obtener_resumen_seguro(promedios_liga.get("visitante", {}), metric_key).get("promedio")
    if local_avg in (None, 0) or vis_avg is None:
        return 1.0
    ratio = float(local_avg if vis_avg == 0 else (local_avg / vis_avg))
    return max(0.95, min(1.08, ratio))


def _obtener_estado_mercados_futbol(
    cursor,
    *,
    min_muestras: int = 100,
    warning_brier: float = 0.24,
    bloquear_brier: float = 0.28,
) -> Dict[str, str]:
    """Retorna estado por mercado: verde|amarillo|rojo."""
    try:
        cursor.execute(
            """
            SELECT mercado::text,
                   COUNT(*) AS n,
                   AVG(
                     POWER(
                       COALESCE(prob_over_calibrada, prob_over)
                       - CASE WHEN outcome_binario THEN 1 ELSE 0 END,
                       2
                     )
                   ) AS brier
            FROM predicciones_futbol
            WHERE outcome_binario IS NOT NULL
              AND COALESCE(prob_over_calibrada, prob_over) IS NOT NULL
            GROUP BY mercado
            HAVING COUNT(*) >= %s
            """,
            [min_muestras],
        )
        estado: Dict[str, str] = {}
        for mercado, _n, brier in cursor.fetchall():
            m = str(mercado).upper()
            b = float(brier) if brier is not None else None
            if b is None:
                continue
            if b >= bloquear_brier:
                estado[m] = "rojo"
            elif b >= warning_brier:
                estado[m] = "amarillo"
            else:
                estado[m] = "verde"
        return estado
    except Exception:
        logger.exception("No se pudo calcular estado de mercados fútbol")
        return {}


def _obtener_mercados_bloqueados_por_brier(
    cursor,
    *,
    min_muestras: int = 100,
    umbral_brier: float = 0.28,
) -> set[str]:
    """Mercados a bloquear automáticamente por baja calidad histórica."""
    try:
        cursor.execute(
            """
            SELECT mercado::text
            FROM predicciones_futbol
            WHERE outcome_binario IS NOT NULL
              AND COALESCE(prob_over_calibrada, prob_over) IS NOT NULL
            GROUP BY mercado
            HAVING COUNT(*) >= %s
               AND AVG(
                    POWER(
                      COALESCE(prob_over_calibrada, prob_over)
                      - CASE WHEN outcome_binario THEN 1 ELSE 0 END,
                      2
                    )
               ) >= %s
            """,
            [min_muestras, umbral_brier],
        )
        return {str(r[0]).upper() for r in cursor.fetchall()}
    except Exception:
        logger.exception("No se pudo calcular política de bloqueo por Brier")
        return set()


def _modo_estricto_futbol_activo(cursor, minimo_predicciones: int = 100) -> bool:
    """Si hay volumen pero cero resueltas, bloquear recomendaciones."""
    try:
        cursor.execute(
            """
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltas
            FROM predicciones_futbol
            """
        )
        row = cursor.fetchone()
        total = int(row[0] or 0)
        resueltas = int(row[1] or 0)
        return total >= minimo_predicciones and resueltas == 0
    except Exception:
        logger.exception("No se pudo evaluar modo estricto de fútbol")
        return False


def _generar_recomendaciones(
    mercados: Dict[str, PrediccionMercado],
    partidos_local: int,
    partidos_visitante: int,
    partidos_relevantes: int,
    umbral_prob: float = 0.55,
    modelo_version_id: Optional[str] = None,
    cuotas_por_linea: Optional[Dict[str, Dict[str, float]]] = None,
    estado_mercados: Optional[Dict[str, str]] = None,
    fuente: str = "HEURISTICO",
) -> List[RecomendacionApuesta]:
    """Genera recomendaciones de apuestas basadas en las predicciones."""
    recomendaciones = []

    for mercado_key, prediccion in mercados.items():
        mercado_estado = (estado_mercados or {}).get(str(prediccion.mercado).upper(), "verde")
        for linea_str, probs in prediccion.lineas.items():
            linea = float(linea_str)
            cuota_over, cuota_under = _obtener_cuotas_para_recomendacion(
                cuotas_por_linea,
                str(prediccion.mercado),
                linea,
            )

            prob_over_ajustada = ajustar_probabilidad_por_muestras(
                probs.over_calibrada, n_total=min(partidos_local, partidos_visitante), n_relevante=partidos_relevantes
            )
            prob_under_ajustada = ajustar_probabilidad_por_muestras(
                probs.under_calibrada, n_total=min(partidos_local, partidos_visitante), n_relevante=partidos_relevantes
            )

            # Evaluar OVER
            if prob_over_ajustada >= umbral_prob:
                confianza = _determinar_confianza(
                    prob_over_ajustada, partidos_local, partidos_visitante, partidos_relevantes
                )
                m_over = _calcular_metricas_mercado(
                    lado="OVER",
                    prob_raw=float(probs.over_raw),
                    prob_cal=float(prob_over_ajustada),
                    cuota_over=cuota_over,
                    cuota_under=cuota_under,
                    std=float(prediccion.std),
                    mercado_estado=mercado_estado,
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="OVER",
                    linea=linea,
                    probabilidad=prob_over_ajustada,
                    confianza=confianza,
                    valor_esperado=m_over["valor_esperado"],
                    p_raw=float(probs.over_raw),
                    p_calibrada=float(prob_over_ajustada),
                    modelo_version_id=modelo_version_id,
                    calibrador_id=None,
                    edge_real=m_over["edge_real"],
                    score=m_over["score"],
                    sizing=m_over["sizing"],
                    cuota=m_over["cuota_lado"],
                    cuota_over=m_over["cuota_over"],
                    cuota_under=m_over["cuota_under"],
                    devig_metodo=m_over["devig_metodo"],
                    devig_overround=m_over["devig_overround"],
                    devig_p_mkt_fair=m_over["devig_p_mkt_fair"],
                    advertencias=m_over["advertencias"],
                    fuente=fuente,
                    metadata_ensemble={"mercado_estado": mercado_estado, "llave": _clave_recomendacion(prediccion.mercado, "OVER", linea)},
                ))

            # Evaluar UNDER
            if prob_under_ajustada >= umbral_prob:
                confianza = _determinar_confianza(
                    prob_under_ajustada, partidos_local, partidos_visitante, partidos_relevantes
                )
                m_under = _calcular_metricas_mercado(
                    lado="UNDER",
                    prob_raw=float(probs.under_raw),
                    prob_cal=float(prob_under_ajustada),
                    cuota_over=cuota_over,
                    cuota_under=cuota_under,
                    std=float(prediccion.std),
                    mercado_estado=mercado_estado,
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="UNDER",
                    linea=linea,
                    probabilidad=prob_under_ajustada,
                    confianza=confianza,
                    valor_esperado=m_under["valor_esperado"],
                    p_raw=float(probs.under_raw),
                    p_calibrada=float(prob_under_ajustada),
                    modelo_version_id=modelo_version_id,
                    calibrador_id=None,
                    edge_real=m_under["edge_real"],
                    score=m_under["score"],
                    sizing=m_under["sizing"],
                    cuota=m_under["cuota_lado"],
                    cuota_over=m_under["cuota_over"],
                    cuota_under=m_under["cuota_under"],
                    devig_metodo=m_under["devig_metodo"],
                    devig_overround=m_under["devig_overround"],
                    devig_p_mkt_fair=m_under["devig_p_mkt_fair"],
                    advertencias=m_under["advertencias"],
                    fuente=fuente,
                    metadata_ensemble={"mercado_estado": mercado_estado, "llave": _clave_recomendacion(prediccion.mercado, "UNDER", linea)},
                ))

    # Ordenar por score descendente (fallback a probabilidad)
    recomendaciones.sort(key=lambda x: (x.score if x.score is not None else x.probabilidad), reverse=True)
    return recomendaciones[:10]  # Top 10 recomendaciones


def _obtener_modelo_version_futbol_id(cursor) -> Optional[int]:
    """Obtiene un modelo_version_id válido para FK de predicciones_futbol."""
    try:
        cursor.execute(
            """
            SELECT id
            FROM modelo_versiones_futbol
            ORDER BY creado_en DESC NULLS LAST, id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return None
        return int(row["id"] if isinstance(row, dict) else row[0])
    except Exception:
        logger.exception("No se pudo obtener modelo_version_id de modelo_versiones_futbol")
        return None


def _registrar_predicciones_futbol(
    cursor,
    *,
    partido: Dict[str, Any],
    mercados: Dict[str, PrediccionMercado],
    modelo_version_id: Optional[int],
) -> int:
    """Persiste predicciones por línea en predicciones_futbol."""
    filas = []

    for prediccion in mercados.values():
        mercado = (prediccion.mercado or "").upper()
        for linea_str, probs in prediccion.lineas.items():
            try:
                linea_valor = float(linea_str)
            except (TypeError, ValueError):
                continue

            filas.append(
                [
                    str(uuid4()),
                    str(partido["id"]),
                    modelo_version_id,
                    str(partido["competicion_id"]),
                    str(partido["temporada_id"]),
                    str(partido["equipo_local_id"]),
                    str(partido["equipo_visitante_id"]),
                    partido["equipo_local"],
                    partido["equipo_visitante"],
                    partido["fecha_partido"],
                    mercado,
                    linea_valor,
                    False,
                    float(prediccion.media),
                    float(prediccion.std),
                    float(probs.over_raw),
                    float(probs.under_raw),
                    float(probs.over_calibrada),
                    float(probs.under_calibrada),
                    float(prediccion.media - 1.96 * prediccion.std),
                    float(prediccion.media + 1.96 * prediccion.std),
                    95,
                ]
            )

    if not filas:
        return 0

    cursor.executemany(
        """
        INSERT INTO predicciones_futbol (
            id,
            partido_id,
            modelo_version_id,
            competicion_id,
            temporada_id,
            equipo_local_id,
            equipo_visitante_id,
            equipo_local_nombre,
            equipo_visitante_nombre,
            fecha_partido,
            mercado,
            linea,
            linea_es_sintetica,
            media_predicha,
            desviacion_predicha,
            prob_over,
            prob_under,
            prob_over_calibrada,
            prob_under_calibrada,
            intervalo_inferior,
            intervalo_superior,
            nivel_intervalo
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::mercado_futbol, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        """,
        filas,
    )

    return len(filas)


@router.post(
    "/analizar",
    response_model=AnalisisResponse,
    summary="Analizar partido",
    description="Analiza un partido y genera predicciones para los 24 mercados de fútbol.",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def analizar_partido(
    request: AnalisisRequest,
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
) -> AnalisisResponse:
    """
    Analiza un partido y genera predicciones para todos los mercados.

    Este es el endpoint principal del sistema de predicción de fútbol.
    """
    inicio = time.time()
    pool = obtener_pool()

    # 1. Validar que el partido existe y es analizable
    partido_query = """
        SELECT
            pf.id,
            pf.competicion_id,
            pf.temporada_id,
            c.nombre as competicion,
            c.codigo as competicion_codigo,
            pf.fecha_partido,
            el.nombre as equipo_local,
            ev.nombre as equipo_visitante,
            pf.estado,
            pf.jornada,
            pf.equipo_local_id,
            pf.equipo_visitante_id
        FROM partidos_futbol pf
        JOIN competiciones_futbol c ON pf.competicion_id = c.id
        JOIN equipos_futbol el ON pf.equipo_local_id = el.id
        JOIN equipos_futbol ev ON pf.equipo_visitante_id = ev.id
        WHERE pf.id = %s
    """

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(partido_query, [str(request.partido_id)])
                partido = cursor.fetchone()

                if not partido:
                    raise HTTPException(
                        status_code=404,
                        detail="Partido no encontrado"
                    )

                estado_partido = str(partido["estado"] or "").upper()
                estados_no_analizables = {
                    "FINALIZADO",
                    "CANCELADO",
                    "POSTERGADO",
                    "POSPUESTO",
                    "APLAZADO",
                    "SUSPENDIDO",
                }
                if estado_partido in estados_no_analizables:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No se puede analizar un partido con estado: {estado_partido}",
                    )

                # 2. Intentar flujo principal ML (P1: PredictorFutbol)
                lineas_corners = request.lineas_corners or [8.5, 9.5, 10.5, 11.5]
                lineas_goles = request.lineas_goles or [1.5, 2.5, 3.5]
                lineas_disparos = request.lineas_disparos or [22.5, 24.5, 26.5]

                mercados_corners_ml: Dict[str, PrediccionMercado] = {}
                mercados_goles_ml: Dict[str, PrediccionMercado] = {}
                mercados_disparos_ml: Dict[str, PrediccionMercado] = {}
                recomendaciones_ml: List[RecomendacionApuesta] = []
                prediccion_ganador_ml: Optional[ProbabilidadesGanadorFutbol] = None
                modelo_version_ml: Optional[str] = None

                if MOTOR_DISPONIBLE:
                    predictor_ml = _obtener_predictor_futbol_ml(pool)
                    if predictor_ml is not None and predictor_ml.modelos_entrenados:
                        try:
                            pred_ml = predictor_ml.predecir_partido(request.partido_id)
                            gestor_calibradores = _obtener_gestor_calibradores_futbol(pool)

                            mercados_corners_ml = {
                                k: _convertir_mercado_ml_a_schema(v, lineas_corners, gestor_calibradores)
                                for k, v in (pred_ml.mercados_corners or {}).items()
                            }
                            mercados_goles_ml = {
                                k: _convertir_mercado_ml_a_schema(v, lineas_goles, gestor_calibradores)
                                for k, v in (pred_ml.mercados_goles or {}).items()
                            }
                            mercados_disparos_ml = {
                                k: _convertir_mercado_ml_a_schema(v, lineas_disparos, gestor_calibradores)
                                for k, v in (pred_ml.mercados_disparos or {}).items()
                            }

                            recomendaciones_ml = _recomendaciones_ml_a_api(
                                pred_ml.recomendaciones,
                                getattr(pred_ml.nivel_confianza, "value", pred_ml.nivel_confianza),
                            )
                            prediccion_ganador_ml = _prediccion_ganador_desde_mercados_ml(
                                pred_ml.mercados_goles or {}
                            )
                            modelo_version_ml = pred_ml.version_modelo or "ml_predictor"

                            logger.info(
                                "Señal ML de fútbol disponible para ensemble (partido_id=%s)",
                                request.partido_id,
                            )
                        except Exception:
                            logger.exception(
                                "Fallo flujo ML principal en /api/futbol/analizar; se mantiene heurístico"
                            )

                # 3. Fallback heurístico actual (base para ensemble)
                equipo_local_id = str(partido["equipo_local_id"])
                equipo_visitante_id = str(partido["equipo_visitante_id"])

                stats_local = _obtener_estadisticas_equipo_cached(cursor, equipo_local_id)
                stats_visitante = _obtener_estadisticas_equipo_cached(cursor, equipo_visitante_id)

                if stats_local["partidos"] < 3:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Datos insuficientes para {partido['equipo_local']}"
                    )

                if stats_visitante["partidos"] < 3:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Datos insuficientes para {partido['equipo_visitante']}"
                    )

                # 2b. Contexto H2H + estadisticas recientes (hasta 100 partidos)
                competicion_id = str(partido["competicion_id"])
                fecha_corte = partido.get("fecha_partido") or datetime.now()
                limite_h2h = _limitar_h2h_limite(request.h2h_limite)

                try:
                    partidos_h2h = _obtener_partidos_h2h(
                        cursor,
                        equipo_local_id,
                        equipo_visitante_id,
                        fecha_corte,
                        limite_h2h,
                    )
                    partidos_local_global = _obtener_partidos_equipo(
                        cursor, equipo_local_id, fecha_corte, MAX_PARTIDOS_STATS, None
                    )
                    partidos_local_home = _obtener_partidos_equipo(
                        cursor, equipo_local_id, fecha_corte, MAX_PARTIDOS_STATS, True
                    )
                    partidos_visitante_global = _obtener_partidos_equipo(
                        cursor, equipo_visitante_id, fecha_corte, MAX_PARTIDOS_STATS, None
                    )
                    partidos_visitante_away = _obtener_partidos_equipo(
                        cursor, equipo_visitante_id, fecha_corte, MAX_PARTIDOS_STATS, False
                    )
                    partidos_liga = _obtener_partidos_liga(
                        cursor, competicion_id, fecha_corte, MAX_PARTIDOS_STATS
                    )

                    resumen_h2h = _resumen_metricas_h2h(
                        partidos_h2h, equipo_local_id, equipo_visitante_id
                    )
                    stats_local_global = _resumen_metricas_equipo(
                        partidos_local_global, equipo_local_id
                    )
                    stats_local_home = _resumen_metricas_equipo(
                        partidos_local_home, equipo_local_id
                    )
                    stats_visitante_global = _resumen_metricas_equipo(
                        partidos_visitante_global, equipo_visitante_id
                    )
                    stats_visitante_away = _resumen_metricas_equipo(
                        partidos_visitante_away, equipo_visitante_id
                    )
                    promedios_liga = _resumen_metricas_liga(partidos_liga)
                except Exception as e:
                    logger.warning(f"Error calculando contexto H2H/estadisticas: {e}")
                    resumen_h2h = {"local": {}, "visitante": {}, "total": {}}
                    stats_local_global = {}
                    stats_local_home = {}
                    stats_visitante_global = {}
                    stats_visitante_away = {}
                    promedios_liga = {"local": {}, "visitante": {}, "global": {}, "total": {}}

                # 3. Calcular predicciones base (robustas: contexto + global + liga)
                local_corners_ctx = _obtener_resumen_seguro(stats_local_home, "corners_ft")
                local_corners_global = _obtener_resumen_seguro(stats_local_global, "corners_ft")
                vis_corners_ctx = _obtener_resumen_seguro(stats_visitante_away, "corners_ft")
                vis_corners_global = _obtener_resumen_seguro(stats_visitante_global, "corners_ft")
                liga_corners = _obtener_resumen_seguro(promedios_liga.get("global", {}), "corners_ft")

                corners_local = combinar_valor_cross_liga(
                    valor_ctx=local_corners_ctx.get("promedio"),
                    n_ctx=int(local_corners_ctx.get("n") or 0),
                    valor_global=local_corners_global.get("promedio"),
                    n_global=int(local_corners_global.get("n") or 0),
                    valor_liga=liga_corners.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                corners_visitante = combinar_valor_cross_liga(
                    valor_ctx=vis_corners_ctx.get("promedio"),
                    n_ctx=int(vis_corners_ctx.get("n") or 0),
                    valor_global=vis_corners_global.get("promedio"),
                    n_global=int(vis_corners_global.get("n") or 0),
                    valor_liga=liga_corners.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                # Ajuste por forma reciente + ventaja local
                corners_local = _aplicar_ajuste_forma(
                    corners_local,
                    _media_reciente_metrica(partidos_local_home, equipo_local_id, "corners_ft"),
                    local_corners_ctx.get("promedio") or local_corners_global.get("promedio"),
                )
                corners_visitante = _aplicar_ajuste_forma(
                    corners_visitante,
                    _media_reciente_metrica(partidos_visitante_away, equipo_visitante_id, "corners_ft"),
                    vis_corners_ctx.get("promedio") or vis_corners_global.get("promedio"),
                )
                ha_corners = _home_advantage_liga(promedios_liga, "corners_ft")
                corners_local *= ha_corners
                corners_visitante /= ha_corners

                corners_total = corners_local + corners_visitante
                corners_std = _std_robusta(
                    std_ctx=local_corners_ctx.get("std") or vis_corners_ctx.get("std"),
                    std_global=local_corners_global.get("std") or vis_corners_global.get("std"),
                    default_std=2.5,
                )

                local_goles_ctx = _obtener_resumen_seguro(stats_local_home, "goles_ft")
                local_goles_global = _obtener_resumen_seguro(stats_local_global, "goles_ft")
                vis_goles_ctx = _obtener_resumen_seguro(stats_visitante_away, "goles_ft")
                vis_goles_global = _obtener_resumen_seguro(stats_visitante_global, "goles_ft")
                liga_goles = _obtener_resumen_seguro(promedios_liga.get("global", {}), "goles_ft")

                goles_local = combinar_valor_cross_liga(
                    valor_ctx=local_goles_ctx.get("promedio"),
                    n_ctx=int(local_goles_ctx.get("n") or 0),
                    valor_global=local_goles_global.get("promedio"),
                    n_global=int(local_goles_global.get("n") or 0),
                    valor_liga=liga_goles.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                goles_visitante = combinar_valor_cross_liga(
                    valor_ctx=vis_goles_ctx.get("promedio"),
                    n_ctx=int(vis_goles_ctx.get("n") or 0),
                    valor_global=vis_goles_global.get("promedio"),
                    n_global=int(vis_goles_global.get("n") or 0),
                    valor_liga=liga_goles.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                goles_local = _aplicar_ajuste_forma(
                    goles_local,
                    _media_reciente_metrica(partidos_local_home, equipo_local_id, "goles_ft"),
                    local_goles_ctx.get("promedio") or local_goles_global.get("promedio"),
                )
                goles_visitante = _aplicar_ajuste_forma(
                    goles_visitante,
                    _media_reciente_metrica(partidos_visitante_away, equipo_visitante_id, "goles_ft"),
                    vis_goles_ctx.get("promedio") or vis_goles_global.get("promedio"),
                )
                ha_goles = _home_advantage_liga(promedios_liga, "goles_ft")
                goles_local *= ha_goles
                goles_visitante /= ha_goles

                goles_total = goles_local + goles_visitante
                goles_std = _std_robusta(
                    std_ctx=local_goles_ctx.get("std") or vis_goles_ctx.get("std"),
                    std_global=local_goles_global.get("std") or vis_goles_global.get("std"),
                    default_std=1.2,
                )

                local_disp_ctx = _obtener_resumen_seguro(stats_local_home, "disparos_ft")
                local_disp_global = _obtener_resumen_seguro(stats_local_global, "disparos_ft")
                vis_disp_ctx = _obtener_resumen_seguro(stats_visitante_away, "disparos_ft")
                vis_disp_global = _obtener_resumen_seguro(stats_visitante_global, "disparos_ft")
                liga_disp = _obtener_resumen_seguro(promedios_liga.get("global", {}), "disparos_ft")

                disparos_local = combinar_valor_cross_liga(
                    valor_ctx=local_disp_ctx.get("promedio"),
                    n_ctx=int(local_disp_ctx.get("n") or 0),
                    valor_global=local_disp_global.get("promedio"),
                    n_global=int(local_disp_global.get("n") or 0),
                    valor_liga=liga_disp.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                disparos_visitante = combinar_valor_cross_liga(
                    valor_ctx=vis_disp_ctx.get("promedio"),
                    n_ctx=int(vis_disp_ctx.get("n") or 0),
                    valor_global=vis_disp_global.get("promedio"),
                    n_global=int(vis_disp_global.get("n") or 0),
                    valor_liga=liga_disp.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                disparos_local = _aplicar_ajuste_forma(
                    disparos_local,
                    _media_reciente_metrica(partidos_local_home, equipo_local_id, "disparos_ft"),
                    local_disp_ctx.get("promedio") or local_disp_global.get("promedio"),
                )
                disparos_visitante = _aplicar_ajuste_forma(
                    disparos_visitante,
                    _media_reciente_metrica(partidos_visitante_away, equipo_visitante_id, "disparos_ft"),
                    vis_disp_ctx.get("promedio") or vis_disp_global.get("promedio"),
                )
                ha_disp = _home_advantage_liga(promedios_liga, "disparos_ft")
                disparos_local *= ha_disp
                disparos_visitante /= ha_disp

                disparos_total = disparos_local + disparos_visitante
                disparos_std = _std_robusta(
                    std_ctx=local_disp_ctx.get("std") or vis_disp_ctx.get("std"),
                    std_global=local_disp_global.get("std") or vis_disp_global.get("std"),
                    default_std=4.0,
                )

                # 4. Generar predicciones para cada mercado (P3: sin porcentajes fijos)
                lineas_corners = request.lineas_corners or [8.5, 9.5, 10.5, 11.5]
                lineas_goles = request.lineas_goles or [1.5, 2.5, 3.5]
                lineas_disparos = request.lineas_disparos or [22.5, 24.5, 26.5]

                # Contar calibradores activos
                cursor.execute(
                    "SELECT COUNT(*) FROM calibradores_futbol WHERE activo = true"
                )
                calibradores_activos = cursor.fetchone()["count"]

                # Corners por tiempo/modelo explícito
                local_corners_1t_ctx = _obtener_resumen_seguro(stats_local_home, "corners_1t")
                local_corners_2t_ctx = _obtener_resumen_seguro(stats_local_home, "corners_2t")
                vis_corners_1t_ctx = _obtener_resumen_seguro(stats_visitante_away, "corners_1t")
                vis_corners_2t_ctx = _obtener_resumen_seguro(stats_visitante_away, "corners_2t")
                local_corners_1t_global = _obtener_resumen_seguro(stats_local_global, "corners_1t")
                local_corners_2t_global = _obtener_resumen_seguro(stats_local_global, "corners_2t")
                vis_corners_1t_global = _obtener_resumen_seguro(stats_visitante_global, "corners_1t")
                vis_corners_2t_global = _obtener_resumen_seguro(stats_visitante_global, "corners_2t")
                liga_corners_1t = _obtener_resumen_seguro(promedios_liga.get("global", {}), "corners_1t")
                liga_corners_2t = _obtener_resumen_seguro(promedios_liga.get("global", {}), "corners_2t")

                corners_local_1t = combinar_valor_cross_liga(
                    valor_ctx=local_corners_1t_ctx.get("promedio"),
                    n_ctx=int(local_corners_1t_ctx.get("n") or 0),
                    valor_global=local_corners_1t_global.get("promedio"),
                    n_global=int(local_corners_1t_global.get("n") or 0),
                    valor_liga=liga_corners_1t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                corners_local_2t = combinar_valor_cross_liga(
                    valor_ctx=local_corners_2t_ctx.get("promedio"),
                    n_ctx=int(local_corners_2t_ctx.get("n") or 0),
                    valor_global=local_corners_2t_global.get("promedio"),
                    n_global=int(local_corners_2t_global.get("n") or 0),
                    valor_liga=liga_corners_2t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                corners_visitante_1t = combinar_valor_cross_liga(
                    valor_ctx=vis_corners_1t_ctx.get("promedio"),
                    n_ctx=int(vis_corners_1t_ctx.get("n") or 0),
                    valor_global=vis_corners_1t_global.get("promedio"),
                    n_global=int(vis_corners_1t_global.get("n") or 0),
                    valor_liga=liga_corners_1t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                corners_visitante_2t = combinar_valor_cross_liga(
                    valor_ctx=vis_corners_2t_ctx.get("promedio"),
                    n_ctx=int(vis_corners_2t_ctx.get("n") or 0),
                    valor_global=vis_corners_2t_global.get("promedio"),
                    n_global=int(vis_corners_2t_global.get("n") or 0),
                    valor_liga=liga_corners_2t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )

                corners_1t_total = corners_local_1t + corners_visitante_1t
                corners_2t_total = corners_local_2t + corners_visitante_2t
                corners_local_ft = corners_local_1t + corners_local_2t
                corners_visitante_ft = corners_visitante_1t + corners_visitante_2t

                corners_1t_std = _std_robusta(
                    std_ctx=local_corners_1t_ctx.get("std") or vis_corners_1t_ctx.get("std"),
                    std_global=local_corners_1t_global.get("std") or vis_corners_1t_global.get("std"),
                    default_std=1.8,
                )
                corners_2t_std = _std_robusta(
                    std_ctx=local_corners_2t_ctx.get("std") or vis_corners_2t_ctx.get("std"),
                    std_global=local_corners_2t_global.get("std") or vis_corners_2t_global.get("std"),
                    default_std=1.8,
                )
                corners_local_ft_std = _std_robusta(
                    std_ctx=local_corners_ctx.get("std"),
                    std_global=local_corners_global.get("std"),
                    default_std=2.0,
                )
                corners_visitante_ft_std = _std_robusta(
                    std_ctx=vis_corners_ctx.get("std"),
                    std_global=vis_corners_global.get("std"),
                    default_std=2.0,
                )

                # Goles por tiempo/modelo explícito
                local_goles_1t_ctx = _obtener_resumen_seguro(stats_local_home, "goles_1t")
                local_goles_2t_ctx = _obtener_resumen_seguro(stats_local_home, "goles_2t")
                vis_goles_1t_ctx = _obtener_resumen_seguro(stats_visitante_away, "goles_1t")
                vis_goles_2t_ctx = _obtener_resumen_seguro(stats_visitante_away, "goles_2t")
                local_goles_1t_global = _obtener_resumen_seguro(stats_local_global, "goles_1t")
                local_goles_2t_global = _obtener_resumen_seguro(stats_local_global, "goles_2t")
                vis_goles_1t_global = _obtener_resumen_seguro(stats_visitante_global, "goles_1t")
                vis_goles_2t_global = _obtener_resumen_seguro(stats_visitante_global, "goles_2t")
                liga_goles_1t = _obtener_resumen_seguro(promedios_liga.get("global", {}), "goles_1t")
                liga_goles_2t = _obtener_resumen_seguro(promedios_liga.get("global", {}), "goles_2t")

                goles_local_1t = combinar_valor_cross_liga(
                    valor_ctx=local_goles_1t_ctx.get("promedio"),
                    n_ctx=int(local_goles_1t_ctx.get("n") or 0),
                    valor_global=local_goles_1t_global.get("promedio"),
                    n_global=int(local_goles_1t_global.get("n") or 0),
                    valor_liga=liga_goles_1t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                goles_local_2t = combinar_valor_cross_liga(
                    valor_ctx=local_goles_2t_ctx.get("promedio"),
                    n_ctx=int(local_goles_2t_ctx.get("n") or 0),
                    valor_global=local_goles_2t_global.get("promedio"),
                    n_global=int(local_goles_2t_global.get("n") or 0),
                    valor_liga=liga_goles_2t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                goles_visitante_1t = combinar_valor_cross_liga(
                    valor_ctx=vis_goles_1t_ctx.get("promedio"),
                    n_ctx=int(vis_goles_1t_ctx.get("n") or 0),
                    valor_global=vis_goles_1t_global.get("promedio"),
                    n_global=int(vis_goles_1t_global.get("n") or 0),
                    valor_liga=liga_goles_1t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                goles_visitante_2t = combinar_valor_cross_liga(
                    valor_ctx=vis_goles_2t_ctx.get("promedio"),
                    n_ctx=int(vis_goles_2t_ctx.get("n") or 0),
                    valor_global=vis_goles_2t_global.get("promedio"),
                    n_global=int(vis_goles_2t_global.get("n") or 0),
                    valor_liga=liga_goles_2t.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )

                goles_1t_total = goles_local_1t + goles_visitante_1t
                goles_2t_total = goles_local_2t + goles_visitante_2t
                goles_local_ft = goles_local_1t + goles_local_2t
                goles_visitante_ft = goles_visitante_1t + goles_visitante_2t

                goles_1t_std = _std_robusta(
                    std_ctx=local_goles_1t_ctx.get("std") or vis_goles_1t_ctx.get("std"),
                    std_global=local_goles_1t_global.get("std") or vis_goles_1t_global.get("std"),
                    default_std=0.8,
                )
                goles_2t_std = _std_robusta(
                    std_ctx=local_goles_2t_ctx.get("std") or vis_goles_2t_ctx.get("std"),
                    std_global=local_goles_2t_global.get("std") or vis_goles_2t_global.get("std"),
                    default_std=0.9,
                )
                goles_local_ft_std = _std_robusta(
                    std_ctx=local_goles_ctx.get("std"),
                    std_global=local_goles_global.get("std"),
                    default_std=1.0,
                )
                goles_visitante_ft_std = _std_robusta(
                    std_ctx=vis_goles_ctx.get("std"),
                    std_global=vis_goles_global.get("std"),
                    default_std=1.0,
                )

                # Disparos a puerta explícitos (sin ratio fijo)
                local_disp_arco_ctx = _obtener_resumen_seguro(stats_local_home, "disparos_arco_ft")
                vis_disp_arco_ctx = _obtener_resumen_seguro(stats_visitante_away, "disparos_arco_ft")
                local_disp_arco_global = _obtener_resumen_seguro(stats_local_global, "disparos_arco_ft")
                vis_disp_arco_global = _obtener_resumen_seguro(stats_visitante_global, "disparos_arco_ft")
                liga_disp_arco = _obtener_resumen_seguro(promedios_liga.get("global", {}), "disparos_arco_ft")

                disparos_arco_local = combinar_valor_cross_liga(
                    valor_ctx=local_disp_arco_ctx.get("promedio"),
                    n_ctx=int(local_disp_arco_ctx.get("n") or 0),
                    valor_global=local_disp_arco_global.get("promedio"),
                    n_global=int(local_disp_arco_global.get("n") or 0),
                    valor_liga=liga_disp_arco.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                disparos_arco_visitante = combinar_valor_cross_liga(
                    valor_ctx=vis_disp_arco_ctx.get("promedio"),
                    n_ctx=int(vis_disp_arco_ctx.get("n") or 0),
                    valor_global=vis_disp_arco_global.get("promedio"),
                    n_global=int(vis_disp_arco_global.get("n") or 0),
                    valor_liga=liga_disp_arco.get("promedio"),
                    codigo_competicion=partido.get("competicion_codigo"),
                )
                disparos_arco_total = disparos_arco_local + disparos_arco_visitante
                disparos_arco_std = _std_robusta(
                    std_ctx=local_disp_arco_ctx.get("std") or vis_disp_arco_ctx.get("std"),
                    std_global=local_disp_arco_global.get("std") or vis_disp_arco_global.get("std"),
                    default_std=2.2,
                )
                disparos_local_std = _std_robusta(
                    std_ctx=local_disp_ctx.get("std"),
                    std_global=local_disp_global.get("std"),
                    default_std=3.2,
                )
                disparos_visitante_std = _std_robusta(
                    std_ctx=vis_disp_ctx.get("std"),
                    std_global=vis_disp_global.get("std"),
                    default_std=3.2,
                )
                disparos_arco_local_std = _std_robusta(
                    std_ctx=local_disp_arco_ctx.get("std"),
                    std_global=local_disp_arco_global.get("std"),
                    default_std=1.8,
                )
                disparos_arco_visitante_std = _std_robusta(
                    std_ctx=vis_disp_arco_ctx.get("std"),
                    std_global=vis_disp_arco_global.get("std"),
                    default_std=1.8,
                )

                # Mercados de Corners
                mercados_corners = {
                    "CORNERS_FT": _generar_predicciones_mercado(
                        "CORNERS_FT", corners_total, corners_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_1T": _generar_predicciones_mercado(
                        "CORNERS_1T", corners_1t_total, corners_1t_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_2T": _generar_predicciones_mercado(
                        "CORNERS_2T", corners_2t_total, corners_2t_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_LOCAL_FT": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_FT", corners_local_ft, corners_local_ft_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_LOCAL_1T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_1T", corners_local_1t, corners_1t_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_LOCAL_2T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_2T", corners_local_2t, corners_2t_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_VISITANTE_FT": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_FT", corners_visitante_ft, corners_visitante_ft_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_VISITANTE_1T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_1T", corners_visitante_1t, corners_1t_std, lineas_corners, distribucion="nbinom"
                    ),
                    "CORNERS_VISITANTE_2T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_2T", corners_visitante_2t, corners_2t_std, lineas_corners, distribucion="nbinom"
                    ),
                }

                # Mercados de Goles
                mercados_goles = {
                    "GOLES_FT": _generar_predicciones_mercado(
                        "GOLES_FT", goles_total, goles_std, lineas_goles
                    ),
                    "GOLES_1T": _generar_predicciones_mercado(
                        "GOLES_1T", goles_1t_total, goles_1t_std, lineas_goles
                    ),
                    "GOLES_2T": _generar_predicciones_mercado(
                        "GOLES_2T", goles_2t_total, goles_2t_std, lineas_goles
                    ),
                    "GOLES_LOCAL_FT": _generar_predicciones_mercado(
                        "GOLES_LOCAL_FT", goles_local_ft, goles_local_ft_std, lineas_goles
                    ),
                    "GOLES_LOCAL_1T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_1T", goles_local_1t, goles_1t_std, lineas_goles
                    ),
                    "GOLES_LOCAL_2T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_2T", goles_local_2t, goles_2t_std, lineas_goles
                    ),
                    "GOLES_VISITANTE_FT": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_FT", goles_visitante_ft, goles_visitante_ft_std, lineas_goles
                    ),
                    "GOLES_VISITANTE_1T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_1T", goles_visitante_1t, goles_1t_std, lineas_goles
                    ),
                    "GOLES_VISITANTE_2T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_2T", goles_visitante_2t, goles_2t_std, lineas_goles
                    ),
                }

                # Mercados de Disparos
                mercados_disparos = {
                    "DISPAROS_FT": _generar_predicciones_mercado(
                        "DISPAROS_FT", disparos_total, disparos_std, lineas_disparos, distribucion="nbinom"
                    ),
                    "DISPAROS_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_ARCO_FT", disparos_arco_total, disparos_arco_std, lineas_disparos, distribucion="nbinom"
                    ),
                    "DISPAROS_LOCAL_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_FT", disparos_local, disparos_local_std, lineas_disparos, distribucion="nbinom"
                    ),
                    "DISPAROS_LOCAL_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_ARCO_FT", disparos_arco_local, disparos_arco_local_std, lineas_disparos, distribucion="nbinom"
                    ),
                    "DISPAROS_VISITANTE_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_FT", disparos_visitante, disparos_visitante_std, lineas_disparos, distribucion="nbinom"
                    ),
                    "DISPAROS_VISITANTE_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_ARCO_FT", disparos_arco_visitante, disparos_arco_visitante_std, lineas_disparos, distribucion="nbinom"
                    ),
                }

                # 4b. Enriquecer con razones por linea
                _agregar_razones_a_mercados(
                    mercados_corners,
                    partido["equipo_local"],
                    partido["equipo_visitante"],
                    resumen_h2h,
                    stats_local_global,
                    stats_local_home,
                    stats_visitante_global,
                    stats_visitante_away,
                    promedios_liga,
                )
                _agregar_razones_a_mercados(
                    mercados_goles,
                    partido["equipo_local"],
                    partido["equipo_visitante"],
                    resumen_h2h,
                    stats_local_global,
                    stats_local_home,
                    stats_visitante_global,
                    stats_visitante_away,
                    promedios_liga,
                )
                _agregar_razones_a_mercados(
                    mercados_disparos,
                    partido["equipo_local"],
                    partido["equipo_visitante"],
                    resumen_h2h,
                    stats_local_global,
                    stats_local_home,
                    stats_visitante_global,
                    stats_visitante_away,
                    promedios_liga,
                )

                # 5. Ensemble ML + heurístico (P5)
                if mercados_corners_ml or mercados_goles_ml or mercados_disparos_ml:
                    mercados_corners = _ensamblar_mercados(mercados_corners_ml, mercados_corners, peso_ml=0.65)
                    mercados_goles = _ensamblar_mercados(mercados_goles_ml, mercados_goles, peso_ml=0.65)
                    mercados_disparos = _ensamblar_mercados(mercados_disparos_ml, mercados_disparos, peso_ml=0.65)

                # 5a. Estado de calidad por mercado (insumo para scoring/arbitraje)
                estado_mercados = _obtener_estado_mercados_futbol(
                    cursor,
                    min_muestras=100,
                    warning_brier=0.24,
                    bloquear_brier=0.28,
                )

                # 5b. Generar recomendaciones heurísticas con pipeline de decisión completo
                todos_mercados = {**mercados_corners, **mercados_goles, **mercados_disparos}
                partidos_relevantes = min(
                    int(local_corners_ctx.get("n") or 0),
                    int(vis_corners_ctx.get("n") or 0),
                )
                recomendaciones_heur = _generar_recomendaciones(
                    todos_mercados,
                    stats_local["partidos"],
                    stats_visitante["partidos"],
                    partidos_relevantes,
                    modelo_version_id=(f"ensemble::{modelo_version_ml}" if modelo_version_ml else "heuristico::1.0.0"),
                    cuotas_por_linea=request.cuotas_por_linea,
                    estado_mercados=estado_mercados,
                    fuente="HEURISTICO",
                )

                # 5c. Arbitraje/dedupe de señales (P5.1)
                recomendaciones = _arbitrar_recomendaciones(
                    recomendaciones_ml,
                    recomendaciones_heur,
                    estado_mercados=estado_mercados,
                    partidos_relevantes=partidos_relevantes,
                )
                mercados_bloqueados = {m for m, s in estado_mercados.items() if s == "rojo"}

                recomendaciones_filtradas = []
                for r in recomendaciones:
                    mercado_r = str(r.mercado).upper()
                    estado = estado_mercados.get(mercado_r, "verde")
                    if estado == "rojo":
                        continue
                    # Modo seguro: en amarillo exigimos mayor probabilidad mínima
                    if estado == "amarillo" and float(r.probabilidad) < 0.60:
                        continue
                    recomendaciones_filtradas.append(r)

                if len(recomendaciones_filtradas) != len(recomendaciones):
                    recomendaciones = recomendaciones_filtradas
                    logger.info(
                        "Policy gate fútbol aplicado. bloqueados=%s recomendaciones_restantes=%s",
                        sorted(mercados_bloqueados),
                        len(recomendaciones),
                    )

                # 5a-bis. Gate global de modo estricto (fútbol)
                if _modo_estricto_futbol_activo(cursor):
                    recomendaciones = []
                    logger.warning(
                        "Modo estricto fútbol activo: recomendaciones deshabilitadas por falta de resueltas con volumen suficiente."
                    )

                # 5b. Registrar predicciones para calibración/métricas
                try:
                    modelo_version_id_futbol = _obtener_modelo_version_futbol_id(cursor)
                    total_registradas = _registrar_predicciones_futbol(
                        cursor,
                        partido=partido,
                        mercados=todos_mercados,
                        modelo_version_id=modelo_version_id_futbol,
                    )
                    logger.info(
                        "Predicciones fútbol registradas: %s (partido_id=%s)",
                        total_registradas,
                        partido["id"],
                    )
                except Exception as e:
                    logger.exception(
                        "Error registrando predicciones_futbol (partido_id=%s): %s",
                        partido["id"],
                        e,
                    )

                # 6. Construir respuesta
                partido_resumen = PartidoResumen(
                    id=partido["id"],
                    competicion=partido["competicion"],
                    fecha_partido=partido["fecha_partido"],
                    equipo_local=partido["equipo_local"],
                    equipo_visitante=partido["equipo_visitante"],
                    estado=partido["estado"],
                    jornada=partido["jornada"],
                )

                prob_local, prob_empate, prob_visitante, marcador_probable = _calcular_1x2_dixon_coles(goles_local, goles_visitante)
                if prediccion_ganador_ml is not None:
                    prob_local = 0.65 * float(prediccion_ganador_ml.prob_local) + 0.35 * float(prob_local)
                    prob_empate = 0.65 * float(prediccion_ganador_ml.prob_empate) + 0.35 * float(prob_empate)
                    prob_visitante = 0.65 * float(prediccion_ganador_ml.prob_visitante) + 0.35 * float(prob_visitante)
                    total_1x2 = prob_local + prob_empate + prob_visitante
                    if total_1x2 > 0:
                        prob_local, prob_empate, prob_visitante = (
                            prob_local / total_1x2,
                            prob_empate / total_1x2,
                            prob_visitante / total_1x2,
                        )
                ganador_probable = "LOCAL" if prob_local >= prob_empate and prob_local >= prob_visitante else ("VISITANTE" if prob_visitante >= prob_empate else "EMPATE")
                diferencial_xg = goles_local - goles_visitante
                razones_1x2 = [
                    f"Diferencial esperado de gol: {diferencial_xg:+.2f} ({partido['equipo_local']} vs {partido['equipo_visitante']}).",
                    f"Probabilidades 1X2: Local {prob_local*100:.1f}%, Empate {prob_empate*100:.1f}%, Visitante {prob_visitante*100:.1f}%.",
                    f"Marcador más probable según modelo Dixon-Coles: {marcador_probable}.",
                    f"Base ofensiva estimada: xG local {goles_local:.2f} y xG visitante {goles_visitante:.2f}.",
                ]

                try:
                    if recomendaciones:
                        for rec in recomendaciones:
                            payload = {
                                "fuente": "analisis_futbol",
                                "partido": {
                                    "equipo_local": partido["equipo_local"],
                                    "equipo_visitante": partido["equipo_visitante"],
                                },
                                "prediccion_ganador": {
                                    "prob_local": prob_local,
                                    "prob_empate": prob_empate,
                                    "prob_visitante": prob_visitante,
                                    "ganador_probable": ganador_probable,
                                    "marcador_probable": marcador_probable,
                                },
                                "decision": {
                                    "p_raw": rec.p_raw,
                                    "p_calibrada": rec.p_calibrada,
                                    "edge_real": rec.edge_real,
                                    "score": rec.score,
                                    "sizing": rec.sizing,
                                    "valor_esperado": rec.valor_esperado,
                                    "calibrador_id": rec.calibrador_id,
                                    "modelo_version_id": rec.modelo_version_id,
                                    "fuente": rec.fuente,
                                    "metadata_ensemble": rec.metadata_ensemble,
                                    "devig_metodo": rec.devig_metodo,
                                    "devig_overround": rec.devig_overround,
                                    "devig_p_mkt_fair": rec.devig_p_mkt_fair,
                                    "cuota": rec.cuota,
                                    "cuota_over": rec.cuota_over,
                                    "cuota_under": rec.cuota_under,
                                    "advertencias": rec.advertencias,
                                },
                            }
                            registrar_apuesta_analizada(
                                deporte="futbol",
                                partido_id=str(partido["id"]),
                                mercado=rec.mercado,
                                lado=rec.lado,
                                linea=float(rec.linea),
                                probabilidad_sistema=float(rec.probabilidad),
                                confianza=rec.confianza,
                                payload_json=json.dumps(payload, ensure_ascii=False),
                                decision_p_raw=rec.p_raw,
                                decision_p_calibrada=rec.p_calibrada,
                                decision_edge_real=rec.edge_real,
                                decision_score=rec.score,
                                decision_sizing=rec.sizing,
                                decision_valor_esperado=rec.valor_esperado,
                                decision_calibrador_id=rec.calibrador_id,
                                decision_modelo_version_id=rec.modelo_version_id,
                                decision_fuente=rec.fuente,
                                decision_devig_metodo=rec.devig_metodo,
                                decision_devig_overround=rec.devig_overround,
                                decision_devig_p_mkt_fair=rec.devig_p_mkt_fair,
                                decision_cuota=rec.cuota,
                                decision_cuota_over=rec.cuota_over,
                                decision_cuota_under=rec.cuota_under,
                            )
                    else:
                        payload = {
                            "fuente": "analisis_futbol",
                            "sin_recomendaciones": True,
                            "prediccion_ganador": {
                                "prob_local": prob_local,
                                "prob_empate": prob_empate,
                                "prob_visitante": prob_visitante,
                                "ganador_probable": ganador_probable,
                                "marcador_probable": marcador_probable,
                            },
                        }
                        registrar_apuesta_analizada(
                            deporte="futbol",
                            partido_id=str(partido["id"]),
                            mercado="ANALISIS_FT",
                            lado=None,
                            linea=None,
                            probabilidad_sistema=max(prob_local, prob_empate, prob_visitante),
                            confianza="MEDIA",
                            payload_json=json.dumps(payload, ensure_ascii=False),
                        )
                except Exception:
                    logger.exception("No se pudo registrar análisis de fútbol en bitácora")

                duracion = time.time() - inicio
                logger.info(f"Análisis completado en {duracion:.2f}s para partido {request.partido_id}")

                return AnalisisResponse(
                    exito=True,
                    partido=partido_resumen,
                    timestamp_analisis=datetime.now(),
                    mercados_corners=mercados_corners,
                    mercados_goles=mercados_goles,
                    mercados_disparos=mercados_disparos,
                    recomendaciones=recomendaciones,
                    modelo_version=(f"ensemble::{modelo_version_ml}" if modelo_version_ml else "heuristico::1.0.0"),
                    calibradores_activos=calibradores_activos,
                    prediccion_ganador=ProbabilidadesGanadorFutbol(
                        prob_local=prob_local,
                        prob_empate=prob_empate,
                        prob_visitante=prob_visitante,
                        ganador_probable=ganador_probable,
                        marcador_probable=marcador_probable,
                        razones=razones_1x2,
                    ),
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando partido {request.partido_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

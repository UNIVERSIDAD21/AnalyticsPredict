# -*- coding: utf-8 -*-
"""
rutas_analisis_futbol.py — Endpoint principal de análisis de partidos de fútbol.

Este es el endpoint más importante del sistema. Genera predicciones para los
24 mercados de fútbol utilizando los modelos Ridge entrenados.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from psycopg.rows import dict_row
from scipy import stats

from db import obtener_pool
from .schemas_futbol import (
    AnalisisRequest,
    AnalisisResponse,
    PartidoResumen,
    PrediccionMercado,
    ProbabilidadLinea,
    RecomendacionApuesta,
    ErrorResponse,
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
        metric_key: _resumen_valores(valores)
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

def _calcular_probabilidad_over(media: float, std: float, linea: float) -> float:
    """Calcula P(over) usando distribución normal."""
    if std <= 0:
        std = 1.0
    z = (linea - media) / std
    return 1.0 - stats.norm.cdf(z)


def _determinar_confianza(prob: float, partidos_local: int, partidos_visitante: int) -> str:
    """Determina el nivel de confianza de una recomendación."""
    # Factores
    datos_suficientes = partidos_local >= 5 and partidos_visitante >= 5
    prob_extrema = prob >= 0.75 or prob <= 0.25

    if datos_suficientes and prob_extrema:
        if prob >= 0.85 or prob <= 0.15:
            return "MUY_ALTA"
        return "ALTA"
    elif datos_suficientes:
        return "MEDIA"
    elif prob_extrema:
        return "MEDIA"
    else:
        return "BAJA"


def _generar_predicciones_mercado(
    tipo_base: str,
    media: float,
    std: float,
    lineas: List[float],
    calibrador: Optional[Any] = None,
) -> PrediccionMercado:
    """Genera predicciones para un mercado específico."""
    lineas_dict = {}

    for linea in lineas:
        prob_over_raw = _calcular_probabilidad_over(media, std, linea)
        prob_under_raw = 1.0 - prob_over_raw

        # Aplicar calibración si está disponible
        if calibrador is not None:
            try:
                prob_over_cal = float(calibrador.transform([[prob_over_raw]])[0])
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


def _generar_recomendaciones(
    mercados: Dict[str, PrediccionMercado],
    partidos_local: int,
    partidos_visitante: int,
    umbral_prob: float = 0.55,
) -> List[RecomendacionApuesta]:
    """Genera recomendaciones de apuestas basadas en las predicciones."""
    recomendaciones = []

    for mercado_key, prediccion in mercados.items():
        for linea_str, probs in prediccion.lineas.items():
            linea = float(linea_str)

            # Evaluar OVER
            if probs.over_calibrada >= umbral_prob:
                confianza = _determinar_confianza(
                    probs.over_calibrada, partidos_local, partidos_visitante
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="OVER",
                    linea=linea,
                    probabilidad=probs.over_calibrada,
                    confianza=confianza,
                ))

            # Evaluar UNDER
            if probs.under_calibrada >= umbral_prob:
                confianza = _determinar_confianza(
                    probs.under_calibrada, partidos_local, partidos_visitante
                )
                recomendaciones.append(RecomendacionApuesta(
                    mercado=prediccion.mercado,
                    lado="UNDER",
                    linea=linea,
                    probabilidad=probs.under_calibrada,
                    confianza=confianza,
                ))

    # Ordenar por probabilidad descendente
    recomendaciones.sort(key=lambda x: x.probabilidad, reverse=True)
    return recomendaciones[:10]  # Top 10 recomendaciones


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
            c.nombre as competicion,
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

                if partido["estado"] == "FINALIZADO":
                    raise HTTPException(
                        status_code=400,
                        detail="No se puede analizar un partido finalizado"
                    )

                # 2. Obtener estadísticas de equipos
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

                # 3. Calcular predicciones base
                # Corners
                corners_local = stats_local["corners_favor"]
                corners_visitante = stats_visitante["corners_favor"]
                corners_total = corners_local + corners_visitante
                corners_std = 2.5  # Std típica para corners

                # Goles
                goles_local = stats_local["goles_favor"]
                goles_visitante = stats_visitante["goles_favor"]
                goles_total = goles_local + goles_visitante
                goles_std = 1.2

                # Disparos
                disparos_local = stats_local["disparos_total"]
                disparos_visitante = stats_visitante["disparos_total"]
                disparos_total = disparos_local + disparos_visitante
                disparos_std = 4.0

                # 4. Generar predicciones para cada mercado
                lineas_corners = request.lineas_corners or [8.5, 9.5, 10.5, 11.5]
                lineas_goles = request.lineas_goles or [1.5, 2.5, 3.5]
                lineas_disparos = request.lineas_disparos or [22.5, 24.5, 26.5]

                # Contar calibradores activos
                cursor.execute(
                    "SELECT COUNT(*) FROM calibradores_futbol WHERE activo = true"
                )
                calibradores_activos = cursor.fetchone()["count"]

                # Mercados de Corners
                mercados_corners = {
                    "CORNERS_FT": _generar_predicciones_mercado(
                        "CORNERS_FT", corners_total, corners_std, lineas_corners
                    ),
                    "CORNERS_1T": _generar_predicciones_mercado(
                        "CORNERS_1T", corners_total * 0.45, corners_std * 0.7, lineas_corners
                    ),
                    "CORNERS_2T": _generar_predicciones_mercado(
                        "CORNERS_2T", corners_total * 0.55, corners_std * 0.7, lineas_corners
                    ),
                    "CORNERS_LOCAL_FT": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_FT", corners_local, corners_std * 0.6, lineas_corners
                    ),
                    "CORNERS_LOCAL_1T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_1T", corners_local * 0.45, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_LOCAL_2T": _generar_predicciones_mercado(
                        "CORNERS_LOCAL_2T", corners_local * 0.55, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_VISITANTE_FT": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_FT", corners_visitante, corners_std * 0.6, lineas_corners
                    ),
                    "CORNERS_VISITANTE_1T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_1T", corners_visitante * 0.45, corners_std * 0.5, lineas_corners
                    ),
                    "CORNERS_VISITANTE_2T": _generar_predicciones_mercado(
                        "CORNERS_VISITANTE_2T", corners_visitante * 0.55, corners_std * 0.5, lineas_corners
                    ),
                }

                # Mercados de Goles
                mercados_goles = {
                    "GOLES_FT": _generar_predicciones_mercado(
                        "GOLES_FT", goles_total, goles_std, lineas_goles
                    ),
                    "GOLES_1T": _generar_predicciones_mercado(
                        "GOLES_1T", goles_total * 0.40, goles_std * 0.7, lineas_goles
                    ),
                    "GOLES_2T": _generar_predicciones_mercado(
                        "GOLES_2T", goles_total * 0.60, goles_std * 0.7, lineas_goles
                    ),
                    "GOLES_LOCAL_FT": _generar_predicciones_mercado(
                        "GOLES_LOCAL_FT", goles_local, goles_std * 0.6, lineas_goles
                    ),
                    "GOLES_LOCAL_1T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_1T", goles_local * 0.40, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_LOCAL_2T": _generar_predicciones_mercado(
                        "GOLES_LOCAL_2T", goles_local * 0.60, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_VISITANTE_FT": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_FT", goles_visitante, goles_std * 0.6, lineas_goles
                    ),
                    "GOLES_VISITANTE_1T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_1T", goles_visitante * 0.40, goles_std * 0.5, lineas_goles
                    ),
                    "GOLES_VISITANTE_2T": _generar_predicciones_mercado(
                        "GOLES_VISITANTE_2T", goles_visitante * 0.60, goles_std * 0.5, lineas_goles
                    ),
                }

                # Mercados de Disparos
                mercados_disparos = {
                    "DISPAROS_FT": _generar_predicciones_mercado(
                        "DISPAROS_FT", disparos_total, disparos_std, lineas_disparos
                    ),
                    "DISPAROS_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_ARCO_FT", disparos_total * 0.35, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_LOCAL_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_FT", disparos_local, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_LOCAL_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_LOCAL_ARCO_FT", disparos_local * 0.35, disparos_std * 0.5, lineas_disparos
                    ),
                    "DISPAROS_VISITANTE_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_FT", disparos_visitante, disparos_std * 0.6, lineas_disparos
                    ),
                    "DISPAROS_VISITANTE_ARCO_FT": _generar_predicciones_mercado(
                        "DISPAROS_VISITANTE_ARCO_FT", disparos_visitante * 0.35, disparos_std * 0.5, lineas_disparos
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

                # 5. Generar recomendaciones
                todos_mercados = {**mercados_corners, **mercados_goles, **mercados_disparos}
                recomendaciones = _generar_recomendaciones(
                    todos_mercados,
                    stats_local["partidos"],
                    stats_visitante["partidos"],
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
                    modelo_version="1.0.0",
                    calibradores_activos=calibradores_activos,
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando partido {request.partido_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# -*- coding: utf-8 -*-
"""
rutas_metricas_futbol.py — Endpoints para métricas del sistema de fútbol.
"""

from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Literal, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from db import obtener_pool
from metricas_probabilisticas import resumir_pares_binarios
from motor_futbol.madurez_beta import clasificar_madurez_mercado, CRITERIOS_DEFAULT
from .schemas_futbol import (
    MetricasCalibracion,
    MetricasRendimiento,
    MetricasModelo,
    EstadoModelos,
    ResumenSistema,
    ListaMetricasCalibracionResponse,
    ListaMetricasRendimientoResponse,
    ReporteMadurezFutbolResponse,
    MadurezMercadoFutbol,
    ErrorResponse,
)

router = APIRouter(prefix="/api/futbol/metricas", tags=["Fútbol - Métricas"])
logger = logging.getLogger(__name__)


UMBRAL_DEGRADACION_BRIER_ABS = 0.03
UMBRAL_DEGRADACION_BRIER_REL = 0.15
MIN_MUESTRA_SEMANAL_B3 = 40


def _tabla_existe(cursor, tabla: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        [tabla],
    )
    return cursor.fetchone()["exists"]


def _columna_existe(cursor, tabla: str, columna: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        )
        """,
        [tabla, columna],
    )
    return cursor.fetchone()["exists"]


def _obtener_metricas_desde_calibradores(
    cursor,
    mercado: Optional[str],
    periodo: Literal["semana", "mes", "temporada", "todo"],
) -> ListaMetricasCalibracionResponse:
    """Sin outcomes verificables no se publican métricas de calibración."""
    if not _tabla_existe(cursor, "calibradores_futbol"):
        return ListaMetricasCalibracionResponse(exito=True, periodo=periodo, metricas=[])
    query = "SELECT mercado, metodo FROM calibradores_futbol WHERE activo = true"
    params: List[str] = []
    if mercado and mercado != "todos":
        query += " AND mercado = %s"
        params.append(mercado.upper())
    cursor.execute(query, params)
    return ListaMetricasCalibracionResponse(
        exito=True,
        periodo=periodo,
        metricas=[MetricasCalibracion(
            mercado=fila["mercado"], n_predicciones=0,
            calibrador_activo=True, metodo_calibrador=fila["metodo"],
        ) for fila in cursor.fetchall()],
    )


def _resolver_columna_estado_apuestas(cursor) -> Optional[str]:
    canonica = "estado"
    for columna in ("estado", "resultado", "status"):
        if _columna_existe(cursor, "apuestas_futbol", columna):
            if columna != canonica:
                logger.warning(
                    "[anti-drift] apuestas_futbol usa columna legacy '%s' para estado (canónica '%s')",
                    columna,
                    canonica,
                )
            return columna
    logger.warning("[anti-drift] No existe columna de estado en apuestas_futbol")
    return None


def _resolver_columna_ganancia_apuestas(cursor) -> Optional[str]:  # CORREGIDO
    canonica = "ganancia"
    for columna in ("ganancia", "ganancia_real", "ganancia_neta", "beneficio_real", "beneficio"):
        if _columna_existe(cursor, "apuestas_futbol", columna):
            if columna != canonica:
                logger.warning(
                    "[anti-drift] apuestas_futbol usa columna legacy '%s' para ganancia (canónica '%s')",
                    columna,
                    canonica,
                )
            return columna
    logger.warning("[anti-drift] No existe columna de ganancia en apuestas_futbol")
    return None


def _resolver_columna_modelo(cursor, columnas: List[str]) -> Optional[str]:  # CORREGIDO
    for columna in columnas:
        if _columna_existe(cursor, "modelo_versiones_futbol", columna):
            return columna
    return None


def _ece_binario(probabilidades: List[float], outcomes: List[int], bins: int = 10) -> Optional[float]:
    if len(probabilidades) != len(outcomes):
        raise ValueError("Probabilidades y outcomes deben corresponder uno a uno")
    return resumir_pares_binarios(zip(probabilidades, outcomes), n_bins=bins)["ece"]


def _metricas_probabilidades_binarias(probabilidades: List[float], outcomes: List[int]) -> dict:
    """Brier, ECE y Log Loss empíricos sobre pares resueltos válidos."""
    if len(probabilidades) != len(outcomes):
        raise ValueError("Probabilidades y outcomes deben corresponder uno a uno")
    resultado = resumir_pares_binarios(zip(probabilidades, outcomes))
    return {clave: resultado[clave] for clave in ("n", "brier", "ece", "log_loss")}


def _estado_mercados_futbol(cursor, min_muestras: int = 100, warning_brier: float = 0.24, bloquear_brier: float = 0.28) -> Dict[str, str]:
    try:
        cursor.execute(
            """
            SELECT mercado::text,
                   COUNT(*) AS n,
                   AVG(POWER(COALESCE(CASE WHEN calibrador_id IS NOT NULL THEN prob_over_calibrada END, prob_over_raw, prob_over) - outcome_binario::int, 2)) AS brier
            FROM predicciones_futbol
            WHERE outcome_binario IS NOT NULL
              AND COALESCE(CASE WHEN calibrador_id IS NOT NULL THEN prob_over_calibrada END, prob_over_raw, prob_over) IS NOT NULL
            GROUP BY mercado
            HAVING COUNT(*) >= %s
            """,
            [min_muestras],
        )
        out: Dict[str, str] = {}
        for row in cursor.fetchall():
            m = str(row["mercado"]).upper()
            b = float(row["brier"]) if row.get("brier") is not None else None
            if b is None:
                continue
            if b >= bloquear_brier:
                out[m] = "rojo"
            elif b >= warning_brier:
                out[m] = "amarillo"
            else:
                out[m] = "verde"
        return out
    except Exception:
        logger.exception("No se pudo calcular estado de mercados en endpoint de madurez")
        return {}


@router.get(
    "/estado-operativo-mercados",
    summary="Estado operativo vigente por mercado (fútbol)",
    description="Retorna estado vigente por mercado desde tabla canónica si existe.",
)
async def obtener_estado_operativo_mercados(
) -> Dict[str, Any]:
    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            if not _tabla_existe(cursor, "futbol_estado_operativo_mercado"):
                return {"exito": True, "disponible": False, "mercados": []}
            cursor.execute(
                """
                SELECT mercado, estado_operativo, fuente, motivos, vigente_desde
                FROM futbol_estado_operativo_mercado
                WHERE vigente_hasta IS NULL
                ORDER BY mercado
                """
            )
            rows = cursor.fetchall()
            return {
                "exito": True,
                "disponible": True,
                "mercados": [dict(r) for r in rows],
            }


def _days_by_window(window: str) -> int:
    w = str(window).lower().strip()
    if w in {"semanal", "7d", "week"}:
        return 7
    if w in {"quincenal", "15d", "fortnight"}:
        return 15
    if w in {"mensual", "30d", "month"}:
        return 30
    return 30


@router.get(
    "/shadow-operativo",
    summary="Métricas operativas de shadow/paper mode por mercado",
    description="Reporte operativo longitudinal por mercado (análisis emitidos, resolubles, resueltos, coverage, degradación y estabilidad).",
)
async def obtener_shadow_operativo_futbol(
    ventana: str = Query("mensual", description="semanal|quincenal|mensual"),
) -> Dict[str, Any]:
    days = _days_by_window(ventana)
    inicio = datetime.now() - timedelta(days=days)
    pool = obtener_pool()

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            fecha_col = "timestamp_generacion" if _columna_existe(cursor, "predicciones_futbol", "timestamp_generacion") else "creado_en"
            cursor.execute(
                f"""
                SELECT
                  mercado::text AS mercado,
                  COUNT(*) AS analisis_emitidos,
                  COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS resueltos,
                  COUNT(*) FILTER (WHERE outcome_binario IS NULL) AS resolubles_pendientes,
                  COUNT(DISTINCT linea) AS lineas_cubiertas,
                  AVG(CASE WHEN calibrador_id IS NULL OR prob_over_calibrada IS NULL THEN 1 ELSE 0 END)::numeric AS fallback_rate,
                  AVG(POWER(COALESCE(CASE WHEN calibrador_id IS NOT NULL THEN prob_over_calibrada END, prob_over) - COALESCE(outcome_binario::int,0),2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier
                FROM predicciones_futbol
                WHERE {fecha_col} >= %s
                GROUP BY mercado
                ORDER BY mercado
                """,
                [inicio],
            )
            metricas = [dict(r) for r in cursor.fetchall()]

            estado_vigente: Dict[str, str] = {}
            if _tabla_existe(cursor, "futbol_estado_operativo_mercado"):
                cursor.execute("SELECT mercado, estado_operativo FROM futbol_estado_operativo_mercado WHERE vigente_hasta IS NULL")
                for r in cursor.fetchall():
                    estado_vigente[str(r["mercado"]).upper()] = str(r["estado_operativo"]).upper()

            for m in metricas:
                mk = str(m["mercado"]).upper()
                m["estado_operativo_vigente"] = estado_vigente.get(mk, "LABORATORIO")
                emitidos = int(m.get("analisis_emitidos") or 0)
                resueltos = int(m.get("resueltos") or 0)
                m["tasa_resolucion"] = round((resueltos / emitidos), 4) if emitidos else 0.0
                m["modo_operativo"] = "PAPER_SHADOW" if m["estado_operativo_vigente"] != "PROMOCIONABLE" else "PROMOCIONABLE_ACTIVO"

            return {
                "exito": True,
                "ventana": ventana,
                "dias": days,
                "desde": inicio.isoformat(),
                "mercados": metricas,
            }


@router.get(
    "/politica-promocion",
    summary="Política formal de salida beta y promoción parcial por mercado",
    description="Retorna la política canónica de estados operativos por mercado para fútbol.",
)
async def obtener_politica_promocion_futbol(
) -> Dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "config" / "futbol_politica_promocion.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No existe política canónica de promoción")
    return json.loads(path.read_text())


@router.get(
    "/madurez-beta",
    response_model=ReporteMadurezFutbolResponse,
    summary="Gate cuantitativo de salida beta del módulo de fútbol",
    description="Clasifica madurez por mercado con criterios cuantitativos reproducibles (NO_APTO/EXPERIMENTAL/VALIDACION/PROMOCIONABLE).",
)
async def obtener_madurez_beta_futbol(
    dias: int = Query(120, ge=30, le=720, description="Ventana principal de evaluación"),
) -> ReporteMadurezFutbolResponse:
    pool = obtener_pool()
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias)
    mitad = fecha_fin - timedelta(days=max(15, dias // 2))

    mercados_catalogo = [
        "CORNERS_1T", "CORNERS_2T", "CORNERS_FT", "CORNERS_LOCAL_1T", "CORNERS_LOCAL_2T", "CORNERS_LOCAL_FT", "CORNERS_VISITANTE_1T", "CORNERS_VISITANTE_2T", "CORNERS_VISITANTE_FT",
        "GOLES_1T", "GOLES_2T", "GOLES_FT", "GOLES_LOCAL_1T", "GOLES_LOCAL_2T", "GOLES_LOCAL_FT", "GOLES_VISITANTE_1T", "GOLES_VISITANTE_2T", "GOLES_VISITANTE_FT",
        "DISPAROS_FT", "DISPAROS_ARCO_FT", "DISPAROS_LOCAL_FT", "DISPAROS_LOCAL_ARCO_FT", "DISPAROS_VISITANTE_FT", "DISPAROS_VISITANTE_ARCO_FT",
    ]

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "predicciones_futbol"):
                    raise HTTPException(status_code=400, detail="No existe tabla predicciones_futbol")

                estado_mercados = _estado_mercados_futbol(cursor)

                fecha_col = "fecha_prediccion" if _columna_existe(cursor, "predicciones_futbol", "fecha_prediccion") else (
                    "timestamp_generacion" if _columna_existe(cursor, "predicciones_futbol", "timestamp_generacion") else "creado_en"
                )

                cursor.execute(
                    f"""
                    SELECT
                      mercado::text AS mercado,
                      linea,
                      {fecha_col} AS fecha_evento,
                      COALESCE(CASE WHEN calibrador_id IS NOT NULL THEN prob_over_calibrada END, prob_over_raw, prob_over) AS p,
                      outcome_binario::int AS y,
                      CASE WHEN outcome_binario IS NOT NULL THEN 1 ELSE 0 END AS resuelta,
                      CASE WHEN calibrador_id IS NULL OR prob_over_calibrada IS NULL THEN 1 ELSE 0 END AS fallback
                    FROM predicciones_futbol
                    WHERE {fecha_col} >= %s
                    """,
                    [fecha_inicio],
                )
                filas = cursor.fetchall()

                por_mercado: Dict[str, Dict[str, Any]] = {}
                for m in mercados_catalogo:
                    por_mercado[m] = {
                        "n_total": 0,
                        "n_resueltas": 0,
                        "lineas": set(),
                        "prob": [],
                        "y": [],
                        "fallback_n": 0,
                        "prob_w1": [],
                        "y_w1": [],
                        "prob_w2": [],
                        "y_w2": [],
                    }

                for row in filas:
                    m = str(row["mercado"]).upper()
                    if m not in por_mercado:
                        por_mercado[m] = {
                            "n_total": 0, "n_resueltas": 0, "lineas": set(), "prob": [], "y": [], "fallback_n": 0,
                            "prob_w1": [], "y_w1": [], "prob_w2": [], "y_w2": [],
                        }
                    acc = por_mercado[m]
                    acc["n_total"] += 1
                    if row.get("linea") is not None:
                        acc["lineas"].add(float(row["linea"]))
                    if int(row.get("fallback") or 0) == 1:
                        acc["fallback_n"] += 1
                    if row.get("resuelta") and row.get("p") is not None and row.get("y") is not None:
                        p = float(row["p"])
                        y = int(row["y"])
                        acc["n_resueltas"] += 1
                        acc["prob"].append(p)
                        acc["y"].append(y)
                        if row.get("fecha_evento") and row["fecha_evento"] < mitad:
                            acc["prob_w1"].append(p)
                            acc["y_w1"].append(y)
                        else:
                            acc["prob_w2"].append(p)
                            acc["y_w2"].append(y)

                mercados_resp: List[MadurezMercadoFutbol] = []
                for mercado, acc in por_mercado.items():
                    n_total = int(acc["n_total"])
                    n_res = int(acc["n_resueltas"])
                    prob = acc["prob"]
                    ys = acc["y"]
                    calculadas = _metricas_probabilidades_binarias(prob, ys)
                    brier = calculadas["brier"]
                    logloss = calculadas["log_loss"]
                    ece = calculadas["ece"]

                    brier_w1 = None
                    if len(acc["prob_w1"]) > 0:
                        brier_w1 = sum((p - y) ** 2 for p, y in zip(acc["prob_w1"], acc["y_w1"])) / len(acc["prob_w1"])
                    brier_w2 = None
                    if len(acc["prob_w2"]) > 0:
                        brier_w2 = sum((p - y) ** 2 for p, y in zip(acc["prob_w2"], acc["y_w2"])) / len(acc["prob_w2"])

                    drift = None
                    if brier_w1 is not None and brier_w2 is not None:
                        drift = float(brier_w2 - brier_w1)

                    metricas = {
                        "n_resueltas": n_res,
                        "lineas_cubiertas": len(acc["lineas"]),
                        "brier": brier,
                        "log_loss": logloss,
                        "ece": ece,
                        "resolved_rate": (n_res / n_total) if n_total > 0 else 0.0,
                        "fallback_rate": (acc["fallback_n"] / n_total) if n_total > 0 else 1.0,
                        "window_drift_brier": drift,
                    }
                    nivel, motivos = clasificar_madurez_mercado(metricas, estado_mercados.get(mercado))
                    mercados_resp.append(MadurezMercadoFutbol(
                        mercado=mercado,
                        clasificacion=nivel,
                        estado_mercado=estado_mercados.get(mercado),
                        n_resueltas=n_res,
                        tasa_resolucion=round(metricas["resolved_rate"], 4),
                        lineas_cubiertas=len(acc["lineas"]),
                        brier=round(brier, 6) if brier is not None else None,
                        log_loss=round(logloss, 6) if logloss is not None else None,
                        ece=round(ece, 6) if ece is not None else None,
                        fallback_rate=round(metricas["fallback_rate"], 4),
                        drift_ventana_brier=round(drift, 6) if drift is not None else None,
                        motivos=motivos,
                    ))

                bloqueados = [m.mercado for m in mercados_resp if m.clasificacion == "NO_APTO"]
                candidatos = [m.mercado for m in mercados_resp if m.clasificacion == "PROMOCIONABLE"]
                validacion = [m for m in mercados_resp if m.clasificacion == "VALIDACION"]

                estado_global: Literal["BETA_LAB", "VALIDACION_CONTROLADA", "LISTO_PARA_PROMOCION_PARCIAL"] = "BETA_LAB"
                if len(candidatos) >= 3:
                    estado_global = "LISTO_PARA_PROMOCION_PARCIAL"
                elif len(validacion) >= 4:
                    estado_global = "VALIDACION_CONTROLADA"

                riesgos = []
                if len(bloqueados) > 0:
                    riesgos.append("mercados_no_aptos_activos")
                if any(m.estado_mercado is None for m in mercados_resp):
                    riesgos.append("estado_mercados_incompleto")
                if any((m.fallback_rate or 0) > CRITERIOS_DEFAULT.max_fallback_rate_validacion for m in mercados_resp):
                    riesgos.append("fallback_elevado")

                criterios = {
                    "min_resueltas_validacion": CRITERIOS_DEFAULT.min_resueltas_validacion,
                    "min_resueltas_promocion": CRITERIOS_DEFAULT.min_resueltas_promocion,
                    "min_lineas_promocion": CRITERIOS_DEFAULT.min_lineas_promocion,
                    "max_brier_promocion": CRITERIOS_DEFAULT.max_brier_promocion,
                    "max_logloss_promocion": CRITERIOS_DEFAULT.max_logloss_promocion,
                    "max_ece_promocion": CRITERIOS_DEFAULT.max_ece_promocion,
                    "min_tasa_resolucion_promocion": CRITERIOS_DEFAULT.min_resolved_rate_promocion,
                    "max_fallback_promocion": CRITERIOS_DEFAULT.max_fallback_rate_promocion,
                    "max_drift_brier_ventana": CRITERIOS_DEFAULT.max_window_drift_promocion,
                    "modo_operativo_recomendado": "SHADOW_PAPER_TRADING para mercados != PROMOCIONABLE",
                }

                mercados_resp.sort(key=lambda x: (x.clasificacion, x.mercado))
                return ReporteMadurezFutbolResponse(
                    exito=True,
                    estado_global=estado_global,
                    criterios=criterios,
                    mercados=mercados_resp,
                    bloqueados=bloqueados,
                    candidatos_promocion=candidatos,
                    riesgos_activos=riesgos,
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando reporte de madurez beta fútbol: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/calibracion",
    response_model=ListaMetricasCalibracionResponse,
    summary="Métricas de calibración",
    description="Obtiene métricas de calibración por mercado.",
)
async def obtener_metricas_calibracion(
    mercado: Optional[str] = Query(None, description="Mercado específico o 'todos'"),
    periodo: Literal["semana", "mes", "temporada", "todo"] = Query("todo"),
) -> ListaMetricasCalibracionResponse:
    """Obtiene métricas de calibración."""
    pool = obtener_pool()

    # Calcular fechas según período
    fecha_fin = datetime.now()
    if periodo == "semana":
        fecha_inicio = fecha_fin - timedelta(days=7)
    elif periodo == "mes":
        fecha_inicio = fecha_fin - timedelta(days=30)
    elif periodo == "temporada":
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = None

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "predicciones_futbol"):
                    return _obtener_metricas_desde_calibradores(cursor, mercado, periodo)

                raw_col = (
                    "prob_over_raw" if _columna_existe(cursor, "predicciones_futbol", "prob_over_raw")
                    else "prob_over" if _columna_existe(cursor, "predicciones_futbol", "prob_over")
                    else None
                )
                if raw_col is None:
                    return _obtener_metricas_desde_calibradores(cursor, mercado, periodo)

                usa_prob_calibrada = _columna_existe(
                    cursor, "predicciones_futbol", "prob_over_calibrada"
                )
                tiene_calibrador_id = _columna_existe(
                    cursor, "predicciones_futbol", "calibrador_id"
                )

                calibradores = {}
                if _tabla_existe(cursor, "calibradores_futbol"):
                    cursor.execute("SELECT mercado, metodo FROM calibradores_futbol WHERE activo = true")
                    calibradores = {row["mercado"]: row for row in cursor.fetchall()}

                # Solo outcomes realmente resueltos: nunca inferir un resultado
                # negativo a partir de la ausencia de marcador o de resultado_real.
                metricas_query = """
                    SELECT p.mercado, p.{raw_col} AS p_raw,
                           {prob_calibrada} AS p_cal, p.outcome_binario::int AS y
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON p.partido_id = pf.id
                    WHERE p.outcome_binario IS NOT NULL
                      AND p.{raw_col} IS NOT NULL
                """.format(prob_calibrada=(
                    "CASE WHEN p.calibrador_id IS NOT NULL THEN p.prob_over_calibrada ELSE NULL::numeric END"
                    if usa_prob_calibrada and tiene_calibrador_id else "NULL::numeric"
                ), raw_col=raw_col)
                params: List = []

                if fecha_inicio:
                    metricas_query += " AND pf.fecha_partido >= %s"
                    params.append(fecha_inicio)

                if mercado and mercado != "todos":
                    metricas_query += " AND p.mercado = %s"
                    params.append(mercado.upper())

                cursor.execute(metricas_query, params)
                filas = cursor.fetchall()
                por_mercado: Dict[str, dict] = {}
                for fila in filas:
                    datos = por_mercado.setdefault(str(fila["mercado"]), {"raw": [], "raw_pareada": [], "cal": [], "y": [], "y_pareada": []})
                    datos["raw"].append(fila["p_raw"])
                    datos["cal"].append(fila["p_cal"])
                    datos["y"].append(fila["y"])
                    if fila["p_cal"] is not None:
                        datos["raw_pareada"].append(fila["p_raw"])
                        datos["y_pareada"].append(fila["y"])

                metricas = []
                for mercado_nombre in sorted(set(por_mercado) | set(calibradores)):
                    if mercado and mercado != "todos" and mercado_nombre != mercado.upper():
                        continue
                    datos = por_mercado.get(mercado_nombre, {"raw": [], "raw_pareada": [], "cal": [], "y": [], "y_pareada": []})
                    raw = _metricas_probabilidades_binarias(datos["raw"], datos["y"])
                    raw_pareada = _metricas_probabilidades_binarias(datos["raw_pareada"], datos["y_pareada"])
                    cal = _metricas_probabilidades_binarias(datos["cal"], datos["y"])
                    mejora = (
                        100 * (raw_pareada["brier"] - cal["brier"]) / raw_pareada["brier"]
                        if raw_pareada["brier"] is not None and raw_pareada["brier"] > 0 and cal["brier"] is not None
                        else None
                    )
                    metricas.append(MetricasCalibracion(
                        mercado=mercado_nombre,
                        brier_score_raw=round(raw["brier"], 4) if raw["brier"] is not None else None,
                        brier_score=round(cal["brier"], 4) if cal["brier"] is not None else None,
                        ece=round(cal["ece"], 4) if cal["ece"] is not None else None,
                        log_loss=round(cal["log_loss"], 4) if cal["log_loss"] is not None else None,
                        n_predicciones=cal["n"],
                        n_raw=raw["n"],
                        n_calibradas=cal["n"],
                        calibrador_activo=mercado_nombre in calibradores,
                        metodo_calibrador=calibradores.get(mercado_nombre, {}).get("metodo"),
                        mejora_brier=round(mejora, 2) if mejora is not None else None,
                    ))

                return ListaMetricasCalibracionResponse(
                    exito=True,
                    periodo=periodo,
                    metricas=metricas,
                )

    except Exception as e:
        logger.error(f"Error obteniendo métricas de calibración: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/rendimiento",
    response_model=ListaMetricasRendimientoResponse,
    summary="Métricas de rendimiento",
    description="Obtiene métricas de rendimiento de apuestas por mercado.",
)
async def obtener_metricas_rendimiento(
    mercado: Optional[str] = Query(None),
    periodo: Literal["semana", "mes", "temporada", "todo"] = Query("todo"),
) -> ListaMetricasRendimientoResponse:
    """Obtiene métricas de rendimiento."""
    pool = obtener_pool()

    fecha_fin = datetime.now()
    if periodo == "semana":
        fecha_inicio = fecha_fin - timedelta(days=7)
    elif periodo == "mes":
        fecha_inicio = fecha_fin - timedelta(days=30)
    elif periodo == "temporada":
        fecha_inicio = fecha_fin - timedelta(days=365)
    else:
        fecha_inicio = None

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "apuestas_futbol"):
                    return ListaMetricasRendimientoResponse(
                        exito=True,
                        periodo=periodo,
                        metricas=[],
                    )

                columna_estado = _resolver_columna_estado_apuestas(cursor)
                if not columna_estado:
                    return ListaMetricasRendimientoResponse(
                        exito=True,
                        periodo=periodo,
                        metricas=[],
                    )

                ganancia_col = _resolver_columna_ganancia_apuestas(cursor) or "NULL::numeric"
                query = """
                    SELECT
                        mercado,
                        COUNT(*) as n_apuestas,
                        SUM(CASE WHEN {estado_col} = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                        SUM(CASE WHEN {estado_col} = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
                        SUM(stake) as stake_total,
                        SUM({ganancia_col}) as ganancia_neta,
                        COUNT({ganancia_col}) as n_ganancias
                    FROM apuestas_futbol
                    WHERE {estado_col} IN ('GANADA', 'PERDIDA', 'PUSH')
                """.format(
                    estado_col=columna_estado,
                    ganancia_col=ganancia_col,  # CORREGIDO
                )
                params = []

                if fecha_inicio:
                    query += " AND fecha_creacion >= %s"
                    params.append(fecha_inicio)

                if mercado and mercado != "todos":
                    query += " AND mercado = %s"
                    params.append(mercado.upper())

                query += " GROUP BY mercado"

                cursor.execute(query, params)
                filas = cursor.fetchall()

                metricas = []
                for fila in filas:
                    total = (fila["ganadas"] or 0) + (fila["perdidas"] or 0)
                    win_rate = (fila["ganadas"] or 0) / total if total > 0 else None
                    stake = float(fila["stake_total"] or 0)
                    ganancias_completas = fila["n_ganancias"] == fila["n_apuestas"]
                    ganancia = float(fila["ganancia_neta"]) if ganancias_completas and fila["ganancia_neta"] is not None else None
                    roi = (ganancia / stake * 100) if ganancia is not None and stake > 0 else None

                    metricas.append(MetricasRendimiento(
                        mercado=fila["mercado"],
                        n_apuestas=fila["n_apuestas"],
                        ganadas=fila["ganadas"] or 0,
                        perdidas=fila["perdidas"] or 0,
                        roi=round(roi, 2) if roi is not None else None,
                        win_rate=round(win_rate, 4) if win_rate is not None else None,
                        stake_total=round(stake, 2),
                        ganancia_neta=round(ganancia, 2) if ganancia is not None else None,
                    ))

                return ListaMetricasRendimientoResponse(
                    exito=True,
                    periodo=periodo,
                    metricas=metricas,
                )

    except Exception as e:
        logger.error(f"Error obteniendo métricas de rendimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/roi-temporal",
    summary="Serie temporal de ROI acumulado (30 días)",
    description="Retorna ROI acumulado diario para el usuario autenticado, sin datos mock.",
)
async def obtener_roi_temporal(
    dias: int = Query(30, ge=7, le=90),
) -> dict:
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "apuestas_futbol"):
                    return {"exito": True, "dias": dias, "serie": []}

                columna_estado = _resolver_columna_estado_apuestas(cursor)
                ganancia_col = _resolver_columna_ganancia_apuestas(cursor)
                if not columna_estado or not ganancia_col:
                    return {"exito": True, "dias": dias, "serie": []}

                query = f"""
                    WITH serie_dias AS (
                        SELECT (CURRENT_DATE - offs)::date AS fecha
                        FROM generate_series(0, %s - 1) AS offs
                    ),
                    delta_diario AS (
                        SELECT
                            DATE(fecha_creacion) AS fecha,
                            SUM({ganancia_col}) AS delta_ganancia,
                            SUM(COALESCE(stake, 0)) AS delta_stake,
                            COUNT(*) AS n_apuestas,
                            COUNT({ganancia_col}) AS n_ganancias
                        FROM apuestas_futbol
                        WHERE {columna_estado} IN ('GANADA', 'PERDIDA', 'PUSH')
                          AND fecha_creacion >= (CURRENT_DATE - (%s - 1) * INTERVAL '1 day')
                        GROUP BY DATE(fecha_creacion)
                    )
                    SELECT
                        s.fecha,
                        SUM(COALESCE(d.delta_ganancia, 0)) OVER (ORDER BY s.fecha) AS ganancia_acumulada,
                        SUM(COALESCE(d.delta_stake, 0)) OVER (ORDER BY s.fecha) AS stake_acumulado,
                        SUM(COALESCE(d.n_apuestas, 0)) OVER (ORDER BY s.fecha) AS n_apuestas,
                        SUM(COALESCE(d.n_ganancias, 0)) OVER (ORDER BY s.fecha) AS n_ganancias
                    FROM serie_dias s
                    LEFT JOIN delta_diario d ON d.fecha = s.fecha
                    ORDER BY s.fecha ASC
                """
                cursor.execute(query, [dias, dias])
                filas = cursor.fetchall()

                serie = []
                for fila in filas:
                    stake_acum = float(fila["stake_acumulado"] or 0)
                    ganancia_completa = fila["n_apuestas"] == fila["n_ganancias"] and fila["n_apuestas"] > 0
                    ganancia_acum = float(fila["ganancia_acumulada"]) if ganancia_completa else None
                    roi_pct = (ganancia_acum / stake_acum * 100.0) if ganancia_acum is not None and stake_acum > 0 else None
                    serie.append(
                        {
                            "fecha": fila["fecha"].isoformat(),
                            "roi": round(roi_pct, 4) if roi_pct is not None else None,
                            "stake_acumulado": round(stake_acum, 2),
                            "ganancia_acumulada": round(ganancia_acum, 2) if ganancia_acum is not None else None,
                        }
                    )

                return {"exito": True, "dias": dias, "serie": serie}
    except Exception as e:
        logger.error("Error obteniendo ROI temporal: %s", e)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/modelos",
    response_model=EstadoModelos,
    summary="Estado de modelos",
    description="Obtiene el estado de los modelos de predicción.",
)
@router.get(
    "/modelo",
    response_model=EstadoModelos,
    include_in_schema=False,
)
async def obtener_estado_modelos(
) -> EstadoModelos:
    """Obtiene estado de los modelos."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                if not _tabla_existe(cursor, "modelo_versiones_futbol"):
                    return EstadoModelos(
                        modelos=[
                            MetricasModelo(
                                tipo_modelo="corners",
                                version="1.0",
                                mae=1.371,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="goles",
                                version="1.0",
                                mae=0.632,
                                n_partidos_entrenamiento=3840,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="disparos",
                                version="1.0",
                                mae=2.493,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                        ],
                        ultima_actualizacion=None,
                        proximo_reentrenamiento=datetime.now() + timedelta(days=7),
                    )
                columna_tipo = _resolver_columna_modelo(cursor, ["tipo_modelo", "tipo", "modelo"])
                columna_version = _resolver_columna_modelo(cursor, ["version"])
                columna_fecha = _resolver_columna_modelo(cursor, ["fecha_entrenamiento", "creado_en"])
                if not all([columna_tipo, columna_version, columna_fecha]):  # CORREGIDO
                    return EstadoModelos(
                        modelos=[
                            MetricasModelo(
                                tipo_modelo="corners",
                                version="1.0",
                                mae=1.371,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="goles",
                                version="1.0",
                                mae=0.632,
                                n_partidos_entrenamiento=3840,
                                n_equipos=28,
                            ),
                            MetricasModelo(
                                tipo_modelo="disparos",
                                version="1.0",
                                mae=2.493,
                                n_partidos_entrenamiento=5196,
                                n_equipos=28,
                            ),
                        ],
                        ultima_actualizacion=None,
                        proximo_reentrenamiento=datetime.now() + timedelta(days=7),
                    )
                columna_mae = _resolver_columna_modelo(cursor, ["mae", "mae_total", "mae_promedio"])
                columna_rmse = _resolver_columna_modelo(cursor, ["rmse", "rmse_total"])
                columna_r2 = _resolver_columna_modelo(cursor, ["r2", "r2_total"])
                columna_partidos = _resolver_columna_modelo(
                    cursor, ["n_partidos_entrenamiento", "partidos_entrenamiento", "n_partidos"]
                )
                columna_equipos = _resolver_columna_modelo(cursor, ["n_equipos", "equipos"])
                # Obtener versiones de modelos
                cursor.execute("""
                    SELECT
                        {columna_tipo} as tipo_modelo,
                        {columna_version} as version,
                        {columna_fecha} as fecha_entrenamiento,
                        {columna_mae} as mae,
                        {columna_rmse} as rmse,
                        {columna_r2} as r2,
                        {columna_partidos} as n_partidos_entrenamiento,
                        {columna_equipos} as n_equipos
                    FROM modelo_versiones_futbol
                    ORDER BY {columna_fecha} DESC
                    LIMIT 3
                """.format(
                    columna_tipo=columna_tipo,
                    columna_version=columna_version,
                    columna_fecha=columna_fecha,
                    columna_mae=columna_mae or "NULL",  # CORREGIDO
                    columna_rmse=columna_rmse or "NULL",  # CORREGIDO
                    columna_r2=columna_r2 or "NULL",  # CORREGIDO
                    columna_partidos=columna_partidos or "NULL",  # CORREGIDO
                    columna_equipos=columna_equipos or "NULL",  # CORREGIDO
                ))
                filas = cursor.fetchall()

                modelos = []
                ultima_actualizacion = None

                for fila in filas:
                    if ultima_actualizacion is None:
                        ultima_actualizacion = fila["fecha_entrenamiento"]

                    modelos.append(MetricasModelo(
                        tipo_modelo=fila["tipo_modelo"],
                        version=str(fila["version"]),
                        fecha_entrenamiento=fila["fecha_entrenamiento"],
                        mae=float(fila["mae"] or 0),
                        rmse=float(fila["rmse"] or 0),
                        r2=float(fila["r2"] or 0),
                        n_partidos_entrenamiento=fila["n_partidos_entrenamiento"] or 0,
                        n_equipos=fila["n_equipos"] or 0,
                    ))

                # Si no hay modelos en BD, crear datos por defecto
                if not modelos:
                    modelos = [
                        MetricasModelo(
                            tipo_modelo="corners",
                            version="1.0",
                            mae=1.371,
                            n_partidos_entrenamiento=5196,
                            n_equipos=28,
                        ),
                        MetricasModelo(
                            tipo_modelo="goles",
                            version="1.0",
                            mae=0.632,
                            n_partidos_entrenamiento=3840,
                            n_equipos=28,
                        ),
                        MetricasModelo(
                            tipo_modelo="disparos",
                            version="1.0",
                            mae=2.493,
                            n_partidos_entrenamiento=5196,
                            n_equipos=28,
                        ),
                    ]

                return EstadoModelos(
                    modelos=modelos,
                    ultima_actualizacion=ultima_actualizacion,
                    proximo_reentrenamiento=datetime.now() + timedelta(days=7),
                )

    except Exception as e:
        logger.error(f"Error obteniendo estado de modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/resumen",
    response_model=ResumenSistema,
    summary="Resumen del sistema",
    description="Obtiene un resumen ejecutivo del sistema de fútbol.",
)
async def obtener_resumen_sistema(
) -> ResumenSistema:
    """Obtiene resumen del sistema."""
    pool = obtener_pool()

    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                # Partidos próximos
                cursor.execute("""
                    SELECT COUNT(*) FROM partidos_futbol
                    WHERE estado = 'PROGRAMADO'
                      AND fecha_partido >= NOW()
                      AND fecha_partido <= NOW() + INTERVAL '7 days'
                """)
                partidos_proximos = cursor.fetchone()["count"]

                # Predicciones pendientes
                cursor.execute("""
                    SELECT COUNT(*) FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON p.partido_id = pf.id
                    WHERE pf.estado = 'PROGRAMADO'
                """)
                predicciones_pendientes = cursor.fetchone()["count"]

                # Apuestas activas del usuario
                columna_estado = _resolver_columna_estado_apuestas(cursor)
                if columna_estado:  # CORREGIDO
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM apuestas_futbol
                        WHERE {columna_estado} = 'PENDIENTE'
                    """)
                    apuestas_activas = cursor.fetchone()["count"]
                else:
                    apuestas_activas = 0

                # ROI y win rate global
                ganancia_col = _resolver_columna_ganancia_apuestas(cursor) or "0"  # CORREGIDO
                if columna_estado:
                    cursor.execute(f"""
                        SELECT
                            SUM(stake) as stake_total,
                            SUM(COALESCE({ganancia_col}, 0)) as ganancia_neta,
                            SUM(CASE WHEN {columna_estado} = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                            SUM(CASE WHEN {columna_estado} IN ('GANADA', 'PERDIDA') THEN 1 ELSE 0 END) as resueltas
                        FROM apuestas_futbol
                    """)
                    stats = cursor.fetchone()
                else:
                    stats = {
                        "stake_total": 0,
                        "ganancia_neta": 0,
                        "ganadas": 0,
                        "resueltas": 0,
                    }

                roi = None
                win_rate = None
                if stats["stake_total"] and float(stats["stake_total"]) > 0:
                    roi = (float(stats["ganancia_neta"] or 0) / float(stats["stake_total"])) * 100

                if stats["resueltas"] and stats["resueltas"] > 0:
                    win_rate = (stats["ganadas"] or 0) / stats["resueltas"]

                # Calibradores activos
                cursor.execute("SELECT COUNT(*) FROM calibradores_futbol WHERE activo = true")
                calibradores_activos = cursor.fetchone()["count"]

                # Verificar modelo activo
                modelo_activo = True  # Asumimos que está activo si existe

                # Alertas de calibración
                cursor.execute("""
                    SELECT mensaje FROM alertas_calibracion
                    WHERE resuelta = false
                    ORDER BY timestamp_deteccion DESC
                    LIMIT 1
                """)
                alerta = cursor.fetchone()
                alerta_calibracion = alerta["mensaje"] if alerta else None

                return ResumenSistema(
                    partidos_proximos=partidos_proximos,
                    predicciones_pendientes=predicciones_pendientes,
                    apuestas_activas=apuestas_activas,
                    roi_global=round(roi, 2) if roi is not None else None,
                    win_rate_global=round(win_rate, 4) if win_rate is not None else None,
                    modelo_activo=modelo_activo,
                    calibradores_activos=calibradores_activos,
                    alerta_calibracion=alerta_calibracion,
                )

    except Exception as e:
        logger.error(f"Error obteniendo resumen del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


def _resumen_calidad_1x2_futbol(cursor) -> dict:
    """Resumen de calidad simple para 1X2 usando apuestas_analizadas."""
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE estado = 'FINALIZADA') AS finalizadas,
            COUNT(*) FILTER (WHERE resultado_outcome = 'GANADA') AS ganadas,
            COUNT(*) FILTER (WHERE resultado_outcome = 'PERDIDA') AS perdidas,
            COUNT(*) FILTER (WHERE resultado_outcome = 'PUSH') AS push
        FROM apuestas_analizadas
        WHERE deporte = 'futbol'
        """
    )
    row = cursor.fetchone()
    total = int(row[0] or 0)
    finalizadas = int(row[1] or 0)
    ganadas = int(row[2] or 0)
    perdidas = int(row[3] or 0)
    push = int(row[4] or 0)
    resueltas_sin_push = ganadas + perdidas
    hit_rate = (ganadas / resueltas_sin_push) * 100.0 if resueltas_sin_push else None
    return {
        'total': total,
        'finalizadas': finalizadas,
        'ganadas': ganadas,
        'perdidas': perdidas,
        'push': push,
        'hit_rate_sin_push': round(hit_rate, 2) if hit_rate is not None else None,
    }


def _clasificar_estabilidad_b3(
    filas_actual: List[Dict[str, Any]],
    filas_prev: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prev_map = {str(f["competicion_id"]): f for f in filas_prev}
    ligas: List[Dict[str, Any]] = []
    criticas = 0

    for fila in filas_actual:
        comp_id = str(fila["competicion_id"])
        n_actual = int(fila.get("n") or 0)
        brier_actual = float(fila["brier"]) if fila.get("brier") is not None else None

        prev = prev_map.get(comp_id)
        n_prev = int((prev or {}).get("n") or 0)
        brier_prev = float(prev["brier"]) if prev and prev.get("brier") is not None else None

        delta_abs = brier_actual - brier_prev if brier_actual is not None and brier_prev is not None else None
        delta_rel = (delta_abs / brier_prev) if (delta_abs is not None and brier_prev is not None and brier_prev > 0) else None

        if (n_actual < MIN_MUESTRA_SEMANAL_B3 or n_prev < MIN_MUESTRA_SEMANAL_B3
                or brier_actual is None or brier_prev is None):
            estado = "insuficiente"
        elif (
            delta_abs is not None
            and delta_abs >= UMBRAL_DEGRADACION_BRIER_ABS
            and (delta_rel is not None and delta_rel >= UMBRAL_DEGRADACION_BRIER_REL)
        ):
            estado = "critico"
            criticas += 1
        elif delta_abs is not None and delta_abs > 0:
            estado = "warning"
        else:
            estado = "estable"

        ligas.append(
            {
                "competicion_id": comp_id,
                "competicion_codigo": fila.get("competicion_codigo"),
                "competicion_nombre": fila.get("competicion_nombre"),
                "n_actual": n_actual,
                "n_previo": n_prev,
                "brier_actual": round(brier_actual, 4) if brier_actual is not None else None,
                "brier_previo": round(brier_prev, 4) if brier_prev is not None else None,
                "delta_abs": round(delta_abs, 4) if delta_abs is not None else None,
                "delta_rel_pct": round((delta_rel or 0) * 100, 2) if delta_rel is not None else None,
                "estado": estado,
            }
        )

    ciclos_validos = sum(
        1 for l in ligas if l["n_actual"] >= MIN_MUESTRA_SEMANAL_B3
        and l["n_previo"] >= MIN_MUESTRA_SEMANAL_B3
        and l["brier_actual"] is not None and l["brier_previo"] is not None
    )

    gate_aprobado = criticas == 0 and ciclos_validos > 0

    return {
        "gate_aprobado": gate_aprobado,
        "ligas_criticas": criticas,
        "ligas_evaluadas": len(ligas),
        "ligas_con_muestra": ciclos_validos,
        "ligas": sorted(ligas, key=lambda x: (x["estado"], x["competicion_nombre"])),
    }


@router.get(
    "/b3-estabilidad",
    summary="Estado semanal de estabilidad B3 por liga",
)
async def obtener_estado_b3_estabilidad(
) -> dict:
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                query = """
                    SELECT
                        pf.competicion_id,
                        c.codigo AS competicion_codigo,
                        c.nombre AS competicion_nombre,
                        COUNT(*) AS n,
                        AVG(
                            POWER(
                                COALESCE(CASE WHEN p.calibrador_id IS NOT NULL THEN p.prob_over_calibrada END, p.prob_over)
                                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                                2
                            )
                        ) AS brier
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON pf.id = p.partido_id
                    JOIN competiciones_futbol c ON c.id = pf.competicion_id
                    WHERE p.outcome_binario IS NOT NULL
                      AND COALESCE(CASE WHEN p.calibrador_id IS NOT NULL THEN p.prob_over_calibrada END, p.prob_over) IS NOT NULL
                      AND pf.fecha_partido >= NOW() - INTERVAL '7 days'
                    GROUP BY pf.competicion_id, c.codigo, c.nombre
                """
                cursor.execute(query)
                filas_actual = cursor.fetchall()

                query_prev = """
                    SELECT
                        pf.competicion_id,
                        c.codigo AS competicion_codigo,
                        c.nombre AS competicion_nombre,
                        COUNT(*) AS n,
                        AVG(
                            POWER(
                                COALESCE(CASE WHEN p.calibrador_id IS NOT NULL THEN p.prob_over_calibrada END, p.prob_over)
                                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                                2
                            )
                        ) AS brier
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON pf.id = p.partido_id
                    JOIN competiciones_futbol c ON c.id = pf.competicion_id
                    WHERE p.outcome_binario IS NOT NULL
                      AND COALESCE(CASE WHEN p.calibrador_id IS NOT NULL THEN p.prob_over_calibrada END, p.prob_over) IS NOT NULL
                      AND pf.fecha_partido >= NOW() - INTERVAL '14 days'
                      AND pf.fecha_partido < NOW() - INTERVAL '7 days'
                    GROUP BY pf.competicion_id, c.codigo, c.nombre
                """
                cursor.execute(query_prev)
                filas_prev = cursor.fetchall()

                resumen = _clasificar_estabilidad_b3(filas_actual, filas_prev)
                resumen["exito"] = True
                resumen["ventana_actual_dias"] = 7
                resumen["ventana_previa_dias"] = 7
                resumen["umbral_brier_abs"] = UMBRAL_DEGRADACION_BRIER_ABS
                resumen["umbral_brier_rel_pct"] = UMBRAL_DEGRADACION_BRIER_REL * 100
                return resumen
    except Exception as e:
        logger.error("Error obteniendo estado B3 estabilidad: %s", e)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get(
    "/resumen-calidad-1x2",
    summary="Resumen de calidad de predicción 1X2 (fútbol)",
)
async def resumen_calidad_1x2() -> dict:
    pool = obtener_pool()
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            return {
                'exito': True,
                'resumen': _resumen_calidad_1x2_futbol(cursor),
            }

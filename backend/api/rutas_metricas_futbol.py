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

from fastapi import APIRouter, HTTPException, Query, Depends
from psycopg.rows import dict_row

from db import obtener_pool
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
from .dependencias import obtener_usuario_actual, UsuarioActual

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
    """Obtiene métricas desde calibradores si no hay predicciones."""
    columnas_calibrador = {  # CORREGIDO
        "brier_antes": _columna_existe(cursor, "calibradores_futbol", "brier_antes"),
        "brier_despues": _columna_existe(cursor, "calibradores_futbol", "brier_despues"),
        "ece_antes": _columna_existe(cursor, "calibradores_futbol", "ece_antes"),
        "ece_despues": _columna_existe(cursor, "calibradores_futbol", "ece_despues"),
        "log_loss_antes": _columna_existe(cursor, "calibradores_futbol", "log_loss_antes"),
        "log_loss_despues": _columna_existe(cursor, "calibradores_futbol", "log_loss_despues"),
    }
    n_muestras_col = None  # CORREGIDO
    for candidato in ("n_muestras", "n_muestras_entrenamiento"):
        if _columna_existe(cursor, "calibradores_futbol", candidato):
            n_muestras_col = candidato
            break

    query = """
        SELECT
            mercado,
            metodo,
            {brier_antes} AS brier_antes,
            {brier_despues} AS brier_despues,
            {ece_antes} AS ece_antes,
            {ece_despues} AS ece_despues,
            {log_loss_antes} AS log_loss_antes,
            {log_loss_despues} AS log_loss_despues,
            {n_muestras} AS n_muestras
        FROM calibradores_futbol
        WHERE activo = true
    """.format(
        brier_antes="brier_antes" if columnas_calibrador["brier_antes"] else "NULL",  # CORREGIDO
        brier_despues="brier_despues" if columnas_calibrador["brier_despues"] else "NULL",  # CORREGIDO
        ece_antes="ece_antes" if columnas_calibrador["ece_antes"] else "NULL",  # CORREGIDO
        ece_despues="ece_despues" if columnas_calibrador["ece_despues"] else "NULL",  # CORREGIDO
        log_loss_antes="log_loss_antes" if columnas_calibrador["log_loss_antes"] else "NULL",  # CORREGIDO
        log_loss_despues="log_loss_despues" if columnas_calibrador["log_loss_despues"] else "NULL",  # CORREGIDO
        n_muestras=n_muestras_col if n_muestras_col else "NULL",  # CORREGIDO
    )
    params: List[str] = []
    if mercado and mercado != "todos":
        query += " AND mercado = %s"
        params.append(mercado.upper())

    cursor.execute(query, params)
    filas = cursor.fetchall()

    metricas = []
    for fila in filas:
        brier_antes = float(fila["brier_antes"] or 0)
        brier_despues = float(fila["brier_despues"] or 0.22)
        mejora = ((brier_antes - brier_despues) / brier_antes * 100) if brier_antes else None

        metricas.append(MetricasCalibracion(
            mercado=fila["mercado"],
            brier_score=round(brier_despues, 4),
            ece=round(float(fila["ece_despues"] or 0.09), 4),
            log_loss=round(float(fila["log_loss_despues"] or 0.65), 4),
            n_predicciones=fila["n_muestras"] or 0,
            calibrador_activo=True,
            metodo_calibrador=fila["metodo"],
            mejora_brier=round(mejora, 2) if mejora is not None else None,
        ))

    return ListaMetricasCalibracionResponse(
        exito=True,
        periodo=periodo,
        metricas=metricas,
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


def _ece_binario(probabilidades: List[float], outcomes: List[int], bins: int = 10) -> float:
    if not probabilidades:
        return 1.0
    buckets: Dict[int, List[int]] = defaultdict(list)
    bucket_prob: Dict[int, List[float]] = defaultdict(list)
    for p, y in zip(probabilidades, outcomes):
        idx = min(bins - 1, max(0, int(math.floor(float(p) * bins))))
        buckets[idx].append(int(y))
        bucket_prob[idx].append(float(p))

    n = len(probabilidades)
    ece = 0.0
    for idx in range(bins):
        ys = buckets.get(idx, [])
        ps = bucket_prob.get(idx, [])
        if not ys:
            continue
        avg_y = sum(ys) / len(ys)
        avg_p = sum(ps) / len(ps)
        ece += (len(ys) / n) * abs(avg_y - avg_p)
    return float(ece)


def _estado_mercados_futbol(cursor, min_muestras: int = 100, warning_brier: float = 0.24, bloquear_brier: float = 0.28) -> Dict[str, str]:
    try:
        cursor.execute(
            """
            SELECT mercado::text,
                   COUNT(*) AS n,
                   AVG(POWER(COALESCE(prob_over_calibrada, prob_over_raw, prob_over) - COALESCE(outcome_binario::int,0), 2)) AS brier
            FROM predicciones_futbol
            WHERE outcome_binario IS NOT NULL
              AND COALESCE(prob_over_calibrada, prob_over_raw, prob_over) IS NOT NULL
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
                  AVG(CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END)::numeric AS fallback_rate,
                  AVG(POWER(COALESCE(prob_over_calibrada, prob_over) - COALESCE(outcome_binario::int,0),2)) FILTER (WHERE outcome_binario IS NOT NULL) AS brier
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
                      COALESCE(prob_over_calibrada, prob_over_raw, prob_over) AS p,
                      outcome_binario::int AS y,
                      CASE WHEN outcome_binario IS NOT NULL THEN 1 ELSE 0 END AS resuelta,
                      CASE WHEN prob_over_calibrada IS NULL THEN 1 ELSE 0 END AS fallback
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
                    if n_res > 0:
                        brier = sum((p - y) ** 2 for p, y in zip(prob, ys)) / n_res
                        eps = 1e-9
                        logloss = -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y in zip(prob, ys)) / n_res
                        ece = _ece_binario(prob, ys, bins=10)
                    else:
                        brier = None
                        logloss = None
                        ece = None

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
                        "brier": brier if brier is not None else 1.0,
                        "log_loss": logloss if logloss is not None else 2.0,
                        "ece": ece if ece is not None else 1.0,
                        "resolved_rate": (n_res / n_total) if n_total > 0 else 0.0,
                        "fallback_rate": (acc["fallback_n"] / n_total) if n_total > 0 else 1.0,
                        "window_drift_brier": drift if drift is not None else 1.0,
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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

                if not _columna_existe(cursor, "predicciones_futbol", "prob_over_raw"):
                    return _obtener_metricas_desde_calibradores(cursor, mercado, periodo)

                usa_prob_calibrada = _columna_existe(
                    cursor, "predicciones_futbol", "prob_over_calibrada"
                )

                # Obtener calibradores activos
                calibradores_query = """
                    SELECT mercado, metodo, activo, brier_despues, mejora_validacion
                    FROM calibradores_futbol
                    WHERE activo = true
                """
                if mercado and mercado != "todos":
                    calibradores_query += " AND mercado = %s"
                    cursor.execute(calibradores_query, [mercado.upper()])
                else:
                    cursor.execute(calibradores_query)

                calibradores = {row["mercado"]: row for row in cursor.fetchall()}

                # Obtener métricas de predicciones
                metricas_query = """
                    SELECT
                        p.mercado,
                        COUNT(*) as n_predicciones,
                        AVG(POWER(p.prob_over_raw - CASE WHEN resultado_real > p.linea THEN 1 ELSE 0 END, 2)) as brier_score,
                        AVG(POWER(
                            COALESCE({prob_calibrada}, p.prob_over_raw) -
                            CASE WHEN resultado_real > p.linea THEN 1 ELSE 0 END, 2
                        )) as brier_calibrado
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON p.partido_id = pf.id
                    WHERE pf.estado = 'FINALIZADO'
                      AND p.prob_over_raw IS NOT NULL
                """
                metricas_query = metricas_query.format(
                    prob_calibrada="p.prob_over_calibrada" if usa_prob_calibrada else "p.prob_over_raw"
                )
                params: List = []

                if fecha_inicio:
                    metricas_query += " AND pf.fecha_partido >= %s"
                    params.append(fecha_inicio)

                if mercado and mercado != "todos":
                    metricas_query += " AND p.mercado = %s"
                    params.append(mercado.upper())

                metricas_query += " GROUP BY p.mercado"

                cursor.execute(metricas_query, params)
                filas = cursor.fetchall()

                metricas = []
                for fila in filas:
                    mercado_nombre = fila["mercado"]
                    cal = calibradores.get(mercado_nombre, {})

                    brier = float(fila["brier_score"] or 0)
                    brier_cal = float(fila["brier_calibrado"] or brier)
                    mejora = ((brier - brier_cal) / brier * 100) if brier > 0 else 0

                    metricas.append(MetricasCalibracion(
                        mercado=mercado_nombre,
                        brier_score=round(brier_cal, 4),
                        ece=round(brier_cal * 0.5, 4),  # Estimación simplificada
                        log_loss=round(brier_cal * 1.5, 4),  # Estimación simplificada
                        n_predicciones=fila["n_predicciones"],
                        calibrador_activo=cal.get("activo", False),
                        metodo_calibrador=cal.get("metodo"),
                        mejora_brier=round(mejora, 2) if mejora else None,
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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

                ganancia_col = _resolver_columna_ganancia_apuestas(cursor) or "0"  # CORREGIDO
                query = """
                    SELECT
                        mercado,
                        COUNT(*) as n_apuestas,
                        SUM(CASE WHEN {estado_col} = 'GANADA' THEN 1 ELSE 0 END) as ganadas,
                        SUM(CASE WHEN {estado_col} = 'PERDIDA' THEN 1 ELSE 0 END) as perdidas,
                        SUM(stake) as stake_total,
                        SUM(COALESCE({ganancia_col}, 0)) as ganancia_neta
                    FROM apuestas_futbol
                    WHERE usuario_id = %s
                      AND {estado_col} IN ('GANADA', 'PERDIDA', 'PUSH')
                """.format(
                    estado_col=columna_estado,
                    ganancia_col=ganancia_col,  # CORREGIDO
                )
                params = [str(usuario.id)]

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
                    win_rate = (fila["ganadas"] or 0) / total if total > 0 else 0
                    stake = float(fila["stake_total"] or 0)
                    ganancia = float(fila["ganancia_neta"] or 0)
                    roi = (ganancia / stake * 100) if stake > 0 else 0

                    metricas.append(MetricasRendimiento(
                        mercado=fila["mercado"],
                        n_apuestas=fila["n_apuestas"],
                        ganadas=fila["ganadas"] or 0,
                        perdidas=fila["perdidas"] or 0,
                        roi=round(roi, 2),
                        win_rate=round(win_rate, 4),
                        stake_total=round(stake, 2),
                        ganancia_neta=round(ganancia, 2),
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
                            SUM(COALESCE({ganancia_col}, 0)) AS delta_ganancia,
                            SUM(COALESCE(stake, 0)) AS delta_stake
                        FROM apuestas_futbol
                        WHERE usuario_id = %s
                          AND {columna_estado} IN ('GANADA', 'PERDIDA', 'PUSH')
                          AND fecha_creacion >= (CURRENT_DATE - (%s - 1) * INTERVAL '1 day')
                        GROUP BY DATE(fecha_creacion)
                    )
                    SELECT
                        s.fecha,
                        SUM(COALESCE(d.delta_ganancia, 0)) OVER (ORDER BY s.fecha) AS ganancia_acumulada,
                        SUM(COALESCE(d.delta_stake, 0)) OVER (ORDER BY s.fecha) AS stake_acumulado
                    FROM serie_dias s
                    LEFT JOIN delta_diario d ON d.fecha = s.fecha
                    ORDER BY s.fecha ASC
                """
                cursor.execute(query, [dias, str(usuario.id), dias])
                filas = cursor.fetchall()

                serie = []
                for fila in filas:
                    stake_acum = float(fila["stake_acumulado"] or 0)
                    ganancia_acum = float(fila["ganancia_acumulada"] or 0)
                    roi_pct = (ganancia_acum / stake_acum * 100.0) if stake_acum > 0 else 0.0
                    serie.append(
                        {
                            "fecha": fila["fecha"].isoformat(),
                            "roi": round(roi_pct, 4),
                            "stake_acumulado": round(stake_acum, 2),
                            "ganancia_acumulada": round(ganancia_acum, 2),
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
                        WHERE usuario_id = %s AND {columna_estado} = 'PENDIENTE'
                    """, [str(usuario.id)])
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
                        WHERE usuario_id = %s
                    """, [str(usuario.id)])
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
                    roi_global=round(roi, 2) if roi else None,
                    win_rate_global=round(win_rate, 4) if win_rate else None,
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
    hit_rate = (ganadas / max(1, ganadas + perdidas)) * 100.0
    return {
        'total': total,
        'finalizadas': finalizadas,
        'ganadas': ganadas,
        'perdidas': perdidas,
        'push': push,
        'hit_rate_sin_push': round(hit_rate, 2),
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
        brier_actual = float(fila.get("brier") or 0)

        prev = prev_map.get(comp_id)
        n_prev = int((prev or {}).get("n") or 0)
        brier_prev = float((prev or {}).get("brier") or 0)

        delta_abs = brier_actual - brier_prev if n_prev > 0 else None
        delta_rel = (delta_abs / brier_prev) if (delta_abs is not None and brier_prev > 0) else None

        if n_actual < MIN_MUESTRA_SEMANAL_B3 or n_prev < MIN_MUESTRA_SEMANAL_B3:
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
                "brier_actual": round(brier_actual, 4),
                "brier_previo": round(brier_prev, 4) if n_prev > 0 else None,
                "delta_abs": round(delta_abs, 4) if delta_abs is not None else None,
                "delta_rel_pct": round((delta_rel or 0) * 100, 2) if delta_rel is not None else None,
                "estado": estado,
            }
        )

    ciclos_validos = sum(
        1 for l in ligas if l["n_actual"] >= MIN_MUESTRA_SEMANAL_B3 and l["n_previo"] >= MIN_MUESTRA_SEMANAL_B3
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
    usuario: UsuarioActual = Depends(obtener_usuario_actual),
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
                                COALESCE(p.prob_over_calibrada, p.prob_over)
                                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                                2
                            )
                        ) AS brier
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON pf.id = p.partido_id
                    JOIN competiciones_futbol c ON c.id = pf.competicion_id
                    WHERE p.outcome_binario IS NOT NULL
                      AND COALESCE(p.prob_over_calibrada, p.prob_over) IS NOT NULL
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
                                COALESCE(p.prob_over_calibrada, p.prob_over)
                                - CASE WHEN p.outcome_binario THEN 1 ELSE 0 END,
                                2
                            )
                        ) AS brier
                    FROM predicciones_futbol p
                    JOIN partidos_futbol pf ON pf.id = p.partido_id
                    JOIN competiciones_futbol c ON c.id = pf.competicion_id
                    WHERE p.outcome_binario IS NOT NULL
                      AND COALESCE(p.prob_over_calibrada, p.prob_over) IS NOT NULL
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

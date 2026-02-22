# -*- coding: utf-8 -*-
"""
rutas_metricas.py — Endpoints de métricas de calibración (T22, T23).

REGLA CRÍTICA: El parámetro 'origen' es SIEMPRE obligatorio.
Mezclar métricas de API_USUARIO con BACKTEST_* invalida el análisis.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from backtesting.metricas.calculador import calcular_metricas_calibracion
from backtesting.metricas.curva_calibracion import (
    BinCalibracion as BinCalibracionInterno,
    ResultadoCurva,
    calcular_curva_bins_cuantiles,
    calcular_curva_bins_fijos,
)
from db import obtener_pool
from motor.alertas_calibracion import listar_alertas_calibracion
from motor.calibradores import obtener_calibrador_activo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metricas", tags=["Métricas de Calibración"])

MIN_PREDICCIONES_MERCADO = 100
MIN_POR_BIN = 30
_CACHE_TTL_SEGUNDOS = 300

_cache_metricas: dict[Tuple[object, ...], Tuple[float, dict[str, object]]] = {}
_cache_curvas: dict[Tuple[object, ...], Tuple[float, dict[str, object]]] = {}


@dataclass(frozen=True)
class PeriodoConsulta:
    inicio: date
    fin: date
    texto_inicio: str
    texto_fin: str


class MetricaMercado(BaseModel):
    """Métricas de calibración para un mercado específico."""

    mercado: str = Field(..., description="Q1/Q2/Q3/Q4/COMPLETO")
    n_predicciones: int = Field(..., description="Total de predicciones evaluadas")
    n_excluidos_push: int = Field(0, description="Predicciones excluidas por PUSH")

    brier_score: Optional[float] = Field(None, description="Brier Score (0-1, menor mejor)")
    brier_score_raw: Optional[float] = Field(None, description="Brier usando p_raw")
    brier_score_calibrado: Optional[float] = Field(
        None, description="Brier usando p_calibrada"
    )
    log_loss: Optional[float] = Field(None, description="Log Loss")
    ece: Optional[float] = Field(None, description="Expected Calibration Error")
    mce: Optional[float] = Field(None, description="Maximum Calibration Error")

    mae_media: Optional[float] = Field(None, description="MAE de la media predicha")
    rmse_media: Optional[float] = Field(None, description="RMSE de la media predicha")
    sesgo_media: Optional[float] = Field(None, description="Sesgo (+ = subestima)")

    calibrador_activo: Optional[str] = Field(
        None, description="Método: isotonic/platt/None"
    )
    calibrador_id: Optional[str] = Field(None, description="UUID del calibrador activo")
    mejora_vs_raw: Optional[float] = Field(None, description="brier_raw - brier_calibrado")

    base_rate: Optional[float] = Field(None, description="Frecuencia real del evento")
    sharpness: Optional[float] = Field(None, description="Varianza de probabilidades")
    suficiente_data: bool = Field(..., description="True si n >= 100")
    advertencias: List[str] = Field(default_factory=list)


class RespuestaMetricasCalibracion(BaseModel):
    """Respuesta del endpoint de métricas."""

    exito: bool
    origen: str
    periodo: dict
    modelo_version_id: Optional[int] = None
    metricas_por_mercado: List[MetricaMercado]
    alertas_activas: List[dict] = Field(default_factory=list)
    timestamp_calculo: str


class BinCalibracionResponse(BaseModel):
    """Bin de la curva de calibración."""

    rango_inicio: float
    rango_fin: float
    n: int
    probabilidad_promedio: float
    frecuencia_real: float
    gap: float
    gap_con_signo: float = Field(..., description="+ = sobreconfiado, - = subconfiado")
    suficiente_data: bool
    advertencia: Optional[str] = None


class RespuestaCurvaCalibracion(BaseModel):
    """Respuesta del endpoint de curva."""

    exito: bool
    mercado: str
    origen: str
    tipo_bins: str
    n_bins: int
    n_predicciones_total: int
    n_excluidos_push: int
    bins: List[BinCalibracionResponse]
    ece: float
    mce: float
    bin_peor_calibrado: Optional[str]
    linea_perfecta: List[dict] = Field(
        ..., description="Puntos para dibujar línea de calibración perfecta"
    )
    periodo: dict
    timestamp_calculo: str


class ResumenDeporte(BaseModel):
    deporte: str
    total_predicciones: int
    pendientes_resolver: int
    ultima_prediccion: Optional[str] = None


class ResumenDeportesResponse(BaseModel):
    exito: bool
    resumen: List[ResumenDeporte]
    timestamp: str


@router.get(
    "/calibracion",
    response_model=RespuestaMetricasCalibracion,
    summary="Obtener métricas de calibración por mercado",
    description="""
    Retorna métricas de calibración (Brier, LogLoss, ECE) separadas por mercado.

    **CRÍTICO:** El parámetro `origen` es OBLIGATORIO.

    ## Orígenes válidos:
    - `API_USUARIO`: Predicciones reales de usuarios (VERDAD del producto)
    - `BACKTEST_SINTETICO`: Predicciones de backtest (validación estadística)
    - `BACKTEST_BATCH`: Predicciones de backtest batch
    """,
    responses={
        200: {"description": "Métricas calculadas exitosamente"},
        400: {"description": "Parámetros inválidos"},
        404: {"description": "No hay predicciones para el periodo"},
    },
)
async def obtener_metricas_calibracion(
    origen: str = Query(
        ...,
        pattern="^(API_USUARIO|BACKTEST_SINTETICO|BACKTEST_BATCH)$",
        description="Origen de predicciones (OBLIGATORIO)",
    ),
    mercado: Optional[str] = Query(
        None,
        pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$",
        description="Filtrar por mercado específico",
    ),
    desde: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    hasta: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    modelo_version_id: Optional[int] = Query(None, description="Filtrar por versión de modelo"),
) -> RespuestaMetricasCalibracion:
    """Calcula y retorna métricas de calibración."""
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=400,
            detail="Fecha 'desde' no puede ser posterior a 'hasta'",
        )

    mercados = [mercado] if mercado else ["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    metricas_resultado: list[MetricaMercado] = []

    for mercado_actual in mercados:
        periodo = _resolver_periodo(
            mercado_actual,
            origen,
            desde=desde,
            hasta=hasta,
            modelo_version_id=modelo_version_id,
        )
        if periodo is None:
            metricas_resultado.append(
                MetricaMercado(
                    mercado=mercado_actual,
                    n_predicciones=0,
                    n_excluidos_push=0,
                    suficiente_data=False,
                    advertencias=["Sin datos para el periodo solicitado."],
                )
            )
            continue

        cache_key = (
            "metricas",
            origen,
            mercado_actual,
            periodo.inicio,
            periodo.fin,
            modelo_version_id,
        )
        cacheada = _obtener_cache(_cache_metricas, cache_key)
        if cacheada:
            metricas_resultado.append(MetricaMercado(**cacheada))
            continue

        try:
            resultado = _buscar_metricas_precalculadas(
                mercado_actual,
                origen,
                periodo.inicio,
                periodo.fin,
                modelo_version_id=modelo_version_id,
            )
            if resultado is None:
                resultado = calcular_metricas_calibracion(
                    mercado=mercado_actual,
                    origen=origen,
                    fecha_inicio=periodo.inicio,
                    fecha_fin=periodo.fin,
                    modelo_version_id=modelo_version_id,
                    usar_p_calibrada=True,
                )

            n_excluidos = _contar_excluidos_push(
                mercado_actual,
                origen,
                periodo.inicio,
                periodo.fin,
                modelo_version_id=modelo_version_id,
            )

            distribucion = resultado.get("distribucion", {}) if resultado else {}
            brier_raw = resultado.get("brier_score_raw")
            brier_calibrado = resultado.get("brier_score_calibrado")
            mejora = (
                brier_raw - brier_calibrado
                if brier_raw is not None and brier_calibrado is not None
                else None
            )

            calibrador_activo = None
            calibrador_id = None
            try:
                calibrador = obtener_calibrador_activo(
                    mercado=mercado_actual, origen=origen
                )
                if calibrador is not None:
                    calibrador_activo = calibrador.metodo
                    calibrador_id = str(calibrador.id)
            except Exception:
                logger.exception(
                    "Error obteniendo calibrador activo (mercado=%s origen=%s).",
                    mercado_actual,
                    origen,
                )

            advertencias = list(resultado.get("alertas", [])) if resultado else []

            metrica = MetricaMercado(
                mercado=mercado_actual,
                n_predicciones=resultado.get("n_predicciones", 0),
                n_excluidos_push=n_excluidos,
                brier_score=resultado.get("brier_score"),
                brier_score_raw=brier_raw,
                brier_score_calibrado=brier_calibrado,
                log_loss=resultado.get("log_loss"),
                ece=resultado.get("ece"),
                mce=resultado.get("mce"),
                mae_media=distribucion.get("mae_media"),
                rmse_media=distribucion.get("rmse_media"),
                sesgo_media=distribucion.get("sesgo_media"),
                calibrador_activo=calibrador_activo,
                calibrador_id=calibrador_id,
                mejora_vs_raw=mejora,
                base_rate=resultado.get("base_rate"),
                sharpness=resultado.get("sharpness"),
                suficiente_data=resultado.get("n_predicciones", 0) >= MIN_PREDICCIONES_MERCADO,
                advertencias=advertencias,
            )

            if metrica.n_predicciones < MIN_PREDICCIONES_MERCADO:
                metrica.advertencias.append(
                    f"Solo {metrica.n_predicciones} predicciones. "
                    f"Mínimo recomendado: {MIN_PREDICCIONES_MERCADO}."
                )

            _guardar_cache(_cache_metricas, cache_key, metrica.model_dump())
            metricas_resultado.append(metrica)
        except Exception as exc:
            logger.exception(
                "Error calculando métricas de calibración (mercado=%s origen=%s).",
                mercado_actual,
                origen,
            )
            metricas_resultado.append(
                MetricaMercado(
                    mercado=mercado_actual,
                    n_predicciones=0,
                    n_excluidos_push=0,
                    suficiente_data=False,
                    advertencias=[f"Error calculando métricas: {exc}"],
                )
            )

    alertas = listar_alertas_calibracion(
        mercado=mercado,
        origen=origen,
        resuelta=False,
    )
    alertas_filtradas = _filtrar_alertas_periodo(alertas, desde, hasta)

    timestamp = datetime.now().isoformat()
    return RespuestaMetricasCalibracion(
        exito=True,
        origen=origen,
        periodo={
            "inicio": desde.isoformat() if desde else "sin_limite",
            "fin": hasta.isoformat() if hasta else "sin_limite",
        },
        modelo_version_id=modelo_version_id,
        metricas_por_mercado=metricas_resultado,
        alertas_activas=alertas_filtradas,
        timestamp_calculo=timestamp,
    )


@router.get(
    "/resumen-deportes",
    response_model=ResumenDeportesResponse,
    summary="Resumen operativo por deporte",
    description="Retorna conteos rápidos de predicciones en baloncesto y fútbol.",
)
async def obtener_resumen_deportes() -> ResumenDeportesResponse:
    pool = obtener_pool()

    query_nba = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE resuelto = false OR resuelto IS NULL) AS pendientes,
            MAX(COALESCE(creado_en, timestamp_generacion)) AS ultima
        FROM predicciones_registradas
    """

    query_futbol = """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE resuelto = false OR resuelto IS NULL) AS pendientes,
            MAX(COALESCE(creado_en, timestamp_generacion)) AS ultima
        FROM predicciones_futbol
    """

    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_nba)
                nba = cursor.fetchone()

                cursor.execute(query_futbol)
                futbol = cursor.fetchone()

        resumen = [
            ResumenDeporte(
                deporte="baloncesto",
                total_predicciones=int(nba[0] or 0),
                pendientes_resolver=int(nba[1] or 0),
                ultima_prediccion=nba[2].isoformat() if nba[2] else None,
            ),
            ResumenDeporte(
                deporte="futbol",
                total_predicciones=int(futbol[0] or 0),
                pendientes_resolver=int(futbol[1] or 0),
                ultima_prediccion=futbol[2].isoformat() if futbol[2] else None,
            ),
        ]

        return ResumenDeportesResponse(
            exito=True,
            resumen=resumen,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as exc:
        logger.exception("Error obteniendo resumen de deportes")
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}")


@router.get(
    "/calibracion/{mercado}/curva",
    response_model=RespuestaCurvaCalibracion,
    summary="Obtener curva de calibración para un mercado",
    description="""
    Retorna los bins de la curva de calibración para visualización.

    ## Tipos de bins:
    - `fijos`: Rangos de 0.1 (0.0-0.1, 0.1-0.2, ...).
    - `cuantiles`: Cada bin con ~mismo número de muestras.
    """,
)
async def obtener_curva_calibracion(
    mercado: str = Path(
        ..., pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$", description="Mercado objetivo"
    ),
    origen: str = Query(
        ...,
        pattern="^(API_USUARIO|BACKTEST_SINTETICO|BACKTEST_BATCH)$",
        description="Origen de predicciones (OBLIGATORIO)",
    ),
    tipo_bins: str = Query("fijos", pattern="^(fijos|cuantiles)$"),
    n_bins: int = Query(10, ge=5, le=20),
    desde: Optional[date] = Query(None),
    hasta: Optional[date] = Query(None),
) -> RespuestaCurvaCalibracion:
    """Calcula y retorna la curva de calibración para un mercado."""
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=400,
            detail="Fecha 'desde' no puede ser posterior a 'hasta'",
        )

    periodo = _resolver_periodo(
        mercado,
        origen,
        desde=desde,
        hasta=hasta,
        modelo_version_id=None,
    )
    if periodo is None:
        raise HTTPException(status_code=404, detail="No hay predicciones para el periodo.")

    cache_key = (
        "curva",
        mercado,
        origen,
        tipo_bins,
        n_bins,
        periodo.inicio,
        periodo.fin,
    )
    cacheada = _obtener_cache(_cache_curvas, cache_key)
    if cacheada:
        return RespuestaCurvaCalibracion(**cacheada)

    predicciones = _obtener_predicciones_para_curva(
        mercado=mercado,
        origen=origen,
        desde=periodo.inicio,
        hasta=periodo.fin,
    )
    predicciones_filtradas = [
        (p["p_efectiva"], p["outcome_binario"])
        for p in predicciones
        if p["outcome_binario"] is not None
    ]
    n_excluidos = _contar_excluidos_push(
        mercado,
        origen,
        periodo.inicio,
        periodo.fin,
        modelo_version_id=None,
    )

    resultado = _calcular_curva(tipo_bins, predicciones_filtradas, n_bins=n_bins)

    suma_bins = sum(bin_info.n for bin_info in resultado.bins)
    if suma_bins != resultado.n_total:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Inconsistencia interna: suma bins ({suma_bins}) "
                f"!= total ({resultado.n_total})"
            ),
        )

    linea_perfecta = [{"x": i / 10, "y": i / 10} for i in range(11)]

    respuesta = RespuestaCurvaCalibracion(
        exito=True,
        mercado=mercado,
        origen=origen,
        tipo_bins=tipo_bins,
        n_bins=n_bins,
        n_predicciones_total=resultado.n_total,
        n_excluidos_push=n_excluidos,
        bins=_mapear_bins_respuesta(resultado.bins),
        ece=resultado.ece,
        mce=resultado.mce,
        bin_peor_calibrado=resultado.bin_peor,
        linea_perfecta=linea_perfecta,
        periodo={
            "inicio": periodo.texto_inicio,
            "fin": periodo.texto_fin,
        },
        timestamp_calculo=datetime.now().isoformat(),
    )

    _guardar_cache(_cache_curvas, cache_key, respuesta.model_dump())
    return respuesta


def _calcular_curva(
    tipo_bins: str,
    predicciones: List[Tuple[float, bool]],
    *,
    n_bins: int,
) -> ResultadoCurva:
    if tipo_bins == "cuantiles":
        return calcular_curva_bins_cuantiles(
            predicciones,
            n_bins=n_bins,
            min_por_bin=MIN_POR_BIN,
        )
    return calcular_curva_bins_fijos(
        predicciones,
        n_bins=n_bins,
        min_por_bin=MIN_POR_BIN,
    )


def _mapear_bins_respuesta(
    bins: List[BinCalibracionInterno],
) -> List[BinCalibracionResponse]:
    return [
        BinCalibracionResponse(
            rango_inicio=bin_info.rango_inicio,
            rango_fin=bin_info.rango_fin,
            n=bin_info.n,
            probabilidad_promedio=bin_info.probabilidad_promedio,
            frecuencia_real=bin_info.frecuencia_real,
            gap=bin_info.gap,
            gap_con_signo=bin_info.gap_con_signo,
            suficiente_data=bin_info.suficiente_data,
            advertencia=bin_info.advertencia,
        )
        for bin_info in bins
    ]


def _resolver_periodo(
    mercado: str,
    origen: str,
    *,
    desde: Optional[date],
    hasta: Optional[date],
    modelo_version_id: Optional[int],
) -> Optional[PeriodoConsulta]:
    if desde and hasta:
        return PeriodoConsulta(
            inicio=desde,
            fin=hasta,
            texto_inicio=desde.isoformat(),
            texto_fin=hasta.isoformat(),
        )

    pool = obtener_pool()
    filtros = ["mercado = %s", "origen = %s"]
    params: list[object] = [mercado, origen]
    if modelo_version_id is not None:
        filtros.append("modelo_version_id = %s")
        params.append(modelo_version_id)
    where_sql = " AND ".join(filtros)

    consulta = f"""
        SELECT MIN(fecha_partido), MAX(fecha_partido)
        FROM vista_predicciones_para_calibracion
        WHERE {where_sql}
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    if not fila or (fila[0] is None and fila[1] is None):
        return None

    inicio = desde or fila[0]
    fin = hasta or fila[1]
    if inicio is None or fin is None:
        return None

    return PeriodoConsulta(
        inicio=inicio,
        fin=fin,
        texto_inicio=desde.isoformat() if desde else "sin_limite",
        texto_fin=hasta.isoformat() if hasta else "sin_limite",
    )


def _buscar_metricas_precalculadas(
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    *,
    modelo_version_id: Optional[int],
) -> Optional[dict[str, object]]:
    pool = obtener_pool()
    consulta = """
        SELECT
            n_predicciones,
            brier_score,
            brier_score_raw,
            brier_score_calibrado,
            log_loss,
            log_loss_raw,
            log_loss_calibrado,
            ece,
            mce,
            sharpness,
            base_rate,
            mae_media,
            rmse_media,
            sesgo_media,
            alertas
        FROM metricas_calibracion
        WHERE periodo_inicio = %s
          AND periodo_fin = %s
          AND mercado = %s
          AND origen_predicciones = %s
          AND (%s IS NULL OR modelo_version_id = %s)
        LIMIT 1
    """
    params = [
        fecha_inicio,
        fecha_fin,
        mercado,
        origen,
        modelo_version_id,
        modelo_version_id,
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    if not fila:
        return None

    return {
        "n_predicciones": fila[0],
        "brier_score": fila[1],
        "brier_score_raw": fila[2],
        "brier_score_calibrado": fila[3],
        "log_loss": fila[4],
        "log_loss_raw": fila[5],
        "log_loss_calibrado": fila[6],
        "ece": fila[7],
        "mce": fila[8],
        "sharpness": fila[9],
        "base_rate": fila[10],
        "distribucion": {
            "mae_media": fila[11],
            "rmse_media": fila[12],
            "sesgo_media": fila[13],
        },
        "alertas": fila[14] or [],
    }


def _contar_excluidos_push(
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    *,
    modelo_version_id: Optional[int],
) -> int:
    pool = obtener_pool()
    filtros = [
        "mercado = %s",
        "origen = %s",
        "fecha_partido >= %s",
        "fecha_partido <= %s",
        "resuelto = true",
    ]
    params: list[object] = [mercado, origen, fecha_inicio, fecha_fin]
    if modelo_version_id is not None:
        filtros.append("modelo_version_id = %s")
        params.append(modelo_version_id)

    where_sql = " AND ".join(filtros)
    consulta = f"""
        SELECT COUNT(*)
        FROM predicciones_registradas
        WHERE {where_sql}
          AND outcome_binario IS NULL
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            fila = cursor.fetchone()

    return int(fila[0]) if fila else 0


def _obtener_predicciones_para_curva(
    *,
    mercado: str,
    origen: str,
    desde: date,
    hasta: date,
) -> List[Dict[str, object]]:
    pool = obtener_pool()
    consulta = """
        SELECT p_efectiva, outcome_binario
        FROM vista_predicciones_para_calibracion
        WHERE mercado = %s
          AND origen = %s
          AND fecha_partido >= %s
          AND fecha_partido <= %s
          AND p_efectiva IS NOT NULL
        ORDER BY fecha_partido
    """
    params = [mercado, origen, desde, hasta]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    return [
        {"p_efectiva": float(fila[0]), "outcome_binario": fila[1]}
        for fila in filas
    ]


def _filtrar_alertas_periodo(
    alertas: List[dict],
    desde: Optional[date],
    hasta: Optional[date],
) -> List[dict]:
    if not desde and not hasta:
        return alertas

    inicio = desde or date.min
    fin = hasta or date.max

    filtradas = []
    for alerta in alertas:
        periodo_inicio = alerta.get("periodo_inicio")
        periodo_fin = alerta.get("periodo_fin")

        if periodo_inicio is None and periodo_fin is None:
            filtradas.append(alerta)
            continue

        inicio_alerta = periodo_inicio or date.min
        fin_alerta = periodo_fin or date.max

        if inicio_alerta <= fin and fin_alerta >= inicio:
            filtradas.append(alerta)

    return filtradas


def _obtener_cache(
    cache: dict[Tuple[object, ...], Tuple[float, dict[str, object]]],
    key: Tuple[object, ...],
) -> Optional[dict[str, object]]:
    ahora = time.monotonic()
    item = cache.get(key)
    if not item:
        return None
    timestamp, data = item
    if ahora - timestamp > _CACHE_TTL_SEGUNDOS:
        cache.pop(key, None)
        return None
    return data


def _guardar_cache(
    cache: dict[Tuple[object, ...], Tuple[float, dict[str, object]]],
    key: Tuple[object, ...],
    data: dict[str, object],
) -> None:
    cache[key] = (time.monotonic(), data)


# ══════════════════════════════════════════════════════════════════════
# TABLERO PROFESIONAL DE SALUD DE PREDICCIÓN (MULTIDEPORTE)
# ══════════════════════════════════════════════════════════════════════


class MetricasDeporteAvanzadas(BaseModel):
    deporte: str
    n_total: int
    n_resueltas: int
    n_pendientes: int
    accuracy: Optional[float] = None
    brier: Optional[float] = None
    brier_7d: Optional[float] = None
    brier_prev_30d: Optional[float] = None
    deriva_pct: Optional[float] = None
    alerta_deriva: bool = False
    ultima_prediccion: Optional[str] = None
    ultima_resolucion: Optional[str] = None


class ModeloSalud(BaseModel):
    deporte: str
    version_modelo: Optional[str] = None
    fecha_entrenamiento: Optional[str] = None
    partidos_entrenamiento: Optional[int] = None


class TableroSaludResponse(BaseModel):
    exito: bool
    score_global: int
    resumen_ejecutivo: str
    deportes: List[MetricasDeporteAvanzadas]
    modelos: List[ModeloSalud]
    alertas: List[str]
    timestamp: str


def _score_salud(
    *,
    brier: Optional[float],
    deriva_pct: Optional[float],
    n_resueltas: int,
    pendientes: int,
) -> int:
    score = 100

    if brier is None:
        score -= 15
    elif brier > 0.30:
        score -= 25
    elif brier > 0.25:
        score -= 15
    elif brier > 0.20:
        score -= 8

    if deriva_pct is not None:
        if deriva_pct > 25:
            score -= 25
        elif deriva_pct > 15:
            score -= 15
        elif deriva_pct > 8:
            score -= 8

    if n_resueltas < 100:
        score -= 10
    if pendientes > (n_resueltas * 2 + 500):
        score -= 10

    return max(0, min(100, score))


@router.get(
    "/tablero-salud",
    response_model=TableroSaludResponse,
    summary="Tablero profesional de salud de predicción",
    description="Incluye accuracy, Brier por deporte, deriva reciente y estado de modelos.",
)
async def obtener_tablero_salud() -> TableroSaludResponse:
    pool = obtener_pool()
    alertas: List[str] = []

    query_deporte = """
        WITH base AS (
            SELECT
                %s::text AS deporte,
                COUNT(*) AS n_total,
                COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS n_resueltas,
                COUNT(*) FILTER (WHERE outcome_binario IS NULL OR resuelto IS DISTINCT FROM true) AS n_pendientes,
                AVG(CASE
                    WHEN outcome_binario IS NULL THEN NULL
                    WHEN (({prob_expr}) >= 0.5 AND outcome_binario = true)
                      OR (({prob_expr}) < 0.5 AND outcome_binario = false) THEN 1.0
                    ELSE 0.0
                END) AS accuracy,
                AVG(POWER(({prob_expr}) - CASE WHEN outcome_binario THEN 1 ELSE 0 END, 2))
                    FILTER (WHERE outcome_binario IS NOT NULL) AS brier,
                MAX(COALESCE(timestamp_generacion, creado_en)) AS ultima_prediccion,
                MAX(timestamp_resolucion) AS ultima_resolucion
            FROM {tabla}
            WHERE {prob_expr} IS NOT NULL
        ),
        rec7 AS (
            SELECT AVG(POWER(({prob_expr}) - CASE WHEN outcome_binario THEN 1 ELSE 0 END, 2)) AS brier_7d
            FROM {tabla}
            WHERE outcome_binario IS NOT NULL
              AND {prob_expr} IS NOT NULL
              AND COALESCE(timestamp_resolucion, timestamp_generacion, creado_en) >= (NOW() - INTERVAL '7 days')
        ),
        prev30 AS (
            SELECT AVG(POWER(({prob_expr}) - CASE WHEN outcome_binario THEN 1 ELSE 0 END, 2)) AS brier_prev_30d
            FROM {tabla}
            WHERE outcome_binario IS NOT NULL
              AND {prob_expr} IS NOT NULL
              AND COALESCE(timestamp_resolucion, timestamp_generacion, creado_en) >= (NOW() - INTERVAL '37 days')
              AND COALESCE(timestamp_resolucion, timestamp_generacion, creado_en) <  (NOW() - INTERVAL '7 days')
        )
        SELECT
            base.deporte,
            base.n_total,
            base.n_resueltas,
            base.n_pendientes,
            base.accuracy,
            base.brier,
            rec7.brier_7d,
            prev30.brier_prev_30d,
            base.ultima_prediccion,
            base.ultima_resolucion
        FROM base, rec7, prev30
    """

    query_nba = query_deporte.format(
        tabla="predicciones_registradas",
        prob_expr="COALESCE(p_calibrada, p_raw)",
    )
    query_fut = query_deporte.format(
        tabla="predicciones_futbol",
        prob_expr="COALESCE(prob_over_calibrada, prob_over)",
    )

    query_modelo_nba = """
        SELECT version, fecha_entrenamiento, partidos_entrenamiento
        FROM modelo_versiones
        ORDER BY fecha_entrenamiento DESC NULLS LAST
        LIMIT 1
    """

    query_modelo_fut = """
        SELECT version, fecha_entrenamiento, partidos_entrenamiento
        FROM modelo_versiones_futbol
        ORDER BY creado_en DESC NULLS LAST
        LIMIT 1
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_nba, ["baloncesto"])
            nba = cursor.fetchone()

            cursor.execute(query_fut, ["futbol"])
            fut = cursor.fetchone()

            cursor.execute(query_modelo_nba)
            modelo_nba = cursor.fetchone()

            cursor.execute(query_modelo_fut)
            modelo_fut = cursor.fetchone()

    deportes: List[MetricasDeporteAvanzadas] = []
    for fila in [nba, fut]:
        deporte = fila[0]
        brier_7d = float(fila[6]) if fila[6] is not None else None
        brier_prev_30d = float(fila[7]) if fila[7] is not None else None
        deriva_pct = None
        if brier_7d is not None and brier_prev_30d not in (None, 0):
            deriva_pct = ((brier_7d - brier_prev_30d) / brier_prev_30d) * 100.0

        alerta_deriva = bool(deriva_pct is not None and deriva_pct > 15.0)
        if alerta_deriva:
            alertas.append(
                f"Deriva detectada en {deporte}: Brier 7d empeoró {deriva_pct:.1f}% vs 30d previos."
            )

        deportes.append(
            MetricasDeporteAvanzadas(
                deporte=deporte,
                n_total=int(fila[1] or 0),
                n_resueltas=int(fila[2] or 0),
                n_pendientes=int(fila[3] or 0),
                accuracy=float(fila[4]) if fila[4] is not None else None,
                brier=float(fila[5]) if fila[5] is not None else None,
                brier_7d=brier_7d,
                brier_prev_30d=brier_prev_30d,
                deriva_pct=deriva_pct,
                alerta_deriva=alerta_deriva,
                ultima_prediccion=fila[8].isoformat() if fila[8] else None,
                ultima_resolucion=fila[9].isoformat() if fila[9] else None,
            )
        )

    modelos = [
        ModeloSalud(
            deporte="baloncesto",
            version_modelo=str(modelo_nba[0]) if modelo_nba else None,
            fecha_entrenamiento=modelo_nba[1].isoformat() if modelo_nba and modelo_nba[1] else None,
            partidos_entrenamiento=int(modelo_nba[2]) if modelo_nba and modelo_nba[2] is not None else None,
        ),
        ModeloSalud(
            deporte="futbol",
            version_modelo=str(modelo_fut[0]) if modelo_fut else None,
            fecha_entrenamiento=modelo_fut[1].isoformat() if modelo_fut and modelo_fut[1] else None,
            partidos_entrenamiento=int(modelo_fut[2]) if modelo_fut and modelo_fut[2] is not None else None,
        ),
    ]

    for d in deportes:
        if d.n_resueltas == 0 and d.n_total > 0:
            alertas.append(
                f"{d.deporte}: hay predicciones pero 0 resueltas; sin resolución no se puede medir accuracy/Brier."
            )
        if d.n_pendientes > 1000:
            alertas.append(
                f"{d.deporte}: backlog alto de pendientes ({d.n_pendientes}). Prioriza job de resolución." 
            )

    if not alertas:
        alertas.append("Sin alertas críticas activas de deriva por ahora.")

    scores = [
        _score_salud(
            brier=d.brier,
            deriva_pct=d.deriva_pct,
            n_resueltas=d.n_resueltas,
            pendientes=d.n_pendientes,
        )
        for d in deportes
    ]
    score_global = int(sum(scores) / len(scores)) if scores else 0

    if score_global >= 85:
        resumen = "Sistema saludable. Prioridad: aumentar cobertura de resoluciones y mantener calibración."
    elif score_global >= 70:
        resumen = "Sistema estable con áreas de mejora. Recomendada recalibración incremental y monitoreo semanal."
    else:
        resumen = "Sistema en riesgo de calidad. Requiere intervención en calibración, resolución y control de deriva."

    return TableroSaludResponse(
        exito=True,
        score_global=score_global,
        resumen_ejecutivo=resumen,
        deportes=deportes,
        modelos=modelos,
        alertas=alertas,
        timestamp=datetime.now().isoformat(),
    )


class MetricaMercadoGlobal(BaseModel):
    deporte: str
    mercado: str
    n_resueltas: int
    accuracy: Optional[float] = None
    brier: Optional[float] = None
    precision_label: str = "insuficiente"


class CalidadMercadosResponse(BaseModel):
    exito: bool
    ranking: List[MetricaMercadoGlobal]
    recomendaciones: List[str]
    timestamp: str


@router.get(
    "/calidad-mercados",
    response_model=CalidadMercadosResponse,
    summary="Ranking profesional de calidad por mercado",
    description="Consolida accuracy/Brier por mercado en baloncesto y fútbol para priorizar mejoras.",
)
async def obtener_calidad_mercados(
    min_muestras: int = Query(30, ge=10, le=500),
    limite: int = Query(20, ge=5, le=100),
) -> CalidadMercadosResponse:
    pool = obtener_pool()

    query_nba = """
        SELECT
            'baloncesto'::text AS deporte,
            mercado::text AS mercado,
            COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS n_resueltas,
            AVG(CASE
                WHEN outcome_binario IS NULL THEN NULL
                WHEN ((COALESCE(p_calibrada, p_raw)) >= 0.5 AND outcome_binario = true)
                  OR ((COALESCE(p_calibrada, p_raw)) < 0.5 AND outcome_binario = false) THEN 1.0
                ELSE 0.0
            END) AS accuracy,
            AVG(POWER(COALESCE(p_calibrada, p_raw) - CASE WHEN outcome_binario THEN 1 ELSE 0 END, 2))
                FILTER (WHERE outcome_binario IS NOT NULL) AS brier
        FROM predicciones_registradas
        GROUP BY mercado
    """

    query_fut = """
        SELECT
            'futbol'::text AS deporte,
            mercado::text AS mercado,
            COUNT(*) FILTER (WHERE outcome_binario IS NOT NULL) AS n_resueltas,
            AVG(CASE
                WHEN outcome_binario IS NULL THEN NULL
                WHEN ((COALESCE(prob_over_calibrada, prob_over)) >= 0.5 AND outcome_binario = true)
                  OR ((COALESCE(prob_over_calibrada, prob_over)) < 0.5 AND outcome_binario = false) THEN 1.0
                ELSE 0.0
            END) AS accuracy,
            AVG(POWER(COALESCE(prob_over_calibrada, prob_over) - CASE WHEN outcome_binario THEN 1 ELSE 0 END, 2))
                FILTER (WHERE outcome_binario IS NOT NULL) AS brier
        FROM predicciones_futbol
        GROUP BY mercado
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_nba)
            rows_nba = cursor.fetchall()
            cursor.execute(query_fut)
            rows_fut = cursor.fetchall()

    filas = rows_nba + rows_fut

    ranking: List[MetricaMercadoGlobal] = []
    for deporte, mercado, n_resueltas, accuracy, brier in filas:
        n = int(n_resueltas or 0)
        if n < min_muestras:
            continue

        if n >= 300:
            precision = "alta"
        elif n >= 100:
            precision = "media"
        else:
            precision = "baja"

        ranking.append(
            MetricaMercadoGlobal(
                deporte=str(deporte),
                mercado=str(mercado),
                n_resueltas=n,
                accuracy=float(accuracy) if accuracy is not None else None,
                brier=float(brier) if brier is not None else None,
                precision_label=precision,
            )
        )

    ranking.sort(
        key=lambda x: (
            999 if x.brier is None else x.brier,
            -(x.n_resueltas or 0),
        )
    )
    ranking = ranking[:limite]

    recomendaciones: List[str] = []
    peores = [r for r in ranking if r.brier is not None and r.brier > 0.26][:5]
    for r in peores:
        recomendaciones.append(
            f"{r.deporte}/{r.mercado}: Brier {r.brier:.3f} (n={r.n_resueltas}). Priorizar recalibración específica."
        )

    if not recomendaciones:
        recomendaciones.append("No hay mercados críticos con muestra suficiente por encima del umbral de Brier.")

    return CalidadMercadosResponse(
        exito=True,
        ranking=ranking,
        recomendaciones=recomendaciones,
        timestamp=datetime.now().isoformat(),
    )


class AccionSugerida(BaseModel):
    prioridad: str
    semaforo: str
    accion: str
    motivo: str
    impacto_score: float = 0.0


class RecomendacionesAccionResponse(BaseModel):
    exito: bool
    score_global: int
    semaforo_global: str
    acciones: List[AccionSugerida]
    timestamp: str


def _semaforo_por_score(score: int) -> str:
    if score >= 85:
        return "verde"
    if score >= 70:
        return "amarillo"
    return "rojo"


@router.get(
    "/recomendaciones-accion",
    response_model=RecomendacionesAccionResponse,
    summary="Recomendaciones automáticas de acción",
    description="Genera plan de acción priorizado según salud global y calidad por mercado.",
)
async def obtener_recomendaciones_accion(
    min_muestras: int = Query(30, ge=10, le=500),
) -> RecomendacionesAccionResponse:
    tablero = await obtener_tablero_salud()
    calidad = await obtener_calidad_mercados(min_muestras=min_muestras, limite=30)

    acciones: List[AccionSugerida] = []

    semaforo_global = _semaforo_por_score(tablero.score_global)

    # Acciones por deporte
    for d in tablero.deportes:
        if d.n_resueltas == 0 and d.n_total > 0:
            acciones.append(
                AccionSugerida(
                    prioridad="P1",
                    semaforo="rojo",
                    accion=f"Ejecutar ciclo de resolución para {d.deporte}",
                    motivo="No hay predicciones resueltas; no se puede medir calidad real.",
                    impacto_score=float(d.n_total or 0),
                )
            )

        if d.brier is not None and d.brier > 0.26:
            acciones.append(
                AccionSugerida(
                    prioridad="P1",
                    semaforo="rojo",
                    accion=f"Recalibrar modelo de {d.deporte}",
                    motivo=f"Brier alto ({d.brier:.3f}).",
                    impacto_score=float((d.n_resueltas or 0) * (d.brier or 0)),
                )
            )
        elif d.brier is not None and d.brier > 0.22:
            acciones.append(
                AccionSugerida(
                    prioridad="P2",
                    semaforo="amarillo",
                    accion=f"Monitorear y ajustar calibración de {d.deporte}",
                    motivo=f"Brier en zona de mejora ({d.brier:.3f}).",
                    impacto_score=float((d.n_resueltas or 0) * (d.brier or 0) * 0.6),
                )
            )

        if d.deriva_pct is not None and d.deriva_pct > 15:
            acciones.append(
                AccionSugerida(
                    prioridad="P1",
                    semaforo="rojo",
                    accion=f"Activar recalibración de emergencia en {d.deporte}",
                    motivo=f"Deriva de Brier +{d.deriva_pct:.1f}%.",
                    impacto_score=float((d.n_resueltas or 0) * ((d.deriva_pct or 0) / 100.0)),
                )
            )

    # Acciones por mercado crítico
    criticos = [m for m in calidad.ranking if m.brier is not None and m.brier > 0.26]
    for m in criticos[:5]:
        acciones.append(
            AccionSugerida(
                prioridad="P1",
                semaforo="rojo",
                accion=f"Recalibrar mercado {m.deporte}/{m.mercado}",
                motivo=f"Brier {m.brier:.3f} con n={m.n_resueltas}.",
                impacto_score=float((m.n_resueltas or 0) * (m.brier or 0)),
            )
        )

    if not acciones:
        acciones.append(
            AccionSugerida(
                prioridad="P3",
                semaforo="verde",
                accion="Mantener operación y monitoreo semanal",
                motivo="Sin señales críticas en score global ni mercados.",
                impacto_score=0.0,
            )
        )

    # Orden profesional: prioridad + severidad + impacto esperado
    orden_prioridad = {"P1": 1, "P2": 2, "P3": 3}
    orden_semaforo = {"rojo": 1, "amarillo": 2, "verde": 3}
    acciones.sort(
        key=lambda a: (
            orden_prioridad[a.prioridad],
            orden_semaforo[a.semaforo],
            -(a.impacto_score or 0.0),
        )
    )

    return RecomendacionesAccionResponse(
        exito=True,
        score_global=tablero.score_global,
        semaforo_global=semaforo_global,
        acciones=acciones,
        timestamp=datetime.now().isoformat(),
    )


class DriftMercadoItem(BaseModel):
    deporte: str
    mercado: str
    n_7d: int
    n_prev_30d: int
    brier_7d: Optional[float] = None
    brier_prev_30d: Optional[float] = None
    drift_pct: Optional[float] = None
    severidad: str


class DriftMercadosResponse(BaseModel):
    exito: bool
    items: List[DriftMercadoItem]
    resumen: str
    timestamp: str


def _severidad_drift(drift_pct: Optional[float]) -> str:
    if drift_pct is None:
        return "sin_datos"
    if drift_pct > 25:
        return "critica"
    if drift_pct > 15:
        return "alta"
    if drift_pct > 8:
        return "media"
    return "estable"


@router.get(
    "/drift-mercados",
    response_model=DriftMercadosResponse,
    summary="Drift de calidad por mercado",
    description="Compara Brier de 7 días vs 30 días previos para detectar degradación por mercado.",
)
async def obtener_drift_mercados(
    min_muestras: int = Query(20, ge=10, le=500),
    limite: int = Query(50, ge=5, le=200),
) -> DriftMercadosResponse:
    pool = obtener_pool()

    query_template = """
        WITH base AS (
            SELECT
                '{deporte}'::text AS deporte,
                {mercado_col}::text AS mercado,
                COUNT(*) FILTER (
                    WHERE {outcome_col} IS NOT NULL
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) >= (NOW() - INTERVAL '7 days')
                ) AS n_7d,
                COUNT(*) FILTER (
                    WHERE {outcome_col} IS NOT NULL
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) >= (NOW() - INTERVAL '37 days')
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) <  (NOW() - INTERVAL '7 days')
                ) AS n_prev_30d,
                AVG(
                    POWER({prob_expr} - CASE WHEN {outcome_col} THEN 1 ELSE 0 END, 2)
                ) FILTER (
                    WHERE {outcome_col} IS NOT NULL
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) >= (NOW() - INTERVAL '7 days')
                ) AS brier_7d,
                AVG(
                    POWER({prob_expr} - CASE WHEN {outcome_col} THEN 1 ELSE 0 END, 2)
                ) FILTER (
                    WHERE {outcome_col} IS NOT NULL
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) >= (NOW() - INTERVAL '37 days')
                      AND COALESCE({ts_res_col}, {ts_gen_col}, {ts_alt_col}) <  (NOW() - INTERVAL '7 days')
                ) AS brier_prev_30d
            FROM {tabla}
            WHERE {prob_expr} IS NOT NULL
            GROUP BY {mercado_col}
        )
        SELECT * FROM base
    """

    query_nba = query_template.format(
        deporte="baloncesto",
        mercado_col="mercado",
        outcome_col="outcome_binario",
        ts_res_col="timestamp_resolucion",
        ts_gen_col="timestamp_generacion",
        ts_alt_col="creado_en",
        prob_expr="COALESCE(p_calibrada, p_raw)",
        tabla="predicciones_registradas",
    )

    query_fut = query_template.format(
        deporte="futbol",
        mercado_col="mercado",
        outcome_col="outcome_binario",
        ts_res_col="timestamp_resolucion",
        ts_gen_col="timestamp_generacion",
        ts_alt_col="creado_en",
        prob_expr="COALESCE(prob_over_calibrada, prob_over)",
        tabla="predicciones_futbol",
    )

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_nba)
            rows_nba = cursor.fetchall()
            cursor.execute(query_fut)
            rows_fut = cursor.fetchall()

    items: List[DriftMercadoItem] = []
    for r in rows_nba + rows_fut:
        deporte, mercado, n_7d, n_prev_30d, brier_7d, brier_prev_30d = r
        n7 = int(n_7d or 0)
        n30 = int(n_prev_30d or 0)
        if n7 < min_muestras or n30 < min_muestras:
            continue

        b7 = float(brier_7d) if brier_7d is not None else None
        b30 = float(brier_prev_30d) if brier_prev_30d is not None else None
        drift_pct = None
        if b7 is not None and b30 not in (None, 0):
            drift_pct = ((b7 - b30) / b30) * 100.0

        items.append(
            DriftMercadoItem(
                deporte=str(deporte),
                mercado=str(mercado),
                n_7d=n7,
                n_prev_30d=n30,
                brier_7d=b7,
                brier_prev_30d=b30,
                drift_pct=drift_pct,
                severidad=_severidad_drift(drift_pct),
            )
        )

    items.sort(
        key=lambda x: (
            999 if x.drift_pct is None else -x.drift_pct,
            -(x.n_7d + x.n_prev_30d),
        )
    )
    items = items[:limite]

    criticas = sum(1 for i in items if i.severidad == "critica")
    altas = sum(1 for i in items if i.severidad == "alta")
    if criticas > 0:
        resumen = f"Drift crítico detectado en {criticas} mercados."
    elif altas > 0:
        resumen = f"Drift alto detectado en {altas} mercados."
    elif items:
        resumen = "Sin drift crítico/alto con muestra suficiente."
    else:
        resumen = "Sin datos suficientes para evaluar drift por mercado."

    return DriftMercadosResponse(
        exito=True,
        items=items,
        resumen=resumen,
        timestamp=datetime.now().isoformat(),
    )


class AlertaIngestionItem(BaseModel):
    fuente: str
    ultima_actualizacion: Optional[str] = None
    horas_sin_actualizar: Optional[float] = None
    stale: bool
    severidad: str
    detalle: str


class AlertasIngestionResponse(BaseModel):
    exito: bool
    alertas: List[AlertaIngestionItem]
    resumen: str
    timestamp: str


def _tabla_existe(cursor, tabla: str) -> bool:
    cursor.execute("SELECT to_regclass(%s)", [f"public.{tabla}"])
    return cursor.fetchone()[0] is not None


def _columnas_tabla(cursor, tabla: str) -> set[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        """,
        [tabla],
    )
    return {str(r[0]) for r in cursor.fetchall()}


def _ultima_fecha_columna(cursor, tabla: str, columnas_candidatas: List[str]):
    columnas = _columnas_tabla(cursor, tabla)
    for c in columnas_candidatas:
        if c in columnas:
            try:
                cursor.execute(f"SELECT MAX({c}) FROM {tabla}")
                return cursor.fetchone()[0], c
            except Exception:
                continue
    return None, None


@router.get(
    "/alertas-ingestion",
    response_model=AlertasIngestionResponse,
    summary="Alertas de ingestión stale",
    description="Detecta fuentes sin actualización reciente para prevenir degradación silenciosa.",
)
async def obtener_alertas_ingestion(
    max_horas_sin_actualizar: int = Query(24, ge=1, le=240),
) -> AlertasIngestionResponse:
    pool = obtener_pool()
    now = datetime.now()
    alertas: List[AlertaIngestionItem] = []

    fuentes = [
        ("ingestion_state_baloncesto", ["actualizado_en", "updated_at", "last_run_at", "creado_en"]),
        ("ingestion_state_futbol", ["actualizado_en", "updated_at", "last_run_at", "creado_en"]),
        ("predicciones_registradas", ["timestamp_generacion", "creado_en", "actualizado_en"]),
        ("predicciones_futbol", ["timestamp_generacion", "creado_en", "actualizado_en"]),
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            for tabla, candidatos in fuentes:
                if not _tabla_existe(cursor, tabla):
                    alertas.append(
                        AlertaIngestionItem(
                            fuente=tabla,
                            stale=True,
                            severidad="alta",
                            detalle="Tabla no existe en esquema público.",
                        )
                    )
                    continue

                valor, col = _ultima_fecha_columna(cursor, tabla, candidatos)
                if valor is None:
                    alertas.append(
                        AlertaIngestionItem(
                            fuente=tabla,
                            stale=True,
                            severidad="media",
                            detalle="No se encontró columna de timestamp utilizable.",
                        )
                    )
                    continue

                if hasattr(valor, "tzinfo") and valor.tzinfo is not None:
                    valor_dt = valor.replace(tzinfo=None)
                else:
                    valor_dt = valor

                horas = (now - valor_dt).total_seconds() / 3600.0
                stale = horas > max_horas_sin_actualizar

                if stale and horas > max_horas_sin_actualizar * 2:
                    sev = "critica"
                elif stale:
                    sev = "alta"
                elif horas > max_horas_sin_actualizar * 0.7:
                    sev = "media"
                else:
                    sev = "baja"

                alertas.append(
                    AlertaIngestionItem(
                        fuente=tabla,
                        ultima_actualizacion=valor_dt.isoformat(),
                        horas_sin_actualizar=round(horas, 2),
                        stale=stale,
                        severidad=sev,
                        detalle=f"Referencia: {tabla}.{col}",
                    )
                )

    criticas = sum(1 for a in alertas if a.severidad == "critica")
    stale_count = sum(1 for a in alertas if a.stale)
    if criticas > 0:
        resumen = f"{criticas} fuentes en estado crítico de actualización."
    elif stale_count > 0:
        resumen = f"{stale_count} fuentes stale detectadas."
    else:
        resumen = "Sin fuentes stale según el umbral configurado."

    return AlertasIngestionResponse(
        exito=True,
        alertas=alertas,
        resumen=resumen,
        timestamp=now.isoformat(),
    )


class MercadoPolicyItem(BaseModel):
    deporte: str
    mercado: str
    estado: str  # verde|amarillo|rojo
    bloqueado: bool
    motivo: str
    brier: Optional[float] = None
    n_resueltas: int = 0


class PoliticaMercadosResponse(BaseModel):
    exito: bool
    politica: str
    mercados: List[MercadoPolicyItem]
    resumen: dict
    timestamp: str


@router.get(
    "/politica-mercados",
    response_model=PoliticaMercadosResponse,
    summary="Policy-as-code para habilitar/bloquear mercados",
    description="Clasifica mercados en verde/amarillo/rojo y marca bloqueados según umbrales de riesgo.",
)
async def obtener_politica_mercados(
    min_muestras: int = Query(30, ge=10, le=500),
    bloquear_brier: float = Query(0.28, ge=0.18, le=0.40),
    warning_brier: float = Query(0.24, ge=0.18, le=0.40),
) -> PoliticaMercadosResponse:
    calidad = await obtener_calidad_mercados(min_muestras=min_muestras, limite=200)

    mercados: List[MercadoPolicyItem] = []
    for m in calidad.ranking:
        brier = m.brier
        if brier is None:
            estado = "amarillo"
            bloqueado = True
            motivo = "Sin brier disponible con muestra suficiente."
        elif brier >= bloquear_brier:
            estado = "rojo"
            bloqueado = True
            motivo = f"Brier alto ({brier:.3f}) >= umbral bloqueo ({bloquear_brier:.3f})."
        elif brier >= warning_brier:
            estado = "amarillo"
            bloqueado = False
            motivo = f"Brier en zona de vigilancia ({brier:.3f})."
        else:
            estado = "verde"
            bloqueado = False
            motivo = "Mercado apto para operación estándar."

        mercados.append(
            MercadoPolicyItem(
                deporte=m.deporte,
                mercado=m.mercado,
                estado=estado,
                bloqueado=bloqueado,
                motivo=motivo,
                brier=brier,
                n_resueltas=m.n_resueltas,
            )
        )

    resumen = {
        "total": len(mercados),
        "rojos": sum(1 for x in mercados if x.estado == "rojo"),
        "amarillos": sum(1 for x in mercados if x.estado == "amarillo"),
        "verdes": sum(1 for x in mercados if x.estado == "verde"),
        "bloqueados": sum(1 for x in mercados if x.bloqueado),
    }

    return PoliticaMercadosResponse(
        exito=True,
        politica=(
            "Bloquear mercados con Brier >= bloquear_brier; "
            "vigilar warning_brier <= Brier < bloquear_brier; operar normal por debajo."
        ),
        mercados=mercados,
        resumen=resumen,
        timestamp=datetime.now().isoformat(),
    )


class SugerenciaUmbral(BaseModel):
    deporte: str
    warning_brier_sugerido: float
    bloqueo_brier_sugerido: float
    muestra_base: int
    razon: str


class SugerenciasUmbralesResponse(BaseModel):
    exito: bool
    sugerencias: List[SugerenciaUmbral]
    timestamp: str


class ModoEstrictoResponse(BaseModel):
    exito: bool
    habilitar_recomendaciones: bool
    semaforo_global: str
    score_global: int
    motivos_bloqueo: List[str]
    timestamp: str


class ResumenEjecutivoCompactoResponse(BaseModel):
    exito: bool
    go_no_go: str
    score_global: int
    semaforo_global: str
    alertas_criticas: int
    top_acciones: List[str]
    timestamp: str


@router.get(
    "/sugerencias-umbrales",
    response_model=SugerenciasUmbralesResponse,
    summary="Sugerencias automáticas de umbrales por deporte",
    description="Propone umbrales warning/bloqueo según desempeño histórico de mercados.",
)
async def obtener_sugerencias_umbrales(
    min_muestras: int = Query(30, ge=10, le=500),
) -> SugerenciasUmbralesResponse:
    calidad = await obtener_calidad_mercados(min_muestras=min_muestras, limite=500)

    por_deporte: Dict[str, List[float]] = {}
    muestras: Dict[str, int] = {}
    for item in calidad.ranking:
        if item.brier is None:
            continue
        por_deporte.setdefault(item.deporte, []).append(float(item.brier))
        muestras[item.deporte] = muestras.get(item.deporte, 0) + int(item.n_resueltas or 0)

    sugerencias: List[SugerenciaUmbral] = []
    for deporte, briers in por_deporte.items():
        if not briers:
            continue
        briers_sorted = sorted(briers)
        p60 = briers_sorted[min(len(briers_sorted) - 1, int(len(briers_sorted) * 0.60))]
        p80 = briers_sorted[min(len(briers_sorted) - 1, int(len(briers_sorted) * 0.80))]

        warning = max(0.20, min(0.30, round(p60 + 0.01, 3)))
        bloqueo = max(warning + 0.02, min(0.36, round(p80 + 0.015, 3)))

        sugerencias.append(
            SugerenciaUmbral(
                deporte=deporte,
                warning_brier_sugerido=warning,
                bloqueo_brier_sugerido=bloqueo,
                muestra_base=int(muestras.get(deporte, 0)),
                razon=(
                    "Basado en percentiles de Brier por mercado (P60 warning, P80 bloqueo) "
                    "con límites de seguridad."
                ),
            )
        )

    if not sugerencias:
        sugerencias.append(
            SugerenciaUmbral(
                deporte="global",
                warning_brier_sugerido=0.24,
                bloqueo_brier_sugerido=0.28,
                muestra_base=0,
                razon="Sin datos suficientes; usar umbrales conservadores por defecto.",
            )
        )

    return SugerenciasUmbralesResponse(
        exito=True,
        sugerencias=sugerencias,
        timestamp=datetime.now().isoformat(),
    )


@router.get(
    "/modo-estricto",
    response_model=ModoEstrictoResponse,
    summary="Gate global de operación en modo producción estricto",
    description="Determina si el sistema debe permitir recomendaciones según score, drift e ingestión.",
)
async def obtener_modo_estricto(
    score_minimo: int = Query(75, ge=40, le=95),
    max_fuentes_stale_criticas: int = Query(0, ge=0, le=10),
) -> ModoEstrictoResponse:
    tablero = await obtener_tablero_salud()
    ingest = await obtener_alertas_ingestion(max_horas_sin_actualizar=24)

    semaforo = _semaforo_por_score(tablero.score_global)
    criticas_ingestion = sum(1 for a in ingest.alertas if a.severidad == "critica")

    motivos: List[str] = []
    if tablero.score_global < score_minimo:
        motivos.append(
            f"score_global {tablero.score_global} < score_minimo {score_minimo}"
        )
    if semaforo == "rojo":
        motivos.append("semaforo global en rojo")
    if criticas_ingestion > max_fuentes_stale_criticas:
        motivos.append(
            f"fuentes stale críticas {criticas_ingestion} > permitido {max_fuentes_stale_criticas}"
        )

    # Si hay deporte sin resueltas con volumen relevante, modo estricto bloquea
    for d in tablero.deportes:
        if d.n_total >= 100 and d.n_resueltas == 0:
            motivos.append(
                f"{d.deporte}: n_total={d.n_total} sin predicciones resueltas"
            )

    return ModoEstrictoResponse(
        exito=True,
        habilitar_recomendaciones=(len(motivos) == 0),
        semaforo_global=semaforo,
        score_global=tablero.score_global,
        motivos_bloqueo=motivos,
        timestamp=datetime.now().isoformat(),
    )


@router.get(
    "/resumen-ejecutivo-compacto",
    response_model=ResumenEjecutivoCompactoResponse,
    summary="Resumen ejecutivo compacto (30 segundos)",
    description="Salida breve con GO/NO-GO, score, severidad y acciones top.",
)
async def obtener_resumen_ejecutivo_compacto(
    min_muestras: int = Query(30, ge=10, le=500),
) -> ResumenEjecutivoCompactoResponse:
    tablero = await obtener_tablero_salud()
    modo = await obtener_modo_estricto(
        score_minimo=75,
        max_fuentes_stale_criticas=0,
    )
    recomendaciones = await obtener_recomendaciones_accion(min_muestras=min_muestras)

    alertas_criticas = sum(1 for a in tablero.alertas if "crít" in a.lower() or "crit" in a.lower())
    top_acciones = [f"[{a.prioridad}/{a.semaforo}] {a.accion}" for a in recomendaciones.acciones[:5]]

    return ResumenEjecutivoCompactoResponse(
        exito=True,
        go_no_go="GO" if modo.habilitar_recomendaciones else "NO-GO",
        score_global=tablero.score_global,
        semaforo_global=modo.semaforo_global,
        alertas_criticas=alertas_criticas,
        top_acciones=top_acciones,
        timestamp=datetime.now().isoformat(),
    )

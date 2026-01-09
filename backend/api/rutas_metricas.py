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

    n_total_antes = len(predicciones)
    predicciones_filtradas = [
        (p["p_raw"], p["outcome_binario"])
        for p in predicciones
        if p["outcome_binario"] is not None
    ]
    n_excluidos = n_total_antes - len(predicciones_filtradas)

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
    ]
    params: list[object] = [mercado, origen, fecha_inicio, fecha_fin]
    if modelo_version_id is not None:
        filtros.append("modelo_version_id = %s")
        params.append(modelo_version_id)

    where_sql = " AND ".join(filtros)
    consulta = f"""
        SELECT COUNT(*)
        FROM vista_predicciones_para_calibracion
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
        SELECT p_raw, outcome_binario
        FROM vista_predicciones_para_calibracion
        WHERE mercado = %s
          AND origen = %s
          AND fecha_partido >= %s
          AND fecha_partido <= %s
          AND p_raw IS NOT NULL
        ORDER BY fecha_partido
    """
    params = [mercado, origen, desde, hasta]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            filas = cursor.fetchall()

    return [
        {"p_raw": float(fila[0]), "outcome_binario": fila[1]}
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

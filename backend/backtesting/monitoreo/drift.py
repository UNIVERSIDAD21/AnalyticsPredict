# -*- coding: utf-8 -*-
"""
drift.py — Detección de drift en métricas de calibración (T24).

Este módulo detecta degradación del modelo comparando métricas actuales
contra umbrales absolutos y baseline histórico.

REGLA CRÍTICA: Siempre separar evaluación por origen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import logging
from typing import Dict, List, Optional
from uuid import uuid4

from backtesting.metricas.calculador import calcular_metricas_calibracion
from backtesting.monitoreo.configuracion_drift import (
    CONFIG_DRIFT_DEFAULT,
    ConfiguracionDrift,
)

logger = logging.getLogger(__name__)


@dataclass
class Alerta:
    """Una alerta de drift detectada."""

    id: str
    mercado: str
    origen: str
    periodo_inicio: Optional[date]
    periodo_fin: Optional[date]
    modelo_version_id: Optional[int]
    tipo: str
    severidad: str
    metrica_afectada: str
    valor_actual: float
    valor_umbral: Optional[float]
    valor_baseline: Optional[float]
    cambio_porcentual: Optional[float]
    mensaje: str
    recomendacion: str
    timestamp: str


@dataclass
class ResultadoEvaluacionDrift:
    """Resultado de evaluar drift para un mercado/origen."""

    mercado: str
    origen: str
    alertas: List[Alerta]
    metricas_actuales: Dict[str, float]
    metricas_baseline: Optional[Dict[str, float]]
    tendencia: Optional[List[Dict[str, float]]]
    evaluacion_exitosa: bool
    mensaje: Optional[str] = None


def detectar_drift(
    mercado: str,
    origen: str,
    config: Optional[ConfiguracionDrift] = None,
    fecha_evaluacion: Optional[date] = None,
) -> ResultadoEvaluacionDrift:
    """
    Detecta drift comparando métricas actuales vs baseline y umbrales.
    """
    config = config or CONFIG_DRIFT_DEFAULT
    fecha_evaluacion = fecha_evaluacion or date.today()

    fecha_inicio_actual = fecha_evaluacion - timedelta(days=config.ventana_actual_dias)
    metricas_actuales = _obtener_metricas_periodo(
        mercado, origen, fecha_inicio_actual, fecha_evaluacion
    )

    if not metricas_actuales:
        return ResultadoEvaluacionDrift(
            mercado=mercado,
            origen=origen,
            alertas=[],
            metricas_actuales={},
            metricas_baseline=None,
            tendencia=None,
            evaluacion_exitosa=False,
            mensaje="Sin métricas para el periodo actual",
        )

    n_actual = metricas_actuales.get("n_predicciones", 0)
    if n_actual < config.min_predicciones_evaluar:
        return ResultadoEvaluacionDrift(
            mercado=mercado,
            origen=origen,
            alertas=[
                _crear_alerta_datos_insuficientes(
                    mercado, origen, n_actual, config
                )
            ],
            metricas_actuales=metricas_actuales,
            metricas_baseline=None,
            tendencia=None,
            evaluacion_exitosa=True,
            mensaje=(
                f"Datos insuficientes: {n_actual} < {config.min_predicciones_evaluar}"
            ),
        )

    fecha_inicio_baseline = fecha_inicio_actual - timedelta(
        days=config.ventana_baseline_dias
    )
    metricas_baseline = _obtener_metricas_periodo(
        mercado, origen, fecha_inicio_baseline, fecha_inicio_actual
    )

    tendencia = None
    if config.evaluar_tendencia:
        tendencia = _obtener_tendencia(
            mercado,
            origen,
            fecha_evaluacion,
            config.ventana_actual_dias,
            config.ventanas_tendencia,
        )

    alertas: list[Alerta] = []

    periodo_inicio = metricas_actuales.get("periodo_inicio")
    periodo_fin = metricas_actuales.get("periodo_fin")
    modelo_version_id = metricas_actuales.get("modelo_version_id")

    alertas.extend(
        _evaluar_metrica(
            mercado,
            origen,
            "ece",
            metricas_actuales.get("ece"),
            metricas_baseline.get("ece") if metricas_baseline else None,
            config,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            modelo_version_id=modelo_version_id,
        )
    )

    alertas.extend(
        _evaluar_metrica(
            mercado,
            origen,
            "brier",
            metricas_actuales.get("brier_score"),
            metricas_baseline.get("brier_score") if metricas_baseline else None,
            config,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            modelo_version_id=modelo_version_id,
        )
    )

    alertas.extend(
        _evaluar_metrica(
            mercado,
            origen,
            "sesgo",
            metricas_actuales.get("sesgo_media"),
            metricas_baseline.get("sesgo_media") if metricas_baseline else None,
            config,
            usar_valor_absoluto=True,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            modelo_version_id=modelo_version_id,
        )
    )

    if config.evaluar_calibrador:
        alertas.extend(
            _evaluar_calibrador(
                mercado,
                origen,
                metricas_actuales,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
            )
        )

    if tendencia and len(tendencia) >= config.ventanas_tendencia:
        alertas.extend(
            _evaluar_tendencia(
                mercado,
                origen,
                tendencia,
                "ece",
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
            )
        )
        alertas.extend(
            _evaluar_tendencia(
                mercado,
                origen,
                tendencia,
                "brier_score",
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
            )
        )

    for alerta in alertas:
        _persistir_alerta(alerta)

    return ResultadoEvaluacionDrift(
        mercado=mercado,
        origen=origen,
        alertas=alertas,
        metricas_actuales=metricas_actuales,
        metricas_baseline=metricas_baseline,
        tendencia=tendencia,
        evaluacion_exitosa=True,
    )


def detectar_drift_todos_mercados(
    origen: str, config: Optional[ConfiguracionDrift] = None
) -> List[ResultadoEvaluacionDrift]:
    """
    Detecta drift en todos los mercados para un origen.

    CRÍTICO: Solo evalúa UN origen a la vez. Nunca mezclar.
    """
    mercados = ["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    resultados = []

    for mercado in mercados:
        resultado = detectar_drift(mercado, origen, config)
        resultados.append(resultado)

        if resultado.alertas:
            logger.info(
                "Drift detectado en %s/%s: %d alertas",
                mercado,
                origen,
                len(resultado.alertas),
            )

    return resultados


def _evaluar_metrica(
    mercado: str,
    origen: str,
    metrica: str,
    valor_actual: Optional[float],
    valor_baseline: Optional[float],
    config: ConfiguracionDrift,
    usar_valor_absoluto: bool = False,
    periodo_inicio: Optional[date] = None,
    periodo_fin: Optional[date] = None,
    modelo_version_id: Optional[int] = None,
) -> List[Alerta]:
    """Evalúa una métrica contra umbrales y baseline."""
    alertas = []

    if valor_actual is None:
        return alertas

    valor_evaluar = abs(valor_actual) if usar_valor_absoluto else valor_actual

    umbral_critical = config.umbral_para(metrica, "absoluto_critical")
    if umbral_critical is not None and valor_evaluar > umbral_critical:
        alertas.append(
            Alerta(
                id=str(uuid4()),
                mercado=mercado,
                origen=origen,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
                tipo=f"DRIFT_{metrica.upper()}_ABSOLUTO_CRITICAL",
                severidad="CRITICAL",
                metrica_afectada=metrica,
                valor_actual=valor_actual,
                valor_umbral=umbral_critical,
                valor_baseline=valor_baseline,
                cambio_porcentual=None,
                mensaje=(
                    f"{metrica.upper()} = {valor_actual:.4f} supera umbral crítico {umbral_critical}"
                ),
                recomendacion=_recomendacion_para_metrica(metrica, "CRITICAL"),
                timestamp=date.today().isoformat(),
            )
        )
        return alertas

    umbral_warning = config.umbral_para(metrica, "absoluto_warning")
    if umbral_warning is not None and valor_evaluar > umbral_warning:
        alertas.append(
            Alerta(
                id=str(uuid4()),
                mercado=mercado,
                origen=origen,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
                tipo=f"DRIFT_{metrica.upper()}_ABSOLUTO_WARNING",
                severidad="WARNING",
                metrica_afectada=metrica,
                valor_actual=valor_actual,
                valor_umbral=umbral_warning,
                valor_baseline=valor_baseline,
                cambio_porcentual=None,
                mensaje=(
                    f"{metrica.upper()} = {valor_actual:.4f} supera umbral de advertencia {umbral_warning}"
                ),
                recomendacion=_recomendacion_para_metrica(metrica, "WARNING"),
                timestamp=date.today().isoformat(),
            )
        )

    if valor_baseline is not None and valor_baseline != 0:
        cambio = (valor_evaluar - abs(valor_baseline)) / abs(valor_baseline)
        umbral_rel_critical = config.umbral_para(metrica, "relativo_critical")
        umbral_rel_warning = config.umbral_para(metrica, "relativo_warning")
        if umbral_rel_critical is not None and cambio > umbral_rel_critical:
            alertas.append(
                Alerta(
                    id=str(uuid4()),
                    mercado=mercado,
                    origen=origen,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    modelo_version_id=modelo_version_id,
                    tipo=f"DRIFT_{metrica.upper()}_RELATIVO",
                    severidad="WARNING",
                    metrica_afectada=metrica,
                    valor_actual=valor_actual,
                    valor_umbral=None,
                    valor_baseline=valor_baseline,
                    cambio_porcentual=cambio * 100,
                    mensaje=(
                        f"{metrica.upper()} aumentó {cambio * 100:.1f}% vs baseline "
                        f"({valor_baseline:.4f} → {valor_actual:.4f})"
                    ),
                    recomendacion="Investigar causa del deterioro y evaluar recalibración",
                    timestamp=date.today().isoformat(),
                )
            )
        elif umbral_rel_warning is not None and cambio > umbral_rel_warning:
            alertas.append(
                Alerta(
                    id=str(uuid4()),
                    mercado=mercado,
                    origen=origen,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    modelo_version_id=modelo_version_id,
                    tipo=f"DRIFT_{metrica.upper()}_RELATIVO",
                    severidad="WARNING",
                    metrica_afectada=metrica,
                    valor_actual=valor_actual,
                    valor_umbral=None,
                    valor_baseline=valor_baseline,
                    cambio_porcentual=cambio * 100,
                    mensaje=(
                        f"{metrica.upper()} aumentó {cambio * 100:.1f}% vs baseline "
                        f"({valor_baseline:.4f} → {valor_actual:.4f})"
                    ),
                    recomendacion="Investigar causa del deterioro y evaluar recalibración",
                    timestamp=date.today().isoformat(),
                )
            )

    return alertas


def _evaluar_calibrador(
    mercado: str,
    origen: str,
    metricas: dict,
    *,
    periodo_inicio: Optional[date] = None,
    periodo_fin: Optional[date] = None,
    modelo_version_id: Optional[int] = None,
) -> List[Alerta]:
    """Evalúa si el calibrador está empeorando las predicciones."""
    brier_raw = metricas.get("brier_score_raw")
    brier_cal = metricas.get("brier_score_calibrado")

    if brier_raw is None or brier_cal is None:
        return []

    if brier_cal > brier_raw:
        return [
            Alerta(
                id=str(uuid4()),
                mercado=mercado,
                origen=origen,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
                tipo="CALIBRADOR_EMPEORA",
                severidad="WARNING",
                metrica_afectada="brier",
                valor_actual=brier_cal,
                valor_umbral=brier_raw,
                valor_baseline=None,
                cambio_porcentual=None,
                mensaje=(
                    f"Calibrador empeora predicciones: Brier raw={brier_raw:.4f}, "
                    f"calibrado={brier_cal:.4f}"
                ),
                recomendacion="Considerar desactivar calibrador para este mercado",
                timestamp=date.today().isoformat(),
            )
        ]

    return []


def _evaluar_tendencia(
    mercado: str,
    origen: str,
    tendencia: List[dict],
    metrica: str,
    *,
    periodo_inicio: Optional[date] = None,
    periodo_fin: Optional[date] = None,
    modelo_version_id: Optional[int] = None,
) -> List[Alerta]:
    """Evalúa si hay tendencia negativa en los últimos periodos."""
    valores = [t.get(metrica) for t in tendencia if t.get(metrica) is not None]

    if len(valores) < 3:
        return []

    empeorando = all(valores[i] < valores[i + 1] for i in range(len(valores) - 1))

    if empeorando:
        return [
            Alerta(
                id=str(uuid4()),
                mercado=mercado,
                origen=origen,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                modelo_version_id=modelo_version_id,
                tipo="TENDENCIA_NEGATIVA",
                severidad="WARNING",
                metrica_afectada=metrica,
                valor_actual=valores[-1],
                valor_umbral=None,
                valor_baseline=valores[0],
                cambio_porcentual=None,
                mensaje=(
                    f"{metrica.upper()} empeorando {len(valores)} periodos consecutivos: "
                    f"{' → '.join(f'{v:.4f}' for v in valores)}"
                ),
                recomendacion="Planear recalibración preventiva",
                timestamp=date.today().isoformat(),
            )
        ]

    return []


def _recomendacion_para_metrica(metrica: str, severidad: str) -> str:
    """Genera recomendación según métrica y severidad."""
    recomendaciones = {
        ("ece", "CRITICAL"): "Recalibrar urgentemente. El modelo está mal calibrado.",
        ("ece", "WARNING"): "Monitorear de cerca. Planear recalibración si persiste.",
        ("brier", "CRITICAL"): "Revisar modelo. Precisión severamente degradada.",
        ("brier", "WARNING"): "Evaluar si recalibración mejora Brier score.",
        ("sesgo", "CRITICAL"): "Investigar datos de entrada. Sesgo sistemático detectado.",
        ("sesgo", "WARNING"): "Monitorear sesgo. Puede indicar cambio en distribución.",
    }
    return recomendaciones.get((metrica, severidad), "Monitorear y evaluar.")


def _crear_alerta_datos_insuficientes(
    mercado: str, origen: str, n: int, config: ConfiguracionDrift
) -> Alerta:
    """Crea alerta de datos insuficientes."""
    return Alerta(
        id=str(uuid4()),
        mercado=mercado,
        origen=origen,
        periodo_inicio=None,
        periodo_fin=None,
        modelo_version_id=None,
        tipo="DATOS_INSUFICIENTES",
        severidad="INFO",
        metrica_afectada="n_predicciones",
        valor_actual=n,
        valor_umbral=config.min_predicciones_evaluar,
        valor_baseline=None,
        cambio_porcentual=None,
        mensaje=(
            f"Solo {n} predicciones. Mínimo requerido: {config.min_predicciones_evaluar}"
        ),
        recomendacion="Esperar más datos antes de evaluar drift.",
        timestamp=date.today().isoformat(),
    )


def _obtener_metricas_periodo(
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
) -> Optional[dict]:
    """Obtiene métricas calculadas para un periodo."""
    return calcular_metricas_calibracion(
        mercado=mercado,
        origen=origen,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


def _obtener_tendencia(
    mercado: str,
    origen: str,
    fecha_fin: date,
    dias_ventana: int,
    n_ventanas: int,
) -> List[dict]:
    """Obtiene métricas de las últimas N ventanas para análisis de tendencia."""
    tendencia = []
    for i in range(n_ventanas):
        fin = fecha_fin - timedelta(days=i * dias_ventana)
        inicio = fin - timedelta(days=dias_ventana)
        metricas = _obtener_metricas_periodo(mercado, origen, inicio, fin)
        if metricas:
            tendencia.insert(0, metricas)
    return tendencia


def _persistir_alerta(alerta: Alerta) -> None:
    """Persiste alerta en tabla alertas_calibracion."""
    from db import obtener_pool

    constraint_alertas = "uq_alerta_calibracion_llave_natural"
    pool = obtener_pool()

    consulta = """
        INSERT INTO alertas_calibracion (
            id,
            timestamp_deteccion,
            periodo_inicio,
            periodo_fin,
            mercado,
            origen,
            modelo_version_id,
            tipo_alerta,
            severidad,
            metrica_afectada,
            valor_actual,
            valor_umbral,
            valor_baseline,
            mensaje,
            resuelta
        ) VALUES (
            %s, now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false
        )
        ON CONFLICT ON CONSTRAINT {constraint_alertas}
        DO UPDATE SET
            timestamp_deteccion = now(),
            severidad = EXCLUDED.severidad,
            valor_actual = EXCLUDED.valor_actual,
            mensaje = EXCLUDED.mensaje,
            resuelta = false,
            timestamp_resolucion = NULL,
            resuelta_por = NULL,
            notas_resolucion = NULL
    """.format(constraint_alertas=constraint_alertas)

    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    consulta,
                    [
                        alerta.id,
                        alerta.periodo_inicio,
                        alerta.periodo_fin,
                        alerta.mercado,
                        alerta.origen,
                        alerta.modelo_version_id,
                        alerta.tipo,
                        alerta.severidad,
                        alerta.metrica_afectada,
                        alerta.valor_actual,
                        alerta.valor_umbral,
                        alerta.valor_baseline,
                        alerta.mensaje,
                    ],
                )
                conn.commit()
    except Exception as exc:
        logger.error("Error persistiendo alerta: %s", exc)

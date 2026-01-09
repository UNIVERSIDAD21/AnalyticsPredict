# -*- coding: utf-8 -*-
"""
calculador.py — Calculador unificado de métricas de calibración.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from datetime import date
from typing import TYPE_CHECKING, Optional

from backtesting.metricas.brier import calcular_brier_score
from backtesting.metricas.distribucion import calcular_metricas_distribucion
from backtesting.metricas.ece import calcular_ece
from backtesting.metricas.log_loss import calcular_log_loss

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


def calcular_metricas_calibracion(
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int] = None,
    usar_p_calibrada: bool = True,
    n_bins: int = 10,
    tipo_bins: str = "fijos",
    min_por_bin: int = 10,
    eps_log_loss: float = 1e-15,
    pool: Optional["ConnectionPool"] = None,
) -> dict[str, object]:
    """
    Calcula métricas de calibración y distribución para un periodo.

    - Usa vista_predicciones_para_calibracion para extraer datos.
    - Excluye PUSHes en métricas probabilísticas.
    - Persiste una fila en metricas_calibracion con UPSERT.
    """
    if pool is None:
        from db import obtener_pool

        pool = obtener_pool()

    filas = _obtener_predicciones(
        pool,
        mercado=mercado,
        origen=origen,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modelo_version_id=modelo_version_id,
    )

    predicciones_raw = []
    predicciones_efectiva = []
    probabilidades_raw = []
    probabilidades_efectiva = []
    resultados = []
    distribucion = []
    niveles_intervalo = []

    for (
        p_raw,
        p_calibrada,
        outcome_binario,
        media_predicha,
        valor_real,
        intervalo_inferior,
        intervalo_superior,
        nivel_intervalo,
    ) in filas:
        if media_predicha is not None and valor_real is not None:
            distribucion.append(
                (media_predicha, valor_real, intervalo_inferior, intervalo_superior)
            )

        if nivel_intervalo is not None:
            niveles_intervalo.append(nivel_intervalo)

        if outcome_binario is None:
            continue

        if p_raw is not None:
            predicciones_raw.append((float(p_raw), bool(outcome_binario)))
            probabilidades_raw.append(float(p_raw))

        p_efectiva = (
            p_calibrada if usar_p_calibrada and p_calibrada is not None else p_raw
        )
        if p_efectiva is not None:
            predicciones_efectiva.append((float(p_efectiva), bool(outcome_binario)))
            probabilidades_efectiva.append(float(p_efectiva))

        resultados.append(bool(outcome_binario))

    n_predicciones = len(predicciones_raw)
    alertas: list[str] = []

    if n_predicciones == 0:
        alertas.append("DATOS_INSUFICIENTES")
        resultado = _armar_resultado(
            mercado=mercado,
            origen=origen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            modelo_version_id=modelo_version_id,
            usar_p_calibrada=usar_p_calibrada,
            n_bins=n_bins,
            tipo_bins=tipo_bins,
            min_por_bin=min_por_bin,
            eps_log_loss=eps_log_loss,
            n_predicciones=0,
            alertas=alertas,
            brier_raw=None,
            brier_calibrado=None,
            log_loss_raw=None,
            log_loss_calibrado=None,
            ece_raw=None,
            mce_raw=None,
            ece_calibrada=None,
            mce_calibrada=None,
            sharpness_raw=None,
            sharpness_calibrada=None,
            base_rate=None,
            distribucion=calcular_metricas_distribucion(distribucion),
            bins_raw=None,
            bins_calibrada=None,
            nivel_intervalo=_determinar_nivel_intervalo(niveles_intervalo),
            persistida=False,
            metricas_id=None,
        )
        return resultado

    brier_raw = calcular_brier_score(predicciones_raw)
    brier_calibrado = calcular_brier_score(predicciones_efectiva)

    log_loss_raw = calcular_log_loss(predicciones_raw, eps=eps_log_loss)
    log_loss_calibrado = calcular_log_loss(predicciones_efectiva, eps=eps_log_loss)

    ece_raw = calcular_ece(
        predicciones_raw,
        n_bins=n_bins,
        tipo_bins=tipo_bins,
        min_por_bin=min_por_bin,
    )
    ece_calibrada = calcular_ece(
        predicciones_efectiva,
        n_bins=n_bins,
        tipo_bins=tipo_bins,
        min_por_bin=min_por_bin,
    )

    sharpness_raw = _calcular_sharpness(probabilidades_raw)
    sharpness_calibrada = _calcular_sharpness(probabilidades_efectiva)

    base_rate = sum(1 for outcome in resultados if outcome) / len(resultados)

    distribucion_metricas = calcular_metricas_distribucion(distribucion)

    nivel_intervalo = _determinar_nivel_intervalo(niveles_intervalo)

    resultado = _armar_resultado(
        mercado=mercado,
        origen=origen,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modelo_version_id=modelo_version_id,
        usar_p_calibrada=usar_p_calibrada,
        n_bins=n_bins,
        tipo_bins=tipo_bins,
        min_por_bin=min_por_bin,
        eps_log_loss=eps_log_loss,
        n_predicciones=n_predicciones,
        alertas=alertas,
        brier_raw=brier_raw,
        brier_calibrado=brier_calibrado,
        log_loss_raw=log_loss_raw,
        log_loss_calibrado=log_loss_calibrado,
        ece_raw=ece_raw,
        mce_raw=ece_raw,
        ece_calibrada=ece_calibrada,
        mce_calibrada=ece_calibrada,
        sharpness_raw=sharpness_raw,
        sharpness_calibrada=sharpness_calibrada,
        base_rate=base_rate,
        distribucion=distribucion_metricas,
        bins_raw=ece_raw,
        bins_calibrada=ece_calibrada,
        nivel_intervalo=nivel_intervalo,
        persistida=False,
        metricas_id=None,
    )

    metricas_id = _persistir_metricas(
        pool,
        resultado=resultado,
        brier_score=_normalizar_numero(resultado["brier_score"]),
        log_loss=_normalizar_numero(resultado["log_loss"]),
        ece=_normalizar_numero(resultado["ece"]),
        mce=_normalizar_numero(resultado["mce"]),
        sharpness=_normalizar_numero(resultado["sharpness"]),
        base_rate=_normalizar_numero(resultado["base_rate"]),
    )

    resultado["persistida"] = True
    resultado["metricas_id"] = metricas_id
    return resultado


def _obtener_predicciones(
    pool: "ConnectionPool",
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int],
) -> list[tuple[object, ...]]:
    consulta = """
        SELECT
            p_raw,
            p_calibrada,
            outcome_binario,
            media_predicha,
            valor_real,
            intervalo_inferior,
            intervalo_superior,
            nivel_intervalo
        FROM vista_predicciones_para_calibracion
        WHERE mercado = %s
          AND origen = %s
          AND fecha_partido >= %s
          AND fecha_partido <= %s
          AND (%s IS NULL OR modelo_version_id = %s)
    """
    params = [
        mercado,
        origen,
        fecha_inicio,
        fecha_fin,
        modelo_version_id,
        modelo_version_id,
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            return list(cursor.fetchall())


def _persistir_metricas(
    pool: "ConnectionPool",
    *,
    resultado: dict[str, object],
    brier_score: Optional[float],
    log_loss: Optional[float],
    ece: Optional[float],
    mce: Optional[float],
    sharpness: Optional[float],
    base_rate: Optional[float],
) -> Optional[str]:
    consulta = """
        INSERT INTO metricas_calibracion (
            timestamp_calculo,
            periodo_inicio,
            periodo_fin,
            mercado,
            origen_predicciones,
            modelo_version_id,
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
            cobertura_intervalo,
            nivel_intervalo_declarado,
            bins_json,
            configuracion_json,
            alertas
        ) VALUES (
            NOW(), %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (periodo_inicio, periodo_fin, mercado, origen_predicciones, modelo_version_id)
        DO UPDATE SET
            timestamp_calculo = EXCLUDED.timestamp_calculo,
            n_predicciones = EXCLUDED.n_predicciones,
            brier_score = EXCLUDED.brier_score,
            brier_score_raw = EXCLUDED.brier_score_raw,
            brier_score_calibrado = EXCLUDED.brier_score_calibrado,
            log_loss = EXCLUDED.log_loss,
            log_loss_raw = EXCLUDED.log_loss_raw,
            log_loss_calibrado = EXCLUDED.log_loss_calibrado,
            ece = EXCLUDED.ece,
            mce = EXCLUDED.mce,
            sharpness = EXCLUDED.sharpness,
            base_rate = EXCLUDED.base_rate,
            mae_media = EXCLUDED.mae_media,
            rmse_media = EXCLUDED.rmse_media,
            sesgo_media = EXCLUDED.sesgo_media,
            cobertura_intervalo = EXCLUDED.cobertura_intervalo,
            nivel_intervalo_declarado = EXCLUDED.nivel_intervalo_declarado,
            bins_json = EXCLUDED.bins_json,
            configuracion_json = EXCLUDED.configuracion_json,
            alertas = EXCLUDED.alertas
        RETURNING id
    """

    distribucion = resultado.get("distribucion", {})

    params = [
        resultado["periodo_inicio"],
        resultado["periodo_fin"],
        resultado["mercado"],
        resultado["origen"],
        resultado["modelo_version_id"],
        resultado["n_predicciones"],
        brier_score,
        resultado["brier_score_raw"],
        resultado["brier_score_calibrado"],
        log_loss,
        resultado["log_loss_raw"],
        resultado["log_loss_calibrado"],
        ece,
        mce,
        sharpness,
        base_rate,
        distribucion.get("mae_media"),
        distribucion.get("rmse_media"),
        distribucion.get("sesgo_media"),
        distribucion.get("cobertura_intervalo"),
        resultado["nivel_intervalo_declarado"],
        json.dumps(resultado["bins_json"], ensure_ascii=False),
        json.dumps(resultado["configuracion_json"], ensure_ascii=False),
        resultado["alertas"],
    ]

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(consulta, params)
            row = cursor.fetchone()

    return row[0] if row else None


def _armar_resultado(
    *,
    mercado: str,
    origen: str,
    fecha_inicio: date,
    fecha_fin: date,
    modelo_version_id: Optional[int],
    usar_p_calibrada: bool,
    n_bins: int,
    tipo_bins: str,
    min_por_bin: int,
    eps_log_loss: float,
    n_predicciones: int,
    alertas: list[str],
    brier_raw: Optional[dict[str, object]],
    brier_calibrado: Optional[dict[str, object]],
    log_loss_raw: Optional[dict[str, object]],
    log_loss_calibrado: Optional[dict[str, object]],
    ece_raw: Optional[dict[str, object]],
    mce_raw: Optional[dict[str, object]],
    ece_calibrada: Optional[dict[str, object]],
    mce_calibrada: Optional[dict[str, object]],
    sharpness_raw: Optional[float],
    sharpness_calibrada: Optional[float],
    base_rate: Optional[float],
    distribucion: dict[str, object],
    bins_raw: Optional[dict[str, object]],
    bins_calibrada: Optional[dict[str, object]],
    nivel_intervalo: Optional[int],
    persistida: bool,
    metricas_id: Optional[str],
) -> dict[str, object]:
    configuracion_json = {
        "periodo_inicio": fecha_inicio.isoformat(),
        "periodo_fin": fecha_fin.isoformat(),
        "mercado": mercado,
        "origen": origen,
        "tipo_bins": tipo_bins,
        "n_bins": n_bins,
        "min_por_bin": min_por_bin,
        "eps_log_loss": eps_log_loss,
        "usar_p_calibrada": usar_p_calibrada,
        "modelo_version_id": modelo_version_id,
    }

    resultado = {
        "periodo_inicio": fecha_inicio,
        "periodo_fin": fecha_fin,
        "mercado": mercado,
        "origen": origen,
        "modelo_version_id": modelo_version_id,
        "n_predicciones": n_predicciones,
        "brier_score_raw": _extraer_metricas(brier_raw, "brier_score"),
        "brier_score_calibrado": _extraer_metricas(brier_calibrado, "brier_score"),
        "log_loss_raw": _extraer_metricas(log_loss_raw, "log_loss"),
        "log_loss_calibrado": _extraer_metricas(log_loss_calibrado, "log_loss"),
        "ece_raw": _extraer_metricas(ece_raw, "ece"),
        "mce_raw": _extraer_metricas(mce_raw, "mce"),
        "ece_calibrada": _extraer_metricas(ece_calibrada, "ece"),
        "mce_calibrada": _extraer_metricas(mce_calibrada, "mce"),
        "sharpness_raw": _normalizar_numero(sharpness_raw),
        "sharpness_calibrada": _normalizar_numero(sharpness_calibrada),
        "base_rate": _normalizar_numero(base_rate),
        "distribucion": distribucion,
        "bins_json": {
            "raw": _construir_bins_json(bins_raw),
            "calibrada": _construir_bins_json(bins_calibrada),
        },
        "configuracion_json": configuracion_json,
        "alertas": alertas,
        "nivel_intervalo_declarado": nivel_intervalo,
        "persistida": persistida,
        "metricas_id": metricas_id,
    }

    resultado["brier_score"] = (
        resultado["brier_score_calibrado"] if usar_p_calibrada else resultado["brier_score_raw"]
    )
    resultado["log_loss"] = (
        resultado["log_loss_calibrado"] if usar_p_calibrada else resultado["log_loss_raw"]
    )
    resultado["ece"] = (
        resultado["ece_calibrada"] if usar_p_calibrada else resultado["ece_raw"]
    )
    resultado["mce"] = (
        resultado["mce_calibrada"] if usar_p_calibrada else resultado["mce_raw"]
    )
    resultado["sharpness"] = (
        resultado["sharpness_calibrada"]
        if usar_p_calibrada
        else resultado["sharpness_raw"]
    )

    return resultado


def _construir_bins_json(datos: Optional[dict[str, object]]) -> Optional[dict[str, object]]:
    if not datos:
        return None
    return {
        "bins": datos.get("bins"),
        "metadatos": datos.get("metadatos"),
        "tipo_bins": datos.get("tipo_bins"),
        "n_bins": datos.get("n_bins"),
        "n": datos.get("n"),
    }


def _extraer_metricas(
    datos: Optional[dict[str, object]],
    clave: str,
) -> Optional[float]:
    if not datos:
        return None
    valor = datos.get(clave)
    return _normalizar_numero(valor) if valor is not None else None


def _determinar_nivel_intervalo(niveles: list[int]) -> Optional[int]:
    valores = {int(nivel) for nivel in niveles if nivel is not None}
    if len(valores) == 1:
        return next(iter(valores))
    return None


def _calcular_sharpness(probabilidades: list[float]) -> Optional[float]:
    if not probabilidades:
        return None
    return _normalizar_numero(statistics.pstdev(probabilidades))


def _normalizar_numero(valor: Optional[float]) -> Optional[float]:
    if valor is None:
        return None
    if isinstance(valor, bool):
        return float(valor)
    try:
        valor_f = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(valor_f):
        return None
    return valor_f

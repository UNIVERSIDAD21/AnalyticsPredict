from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal
import math

NivelMadurez = Literal["NO_APTO", "EXPERIMENTAL", "VALIDACION", "PROMOCIONABLE"]
StatusPromocion = Literal["BLOQUEADO", "LABORATORIO", "VALIDACION", "PROMOCIONABLE"]


@dataclass(frozen=True)
class CriteriosMadurezMercado:
    min_resueltas_validacion: int = 120
    min_resueltas_promocion: int = 250
    min_lineas_validacion: int = 2
    min_lineas_promocion: int = 4
    max_brier_promocion: float = 0.23
    max_logloss_promocion: float = 0.67
    max_ece_promocion: float = 0.06
    min_resolved_rate_validacion: float = 0.70
    min_resolved_rate_promocion: float = 0.85
    max_fallback_rate_validacion: float = 0.35
    max_fallback_rate_promocion: float = 0.15
    max_window_drift_promocion: float = 0.03


CRITERIOS_DEFAULT = CriteriosMadurezMercado()


def _metrica_valida(metricas: Dict[str, float | None], nombre: str) -> float | None:
    valor = metricas.get(nombre)
    if valor is None:
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def clasificar_madurez_mercado(metricas: Dict[str, float | None], estado_mercado: str | None, criterios: CriteriosMadurezMercado = CRITERIOS_DEFAULT) -> tuple[NivelMadurez, List[str]]:
    n = int(metricas.get("n_resueltas", 0) or 0)
    lineas = int(metricas.get("lineas_cubiertas", 0) or 0)
    brier = _metrica_valida(metricas, "brier")
    logloss = _metrica_valida(metricas, "log_loss")
    ece = _metrica_valida(metricas, "ece")
    resolved_rate = _metrica_valida(metricas, "resolved_rate")
    fallback_rate = _metrica_valida(metricas, "fallback_rate")
    drift_raw = _metrica_valida(metricas, "window_drift_brier")
    drift = abs(drift_raw) if drift_raw is not None else None

    razones: List[str] = []

    if estado_mercado in (None, "", "rojo"):
        razones.append("estado_mercado_no_estable")
    if n < 50 or resolved_rate is None or resolved_rate < 0.50:
        razones.append("volumen_o_resolucion_critica")
    if len(razones) > 0:
        return "NO_APTO", razones

    promo_ok = all([
        estado_mercado == "verde",
        n >= criterios.min_resueltas_promocion,
        lineas >= criterios.min_lineas_promocion,
        brier is not None and brier <= criterios.max_brier_promocion,
        logloss is not None and logloss <= criterios.max_logloss_promocion,
        ece is not None and ece <= criterios.max_ece_promocion,
        resolved_rate >= criterios.min_resolved_rate_promocion,
        fallback_rate is not None and fallback_rate <= criterios.max_fallback_rate_promocion,
        drift is not None and drift <= criterios.max_window_drift_promocion,
    ])
    if promo_ok:
        return "PROMOCIONABLE", ["cumple_umbral_promocion"]

    valid_ok = all([
        estado_mercado in ("verde", "amarillo"),
        n >= criterios.min_resueltas_validacion,
        lineas >= criterios.min_lineas_validacion,
        resolved_rate >= criterios.min_resolved_rate_validacion,
        fallback_rate is not None and fallback_rate <= criterios.max_fallback_rate_validacion,
    ])
    if valid_ok:
        razones.append("cumple_base_validacion_pero_no_promocion")
        if brier is None or logloss is None or ece is None or drift is None:
            razones.append("metricas_calibracion_no_disponibles")
        elif brier > criterios.max_brier_promocion or ece > criterios.max_ece_promocion:
            razones.append("calibracion_aun_no_promocionable")
        return "VALIDACION", razones

    razones.append("cobertura_o_estabilidad_insuficiente")
    return "EXPERIMENTAL", razones


def mapear_status_promocion(nivel: NivelMadurez) -> StatusPromocion:
    if nivel == "NO_APTO":
        return "BLOQUEADO"
    if nivel == "EXPERIMENTAL":
        return "LABORATORIO"
    if nivel == "VALIDACION":
        return "VALIDACION"
    return "PROMOCIONABLE"


def aplicar_autodemotion(
    estado_actual: StatusPromocion,
    estado_objetivo: StatusPromocion,
    motivos_objetivo: List[str],
) -> tuple[StatusPromocion, List[str]]:
    orden = {
        "BLOQUEADO": 0,
        "LABORATORIO": 1,
        "VALIDACION": 2,
        "PROMOCIONABLE": 3,
    }

    # En monitoreo continuo, la regla es conservadora: se permite bajar automáticamente,
    # pero no subir automáticamente sin proceso explícito de promoción.
    if orden[estado_objetivo] < orden[estado_actual]:
        return estado_objetivo, ["auto_demotion", *motivos_objetivo]

    return estado_actual, ["sin_demotion", *motivos_objetivo]

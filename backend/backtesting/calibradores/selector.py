# -*- coding: utf-8 -*-
"""
selector.py — Selector determinista de calibradores (T20).
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional, Sequence

from backtesting.metricas.brier import calcular_brier_score

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CalibradorPlatt:
    metodo: str
    a: float
    b: float

    def calibrar(self, p_raw: float) -> float:
        return _aplicar_platt(p_raw, self.a, self.b)


@dataclass(frozen=True)
class CalibradorIsotonic:
    metodo: str
    x_max: list[float]
    y: list[float]

    def calibrar(self, p_raw: float) -> float:
        return _aplicar_isotonic(p_raw, self.x_max, self.y)


def seleccionar_calibrador(
    mercado: str,
    predicciones: Sequence[object],
    cutoff: date | datetime,
) -> tuple[Optional[object], dict[str, object], str]:
    """
    Selecciona un calibrador según reglas T20.

    Retorna: (calibrador, metricas, razon)
    """
    datos = _filtrar_predicciones(predicciones, cutoff=cutoff)
    origenes = sorted({fila["origen"] for fila in datos if fila["origen"]})

    metricas_base = {
        "mercado": mercado,
        "cutoff": cutoff.isoformat(),
        "n_total": len(datos),
        "origenes": origenes,
    }

    if not datos:
        razon = f"NO_CALIBRAR: SIN_DATOS cutoff={cutoff.isoformat()}"
        return None, metricas_base, razon

    if len(origenes) > 1:
        razon = (
            "NO_CALIBRAR: ORIGEN_MIXTO "
            f"origenes={','.join(origenes)} cutoff={cutoff.isoformat()}"
        )
        return None, metricas_base, razon

    n = len(datos)
    if n < 100:
        razon = f"NO_CALIBRAR: n={n} < 100 cutoff={cutoff.isoformat()}"
        return None, metricas_base, razon

    if 100 <= n < 500:
        calibrador = _entrenar_platt(datos)
        metricas = {
            **metricas_base,
            "n_entrenamiento": n,
            "brier_val_platt": None,
            "brier_val_isotonic": None,
        }
        razon = f"PLATT: 100<=n<500 (n={n}) cutoff={cutoff.isoformat()}"
        return calibrador, metricas, razon

    train, val = _split_train_val(datos, ratio=0.8, seed=42)
    calibrador_platt = _entrenar_platt(train)
    calibrador_iso = _entrenar_isotonic(train)

    brier_platt = _brier_validacion(calibrador_platt, val)
    brier_iso = _brier_validacion(calibrador_iso, val)

    if brier_iso is not None and (brier_platt is None or brier_iso < brier_platt):
        calibrador_final = _entrenar_isotonic(datos)
        razon = (
            "ELEGIDO_ISOTONIC: "
            f"n={n}, cutoff={cutoff.isoformat()}, "
            f"brier_val_iso={brier_iso:.4f} < brier_val_platt={_fmt_brier(brier_platt)}"
        )
        elegido = "isotonic"
    else:
        calibrador_final = _entrenar_platt(datos)
        razon = (
            "ELEGIDO_PLATT: "
            f"n={n}, cutoff={cutoff.isoformat()}, "
            f"brier_val_platt={_fmt_brier(brier_platt)} <= brier_val_iso={_fmt_brier(brier_iso)}"
        )
        elegido = "platt"

    metricas = {
        **metricas_base,
        "n_entrenamiento": len(train),
        "n_validacion": len(val),
        "brier_val_platt": brier_platt,
        "brier_val_isotonic": brier_iso,
        "calibrador_elegido": elegido,
    }

    return calibrador_final, metricas, razon


def _filtrar_predicciones(
    predicciones: Sequence[object],
    *,
    cutoff: date | datetime,
) -> list[dict[str, object]]:
    datos: list[dict[str, object]] = []
    for pred in predicciones:
        fecha = _extraer_valor(pred, "fecha_partido") or _extraer_valor(pred, "fecha")
        if fecha is None:
            continue
        if isinstance(fecha, datetime):
            fecha_val = fecha.date()
        else:
            fecha_val = fecha
        cutoff_val = cutoff.date() if isinstance(cutoff, datetime) else cutoff
        if fecha_val >= cutoff_val:
            continue

        p_raw = _extraer_valor(pred, "p_raw")
        outcome = _extraer_valor(pred, "outcome_binario")
        origen = _extraer_valor(pred, "origen")

        if outcome is None:
            continue
        if p_raw is None:
            continue
        if not isinstance(outcome, bool):
            continue
        if not _es_probabilidad_valida(p_raw):
            continue

        datos.append(
            {
                "p_raw": float(p_raw),
                "outcome": bool(outcome),
                "origen": str(origen) if origen is not None else None,
            }
        )

    return datos


def _entrenar_platt(datos: Sequence[dict[str, object]]) -> CalibradorPlatt:
    probabilidades = [float(d["p_raw"]) for d in datos]
    resultados = [bool(d["outcome"]) for d in datos]
    a, b = _ajustar_platt(probabilidades, resultados)
    return CalibradorPlatt(metodo="platt", a=a, b=b)


def _entrenar_isotonic(datos: Sequence[dict[str, object]]) -> CalibradorIsotonic:
    probabilidades = [float(d["p_raw"]) for d in datos]
    resultados = [bool(d["outcome"]) for d in datos]
    x_max, y = _ajustar_isotonic(probabilidades, resultados)
    return CalibradorIsotonic(metodo="isotonic", x_max=x_max, y=y)


def _split_train_val(
    datos: Sequence[dict[str, object]],
    *,
    ratio: float,
    seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    indices = list(range(len(datos)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    corte = int(len(indices) * ratio)
    train = [datos[i] for i in indices[:corte]]
    val = [datos[i] for i in indices[corte:]]
    if not train or not val:
        logger.warning("Split train/val degenerado (train=%s val=%s).", len(train), len(val))
    return train, val


def _brier_validacion(calibrador: object, datos: Sequence[dict[str, object]]) -> Optional[float]:
    if not datos:
        return None
    predicciones = [
        (float(getattr(calibrador, "calibrar")(d["p_raw"])), bool(d["outcome"]))
        for d in datos
    ]
    resultado = calcular_brier_score(predicciones)
    return resultado.get("brier_score")


def _ajustar_platt(probabilidades: Sequence[float], resultados: Sequence[bool]) -> tuple[float, float]:
    eps = 1e-6
    x_vals = [_logit(_clip(p, eps, 1 - eps)) for p in probabilidades]
    y_vals = [1.0 if r else 0.0 for r in resultados]

    a, b = 1.0, 0.0
    for _ in range(50):
        grad_a = 0.0
        grad_b = 0.0
        h_aa = 0.0
        h_bb = 0.0
        h_ab = 0.0
        for x, y in zip(x_vals, y_vals):
            z = a * x + b
            p = 1.0 / (1.0 + math.exp(-z))
            diff = p - y
            grad_a += diff * x
            grad_b += diff
            w = p * (1.0 - p)
            h_aa += w * x * x
            h_bb += w
            h_ab += w * x

        h_aa += 1e-6
        h_bb += 1e-6
        det = h_aa * h_bb - h_ab * h_ab
        if det == 0:
            break

        delta_a = (h_bb * grad_a - h_ab * grad_b) / det
        delta_b = (-h_ab * grad_a + h_aa * grad_b) / det
        a -= delta_a
        b -= delta_b

        if abs(delta_a) < 1e-6 and abs(delta_b) < 1e-6:
            break

    return a, b


def _aplicar_platt(p_raw: float, a: float, b: float) -> float:
    p = _clip(float(p_raw), 1e-6, 1 - 1e-6)
    x = _logit(p)
    return _clip(1.0 / (1.0 + math.exp(-(a * x + b))), 0.0, 1.0)


def _ajustar_isotonic(probabilidades: Sequence[float], resultados: Sequence[bool]) -> tuple[list[float], list[float]]:
    pares = sorted(zip(probabilidades, resultados), key=lambda x: x[0])
    bloques: list[dict[str, object]] = []

    for p, r in pares:
        bloques.append({"x_min": p, "x_max": p, "sum": 1.0 if r else 0.0, "count": 1})
        while len(bloques) >= 2:
            b2 = bloques[-1]
            b1 = bloques[-2]
            avg1 = b1["sum"] / b1["count"]
            avg2 = b2["sum"] / b2["count"]
            if avg1 <= avg2:
                break
            b1["x_max"] = b2["x_max"]
            b1["sum"] += b2["sum"]
            b1["count"] += b2["count"]
            bloques.pop()

    x_max = [float(b["x_max"]) for b in bloques]
    y = [float(b["sum"]) / float(b["count"]) for b in bloques]
    return x_max, y


def _aplicar_isotonic(p_raw: float, x_max: Iterable[float], y: Iterable[float]) -> float:
    p = float(p_raw)
    x_list = list(x_max)
    y_list = list(y)
    if not x_list:
        return _clip(p, 0.0, 1.0)
    idx = 0
    while idx < len(x_list) and p > x_list[idx]:
        idx += 1
    idx = min(idx, len(y_list) - 1)
    return _clip(float(y_list[idx]), 0.0, 1.0)


def _extraer_valor(obj: object, clave: str) -> Optional[object]:
    if isinstance(obj, dict):
        return obj.get(clave)
    return getattr(obj, clave, None)


def _es_probabilidad_valida(valor: float) -> bool:
    if valor is None:
        return False
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(v):
        return False
    return 0.0 <= v <= 1.0


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def _clip(valor: float, minimo: float, maximo: float) -> float:
    return max(min(valor, maximo), minimo)


def _fmt_brier(valor: Optional[float]) -> str:
    if valor is None:
        return "None"
    return f"{valor:.4f}"

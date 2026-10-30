"""Consulta NBA RAW del artefacto: sin BD, fit, cuotas, registro ni contexto."""
from datetime import datetime, timezone
import math
from uuid import uuid4

import numpy as np

from motor.nba_predictor_cuartos import predecir_cuartos
from motor.tipos import Ubicacion
from motor.utilidades import resolver_nombre_en_modelo
from motor.calculadora_probabilidad import calcular_probabilidad_over


def identidad_modelo(modelo):
    m = getattr(modelo, "metricas", {}) or {}
    fecha = getattr(modelo, "fecha_entrenamiento", None)
    return {
        "modelo_version": getattr(modelo, "version", None),
        "dataset_hash": m.get("hash_datos"),
        "corte_modelo": m.get("training_data_latest_game_date") or m.get("fecha_max_entrenamiento"),
        "modelo_generado_en": fecha.isoformat() if fecha is not None else None,
        "muestra_entrenamiento": m.get("partidos_entrenamiento"),
        "eficacia_certificada": False,
        "confianza_metodo": "heuristico_no_validado",
        "incluye_ot": False,
        "minutos_regulacion": 48,
    }


def consultar(modelo, local, visitante, periodo, linea):
    a = resolver_nombre_en_modelo(local, modelo.entidad_a_indice)
    b = resolver_nombre_en_modelo(visitante, modelo.entidad_a_indice)
    if not a or not b or a == b:
        raise ValueError("Selecciona dos equipos diferentes presentes en el artefacto NBA")
    if periodo not in ("Q1", "Q2", "Q3", "Q4", "TOTAL"):
        raise ValueError("Periodo no soportado por el modo base")
    if not math.isfinite(linea) or not 0 < linea < 1000:
        raise ValueError("Línea fuera de rango")
    me, se, mr, sr = predecir_cuartos(modelo, a, b, Ubicacion.LOCAL)
    indices = list(range(4)) if periodo == "TOTAL" else [int(periodo[1])-1]
    media = float(np.sum(me[indices] + mr[indices]))
    sigma = float(np.sqrt(np.sum(se[indices]**2 + sr[indices]**2)))
    if not math.isfinite(media) or not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("Distribución no disponible en el artefacto")
    # No hay modelo discreto acreditado de empate/push en este artefacto.
    media_linea = math.isclose(linea % 1, 0.5, abs_tol=1e-9)
    over = calcular_probabilidad_over(media, sigma, linea) if media_linea else None
    return {
        "formato": "consulta-local-v1", "analisis_id": str(uuid4()), "liga": "nba",
        "equipo_local": a, "equipo_visitante": b, "periodo": periodo, "linea": linea,
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "modo": "BASE_LOCAL", "metadata": identidad_modelo(modelo),
        "distribucion": {"familia": "normal_continua", "media": media, "desviacion": sigma,
                         "origen": "artefacto_publicado", "probabilidad_tipo": "RAW"},
        "probabilidad_over": over, "probabilidad_under": None if over is None else 1-over,
        "probabilidad_push": 0.0 if media_linea else None,
        "motivo_nd": None if media_linea else "Línea entera/fraccionaria: masa de push no acreditada; usa una línea terminada en .5",
        "advertencias": [
            "Base RAW de regulación NBA (48 min), sin OT. No equivale a la consulta con contexto.",
            "No consulta fixture, lesiones, forma reciente, calibradores ni BD. No acredita vigencia de los datos.",
            "Dispersión global del artefacto; suma de varianzas sin covarianzas. Intervalos y probabilidades sin validación temporal propia.",
        ],
    }

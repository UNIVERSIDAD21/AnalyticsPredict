"""Describe la salida base ya calculada; no recalcula ni calibra porcentajes."""
import math


def describir_probabilidad(mercado, linea, es_corte):
    media_linea = isinstance(linea, (int, float)) and math.isfinite(linea) and math.isclose(linea % 1, .5, abs_tol=1e-9)
    return {
        "formato": "nba-base-normal-v1", "mercado": mercado, "linea": linea,
        "familia": "normal_continua", "tipo": "RAW", "calibrador": None,
        "origen": "corte_heuristico" if es_corte else "distribucion_base",
        "parametros_y_probabilidades": "predicciones del mercado seleccionado; no candidato ni escenario contextual",
        "incluye_ot": False, "minutos_regulacion": 48,
        "linea_evento_discreto_compatible": media_linea,
        "push": 0.0 if media_linea else None,
        "motivo_nd": None if media_linea else "Línea entera/fraccionaria: el modelo continuo no acredita masa de push. Probabilidad del evento discreto N/D; se conservan media y desviación.",
        "limite": "RAW sin validación temporal/calibración propia; el escenario contextual se presenta separado.",
    }

# -*- coding: utf-8 -*-
"""
constantes.py — Constantes y configuraciones del motor de fútbol.

Este módulo contiene todas las constantes utilizadas en el motor de predicción.
"""

from typing import Dict, List

# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS DE MODELO
# ══════════════════════════════════════════════════════════════════════════════

# Parámetro de regularización Ridge por defecto
ALPHA_RIDGE_DEFAULT = 5.0

# Rango de alphas para búsqueda de hiperparámetros
ALPHAS_BUSQUEDA = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]

# Número de folds para validación cruzada temporal
N_FOLDS_CV_DEFAULT = 4


# ══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS DE FEATURES
# ══════════════════════════════════════════════════════════════════════════════

# Número de partidos para cálculo de forma reciente
N_PARTIDOS_FORMA = 5

# Mínimo de partidos para estadísticas confiables
MIN_PARTIDOS_ESTADISTICAS = 3

# Mínimo de partidos para entrenamiento por equipo
MIN_PARTIDOS_EQUIPO_ENTRENAMIENTO = 5


# ══════════════════════════════════════════════════════════════════════════════
# LÍNEAS TÍPICAS PARA CADA MERCADO
# ══════════════════════════════════════════════════════════════════════════════

LINEAS_CORNERS: Dict[str, List[float]] = {
    "CORNERS_1T": [4.5, 5.5],
    "CORNERS_2T": [4.5, 5.5, 6.5],
    "CORNERS_FT": [8.5, 9.5, 10.5, 11.5],
    "CORNERS_LOCAL_1T": [2.5, 3.5],
    "CORNERS_LOCAL_2T": [2.5, 3.5],
    "CORNERS_LOCAL_FT": [4.5, 5.5, 6.5],
    "CORNERS_VISITANTE_1T": [1.5, 2.5],
    "CORNERS_VISITANTE_2T": [1.5, 2.5, 3.5],
    "CORNERS_VISITANTE_FT": [3.5, 4.5, 5.5],
}

LINEAS_GOLES: Dict[str, List[float]] = {
    "GOLES_1T": [0.5, 1.5],
    "GOLES_2T": [0.5, 1.5, 2.5],
    "GOLES_FT": [1.5, 2.5, 3.5, 4.5],
    "GOLES_LOCAL_1T": [0.5],
    "GOLES_LOCAL_2T": [0.5],
    "GOLES_LOCAL_FT": [0.5, 1.5, 2.5],
    "GOLES_VISITANTE_1T": [0.5],
    "GOLES_VISITANTE_2T": [0.5],
    "GOLES_VISITANTE_FT": [0.5, 1.5],
}

LINEAS_DISPAROS: Dict[str, List[float]] = {
    "DISPAROS_FT": [20.5, 22.5, 24.5],
    "DISPAROS_ARCO_FT": [8.5, 9.5, 10.5],
    "DISPAROS_LOCAL_FT": [10.5, 11.5, 12.5],
    "DISPAROS_LOCAL_ARCO_FT": [4.5, 5.5],
    "DISPAROS_VISITANTE_FT": [8.5, 9.5, 10.5],
    "DISPAROS_VISITANTE_ARCO_FT": [3.5, 4.5],
}


# ══════════════════════════════════════════════════════════════════════════════
# TARGETS DE MODELOS
# ══════════════════════════════════════════════════════════════════════════════

# Targets para el modelo de corners (4 targets básicos)
TARGETS_CORNERS = [
    "corners_local_1t",
    "corners_local_2t",
    "corners_visitante_1t",
    "corners_visitante_2t",
]

# Targets para el modelo de goles (4 targets básicos)
TARGETS_GOLES = [
    "goles_local_1t",
    "goles_local_2t",
    "goles_visitante_1t",
    "goles_visitante_2t",
]

# Targets para el modelo de disparos (4 targets)
TARGETS_DISPAROS = [
    "disparos_local_total",
    "disparos_local_arco",
    "disparos_visitante_total",
    "disparos_visitante_arco",
]


# ══════════════════════════════════════════════════════════════════════════════
# VALORES POR DEFECTO (FALLBACKS)
# ══════════════════════════════════════════════════════════════════════════════

# Valores por defecto cuando no hay suficientes datos históricos
DEFAULTS_CORNERS = {
    "corners_favor": 5.0,
    "corners_contra": 5.0,
    "corners_1t": 2.3,
    "corners_2t": 2.7,
}

DEFAULTS_GOLES = {
    "goles_favor": 1.3,
    "goles_contra": 1.3,
    "goles_1t": 0.6,
    "goles_2t": 0.7,
}

DEFAULTS_DISPAROS = {
    "disparos_total": 12.0,
    "disparos_arco": 4.5,
}

# Posesión por defecto
DEFAULT_POSESION = 50.0

# xG por defecto
DEFAULT_XG = 1.3


# ══════════════════════════════════════════════════════════════════════════════
# ESTADÍSTICAS DE REFERENCIA (para normalización y validación)
# ══════════════════════════════════════════════════════════════════════════════

# Estadísticas típicas observadas en La Liga (referencia)
STATS_REFERENCIA = {
    "corners_total_media": 10.2,
    "corners_total_std": 3.1,
    "corners_local_media": 5.5,
    "corners_local_std": 2.3,
    "corners_visitante_media": 4.7,
    "corners_visitante_std": 2.1,
    "goles_total_media": 2.65,
    "goles_total_std": 1.58,
    "disparos_total_media": 24.3,
    "disparos_total_std": 5.8,
}

# Ventaja de local observada
VENTAJA_LOCAL = {
    "goles": 0.39,      # +0.39 goles
    "corners": 0.8,     # +0.8 corners
    "disparos": 1.9,    # +1.9 disparos
    "posesion": 3.0,    # +3% posesión
}

# Ratio de distribución por tiempos
RATIO_PRIMER_TIEMPO = {
    "goles": 0.43,      # 43% de goles en 1T
    "corners": 0.44,    # 44% de corners en 1T
}


# ══════════════════════════════════════════════════════════════════════════════
# UMBRALES DE CONFIANZA
# ══════════════════════════════════════════════════════════════════════════════

# Umbral mínimo de edge para recomendar apuesta
UMBRAL_EDGE_RECOMENDACION = 0.05

# Umbral de partidos para confianza ALTA
UMBRAL_PARTIDOS_CONFIANZA_ALTA = 5

# Umbral de partidos para confianza MEDIA
UMBRAL_PARTIDOS_CONFIANZA_MEDIA = 3


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CACHE
# ══════════════════════════════════════════════════════════════════════════════

# Tiempo de vida del cache de estadísticas (segundos)
CACHE_TTL_ESTADISTICAS = 3600  # 1 hora

# Máximo de elementos en cache
CACHE_MAX_ELEMENTOS = 1000


# ══════════════════════════════════════════════════════════════════════════════
# MAPEO DE NOMBRES DE EQUIPOS
# ══════════════════════════════════════════════════════════════════════════════

MAPEO_NOMBRES_EQUIPOS: Dict[str, str] = {
    # La Liga
    "atlético madrid": "atletico madrid",
    "atlético de madrid": "atletico madrid",
    "athletic bilbao": "athletic club",
    "athletic de bilbao": "athletic club",
    "rayo": "rayo vallecano",

    # Premier League
    "man utd": "manchester united",
    "man city": "manchester city",
    "spurs": "tottenham hotspur",
    "tottenham": "tottenham hotspur",
    "wolves": "wolverhampton wanderers",
    "wolverhampton": "wolverhampton wanderers",

    # Bundesliga
    "bayern": "bayern munich",
    "bayern münchen": "bayern munich",
    "dortmund": "borussia dortmund",
    "bvb": "borussia dortmund",
    "gladbach": "borussia monchengladbach",
    "leverkusen": "bayer leverkusen",

    # Serie A
    "inter": "inter milan",
    "internazionale": "inter milan",
    "ac milan": "milan",

    # Ligue 1
    "psg": "paris saint-germain",
    "paris sg": "paris saint-germain",
    "monaco": "as monaco",
    "marseille": "olympique marseille",
    "lyon": "olympique lyon",
}


# ══════════════════════════════════════════════════════════════════════════════
# CÓDIGOS DE COMPETICIONES
# ══════════════════════════════════════════════════════════════════════════════

CODIGOS_COMPETICIONES = {
    "ESP_LALIGA": "La Liga",
    "ENG_PREMIER": "Premier League",
    "GER_BUNDESLIGA": "Bundesliga",
    "ITA_SERIEA": "Serie A",
    "FRA_LIGUE1": "Ligue 1",
    "EUR_CHAMPIONS": "Champions League",
    "EUR_EUROPA": "Europa League",
}

# Competiciones que son copas (eliminatorias)
COMPETICIONES_COPA = [
    "EUR_CHAMPIONS",
    "EUR_EUROPA",
    "ESP_COPA",
    "ENG_FA_CUP",
    "GER_DFB_POKAL",
]

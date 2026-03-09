# -*- coding: utf-8 -*-
"""
tipos.py — Definiciones de tipos y estructuras de datos para fútbol.

Este módulo contiene todas las clases de datos (dataclasses) y enumeraciones
que se utilizan en el motor de predicción de fútbol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from uuid import UUID

import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: ENUMERACIONES
# ══════════════════════════════════════════════════════════════════════════════

class TipoMercadoFutbol(str, Enum):
    """Tipos de mercados de apuestas de fútbol soportados (24 mercados)."""

    # Mercados de Corners (9 mercados)
    CORNERS_1T = "CORNERS_1T"
    CORNERS_2T = "CORNERS_2T"
    CORNERS_FT = "CORNERS_FT"
    CORNERS_LOCAL_1T = "CORNERS_LOCAL_1T"
    CORNERS_LOCAL_2T = "CORNERS_LOCAL_2T"
    CORNERS_LOCAL_FT = "CORNERS_LOCAL_FT"
    CORNERS_VISITANTE_1T = "CORNERS_VISITANTE_1T"
    CORNERS_VISITANTE_2T = "CORNERS_VISITANTE_2T"
    CORNERS_VISITANTE_FT = "CORNERS_VISITANTE_FT"

    # Mercados de Goles (9 mercados)
    GOLES_1T = "GOLES_1T"
    GOLES_2T = "GOLES_2T"
    GOLES_FT = "GOLES_FT"
    GOLES_LOCAL_1T = "GOLES_LOCAL_1T"
    GOLES_LOCAL_2T = "GOLES_LOCAL_2T"
    GOLES_LOCAL_FT = "GOLES_LOCAL_FT"
    GOLES_VISITANTE_1T = "GOLES_VISITANTE_1T"
    GOLES_VISITANTE_2T = "GOLES_VISITANTE_2T"
    GOLES_VISITANTE_FT = "GOLES_VISITANTE_FT"

    # Mercados de Disparos (6 mercados)
    DISPAROS_FT = "DISPAROS_FT"
    DISPAROS_ARCO_FT = "DISPAROS_ARCO_FT"
    DISPAROS_LOCAL_FT = "DISPAROS_LOCAL_FT"
    DISPAROS_LOCAL_ARCO_FT = "DISPAROS_LOCAL_ARCO_FT"
    DISPAROS_VISITANTE_FT = "DISPAROS_VISITANTE_FT"
    DISPAROS_VISITANTE_ARCO_FT = "DISPAROS_VISITANTE_ARCO_FT"

    @classmethod
    def mercados_corners(cls) -> List["TipoMercadoFutbol"]:
        """Retorna todos los mercados de corners."""
        return [
            cls.CORNERS_1T, cls.CORNERS_2T, cls.CORNERS_FT,
            cls.CORNERS_LOCAL_1T, cls.CORNERS_LOCAL_2T, cls.CORNERS_LOCAL_FT,
            cls.CORNERS_VISITANTE_1T, cls.CORNERS_VISITANTE_2T, cls.CORNERS_VISITANTE_FT,
        ]

    @classmethod
    def mercados_goles(cls) -> List["TipoMercadoFutbol"]:
        """Retorna todos los mercados de goles."""
        return [
            cls.GOLES_1T, cls.GOLES_2T, cls.GOLES_FT,
            cls.GOLES_LOCAL_1T, cls.GOLES_LOCAL_2T, cls.GOLES_LOCAL_FT,
            cls.GOLES_VISITANTE_1T, cls.GOLES_VISITANTE_2T, cls.GOLES_VISITANTE_FT,
        ]

    @classmethod
    def mercados_disparos(cls) -> List["TipoMercadoFutbol"]:
        """Retorna todos los mercados de disparos."""
        return [
            cls.DISPAROS_FT, cls.DISPAROS_ARCO_FT,
            cls.DISPAROS_LOCAL_FT, cls.DISPAROS_LOCAL_ARCO_FT,
            cls.DISPAROS_VISITANTE_FT, cls.DISPAROS_VISITANTE_ARCO_FT,
        ]


class NivelConfianza(str, Enum):
    """Niveles de confianza para las predicciones."""
    ALTA = "ALTA"      # >= 5 partidos por equipo, datos completos
    MEDIA = "MEDIA"    # 3-4 partidos por equipo
    BAJA = "BAJA"      # < 3 partidos o datos incompletos


class TipoModelo(str, Enum):
    """Tipos de modelos de predicción."""
    CORNERS = "corners"
    GOLES = "goles"
    DISPAROS = "disparos"


class LadoApuesta(str, Enum):
    """Lado de una apuesta Over/Under."""
    OVER = "OVER"
    UNDER = "UNDER"


class ResultadoApuesta(str, Enum):
    """Posibles resultados de una apuesta."""
    PENDIENTE = "PENDIENTE"
    GANADA = "GANADA"
    PERDIDA = "PERDIDA"
    PUSH = "PUSH"


class Ubicacion(str, Enum):
    """Ubicación del equipo en el partido."""
    LOCAL = "LOCAL"
    VISITANTE = "VISITANTE"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: ESTRUCTURAS DE DATOS PARA FEATURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EstadisticasEquipo:
    """Estadísticas agregadas de un equipo."""

    # Goles
    goles_favor: float = 0.0
    goles_contra: float = 0.0

    # Corners
    corners_favor: float = 0.0
    corners_contra: float = 0.0
    corners_1t_favor: float = 0.0
    corners_2t_favor: float = 0.0

    # Disparos
    disparos_total: float = 0.0
    disparos_arco: float = 0.0

    # Otros
    posesion: float = 50.0
    xg: float = 0.0

    # Metadatos
    partidos_jugados: int = 0


@dataclass
class FeaturesPartidoFutbol:
    """Contenedor de features para un partido de fútbol."""

    # Identificación
    partido_id: UUID
    fecha_partido: datetime
    competicion_id: Optional[UUID] = None
    temporada_id: Optional[UUID] = None
    es_copa: bool = False

    # Índices para matriz de diseño
    equipo_local_idx: int = -1
    equipo_visitante_idx: int = -1
    equipo_local_id: Optional[UUID] = None
    equipo_visitante_id: Optional[UUID] = None
    equipo_local_nombre: str = ""
    equipo_visitante_nombre: str = ""

    # Equipo LOCAL - Temporada completa
    local_goles_favor_temp: float = 0.0
    local_goles_contra_temp: float = 0.0
    local_corners_favor_temp: float = 0.0
    local_corners_contra_temp: float = 0.0
    local_corners_1t_temp: float = 0.0
    local_corners_2t_temp: float = 0.0
    local_disparos_temp: float = 0.0
    local_disparos_arco_temp: float = 0.0
    local_posesion_temp: float = 50.0
    local_xg_temp: float = 0.0
    local_partidos_jugados: int = 0

    # Equipo LOCAL - Solo como local
    local_goles_como_local: float = 0.0
    local_goles_contra_como_local: float = 0.0
    local_corners_como_local: float = 0.0
    local_corners_contra_como_local: float = 0.0
    local_partidos_local: int = 0

    # Equipo LOCAL - Forma reciente (últimos N partidos)
    local_goles_ultimos_5: float = 0.0
    local_corners_ultimos_5: float = 0.0
    local_disparos_ultimos_5: float = 0.0
    local_tendencia_corners: float = 0.0

    # Equipo VISITANTE - Temporada completa
    visitante_goles_favor_temp: float = 0.0
    visitante_goles_contra_temp: float = 0.0
    visitante_corners_favor_temp: float = 0.0
    visitante_corners_contra_temp: float = 0.0
    visitante_corners_1t_temp: float = 0.0
    visitante_corners_2t_temp: float = 0.0
    visitante_disparos_temp: float = 0.0
    visitante_disparos_arco_temp: float = 0.0
    visitante_posesion_temp: float = 50.0
    visitante_xg_temp: float = 0.0
    visitante_partidos_jugados: int = 0

    # Equipo VISITANTE - Solo como visitante
    visitante_goles_como_visitante: float = 0.0
    visitante_goles_contra_como_visitante: float = 0.0
    visitante_corners_como_visitante: float = 0.0
    visitante_corners_contra_como_visitante: float = 0.0
    visitante_partidos_visitante: int = 0

    # Equipo VISITANTE - Forma reciente
    visitante_goles_ultimos_5: float = 0.0
    visitante_corners_ultimos_5: float = 0.0
    visitante_disparos_ultimos_5: float = 0.0
    visitante_tendencia_corners: float = 0.0

    # Features derivados
    diff_goles_favor: float = 0.0
    diff_corners_favor: float = 0.0
    suma_corners_promedio: float = 0.0
    ratio_posesion: float = 0.5

    # Campos legacy de compatibilidad (tests históricos)
    nombre_local: str = ""
    nombre_visitante: str = ""
    local_corners_favor_ultimos: float = 0.0
    local_corners_contra_ultimos: float = 0.0
    local_corners_casa: float = 0.0
    visitante_corners_favor_ultimos: float = 0.0
    visitante_corners_contra_ultimos: float = 0.0
    visitante_corners_fuera: float = 0.0
    local_goles_favor_ultimos: float = 0.0
    local_goles_contra_ultimos: float = 0.0
    local_goles_casa: float = 0.0
    visitante_goles_favor_ultimos: float = 0.0
    visitante_goles_contra_ultimos: float = 0.0
    visitante_goles_fuera: float = 0.0
    local_disparos_ultimos: float = 0.0
    local_disparos_arco_ultimos: float = 0.0
    visitante_disparos_ultimos: float = 0.0
    visitante_disparos_arco_ultimos: float = 0.0
    local_faltas_temp: float = 0.0
    visitante_faltas_temp: float = 0.0
    partidos_local_temp: int = 0
    partidos_visitante_temp: int = 0
    partidos_local_ultimos: int = 0
    partidos_visitante_ultimos: int = 0

    def __post_init__(self) -> None:
        """Mapea aliases legacy para mantener compatibilidad hacia atrás."""
        if self.nombre_local and not self.equipo_local_nombre:
            self.equipo_local_nombre = self.nombre_local
        if self.nombre_visitante and not self.equipo_visitante_nombre:
            self.equipo_visitante_nombre = self.nombre_visitante

        if self.local_corners_favor_ultimos and self.local_corners_ultimos_5 == 0.0:
            self.local_corners_ultimos_5 = self.local_corners_favor_ultimos
        if self.visitante_corners_favor_ultimos and self.visitante_corners_ultimos_5 == 0.0:
            self.visitante_corners_ultimos_5 = self.visitante_corners_favor_ultimos
        if self.local_goles_favor_ultimos and self.local_goles_ultimos_5 == 0.0:
            self.local_goles_ultimos_5 = self.local_goles_favor_ultimos
        if self.visitante_goles_favor_ultimos and self.visitante_goles_ultimos_5 == 0.0:
            self.visitante_goles_ultimos_5 = self.visitante_goles_favor_ultimos
        if self.local_disparos_ultimos and self.local_disparos_ultimos_5 == 0.0:
            self.local_disparos_ultimos_5 = self.local_disparos_ultimos
        if self.visitante_disparos_ultimos and self.visitante_disparos_ultimos_5 == 0.0:
            self.visitante_disparos_ultimos_5 = self.visitante_disparos_ultimos

    def to_array_corners(self) -> np.ndarray:
        """Convierte a array de features para modelo de corners."""
        return np.array([
            # Temporada local
            self.local_corners_favor_temp,
            self.local_corners_contra_temp,
            self.local_corners_1t_temp,
            self.local_corners_2t_temp,
            self.local_posesion_temp,

            # Como local
            self.local_corners_como_local,
            self.local_corners_contra_como_local,

            # Forma local
            self.local_corners_ultimos_5,
            self.local_tendencia_corners,

            # Temporada visitante
            self.visitante_corners_favor_temp,
            self.visitante_corners_contra_temp,
            self.visitante_corners_1t_temp,
            self.visitante_corners_2t_temp,
            self.visitante_posesion_temp,

            # Como visitante
            self.visitante_corners_como_visitante,
            self.visitante_corners_contra_como_visitante,

            # Forma visitante
            self.visitante_corners_ultimos_5,
            self.visitante_tendencia_corners,

            # Derivados
            self.diff_corners_favor,
            self.suma_corners_promedio,
        ], dtype=float)

    def to_array_goles(self) -> np.ndarray:
        """Convierte a array de features para modelo de goles."""
        return np.array([
            # Temporada local
            self.local_goles_favor_temp,
            self.local_goles_contra_temp,
            self.local_xg_temp,
            self.local_posesion_temp,

            # Como local
            self.local_goles_como_local,
            self.local_goles_contra_como_local,

            # Forma local
            self.local_goles_ultimos_5,

            # Temporada visitante
            self.visitante_goles_favor_temp,
            self.visitante_goles_contra_temp,
            self.visitante_xg_temp,
            self.visitante_posesion_temp,

            # Como visitante
            self.visitante_goles_como_visitante,
            self.visitante_goles_contra_como_visitante,

            # Forma visitante
            self.visitante_goles_ultimos_5,

            # Derivados
            self.diff_goles_favor,
        ], dtype=float)

    def to_array_disparos(self) -> np.ndarray:
        """Convierte a array de features para modelo de disparos."""
        return np.array([
            # Local
            self.local_disparos_temp,
            self.local_disparos_arco_temp,
            self.local_posesion_temp,
            self.local_disparos_ultimos_5,

            # Visitante
            self.visitante_disparos_temp,
            self.visitante_disparos_arco_temp,
            self.visitante_posesion_temp,
            self.visitante_disparos_ultimos_5,
        ], dtype=float)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "partido_id": str(self.partido_id),
            "fecha_partido": self.fecha_partido.isoformat() if self.fecha_partido else None,
            "competicion_id": str(self.competicion_id),
            "temporada_id": str(self.temporada_id),
            "es_copa": self.es_copa,
            "equipo_local_idx": self.equipo_local_idx,
            "equipo_visitante_idx": self.equipo_visitante_idx,
            "equipo_local_nombre": self.equipo_local_nombre,
            "equipo_visitante_nombre": self.equipo_visitante_nombre,
            # ... (todos los demás campos)
            "local_goles_favor_temp": self.local_goles_favor_temp,
            "local_corners_favor_temp": self.local_corners_favor_temp,
            "visitante_corners_favor_temp": self.visitante_corners_favor_temp,
            "suma_corners_promedio": self.suma_corners_promedio,
        }

    @classmethod
    def desde_dict(cls, data: Dict[str, Any]) -> "FeaturesPartidoFutbol":
        """Construye desde diccionario."""
        return cls(
            partido_id=UUID(data["partido_id"]) if isinstance(data.get("partido_id"), str) else data.get("partido_id"),
            fecha_partido=datetime.fromisoformat(data["fecha_partido"]) if data.get("fecha_partido") else datetime.now(),
            competicion_id=UUID(data["competicion_id"]) if isinstance(data.get("competicion_id"), str) else data.get("competicion_id"),
            temporada_id=UUID(data["temporada_id"]) if isinstance(data.get("temporada_id"), str) else data.get("temporada_id"),
            es_copa=data.get("es_copa", False),
            equipo_local_idx=data.get("equipo_local_idx", -1),
            equipo_visitante_idx=data.get("equipo_visitante_idx", -1),
            equipo_local_nombre=data.get("equipo_local_nombre", ""),
            equipo_visitante_nombre=data.get("equipo_visitante_nombre", ""),
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: ESTRUCTURAS DE DATOS PARA PREDICCIONES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PrediccionMercado:
    """Predicción para un mercado específico.

    Compatibilidad legacy:
    - `interval_conf_90` se acepta como alias histórico de `intervalo_90`.
    """
    mercado: TipoMercadoFutbol
    media: float
    std: float
    intervalo_90: Tuple[float, float] = (0.0, 0.0)
    probabilidades: Dict[str, float] = field(default_factory=dict)  # {"over_9.5": 0.58, "under_9.5": 0.42}
    interval_conf_90: Optional[Tuple[float, float]] = None
    intervalo_confianza_90: Optional[Tuple[float, float]] = None

    def __post_init__(self) -> None:
        if self.interval_conf_90 is not None:
            self.intervalo_90 = self.interval_conf_90
        if self.intervalo_confianza_90 is not None:
            self.intervalo_90 = self.intervalo_confianza_90

    def prob_over(self, linea: float) -> float:
        """Obtiene probabilidad over para una línea específica."""
        clave = f"over_{linea}"
        return self.probabilidades.get(clave, 0.5)

    def prob_under(self, linea: float) -> float:
        """Obtiene probabilidad under para una línea específica."""
        clave = f"under_{linea}"
        return self.probabilidades.get(clave, 0.5)


@dataclass
class PrediccionPartido:
    """Predicción completa para un partido."""
    partido_id: UUID
    fecha_analisis: datetime
    equipo_local: str
    equipo_visitante: str
    competicion: str

    mercados_corners: Dict[str, PrediccionMercado] = field(default_factory=dict)
    mercados_goles: Dict[str, PrediccionMercado] = field(default_factory=dict)
    mercados_disparos: Dict[str, PrediccionMercado] = field(default_factory=dict)

    nivel_confianza: NivelConfianza = NivelConfianza.MEDIA
    version_modelo: str = ""

    metricas_modelo: Dict[str, float] = field(default_factory=dict)
    recomendaciones: List[Dict[str, Any]] = field(default_factory=list)

    def obtener_mercado(self, tipo: TipoMercadoFutbol) -> Optional[PrediccionMercado]:
        """Obtiene predicción para un mercado específico."""
        if tipo in TipoMercadoFutbol.mercados_corners():
            return self.mercados_corners.get(tipo.value)
        elif tipo in TipoMercadoFutbol.mercados_goles():
            return self.mercados_goles.get(tipo.value)
        elif tipo in TipoMercadoFutbol.mercados_disparos():
            return self.mercados_disparos.get(tipo.value)
        return None

    def a_json(self) -> Dict[str, Any]:
        """Serializa a diccionario JSON-compatible."""
        return {
            "partido_id": str(self.partido_id),
            "fecha_analisis": self.fecha_analisis.isoformat(),
            "equipo_local": self.equipo_local,
            "equipo_visitante": self.equipo_visitante,
            "competicion": self.competicion,
            "mercados_corners": {
                k: {
                    "mercado": v.mercado.value,
                    "media": v.media,
                    "std": v.std,
                    "intervalo_90": list(v.intervalo_90),
                    "probabilidades": v.probabilidades,
                }
                for k, v in self.mercados_corners.items()
            },
            "mercados_goles": {
                k: {
                    "mercado": v.mercado.value,
                    "media": v.media,
                    "std": v.std,
                    "intervalo_90": list(v.intervalo_90),
                    "probabilidades": v.probabilidades,
                }
                for k, v in self.mercados_goles.items()
            },
            "mercados_disparos": {
                k: {
                    "mercado": v.mercado.value,
                    "media": v.media,
                    "std": v.std,
                    "intervalo_90": list(v.intervalo_90),
                    "probabilidades": v.probabilidades,
                }
                for k, v in self.mercados_disparos.items()
            },
            "nivel_confianza": self.nivel_confianza.value,
            "version_modelo": self.version_modelo,
            "metricas_modelo": self.metricas_modelo,
            "recomendaciones": self.recomendaciones,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: ESTRUCTURAS DE DATOS PARA MODELOS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConfiguracionEntrenamiento:
    """Configuración para entrenamiento de modelos."""
    competiciones: Optional[List[str]] = None  # None = todas
    temporadas: Optional[List[str]] = None     # None = todas
    fecha_corte: Optional[date] = None
    n_folds_cv: int = 4
    alpha_ridge: Optional[float] = None  # None = buscar óptimo
    min_partidos_equipo: int = 5
    incluir_copas: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "competiciones": self.competiciones,
            "temporadas": self.temporadas,
            "fecha_corte": self.fecha_corte.isoformat() if self.fecha_corte else None,
            "n_folds_cv": self.n_folds_cv,
            "alpha_ridge": self.alpha_ridge,
            "min_partidos_equipo": self.min_partidos_equipo,
            "incluir_copas": self.incluir_copas,
        }


@dataclass
class ResultadoEntrenamiento:
    """Resultado de entrenar un modelo."""
    tipo_modelo: TipoModelo
    targets: List[str]
    fecha_entrenamiento: datetime
    n_partidos: int
    n_equipos: int

    mae_por_target: Dict[str, float] = field(default_factory=dict)
    rmse_por_target: Dict[str, float] = field(default_factory=dict)
    r2_por_target: Dict[str, float] = field(default_factory=dict)
    std_residuales: Dict[str, float] = field(default_factory=dict)

    alpha_usado: float = 5.0
    duracion_segundos: float = 0.0
    hash_datos: str = ""
    version_id: int = 0

    def mae_promedio(self) -> float:
        """Calcula MAE promedio de todos los targets."""
        if not self.mae_por_target:
            return 0.0
        return sum(self.mae_por_target.values()) / len(self.mae_por_target)


@dataclass
class ModeloRidgeFutbol:
    """Modelo Ridge entrenado para fútbol."""
    tipo: TipoModelo
    alfa: float
    entidad_a_indice: Dict[str, int]
    pesos: Dict[str, np.ndarray]       # {"local_1t": array, ...}
    std_residuales: Dict[str, float]   # {"local_1t": 2.1, ...}

    fecha_entrenamiento: Optional[datetime] = None
    version_id: Optional[int] = None
    metricas: Dict[str, float] = field(default_factory=dict)

    def contiene_equipo(self, nombre: str) -> bool:
        """Verifica si un equipo está en el modelo."""
        nombre_normalizado = normalizar_nombre_equipo(nombre)
        return nombre_normalizado in self.entidad_a_indice

    @property
    def cantidad_equipos(self) -> int:
        """Retorna la cantidad de equipos en el modelo."""
        return len(self.entidad_a_indice)

    def obtener_equipos(self) -> List[str]:
        """Retorna lista de nombres de equipos en el modelo."""
        return list(self.entidad_a_indice.keys())

    def predecir(self, X: np.ndarray) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Genera predicciones para cada target.

        Args:
            X: Matriz de features (n_partidos, n_features)

        Returns:
            Dict con {target: (medias, stds)}
        """
        resultados = {}
        for target, pesos in self.pesos.items():
            medias = X @ pesos
            std = self.std_residuales.get(target, 1.0)
            stds = np.full_like(medias, std)
            resultados[target] = (medias, stds)
        return resultados


@dataclass
class DatosPartidoEntrenamiento:
    """Datos de un partido para entrenamiento."""
    partido_id: UUID
    fecha_partido: datetime
    equipo_local: str
    equipo_visitante: str

    # Corners
    local_corners_1t: Optional[int] = None
    local_corners_2t: Optional[int] = None
    visitante_corners_1t: Optional[int] = None
    visitante_corners_2t: Optional[int] = None

    # Goles
    local_goles_1t: Optional[int] = None
    local_goles_2t: Optional[int] = None
    visitante_goles_1t: Optional[int] = None
    visitante_goles_2t: Optional[int] = None

    # Disparos
    local_disparos_total: Optional[int] = None
    local_disparos_arco: Optional[int] = None
    visitante_disparos_total: Optional[int] = None
    visitante_disparos_arco: Optional[int] = None


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5: FUNCIONES DE UTILIDAD
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_nombre_equipo(nombre: str) -> str:
    """
    Normaliza el nombre de un equipo a minúsculas sin espacios extra.

    Args:
        nombre: Nombre del equipo

    Returns:
        Nombre normalizado
    """
    return " ".join((nombre or "").strip().lower().replace("_", " ").split())


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6: ESTRUCTURAS DE DATOS PARA CALIBRACIÓN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConfiguracionCalibracion:
    """Configuración para el sistema de calibración de probabilidades."""

    metodo: str = "platt"  # 'platt' | 'isotonic' | 'auto'
    min_muestras: int = 100
    n_bins_ece: int = 10
    validacion_cruzada: bool = True
    n_folds: int = 5
    train_ratio: float = 0.8  # Proporción de datos para entrenamiento

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "metodo": self.metodo,
            "min_muestras": self.min_muestras,
            "n_bins_ece": self.n_bins_ece,
            "validacion_cruzada": self.validacion_cruzada,
            "n_folds": self.n_folds,
            "train_ratio": self.train_ratio,
        }

    @classmethod
    def desde_dict(cls, data: Dict[str, Any]) -> "ConfiguracionCalibracion":
        """Construye desde diccionario."""
        return cls(
            metodo=data.get("metodo", "platt"),
            min_muestras=data.get("min_muestras", 100),
            n_bins_ece=data.get("n_bins_ece", 10),
            validacion_cruzada=data.get("validacion_cruzada", True),
            n_folds=data.get("n_folds", 5),
            train_ratio=data.get("train_ratio", 0.8),
        )


@dataclass
class ResultadoCalibracion:
    """Resultado de entrenar un calibrador de probabilidades."""

    mercado: TipoMercadoFutbol
    metodo: str  # 'platt' | 'isotonic'

    # Métricas antes de calibración
    brier_antes: float
    log_loss_antes: float
    ece_antes: float

    # Métricas después de calibración
    brier_despues: float
    log_loss_despues: float
    ece_despues: float

    # Mejora
    mejora_brier_porcentual: float = field(init=False)
    mejora_ece_porcentual: float = field(init=False)

    # Metadatos
    n_muestras: int = 0
    n_muestras_train: int = 0
    n_muestras_validation: int = 0
    fecha_entrenamiento: datetime = field(default_factory=datetime.now)
    parametros: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calcula métricas derivadas después de inicialización."""
        if self.brier_antes > 0:
            self.mejora_brier_porcentual = (
                (self.brier_antes - self.brier_despues) / self.brier_antes * 100
            )
        else:
            self.mejora_brier_porcentual = 0.0

        if self.ece_antes > 0:
            self.mejora_ece_porcentual = (
                (self.ece_antes - self.ece_despues) / self.ece_antes * 100
            )
        else:
            self.mejora_ece_porcentual = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "mercado": self.mercado.value,
            "metodo": self.metodo,
            "brier_antes": self.brier_antes,
            "log_loss_antes": self.log_loss_antes,
            "ece_antes": self.ece_antes,
            "brier_despues": self.brier_despues,
            "log_loss_despues": self.log_loss_despues,
            "ece_despues": self.ece_despues,
            "mejora_brier_porcentual": self.mejora_brier_porcentual,
            "mejora_ece_porcentual": self.mejora_ece_porcentual,
            "n_muestras": self.n_muestras,
            "n_muestras_train": self.n_muestras_train,
            "n_muestras_validation": self.n_muestras_validation,
            "fecha_entrenamiento": self.fecha_entrenamiento.isoformat(),
            "parametros": self.parametros,
        }


@dataclass
class DatosReliabilityDiagram:
    """Datos para generar un diagrama de confiabilidad (reliability diagram)."""

    bins: List[Tuple[float, float]]  # Lista de (inicio, fin) de cada bin
    frecuencia_predicha: List[float]  # Promedio de prob en cada bin
    frecuencia_real: List[float]  # Proporción de outcomes=1 en cada bin
    conteo: List[int]  # Número de muestras en cada bin

    @property
    def n_bins(self) -> int:
        """Número de bins."""
        return len(self.bins)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "bins": self.bins,
            "frecuencia_predicha": self.frecuencia_predicha,
            "frecuencia_real": self.frecuencia_real,
            "conteo": self.conteo,
        }

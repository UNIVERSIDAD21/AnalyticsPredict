# -*- coding: utf-8 -*-
"""
tipos.py — Definiciones de tipos y estructuras de datos.

Este módulo contiene todas las clases de datos (dataclasses) y enumeraciones
que se utilizan en el motor de predicción y la API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
from enum import Enum


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: ENUMERACIONES
# ══════════════════════════════════════════════════════════════════════════════

class NivelConfianza(str, Enum):
    """Niveles de confianza para las predicciones."""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class TipoMercado(str, Enum):
    """Tipos de mercados de apuestas soportados."""
    TOTAL = "TOTAL"
    EQUIPO = "EQUIPO"
    RIVAL = "RIVAL"


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


class TipoRecomendacion(str, Enum):
    """Tipos de recomendación basados en el análisis de valor."""
    VALOR = "VALOR"
    JUSTO = "JUSTO"
    EVITAR = "EVITAR"


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: ESTRUCTURAS DE DATOS BÁSICAS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class InfoEquipo:
    """Información básica de un equipo NBA."""
    id: str
    nombre: str
    nombre_corto: str
    abreviatura: str
    conferencia: Optional[str] = None
    division: Optional[str] = None


@dataclass
class RazonPrediccion:
    """Razón que explica por qué el sistema hizo cierta predicción."""
    factor: str
    direccion: Literal["sube", "baja"]
    impacto: float
    descripcion: str

    def formato_impacto(self) -> str:
        """Retorna el impacto formateado con signo y unidad."""
        signo = "+" if self.impacto >= 0 else ""
        return f"{signo}{self.impacto:.1f} pts"


@dataclass
class AnalisisMercado:
    """Análisis del valor de mercado cuando se proporciona una cuota."""
    cuota: float
    probabilidad_implicita_raw: float
    probabilidad_implicita_fair: float
    datos_devig: "DatosDeVig"
    edge_raw: float
    edge_real: float
    valor_esperado: float
    recomendacion: TipoRecomendacion
    probabilidad_implicita: Optional[float] = None
    edge: Optional[float] = None

    @classmethod
    def calcular(
        cls,
        probabilidad_sistema: float,
        cuota: float,
        datos_devig: "DatosDeVig",
        umbral_edge_valor: float = 0.05,
    ) -> "AnalisisMercado":
        """Crea un AnalisisMercado calculando todos los valores."""
        prob_implicita_raw = 1.0 / cuota
        prob_implicita_fair = datos_devig.p_mkt_fair
        edge_raw = probabilidad_sistema - prob_implicita_raw
        edge_real = probabilidad_sistema - prob_implicita_fair
        ev = (probabilidad_sistema * cuota) - 1

        if ev <= 0 or edge_real <= 0:
            recomendacion = TipoRecomendacion.EVITAR
        elif edge_real > umbral_edge_valor:
            recomendacion = TipoRecomendacion.VALOR
        else:
            recomendacion = TipoRecomendacion.JUSTO

        return cls(
            cuota=cuota,
            probabilidad_implicita_raw=prob_implicita_raw,
            probabilidad_implicita_fair=prob_implicita_fair,
            datos_devig=datos_devig,
            edge_raw=edge_raw,
            edge_real=edge_real,
            valor_esperado=ev,
            recomendacion=recomendacion,
            probabilidad_implicita=prob_implicita_raw,
            edge=edge_raw,
        )


@dataclass
class DatosDeVig:
    """Resultado normalizado de quitar el vig para un lado del mercado."""
    metodo: Literal["exacto", "estimado", "no_aplicado"]
    overround: Optional[float]
    p_mkt_raw: float
    p_mkt_fair: float
    advertencias: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.metodo == "exacto" and self.overround is None:
            raise ValueError("overround no puede ser None cuando el método es exacto.")

        if self.metodo == "no_aplicado" and self.p_mkt_fair != self.p_mkt_raw:
            raise ValueError(
                "p_mkt_fair debe ser igual a p_mkt_raw cuando el método es no_aplicado."
            )

        if not (0.0 <= self.p_mkt_raw <= 1.0):
            raise ValueError("p_mkt_raw debe estar entre 0 y 1.")

        if not (0.0 <= self.p_mkt_fair <= 1.0):
            raise ValueError("p_mkt_fair debe estar entre 0 y 1.")

        if self.overround is not None and self.overround <= 0:
            raise ValueError("overround debe ser mayor a 0 cuando se proporciona.")

        if self.advertencias is None:
            raise ValueError("advertencias siempre debe ser una lista.")

    @property
    def vig_porcentaje(self) -> Optional[float]:
        if self.overround is None:
            return None
        return max((self.overround - 1.0) * 100, 0.0)


@dataclass
class CandidatoApuesta:
    """Candidato de apuesta evaluado por el sistema."""
    cuarto: str
    mercado: TipoMercado
    lado: LadoApuesta
    linea: float
    probabilidad: float
    media: float
    desviacion: float
    distancia_z: float

    def etiqueta(self, nombre_equipo: str, nombre_rival: str) -> str:
        """Genera una etiqueta legible para mostrar al usuario."""
        if self.mercado == TipoMercado.TOTAL:
            sujeto = "TOTAL"
        elif self.mercado == TipoMercado.EQUIPO:
            sujeto = nombre_equipo
        else:
            sujeto = nombre_rival

        return f"{self.lado.value} {self.linea:.1f} ({sujeto})"

    def es_recomendable(self, probabilidad_minima: float = 0.55) -> bool:
        """Indica si la apuesta supera el umbral de probabilidad mínima."""
        return self.probabilidad >= probabilidad_minima


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: ESTRUCTURAS DE DATOS COMPLEJAS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PrediccionCuarto:
    """Predicción completa para un cuarto específico."""
    cuarto: str
    media_equipo: float
    desviacion_equipo: float
    rango_equipo: tuple
    media_rival: float
    desviacion_rival: float
    rango_rival: tuple
    media_total: float
    desviacion_total: float
    rango_total: tuple
    linea_analizada: Optional[float] = None
    probabilidad_over: Optional[float] = None
    probabilidad_under: Optional[float] = None
    ganador_probable: str = ""
    probabilidad_ganador: float = 0.5

    @property
    def tiene_linea(self) -> bool:
        """Indica si se analizó una línea específica."""
        return self.linea_analizada is not None


@dataclass
class FactoresConfianza:
    """Factores que determinan el nivel de confianza de una predicción."""
    tamano_muestra: str
    volatilidad: str
    frescura_datos: str
    puntaje_total: int

    def obtener_nivel(self) -> NivelConfianza:
        """Determina el nivel de confianza basado en el puntaje."""
        if self.puntaje_total >= 3:
            return NivelConfianza.ALTA
        if self.puntaje_total >= 3:
            return NivelConfianza.MEDIA
        return NivelConfianza.BAJA

    def como_diccionario(self) -> Dict[str, str]:
        """Retorna los factores como diccionario para la API."""
        return {
            "tamano_muestra": self.tamano_muestra,
            "volatilidad": self.volatilidad,
            "frescura_datos": self.frescura_datos,
        }


@dataclass
class ResultadoAnalisis:
    """Resultado completo de un análisis de partido."""
    equipo: str
    equipo_nombre_completo: str
    rival: str
    rival_nombre_completo: str
    ubicacion: Ubicacion
    fecha_analisis: str
    predicciones: Dict[str, PrediccionCuarto]
    prediccion_juego_completo: Optional[PrediccionCuarto] = None
    razones: List[RazonPrediccion] = field(default_factory=list)
    nivel_confianza: NivelConfianza = NivelConfianza.MEDIA
    factores_confianza: FactoresConfianza = None
    analisis_mercado: Optional[AnalisisMercado] = None
    mejor_apuesta: Optional[CandidatoApuesta] = None
    es_en_vivo: bool = False
    cuartos_reales: Dict[str, tuple] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: ESTRUCTURAS PARA EL MODELO RIDGE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ModeloRidge:
    """Modelo de regresión Ridge entrenado para predicción de puntos por cuarto."""
    alfa: float
    entidad_a_indice: Dict[str, int]
    pesos_equipo: Any
    pesos_rival: Any
    desviacion_equipo: Any
    desviacion_rival: Any

    def contiene_equipo(self, nombre: str) -> bool:
        """Verifica si un equipo está en el modelo."""
        from .utilidades import resolver_nombre_en_modelo
        return resolver_nombre_en_modelo(nombre, self.entidad_a_indice) is not None

    @property
    def cantidad_equipos(self) -> int:
        """Retorna la cantidad de equipos en el modelo."""
        return len(self.entidad_a_indice)

    def obtener_equipos(self) -> List[str]:
        """Retorna lista de nombres de equipos en el modelo."""
        return list(self.entidad_a_indice.keys())


@dataclass
class ConfiguracionDataset:
    """Configuración para cargar datasets de entrenamiento."""
    columna_rival: Optional[str] = None
    columna_ubicacion: Optional[str] = None
    columnas_cuartos_equipo: Optional[List[str]] = None
    columnas_cuartos_rival: Optional[List[str]] = None

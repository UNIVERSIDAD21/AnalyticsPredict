# -*- coding: utf-8 -*-
"""
schemas_futbol.py — Modelos Pydantic para la API de fútbol.

Este módulo contiene todos los schemas de request/response para los endpoints
del módulo de fútbol.
"""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE COMPETICIONES
# ═══════════════════════════════════════════════════════════════════════════════

class CompeticionBase(BaseModel):
    """Schema base para una competición de fútbol."""
    id: UUID
    codigo: str
    nombre: str
    pais: str
    tipo: str = Field(description="liga, copa_nacional, continental")
    prioridad: int = 0
    activa: bool = True


class CompeticionDetalle(CompeticionBase):
    """Schema con detalle adicional de una competición."""
    temporada_actual: Optional[str] = None
    total_equipos: int = 0
    total_partidos: int = 0


class ListaCompeticionesResponse(BaseModel):
    """Respuesta para listado de competiciones."""
    exito: bool = True
    total: int
    competiciones: List[CompeticionBase]


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE EQUIPOS
# ═══════════════════════════════════════════════════════════════════════════════

class EstadisticasEquipo(BaseModel):
    """Estadísticas agregadas de un equipo."""
    partidos_jugados: int = 0
    victorias: int = 0
    empates: int = 0
    derrotas: int = 0
    goles_favor: float = 0.0
    goles_contra: float = 0.0
    corners_favor: float = 0.0
    corners_contra: float = 0.0
    disparos_total: float = 0.0
    disparos_arco: float = 0.0


class EquipoBase(BaseModel):
    """Schema base para un equipo de fútbol."""
    id: UUID
    nombre: str
    nombre_corto: Optional[str] = None
    pais: str
    competicion_principal: Optional[str] = None
    logo_url: Optional[str] = None


class EquipoDetalle(EquipoBase):
    """Schema con detalle completo de un equipo."""
    estadisticas: Optional[EstadisticasEquipo] = None


class ListaEquiposResponse(BaseModel):
    """Respuesta para listado de equipos."""
    exito: bool = True
    total: int
    pagina: int = 1
    tamano: int = 20
    equipos: List[EquipoBase]


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE PARTIDOS
# ═══════════════════════════════════════════════════════════════════════════════

class PartidoResumen(BaseModel):
    """Schema resumen de un partido."""
    id: UUID
    competicion: str
    competicion_nombre: Optional[str] = None
    fecha_partido: datetime
    equipo_local: str
    equipo_local_nombre: Optional[str] = None
    equipo_visitante: str
    equipo_visitante_nombre: Optional[str] = None
    estado: str
    jornada: Optional[int] = None
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None


class PartidoDetalle(PartidoResumen):
    """Schema con detalle completo de un partido."""
    equipo_local_id: Optional[UUID] = None
    equipo_visitante_id: Optional[UUID] = None
    # Goles
    local_goles_1t: Optional[int] = None
    local_goles_2t: Optional[int] = None
    local_goles_total: Optional[int] = None
    visitante_goles_1t: Optional[int] = None
    visitante_goles_2t: Optional[int] = None
    visitante_goles_total: Optional[int] = None

    # Corners
    local_corners_1t: Optional[int] = None
    local_corners_2t: Optional[int] = None
    local_corners_total: Optional[int] = None
    visitante_corners_1t: Optional[int] = None
    visitante_corners_2t: Optional[int] = None
    visitante_corners_total: Optional[int] = None

    # Disparos
    local_disparos_total: Optional[int] = None
    local_disparos_arco: Optional[int] = None
    visitante_disparos_total: Optional[int] = None
    visitante_disparos_arco: Optional[int] = None

    # Estadísticas de equipos
    estadisticas_local: Optional[EstadisticasEquipo] = None
    estadisticas_visitante: Optional[EstadisticasEquipo] = None


class PartidoEstadistico(BaseModel):
    """Schema con estadísticas clave para análisis contextual."""
    id: UUID
    fecha_partido: datetime
    equipo_local_id: UUID
    equipo_visitante_id: UUID
    equipo_local: str
    equipo_visitante: str
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None
    corners_local: Optional[int] = None
    corners_visitante: Optional[int] = None
    corners_local_1t: Optional[int] = None
    corners_local_2t: Optional[int] = None
    corners_visitante_1t: Optional[int] = None
    corners_visitante_2t: Optional[int] = None
    disparos_local: Optional[int] = None
    disparos_visitante: Optional[int] = None
    disparos_arco_local: Optional[int] = None
    disparos_arco_visitante: Optional[int] = None


class ListaPartidosResponse(BaseModel):
    """Respuesta para listado de partidos."""
    exito: bool = True
    total: int
    partidos: List[PartidoResumen]


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════════

class AnalisisRequest(BaseModel):
    """Request para análisis de un partido."""
    partido_id: UUID
    h2h_limite: Optional[int] = Field(
        default=10,
        ge=5,
        le=20,
        description="Cantidad de partidos H2H a considerar (5-20).",
    )
    cuotas_por_linea: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None,
        description=(
            "Mapa opcional de cuotas por llave 'MERCADO|LINEA'. "
            "Ejemplo: {'GOLES_FT|2.5': {'cuota_over': 1.9, 'cuota_under': 1.95}}"
        ),
    )
    lineas_corners: Optional[List[float]] = Field(
        default=[8.5, 9.5, 10.5, 11.5],
        description="Líneas a analizar para corners"
    )
    lineas_goles: Optional[List[float]] = Field(
        default=[1.5, 2.5, 3.5],
        description="Líneas a analizar para goles"
    )
    lineas_disparos: Optional[List[float]] = Field(
        default=[22.5, 24.5, 26.5],
        description="Líneas a analizar para disparos"
    )
    mercado_objetivo: Optional[str] = Field(default=None, description="Mercado específico seleccionado por el usuario")
    lado_objetivo: Optional[Literal["OVER", "UNDER"]] = Field(default=None)
    linea_objetivo: Optional[float] = Field(default=None)
    temporadas: Optional[List[str]] = Field(
        default=None,
        description=(
            "IDs o nombres de temporadas a respetar estrictamente en el análisis. "
            "Si no se envía, backend usa temporada activa + anterior; "
            "si eso falla, aplica ventana temporal trazable."
        ),
    )
    ventana_dias_fallback: Optional[int] = Field(
        default=730,
        ge=30,
        le=3650,
        description="Ventana temporal fallback (días) si no se resuelven temporadas.",
    )
    fecha_minima: Optional[datetime] = Field(
        default=None,
        description="Fecha mínima explícita opcional para fallback temporal (ISO8601).",
    )

    @field_validator("lineas_corners", "lineas_goles", "lineas_disparos", mode="before")
    @classmethod
    def validar_lineas(cls, v):
        if v is None:
            return v
        if not isinstance(v, list) or len(v) == 0:
            return None
        return v

    @field_validator("temporadas", mode="before")
    @classmethod
    def validar_temporadas(cls, valor):
        if valor is None:
            return valor
        if not isinstance(valor, list):
            raise ValueError("temporadas debe ser una lista de IDs o nombres")
        limpias = [str(v).strip() for v in valor if str(v).strip()]
        if not limpias:
            raise ValueError("temporadas no puede estar vacía")
        return limpias

    @model_validator(mode="after")
    def validar_temporalidad(self):
        if self.fecha_minima is not None and self.temporadas:
            raise ValueError("No envíes temporadas y fecha_minima al mismo tiempo")
        return self


class ProbabilidadLinea(BaseModel):
    """Probabilidades para una línea específica."""
    over_raw: float = Field(ge=0, le=1)
    over_calibrada: float = Field(ge=0, le=1)
    under_raw: float = Field(ge=0, le=1)
    under_calibrada: float = Field(ge=0, le=1)
    razones: Optional[List[Dict[str, Any]]] = None


class PrediccionMercado(BaseModel):
    """Predicción para un mercado específico."""
    mercado: str
    media: float
    std: float
    lineas: Dict[str, ProbabilidadLinea]


class RecomendacionApuesta(BaseModel):
    """Recomendación de apuesta generada por el análisis."""
    mercado: str
    lado: Literal["OVER", "UNDER"]
    linea: float
    probabilidad: float = Field(ge=0, le=1)
    confianza: Literal["MUY_ALTA", "ALTA", "MEDIA", "BAJA", "MUY_BAJA"]
    valor_esperado: Optional[float] = None

    # Contrato unificado estilo NBA (P6)
    p_raw: Optional[float] = Field(default=None, ge=0, le=1)
    p_calibrada: Optional[float] = Field(default=None, ge=0, le=1)
    calibracion_aplicada: Optional[bool] = None
    modelo_version_id: Optional[str] = None
    calibrador_id: Optional[str] = None
    edge_raw: Optional[float] = None
    edge_real: Optional[float] = None
    score: Optional[float] = None
    sizing: Optional[float] = None
    cuota: Optional[float] = None
    cuota_over: Optional[float] = None
    cuota_under: Optional[float] = None
    devig_metodo: Optional[str] = None
    devig_overround: Optional[float] = None
    devig_p_mkt_fair: Optional[float] = None
    advertencias: Optional[List[str]] = None
    fuente: Optional[str] = None
    metadata_ensemble: Optional[Dict[str, Any]] = None




class ProbabilidadesGanadorFutbol(BaseModel):
    """Probabilidades 1X2 para ganador del partido."""
    prob_local: float = Field(ge=0, le=1)
    prob_empate: float = Field(ge=0, le=1)
    prob_visitante: float = Field(ge=0, le=1)
    ganador_probable: Literal["LOCAL", "EMPATE", "VISITANTE"]
    marcador_probable: str
    razones: List[str] = []

class ObjetivoProbabilidadesFutbol(BaseModel):
    over: Optional[float] = Field(default=None, ge=0, le=1)
    under: Optional[float] = Field(default=None, ge=0, le=1)


class ObjetivoBloqueFutbol(BaseModel):
    estado: Literal["disponible", "no_disponible", "degradacion_controlada", "datos_insuficientes"]
    media: Optional[float] = None
    desviacion: Optional[float] = None
    probabilidades: ObjetivoProbabilidadesFutbol


class ObjetivoDevigFutbol(BaseModel):
    estado: Literal["disponible", "no_disponible", "degradacion_controlada", "datos_insuficientes"]
    metodo: Optional[str] = None
    overround: Optional[float] = None
    p_mkt_fair: Optional[float] = None
    advertencias: List[str] = []


class ObjetivoCalibracionFutbol(BaseModel):
    estado: Literal["disponible", "no_disponible", "degradacion_controlada", "datos_insuficientes"]
    p_raw: Optional[float] = Field(default=None, ge=0, le=1)
    p_calibrada: Optional[float] = Field(default=None, ge=0, le=1)
    calibracion_aplicada: Optional[bool] = None
    calibrador_id: Optional[str] = None


class ObjetivoScoreRiesgoFutbol(BaseModel):
    estado: Literal["disponible", "no_disponible", "degradacion_controlada", "datos_insuficientes"]
    score: Optional[float] = None
    sizing: Optional[float] = None
    edge_raw: Optional[float] = None
    edge_real: Optional[float] = None
    valor_esperado: Optional[float] = None
    confianza: Optional[str] = None


class ObjetivoDisponibilidadFutbol(BaseModel):
    reales_disponibles: List[str] = []
    no_disponibles: List[str] = []
    degradacion_controlada: List[str] = []
    datos_insuficientes: List[str] = []


class ObjetivoMuestraContextoFutbol(BaseModel):
    h2h: int = 0
    local_home: int = 0
    visitante_away: int = 0
    local_global: int = 0
    visitante_global: int = 0
    liga: int = 0


class ObjetivoRangoTemporalFutbol(BaseModel):
    fecha_min: Optional[datetime] = None
    fecha_max: Optional[datetime] = None


class ObjetivoCalidadDatosFutbol(BaseModel):
    muestras: ObjetivoMuestraContextoFutbol = ObjetivoMuestraContextoFutbol()
    rango_temporal: ObjetivoRangoTemporalFutbol = ObjetivoRangoTemporalFutbol()
    temporadas_incluidas: List[str] = []
    competiciones_incluidas: List[str] = []
    muestra_insuficiente: bool = False
    datos_incompletos: bool = False
    penalizaciones_aplicadas: List[str] = []


class ObjetivoAnalisisFutbol(BaseModel):
    estado: Literal["disponible", "no_disponible", "degradacion_controlada", "datos_insuficientes"]
    mercado: str
    lado: Literal["OVER", "UNDER"]
    linea: float
    unidad: str
    media_objetivo: Optional[float] = None
    desviacion_objetivo: Optional[float] = None
    probabilidades_objetivo: ObjetivoProbabilidadesFutbol
    bloque_base: ObjetivoBloqueFutbol
    bloque_ajustado: ObjetivoBloqueFutbol
    devig: ObjetivoDevigFutbol
    calibracion: ObjetivoCalibracionFutbol
    score_riesgo: ObjetivoScoreRiesgoFutbol
    disponibilidad_datos: ObjetivoDisponibilidadFutbol
    calidad_datos: ObjetivoCalidadDatosFutbol = ObjetivoCalidadDatosFutbol()
    trazabilidad: Dict[str, Any] = {}


class AnalisisResponse(BaseModel):
    """Respuesta del análisis de un partido."""
    exito: bool = True
    partido: PartidoResumen
    timestamp_analisis: datetime
    objetivo: ObjetivoAnalisisFutbol
    mercados_corners: Dict[str, PrediccionMercado]
    mercados_goles: Dict[str, PrediccionMercado]
    mercados_disparos: Dict[str, PrediccionMercado]
    recomendaciones: List[RecomendacionApuesta]
    modelo_version: str
    calibradores_activos: int = 0
    prediccion_ganador: Optional[ProbabilidadesGanadorFutbol] = None


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE APUESTAS
# ═══════════════════════════════════════════════════════════════════════════════

class ApuestaRequest(BaseModel):
    """Request para crear una apuesta."""
    partido_id: UUID
    mercado: str = Field(description="Uno de los 24 mercados de fútbol")
    lado: Literal["OVER", "UNDER"]
    linea: float = Field(gt=0)
    cuota: Optional[float] = Field(default=None, ge=0)
    stake: float = Field(gt=0)
    casa_apuestas: Optional[str] = None
    notas: Optional[str] = None

    @field_validator("mercado")
    @classmethod
    def validar_mercado(cls, v: str) -> str:
        mercados_validos = {
            # Corners (9)
            "CORNERS_1T", "CORNERS_2T", "CORNERS_FT",
            "CORNERS_LOCAL_1T", "CORNERS_LOCAL_2T", "CORNERS_LOCAL_FT",
            "CORNERS_VISITANTE_1T", "CORNERS_VISITANTE_2T", "CORNERS_VISITANTE_FT",
            # Goles (9)
            "GOLES_1T", "GOLES_2T", "GOLES_FT",
            "GOLES_LOCAL_1T", "GOLES_LOCAL_2T", "GOLES_LOCAL_FT",
            "GOLES_VISITANTE_1T", "GOLES_VISITANTE_2T", "GOLES_VISITANTE_FT",
            # Disparos (6)
            "DISPAROS_FT", "DISPAROS_ARCO_FT",
            "DISPAROS_LOCAL_FT", "DISPAROS_LOCAL_ARCO_FT",
            "DISPAROS_VISITANTE_FT", "DISPAROS_VISITANTE_ARCO_FT",
        }
        v_upper = v.upper()
        if v_upper not in mercados_validos:
            raise ValueError(f"Mercado inválido: {v}. Debe ser uno de: {mercados_validos}")
        return v_upper

    @field_validator("cuota")
    @classmethod
    def validar_cuota(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v == 0:
            return v
        if v < 1.0:
            raise ValueError("Cuota invalida: debe ser 0 (sin cuota) o >= 1.0")
        return v


class ApuestaResponse(BaseModel):
    """Respuesta con datos de una apuesta."""
    id: UUID
    partido_id: UUID
    partido: Optional[PartidoResumen] = None
    mercado: str
    lado: str
    linea: float
    cuota: float
    stake: float
    estado: Literal["PENDIENTE", "GANADA", "PERDIDA", "PUSH", "CANCELADA", "VOID"]
    probabilidad_sistema: float
    confianza: str
    valor_esperado: float
    ganancia_potencial: float
    resultado: Optional[str] = None
    ganancia_real: Optional[float] = None
    fecha_creacion: datetime
    fecha_resolucion: Optional[datetime] = None
    casa_apuestas: Optional[str] = None
    notas: Optional[str] = None


class ApuestaUpdateRequest(BaseModel):
    """Request para actualizar una apuesta pendiente."""
    stake: Optional[float] = Field(None, gt=0)
    cuota: Optional[float] = Field(None, gt=1.0)
    notas: Optional[str] = None
    cancelar: Optional[bool] = False


class ResumenApuestas(BaseModel):
    """Resumen estadístico de apuestas."""
    total: int = 0
    pendientes: int = 0
    ganadas: int = 0
    perdidas: int = 0
    push: int = 0
    roi: Optional[float] = None
    win_rate: Optional[float] = None
    stake_total: float = 0.0
    ganancia_neta: float = 0.0


class ListaApuestasResponse(BaseModel):
    """Respuesta para listado de apuestas."""
    exito: bool = True
    total: int
    resumen: ResumenApuestas
    apuestas: List[ApuestaResponse]


class ResolucionRequest(BaseModel):
    """Request para resolver apuestas."""
    partido_id: Optional[UUID] = None
    forzar: bool = False


class ResolucionResponse(BaseModel):
    """Respuesta de resolución de apuestas."""
    exito: bool = True
    resueltas: int = 0
    ganadas: int = 0
    perdidas: int = 0
    push: int = 0
    errores: int = 0
    ganancia_neta: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════

class MetricasCalibracion(BaseModel):
    """Métricas de calibración para un mercado."""
    mercado: str
    brier_score: float
    ece: float
    log_loss: float
    n_predicciones: int
    calibrador_activo: bool = False
    metodo_calibrador: Optional[str] = None
    mejora_brier: Optional[float] = None


class MetricasRendimiento(BaseModel):
    """Métricas de rendimiento de apuestas."""
    mercado: str
    n_apuestas: int = 0
    ganadas: int = 0
    perdidas: int = 0
    roi: float = 0.0
    win_rate: float = 0.0
    stake_total: float = 0.0
    ganancia_neta: float = 0.0


class MetricasModelo(BaseModel):
    """Métricas de un modelo de predicción."""
    tipo_modelo: str
    version: str
    fecha_entrenamiento: Optional[datetime] = None
    mae: float = 0.0
    rmse: float = 0.0
    r2: float = 0.0
    n_partidos_entrenamiento: int = 0
    n_equipos: int = 0


class EstadoModelos(BaseModel):
    """Estado completo de los modelos."""
    modelos: List[MetricasModelo]
    ultima_actualizacion: Optional[datetime] = None
    proximo_reentrenamiento: Optional[datetime] = None


class ResumenSistema(BaseModel):
    """Resumen ejecutivo del sistema."""
    partidos_proximos: int = 0
    predicciones_pendientes: int = 0
    apuestas_activas: int = 0
    roi_global: Optional[float] = None
    win_rate_global: Optional[float] = None
    modelo_activo: bool = False
    calibradores_activos: int = 0
    prediccion_ganador: Optional[ProbabilidadesGanadorFutbol] = None
    alerta_calibracion: Optional[str] = None


class ListaMetricasCalibracionResponse(BaseModel):
    """Respuesta para métricas de calibración."""
    exito: bool = True
    periodo: str
    metricas: List[MetricasCalibracion]


class ListaMetricasRendimientoResponse(BaseModel):
    """Respuesta para métricas de rendimiento."""
    exito: bool = True
    periodo: str
    metricas: List[MetricasRendimiento]


class MadurezMercadoFutbol(BaseModel):
    mercado: str
    clasificacion: Literal["NO_APTO", "EXPERIMENTAL", "VALIDACION", "PROMOCIONABLE"]
    estado_mercado: Optional[Literal["verde", "amarillo", "rojo"]] = None
    n_resueltas: int = 0
    tasa_resolucion: float = 0.0
    lineas_cubiertas: int = 0
    brier: Optional[float] = None
    log_loss: Optional[float] = None
    ece: Optional[float] = None
    fallback_rate: float = 1.0
    drift_ventana_brier: Optional[float] = None
    motivos: List[str] = []


class ReporteMadurezFutbolResponse(BaseModel):
    exito: bool = True
    estado_global: Literal["BETA_LAB", "VALIDACION_CONTROLADA", "LISTO_PARA_PROMOCION_PARCIAL"]
    criterios: Dict[str, Any]
    mercados: List[MadurezMercadoFutbol]
    bloqueados: List[str] = []
    candidatos_promocion: List[str] = []
    riesgos_activos: List[str] = []


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS GENÉRICOS
# ═══════════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    exito: bool = False
    error: str
    detalle: Optional[str] = None
    codigo: Optional[str] = None


class MensajeResponse(BaseModel):
    """Schema para mensajes simples."""
    exito: bool = True
    mensaje: str

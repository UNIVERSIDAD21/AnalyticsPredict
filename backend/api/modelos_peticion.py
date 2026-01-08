# -*- coding: utf-8 -*-
"""
modelos_peticion.py — Modelos de entrada para la API.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class PeticionAnalisis(BaseModel):
    """Solicitud para analizar un partido."""

    equipo_local: str = Field(..., description="Equipo que juega de local")
    equipo_visitante: str = Field(..., description="Equipo que juega de visitante")
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    linea: float = Field(..., gt=0, description="Línea de puntos a analizar")
    cuota: Optional[float] = Field(None, gt=1.0, description="Cuota decimal opcional")
    cuota_over: Optional[float] = Field(
        None,
        gt=1.0,
        description="Cuota decimal para el lado OVER (opcional)",
    )
    cuota_under: Optional[float] = Field(
        None,
        gt=1.0,
        description="Cuota decimal para el lado UNDER (opcional)",
    )
    lado: Literal["OVER", "UNDER"] = Field(
        "OVER",
        description="Lado asociado a la cuota legacy (OVER/UNDER)",
    )
    modo_devig: Literal["estimado", "estricto"] = Field(
        "estricto",
        description="Modo para calcular de-vig cuando falta una cuota",
    )
    bankroll: Optional[float] = Field(
        None,
        gt=0,
        description="Bankroll del usuario para sizing (override opcional)",
    )
    perfil_riesgo: Optional[str] = Field(
        "CONSERVADOR",
        description="Perfil de riesgo (CONSERVADOR, MEDIO, AGRESIVO)",
    )
    temporadas: Optional[List[str]] = Field(
        None,
        description="Lista opcional de temporadas (IDs) para filtrar el análisis",
    )

    @field_validator("equipo_local", "equipo_visitante")
    @classmethod
    def validar_equipo(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("El nombre del equipo no puede estar vacío.")
        return valor

    @model_validator(mode="after")
    def normalizar_cuotas(self) -> "PeticionAnalisis":
        tiene_over = self.cuota_over is not None
        tiene_under = self.cuota_under is not None

        if not tiene_over and not tiene_under and self.cuota is not None:
            if self.lado == "UNDER":
                object.__setattr__(self, "cuota_under", self.cuota)
            else:
                object.__setattr__(self, "cuota_over", self.cuota)

        return self

    @field_validator("modo_devig", mode="before")
    @classmethod
    def normalizar_modo_devig(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        return str(valor).lower()

    @field_validator("perfil_riesgo", mode="before")
    @classmethod
    def normalizar_perfil_riesgo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        return str(valor).upper()

    @field_validator("perfil_riesgo")
    @classmethod
    def validar_perfil_riesgo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        if valor not in {"CONSERVADOR", "MEDIO", "AGRESIVO"}:
            raise ValueError("perfil_riesgo debe ser CONSERVADOR, MEDIO o AGRESIVO.")
        return valor

    @property
    def cuota_analisis(self) -> Optional[float]:
        if self.cuota_over is not None and self.cuota_under is not None:
            return self.cuota_over if self.lado == "OVER" else self.cuota_under
        if self.cuota_over is not None:
            return self.cuota_over
        if self.cuota_under is not None:
            return self.cuota_under
        return self.cuota

    @field_validator("temporadas")
    @classmethod
    def validar_temporadas(cls, valor: Optional[List[str]]) -> Optional[List[str]]:
        if valor is None:
            return valor
        if len(valor) == 0:
            raise ValueError("Debes seleccionar al menos una temporada.")
        if any(not temporada or not temporada.strip() for temporada in valor):
            raise ValueError("Las temporadas no pueden estar vacías.")
        return valor


class PeticionAnalisisEnVivo(PeticionAnalisis):
    """Solicitud para análisis en vivo con marcadores reales."""

    marcador_q1: Optional[str] = Field(None, description="Marcador Q1 (ej: 28-32)")
    marcador_q2: Optional[str] = Field(None, description="Marcador Q2 (ej: 25-24)")
    marcador_q3: Optional[str] = Field(None, description="Marcador Q3 (ej: 30-28)")
    peso_en_vivo: float = Field(0.5, ge=0.0, le=1.0, description="Peso del ajuste en vivo")


class PeticionCrearApuesta(BaseModel):
    """Solicitud para guardar una apuesta en la bitácora."""

    partido_id: Optional[str] = Field(None, description="ID opcional del partido")
    equipo_local: str = Field(..., min_length=1, description="Nombre del equipo local")
    equipo_visitante: str = Field(..., min_length=1, description="Nombre del equipo visitante")
    fecha_partido: Optional[date] = Field(None, description="Fecha del partido")
    mercado: Literal["Q1", "Q2", "Q3", "Q4", "COMPLETO"]
    lado: Literal["OVER", "UNDER"]
    linea: Decimal = Field(..., gt=0)
    cuota: Decimal = Field(..., ge=Decimal("1.01"))
    cuota_over: Optional[Decimal] = Field(None, ge=Decimal("1.01"))
    cuota_under: Optional[Decimal] = Field(None, ge=Decimal("1.01"))
    stake: Decimal = Field(..., gt=0)
    probabilidad_sistema: float = Field(..., ge=0.0, le=1.0)
    confianza_sistema: Literal["ALTA", "MEDIA", "BAJA"]
    valor_esperado: Optional[float] = None
    devig_metodo: Optional[str] = None
    modo_devig: Optional[str] = None
    devig_overround: Optional[float] = None
    devig_p_mkt_raw: Optional[float] = None
    devig_p_mkt_fair: Optional[float] = None
    devig_advertencias: Optional[List[str]] = None
    edge_real: Optional[float] = None
    kelly_full: Optional[float] = None
    kelly_fraccional: Optional[float] = None
    fraccion_kelly: Optional[float] = None
    stake_porcentaje: Optional[float] = None
    bankroll_momento: Optional[float] = None
    perfil_riesgo_usado: Optional[str] = None
    sizing_advertencias: Optional[List[str]] = None
    sizing_penalizaciones: Optional[Dict[str, float]] = None
    prediccion_media: Optional[float] = None
    prediccion_desviacion: Optional[float] = None
    razones: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("equipo_local", "equipo_visitante")
    @classmethod
    def validar_equipo(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El nombre del equipo no puede estar vacío.")
        return valor.strip()


class PeticionActualizarResultado(BaseModel):
    """Solicitud para actualizar el resultado de una apuesta."""

    resultado: Literal["GANADA", "PERDIDA", "PUSH", "ANULADA"]
    puntos_reales: Optional[Decimal] = Field(None, ge=0)

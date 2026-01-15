from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ModoVentana(str, Enum):
    TODAS_TEMPORADAS = "TODAS_TEMPORADAS"
    ULTIMAS_N_TEMPORADAS = "ULTIMAS_N_TEMPORADAS"
    ULTIMOS_N_PARTIDOS = "ULTIMOS_N_PARTIDOS"


class ModoCutoff(str, Enum):
    DIARIO = "DIARIO"
    SEMANAL = "SEMANAL"
    POR_BLOQUE = "POR_BLOQUE"


class Mercado(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    COMPLETO = "COMPLETO"


class ConfiguracionBacktest(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, use_enum_values=True)

    modo_ventana: ModoVentana = ModoVentana.TODAS_TEMPORADAS
    n_temporadas: int | None = None
    n_partidos_por_equipo: int | None = None
    excluir_pretemporada: bool = True

    modo_cutoff: ModoCutoff = ModoCutoff.DIARIO
    tamano_bloque: int | None = None

    mercados: list[Mercado] = Field(default_factory=lambda: [
        Mercado.Q1,
        Mercado.Q2,
        Mercado.Q3,
        Mercado.Q4,
        Mercado.COMPLETO,
    ])
    incluir_completo: bool = True

    usar_lineas_sinteticas: bool = False
    offsets_linea: list[float] | None = Field(default_factory=lambda: [0.0])

    fecha_inicio: date
    fecha_fin: date | None = None

    min_partidos_entrenamiento: int = 10
    min_temporadas_historia: int = 1

    @field_validator("mercados")
    @classmethod
    def _validar_mercados(cls, mercados: Iterable[Mercado]) -> list[Mercado]:
        mercados_list = list(mercados)
        if not mercados_list:
            raise ValueError("mercados no puede estar vacío")
        return mercados_list

    @field_validator("min_partidos_entrenamiento", "min_temporadas_historia")
    @classmethod
    def _validar_minimos(cls, valor: int) -> int:
        if valor <= 0:
            raise ValueError("los mínimos deben ser mayores a 0")
        return valor

    @field_validator("n_temporadas", "n_partidos_por_equipo", "tamano_bloque")
    @classmethod
    def _validar_no_negativos(cls, valor: int | None) -> int | None:
        if valor is not None and valor < 0:
            raise ValueError("los tamaños no pueden ser negativos")
        return valor

    @model_validator(mode="after")
    def _validar_reglas(self) -> "ConfiguracionBacktest":
        if self.fecha_fin is not None and self.fecha_inicio > self.fecha_fin:
            raise ValueError("fecha_inicio debe ser <= fecha_fin")

        if self.modo_cutoff == ModoCutoff.POR_BLOQUE:
            if self.tamano_bloque is None or self.tamano_bloque <= 0:
                raise ValueError("tamano_bloque debe ser > 0 para POR_BLOQUE")

        if self.modo_ventana == ModoVentana.ULTIMAS_N_TEMPORADAS:
            if self.n_temporadas is None or self.n_temporadas < 1:
                raise ValueError("n_temporadas debe ser >= 1 para ULTIMAS_N_TEMPORADAS")

        if self.modo_ventana == ModoVentana.ULTIMOS_N_PARTIDOS:
            if self.n_partidos_por_equipo is None or self.n_partidos_por_equipo < 1:
                raise ValueError(
                    "n_partidos_por_equipo debe ser >= 1 para ULTIMOS_N_PARTIDOS"
                )

        if self.usar_lineas_sinteticas:
            if not self.offsets_linea:
                raise ValueError("offsets_linea no puede estar vacío si usar_lineas_sinteticas")
            if 0 not in self.offsets_linea:
                raise ValueError("offsets_linea debe incluir 0")

        return self

    def to_json_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        return _ordenar_dict_recursivo(data)

    def to_json_string(self) -> str:
        return json.dumps(self.to_json_dict(), ensure_ascii=False, sort_keys=True)


def _ordenar_dict_recursivo(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: _ordenar_dict_recursivo(data[key]) for key in sorted(data.keys())}
    if isinstance(data, list):
        return [_ordenar_dict_recursivo(item) for item in data]
    if isinstance(data, date):
        return data.isoformat()
    return data

# -*- coding: utf-8 -*-
"""rutas_analisis.py — Endpoints de análisis."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from configuracion import CONFIGURACION
from motor import analizar_partido, cargar_modelo, resultado_a_dict
from motor.tipos import Ubicacion
from .excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion
from motor.utilidades import resolver_nombre_en_modelo
from .modelos_peticion import PeticionAnalisis, PeticionAnalisisEnVivo
from .modelos_respuesta import RespuestaAnalisis

router = APIRouter(prefix="/api", tags=["Análisis"])

_modelo_cache = None


def obtener_modelo():
    """Carga el modelo de predicción (con caché en memoria)."""
    global _modelo_cache
    if _modelo_cache is None:
        try:
            _modelo_cache = cargar_modelo(CONFIGURACION.ruta_modelo)
        except FileNotFoundError as exc:
            raise ErrorAnalisis(
                f"No se encontró el modelo en {CONFIGURACION.ruta_modelo}."
            ) from exc
        except Exception as exc:
            raise ErrorAnalisis("Error cargando el modelo de predicción.") from exc
    return _modelo_cache


def validar_equipos(modelo, equipo_local: str, equipo_visitante: str) -> None:
    """Valida que ambos equipos existan en el modelo."""
    equipos_modelo = set(modelo.obtener_equipos())
    equipo_local_resuelto = resolver_nombre_en_modelo(equipo_local, modelo.entidad_a_indice)
    equipo_visitante_resuelto = resolver_nombre_en_modelo(
        equipo_visitante,
        modelo.entidad_a_indice,
    )
    if equipo_local_resuelto is None:
        raise ErrorEquipoNoEncontrado(equipo_local, equipos_similares=sorted(equipos_modelo))
    if equipo_visitante_resuelto is None:
        raise ErrorEquipoNoEncontrado(equipo_visitante, equipos_similares=sorted(equipos_modelo))


def ejecutar_analisis(
    peticion: PeticionAnalisis,
    marcador_q1: Optional[str] = None,
    marcador_q2: Optional[str] = None,
    marcador_q3: Optional[str] = None,
    peso_en_vivo: float = 0.5,
) -> RespuestaAnalisis:
    """Ejecuta el análisis y retorna la respuesta de API."""
    modelo = obtener_modelo()
    validar_equipos(modelo, peticion.equipo_local, peticion.equipo_visitante)

    try:
        resultado = analizar_partido(
            modelo=modelo,
            equipo=peticion.equipo_local,
            rival=peticion.equipo_visitante,
            ubicacion=Ubicacion.LOCAL,
            mercado=peticion.mercado,
            linea=peticion.linea,
            cuota=peticion.cuota,
            marcador_q1=marcador_q1,
            marcador_q2=marcador_q2,
            marcador_q3=marcador_q3,
            peso_en_vivo=peso_en_vivo,
        )
    except ValueError as exc:
        raise ErrorValidacion(str(exc)) from exc
    except Exception as exc:
        raise ErrorAnalisis("No se pudo completar el análisis.") from exc

    return RespuestaAnalisis(
        exito=True,
        datos=resultado_a_dict(resultado),
    )


@router.post(
    "/analizar",
    summary="Analizar partido",
    response_model=RespuestaAnalisis,
)
async def analizar(peticion: PeticionAnalisis) -> RespuestaAnalisis:
    """Analiza un partido en modalidad pre-partido."""
    return ejecutar_analisis(peticion)


@router.post(
    "/analizar-en-vivo",
    summary="Analizar partido en vivo",
    response_model=RespuestaAnalisis,
)
async def analizar_en_vivo(peticion: PeticionAnalisisEnVivo) -> RespuestaAnalisis:
    """Analiza un partido usando marcadores reales de cuartos previos."""
    if not (peticion.marcador_q1 or peticion.marcador_q2 or peticion.marcador_q3):
        raise ErrorValidacion("Debes enviar al menos un marcador (Q1, Q2 o Q3).")

    return ejecutar_analisis(
        peticion,
        marcador_q1=peticion.marcador_q1,
        marcador_q2=peticion.marcador_q2,
        marcador_q3=peticion.marcador_q3,
        peso_en_vivo=peticion.peso_en_vivo,
    )

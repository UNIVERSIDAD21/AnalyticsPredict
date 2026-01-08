# -*- coding: utf-8 -*-
"""
rutas_analisis.py — Endpoints de análisis ACTUALIZADO.

CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
- Ya NO usa cargar_modelo() desde archivo .npz
- Usa obtener_modelo() del sistema de auto-entrenamiento
- El modelo siempre está actualizado con los últimos datos de la BD
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

# ═══════════════════════════════════════════════════════════════════════════════
# CAMBIO PRINCIPAL: Usar motor_autoentrenamiento en lugar de cargar desde archivo
# ═══════════════════════════════════════════════════════════════════════════════
# ANTES:
# from configuracion import CONFIGURACION
# from motor import analizar_partido, cargar_modelo, resultado_a_dict
# 
# AHORA:
from motor import analizar_partido, resultado_a_dict
from motor_autoentrenamiento import EntrenadorBD, ModeloEnMemoria, obtener_modelo  # ← NUEVO
from motor.tipos import Ubicacion
from motor.utilidades import resolver_nombre_en_modelo
from db import obtener_pool
from .excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion
from .modelos_peticion import PeticionAnalisis, PeticionAnalisisEnVivo
from .modelos_respuesta import RespuestaAnalisis

router = APIRouter(prefix="/api", tags=["Análisis"])

# ═══════════════════════════════════════════════════════════════════════════════
# YA NO NECESITAMOS CACHÉ MANUAL
# El GestorModelo mantiene el modelo en memoria automáticamente
# ═══════════════════════════════════════════════════════════════════════════════
# ELIMINADO:
# _modelo_cache = None
# def obtener_modelo():
#     global _modelo_cache
#     if _modelo_cache is None:
#         _modelo_cache = cargar_modelo(CONFIGURACION.ruta_modelo)
#     return _modelo_cache


def validar_equipos(modelo, equipo_local: str, equipo_visitante: str) -> None:
    """Valida que ambos equipos existan en el modelo."""
    equipos_modelo = set(modelo.obtener_equipos())
    
    equipo_local_resuelto = resolver_nombre_en_modelo(
        equipo_local, 
        modelo.entidad_a_indice
    )
    equipo_visitante_resuelto = resolver_nombre_en_modelo(
        equipo_visitante,
        modelo.entidad_a_indice,
    )
    
    if equipo_local_resuelto is None:
        raise ErrorEquipoNoEncontrado(
            equipo_local, 
            equipos_similares=sorted(equipos_modelo)
        )
    
    if equipo_visitante_resuelto is None:
        raise ErrorEquipoNoEncontrado(
            equipo_visitante, 
            equipos_similares=sorted(equipos_modelo)
        )


def ejecutar_analisis(
    peticion: PeticionAnalisis,
    marcador_q1: Optional[str] = None,
    marcador_q2: Optional[str] = None,
    marcador_q3: Optional[str] = None,
    peso_en_vivo: float = 0.5,
) -> RespuestaAnalisis:
    """Ejecuta el análisis y retorna la respuesta de API."""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CAMBIO: obtener_modelo() ahora viene de motor_autoentrenamiento
    # Siempre retorna el modelo más actualizado desde BD
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        if peticion.temporadas:
            entrenador = EntrenadorBD(obtener_pool())
            datos_modelo = entrenador.entrenar(temporadas=peticion.temporadas)
            modelo = ModeloEnMemoria(datos_modelo)
        else:
            modelo = obtener_modelo()
    except RuntimeError as exc:
        raise ErrorAnalisis(
            "El modelo no está disponible. "
            "Verifica que el servidor se haya inicializado correctamente."
        ) from exc
    except ValueError as exc:
        raise ErrorValidacion(str(exc)) from exc
    
    # Validar equipos
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
    """
    Analiza un partido en modalidad pre-partido.
    
    El modelo se entrena automáticamente desde la base de datos
    y siempre contiene los datos más recientes.
    """
    return ejecutar_analisis(peticion)


@router.post(
    "/analizar-en-vivo",
    summary="Analizar partido en vivo",
    response_model=RespuestaAnalisis,
)
async def analizar_en_vivo(peticion: PeticionAnalisisEnVivo) -> RespuestaAnalisis:
    """
    Analiza un partido usando marcadores reales de cuartos previos.
    
    Proporciona ajustes en tiempo real basados en el rendimiento
    actual del partido.
    """
    if not (peticion.marcador_q1 or peticion.marcador_q2 or peticion.marcador_q3):
        raise ErrorValidacion("Debes enviar al menos un marcador (Q1, Q2 o Q3).")

    return ejecutar_analisis(
        peticion,
        marcador_q1=peticion.marcador_q1,
        marcador_q2=peticion.marcador_q2,
        marcador_q3=peticion.marcador_q3,
        peso_en_vivo=peticion.peso_en_vivo,
    )

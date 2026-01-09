# -*- coding: utf-8 -*-
"""
rutas_analisis.py — Endpoints de análisis ACTUALIZADO.

CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
- Ya NO usa cargar_modelo() desde archivo .npz
- Usa obtener_modelo() del sistema de auto-entrenamiento
- El modelo siempre está actualizado con los últimos datos de la BD
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from psycopg.rows import dict_row

# ═══════════════════════════════════════════════════════════════════════════════
# CAMBIO PRINCIPAL: Usar motor_autoentrenamiento en lugar de cargar desde archivo
# ═══════════════════════════════════════════════════════════════════════════════
# ANTES:
# from configuracion import CONFIGURACION
# from motor import analizar_partido, cargar_modelo, resultado_a_dict
# 
# AHORA:
from motor import analizar_partido, resultado_a_dict
from motor.registro_predicciones import registrar_prediccion
from motor_autoentrenamiento import EntrenadorBD, ModeloEnMemoria, obtener_modelo  # ← NUEVO
from motor.tipos import ConfiguracionSizing, Ubicacion
from motor.utilidades import resolver_nombre_en_modelo
from db import obtener_pool
from .dependencias import obtener_usuario_id_opcional
from .excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion
from .modelos_peticion import PeticionAnalisis, PeticionAnalisisEnVivo
from .modelos_respuesta import RespuestaAnalisis

router = APIRouter(prefix="/api", tags=["Análisis"])
logger = logging.getLogger(__name__)

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


def _obtener_config_usuario(usuario_id: Optional[UUID]) -> Optional[dict]:
    if usuario_id is None:
        return None
    with obtener_pool().connection() as conexion:
        with conexion.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT bankroll_actual, perfil_riesgo_default, config_sizing
                FROM usuarios
                WHERE id = %s
                """,
                [str(usuario_id)],
            )
            return cursor.fetchone()


def _construir_configuracion_sizing(
    peticion: PeticionAnalisis,
    datos_usuario: Optional[dict],
) -> Optional[ConfiguracionSizing]:
    bankroll_override = (
        peticion.bankroll if "bankroll" in peticion.model_fields_set else None
    )
    perfil_override = (
        peticion.perfil_riesgo if "perfil_riesgo" in peticion.model_fields_set else None
    )

    bankroll_usuario = datos_usuario.get("bankroll_actual") if datos_usuario else None
    perfil_default = datos_usuario.get("perfil_riesgo_default") if datos_usuario else None
    config_sizing_usuario = datos_usuario.get("config_sizing") if datos_usuario else None

    bankroll = bankroll_override if bankroll_override is not None else bankroll_usuario
    if bankroll is None:
        return None

    return ConfiguracionSizing.construir_desde_fuentes(
        config_sizing_usuario=config_sizing_usuario,
        bankroll_override=bankroll,
        perfil_override=perfil_override,
        bankroll_usuario=bankroll_usuario,
        perfil_default=perfil_default,
    )


def _validar_entrada_devig(peticion: PeticionAnalisis) -> List[str]:
    advertencias: List[str] = []
    tiene_over = peticion.cuota_over is not None
    tiene_under = peticion.cuota_under is not None

    if tiene_over and tiene_under:
        p_over = 1.0 / peticion.cuota_over
        p_under = 1.0 / peticion.cuota_under
        overround = p_over + p_under
        if overround < 1.0:
            advertencias.append("OVERROUND_BAJO_POSIBLE_ARB")
        if overround > 1.10:
            advertencias.append("OVERROUND_ALTO_REVISAR")
    elif tiene_over ^ tiene_under:
        if peticion.modo_devig == "estricto":
            advertencias.append("DEVIG_ESTRICTO_REQUIERE_AMBAS_CUOTAS")
        else:
            advertencias.append("DEVIG_ESTIMADO_PENALIZA")

    return advertencias


def _validar_peticion_analisis(peticion: PeticionAnalisis) -> List[str]:
    advertencias: List[str] = []
    cuotas_presentes = any(
        cuota is not None
        for cuota in (peticion.cuota, peticion.cuota_over, peticion.cuota_under)
    )

    if cuotas_presentes and "lado" not in peticion.model_fields_set:
        raise ErrorValidacion("Debes indicar lado cuando envías cuotas.")

    if peticion.lado not in {"OVER", "UNDER"}:
        raise ErrorValidacion("lado debe ser OVER o UNDER.")

    if peticion.mercado not in {"Q1", "Q2", "Q3", "Q4", "COMPLETO"}:
        raise ErrorValidacion("mercado debe ser Q1, Q2, Q3, Q4 o COMPLETO.")

    if peticion.modo_devig not in {"estricto", "estimado"}:
        raise ErrorValidacion("modo_devig debe ser estricto o estimado.")

    if peticion.perfil_riesgo is not None and peticion.perfil_riesgo not in {
        "CONSERVADOR",
        "MEDIO",
        "AGRESIVO",
    }:
        raise ErrorValidacion("perfil_riesgo debe ser CONSERVADOR, MEDIO o AGRESIVO.")

    if peticion.linea is not None and peticion.linea <= 0:
        raise ErrorValidacion("linea debe ser mayor a 0.")

    if peticion.bankroll is not None and peticion.bankroll <= 0:
        raise ErrorValidacion("bankroll debe ser mayor a 0.")

    for cuota in (peticion.cuota, peticion.cuota_over, peticion.cuota_under):
        if cuota is not None and cuota <= 1.0:
            raise ErrorValidacion("Las cuotas deben ser mayores a 1.0.")

    advertencias.extend(_validar_entrada_devig(peticion))
    return advertencias


def _colectar_advertencias_resultado(resultado) -> List[str]:
    advertencias: List[str] = []
    if resultado.analisis_mercado and resultado.analisis_mercado.datos_devig:
        advertencias.extend(resultado.analisis_mercado.datos_devig.advertencias)
    if resultado.mejor_apuesta and resultado.mejor_apuesta.datos_devig:
        advertencias.extend(resultado.mejor_apuesta.datos_devig.advertencias)
    if resultado.mejor_apuesta and resultado.mejor_apuesta.sizing:
        advertencias.extend(resultado.mejor_apuesta.sizing.advertencias)
    return advertencias


def _extraer_contexto_registro(peticion: PeticionAnalisis) -> Optional[Dict[str, Any]]:
    campos = {
        "partido_id": peticion.partido_id,
        "temporada_id": peticion.temporada_id,
        "equipo_local_id": peticion.equipo_local_id,
        "equipo_visitante_id": peticion.equipo_visitante_id,
        "fecha_partido": peticion.fecha_partido,
        "tipo_partido": peticion.tipo_partido,
    }
    faltantes = [clave for clave, valor in campos.items() if valor is None]
    if faltantes:
        logger.warning(
            "Predicción no registrable por falta de contexto: %s",
            ", ".join(faltantes),
        )
        return None
    return campos


def ejecutar_analisis(
    peticion: PeticionAnalisis,
    marcador_q1: Optional[str] = None,
    marcador_q2: Optional[str] = None,
    marcador_q3: Optional[str] = None,
    peso_en_vivo: float = 0.5,
    usuario_id: Optional[UUID] = None,
) -> RespuestaAnalisis:
    """Ejecuta el análisis y retorna la respuesta de API."""
    advertencias_entrada = _validar_peticion_analisis(peticion)
    
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

    datos_usuario = _obtener_config_usuario(usuario_id)
    bankroll_override = (
        peticion.bankroll if "bankroll" in peticion.model_fields_set else None
    )
    perfil_override = (
        peticion.perfil_riesgo if "perfil_riesgo" in peticion.model_fields_set else None
    )

    try:
        resultado = analizar_partido(
            modelo=modelo,
            equipo=peticion.equipo_local,
            rival=peticion.equipo_visitante,
            ubicacion=Ubicacion.LOCAL,
            mercado=peticion.mercado,
            linea=peticion.linea,
            cuota=peticion.cuota_analisis,
            cuota_over=peticion.cuota_over,
            cuota_under=peticion.cuota_under,
            lado=peticion.lado,
            modo_devig=peticion.modo_devig,
            bankroll_override=bankroll_override,
            perfil_riesgo_override=perfil_override,
            usuario_config=datos_usuario,
            marcador_q1=marcador_q1,
            marcador_q2=marcador_q2,
            marcador_q3=marcador_q3,
            peso_en_vivo=peso_en_vivo,
        )
    except ValueError as exc:
        raise ErrorValidacion(str(exc)) from exc
    except Exception as exc:
        raise ErrorAnalisis("No se pudo completar el análisis.") from exc

    contexto_registro = _extraer_contexto_registro(peticion)
    if contexto_registro and resultado.candidatos:
        modelo_version_id = getattr(modelo, "version", None)
        if modelo_version_id is None or not isinstance(modelo_version_id, int):
            logger.warning(
                "No se encontró modelo_version_id válido para registrar predicción: %s",
                modelo_version_id,
            )
        else:
            for candidato in resultado.candidatos:
                registrar_prediccion(
                    partido_id=contexto_registro["partido_id"],
                    temporada_id=contexto_registro["temporada_id"],
                    equipo_local_id=contexto_registro["equipo_local_id"],
                    equipo_visitante_id=contexto_registro["equipo_visitante_id"],
                    fecha_partido=contexto_registro["fecha_partido"],
                    tipo_partido=contexto_registro["tipo_partido"],
                    mercado=candidato.cuarto,
                    lado=candidato.lado.value,
                    linea=candidato.linea,
                    linea_es_sintetica=False,
                    origen="API_USUARIO",
                    modelo_version_id=modelo_version_id,
                    calibrador_id=None,
                    media_predicha=candidato.media,
                    desviacion_predicha=candidato.desviacion,
                    p_raw=candidato.probabilidad,
                    cuota=candidato.cuota,
                    cuota_over=candidato.cuota_over,
                    cuota_under=candidato.cuota_under,
                    calibrador_metodo=None,
                    p_calibrada=None,
                )
    datos_respuesta = resultado_a_dict(resultado)
    datos_respuesta.pop("advertencias", None)
    if datos_respuesta.get("mejor_apuesta") is not None:
        mejor = datos_respuesta["mejor_apuesta"]
        if isinstance(mejor, dict):
            mejor["cuota"] = peticion.cuota_analisis
            mejor["cuota_over"] = peticion.cuota_over
            mejor["cuota_under"] = peticion.cuota_under

    advertencias_motor = _colectar_advertencias_resultado(resultado)
    advertencias = list(dict.fromkeys(advertencias_entrada + advertencias_motor))
    return RespuestaAnalisis(
        exito=True,
        datos=datos_respuesta,
        advertencias=advertencias or None,
    )


@router.post(
    "/analizar",
    summary="Analizar partido",
    response_model=RespuestaAnalisis,
)
async def analizar(
    peticion: PeticionAnalisis,
    usuario_id: Optional[UUID] = Depends(obtener_usuario_id_opcional),
) -> RespuestaAnalisis:
    """
    Analiza un partido en modalidad pre-partido.
    
    El modelo se entrena automáticamente desde la base de datos
    y siempre contiene los datos más recientes.
    """
    return ejecutar_analisis(peticion, usuario_id=usuario_id)


@router.post(
    "/analizar-en-vivo",
    summary="Analizar partido en vivo",
    response_model=RespuestaAnalisis,
)
async def analizar_en_vivo(
    peticion: PeticionAnalisisEnVivo,
    usuario_id: Optional[UUID] = Depends(obtener_usuario_id_opcional),
) -> RespuestaAnalisis:
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
        usuario_id=usuario_id,
    )

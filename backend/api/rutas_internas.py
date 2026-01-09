# -*- coding: utf-8 -*-
"""
rutas_internas.py — Endpoints internos para operaciones de sistema.

Incluye:
- Resolución de predicciones (Tarea 6)
- Estadísticas de predicciones
- Operaciones administrativas
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backtesting.configuracion import ConfiguracionBacktest
from backtesting.ejecutor import (
    ejecutar_backtest,
    obtener_estado_backtest,
    obtener_resultado_backtest,
)
from motor.resolucion_predicciones import (
    resolver_predicciones,
    obtener_estadisticas_predicciones,
    obtener_predicciones_pendientes_por_mercado,
)

router = APIRouter(prefix="/api/interno", tags=["Interno"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS DE PETICIÓN/RESPUESTA
# ═══════════════════════════════════════════════════════════════════════════════


class PeticionResolverPredicciones(BaseModel):
    """Parámetros para resolver predicciones."""

    limite: int = Field(default=1000, gt=0, le=10000, description="Batch size máximo")
    mercado: Optional[str] = Field(
        default=None,
        pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$",
        description="Filtrar por mercado específico",
    )
    origen: Optional[str] = Field(
        default=None,
        description="Filtrar por origen (API_USUARIO, BACKTEST_BATCH, etc.)",
    )
    solo_hasta_fecha: Optional[date] = Field(
        default=None, description="Solo resolver hasta esta fecha (YYYY-MM-DD)"
    )
    force: bool = Field(
        default=False,
        description="Re-resolver predicciones ya resueltas (peligroso)",
    )


class RespuestaResolucion(BaseModel):
    """Respuesta del proceso de resolución."""

    exito: bool
    resumen: dict
    mensaje: str


class RespuestaEstadisticas(BaseModel):
    """Estadísticas de predicciones."""

    exito: bool
    estadisticas: dict


class PeticionBacktest(BaseModel):
    """Petición para iniciar un backtest."""

    configuracion: ConfiguracionBacktest
    ejecutar_sincrono: bool = Field(
        default=True,
        description="Si true, ejecuta el backtest en la misma petición.",
    )


class RespuestaBacktest(BaseModel):
    """Respuesta genérica para backtest."""

    exito: bool
    backtest_id: str
    estado: str
    detalle: dict | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE RESOLUCIÓN DE PREDICCIONES
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/resolver-predicciones",
    response_model=RespuestaResolucion,
    summary="Resolver predicciones pendientes",
    description="""
    Ejecuta el proceso de resolución de predicciones pendientes.

    Toma predicciones de `predicciones_registradas` donde `resuelto=false`
    y las resuelve usando los datos reales de la tabla `partidos`.

    **IDEMPOTENCIA**: Correr múltiples veces produce el mismo resultado.
    Predicciones ya resueltas no se tocan (a menos que force=True).

    **REGLAS**:
    - Solo resuelve si el partido tiene datos completos
    - PUSH (valor_real == linea): outcome_binario=NULL pero resuelto=True
    - No hay data leakage: solo usa datos de partidos ya terminados
    """,
)
async def resolver_predicciones_endpoint(
    peticion: PeticionResolverPredicciones,
) -> RespuestaResolucion:
    """Resuelve predicciones pendientes."""
    logger.info(
        "Iniciando resolución de predicciones: limite=%d mercado=%s origen=%s hasta=%s force=%s",
        peticion.limite,
        peticion.mercado,
        peticion.origen,
        peticion.solo_hasta_fecha,
        peticion.force,
    )

    try:
        resumen = resolver_predicciones(
            limite=peticion.limite,
            mercado=peticion.mercado,
            origen=peticion.origen,
            solo_hasta_fecha=peticion.solo_hasta_fecha,
            force=peticion.force,
        )

        mensaje = f"Resolución completada: {resumen.resueltas} resueltas"
        if resumen.push > 0:
            mensaje += f", {resumen.push} PUSH"
        if resumen.pendientes > 0:
            mensaje += f", {resumen.pendientes} pendientes (datos incompletos)"
        if resumen.errores > 0:
            mensaje += f", {resumen.errores} errores"

        return RespuestaResolucion(
            exito=True,
            resumen=resumen.to_dict(),
            mensaje=mensaje,
        )

    except Exception as e:
        logger.exception("Error en resolución de predicciones")
        return RespuestaResolucion(
            exito=False,
            resumen={},
            mensaje=f"Error: {str(e)}",
        )


@router.get(
    "/estadisticas-predicciones",
    response_model=RespuestaEstadisticas,
    summary="Estadísticas de predicciones",
    description="Obtiene estadísticas actuales de predicciones registradas.",
)
async def estadisticas_predicciones_endpoint() -> RespuestaEstadisticas:
    """Obtiene estadísticas de predicciones."""
    try:
        estadisticas = obtener_estadisticas_predicciones()
        pendientes_por_mercado = obtener_predicciones_pendientes_por_mercado()

        estadisticas["pendientes_por_mercado"] = pendientes_por_mercado

        return RespuestaEstadisticas(
            exito=True,
            estadisticas=estadisticas,
        )

    except Exception as e:
        logger.exception("Error obteniendo estadísticas de predicciones")
        return RespuestaEstadisticas(
            exito=False,
            estadisticas={"error": str(e)},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE BACKTEST WALK-FORWARD
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/backtest",
    response_model=RespuestaBacktest,
    summary="Iniciar backtest walk-forward",
    description="Crea y ejecuta un backtest walk-forward con tracking en BD.",
)
async def iniciar_backtest_endpoint(peticion: PeticionBacktest) -> RespuestaBacktest:
    if not peticion.ejecutar_sincrono:
        raise HTTPException(
            status_code=501,
            detail="Ejecución asíncrona no implementada en este entorno.",
        )

    try:
        resultado = ejecutar_backtest(peticion.configuracion)
        return RespuestaBacktest(
            exito=True,
            backtest_id=str(resultado.backtest_id),
            estado=resultado.estado,
            detalle={
                "iteraciones_completadas": resultado.iteraciones_completadas,
                "iteraciones_fallidas": resultado.iteraciones_fallidas,
                "total_predicciones_generadas": resultado.total_predicciones_generadas,
            },
        )
    except Exception as exc:
        logger.exception("Error ejecutando backtest")
        return RespuestaBacktest(
            exito=False,
            backtest_id="",
            estado="FALLIDO",
            detalle={"error": str(exc)},
        )


@router.get(
    "/backtest/{backtest_id}/estado",
    response_model=RespuestaBacktest,
    summary="Estado de ejecución de backtest",
)
async def estado_backtest_endpoint(backtest_id: str) -> RespuestaBacktest:
    try:
        estado = obtener_estado_backtest(backtest_id)
        return RespuestaBacktest(
            exito=True,
            backtest_id=str(estado["id"]),
            estado=estado["estado"],
            detalle=estado,
        )
    except Exception as exc:
        logger.exception("Error consultando estado de backtest")
        return RespuestaBacktest(
            exito=False,
            backtest_id=backtest_id,
            estado="ERROR",
            detalle={"error": str(exc)},
        )


@router.get(
    "/backtest/{backtest_id}/resultado",
    response_model=RespuestaBacktest,
    summary="Resultado de ejecución de backtest",
)
async def resultado_backtest_endpoint(backtest_id: str) -> RespuestaBacktest:
    try:
        resultado = obtener_resultado_backtest(backtest_id)
        return RespuestaBacktest(
            exito=True,
            backtest_id=str(resultado["id"]),
            estado=resultado["estado"],
            detalle=resultado,
        )
    except Exception as exc:
        logger.exception("Error consultando resultado de backtest")
        return RespuestaBacktest(
            exito=False,
            backtest_id=backtest_id,
            estado="ERROR",
            detalle={"error": str(exc)},
        )

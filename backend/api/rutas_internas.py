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
from db import obtener_pool
from backtesting.ejecutor import (
    ejecutar_backtest,
    obtener_estado_backtest,
    obtener_resultado_backtest,
)
from motor.alertas_calibracion import (
    evaluar_alertas_calibracion,
    listar_alertas_calibracion,
    resolver_alerta_calibracion,
)
from motor.recalibracion import (
    recalibrar_mercado,
    sugerir_recalibracion,
    listar_calibradores,
)
from motor.resolucion_predicciones import (
    resolver_predicciones,
    obtener_estadisticas_predicciones,
    obtener_predicciones_pendientes_por_mercado,
)
from motor.resolucion_predicciones_futbol import resolver_predicciones_futbol

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


class PeticionResolverPrediccionesFutbol(BaseModel):
    """Parámetros para resolver predicciones de fútbol."""

    limite: int = Field(default=2000, gt=0, le=20000, description="Batch size máximo")
    mercado: Optional[str] = Field(
        default=None,
        description="Filtrar por mercado de fútbol (opcional)",
    )
    solo_hasta_fecha: Optional[date] = Field(
        default=None, description="Solo resolver hasta esta fecha (YYYY-MM-DD)"
    )
    force: bool = Field(
        default=False,
        description="Re-resolver predicciones ya resueltas (peligroso)",
    )


class RespuestaEstadisticas(BaseModel):
    """Estadísticas de predicciones."""

    exito: bool
    estadisticas: dict


class RespuestaCicloCalidad(BaseModel):
    exito: bool
    resumen_baloncesto: dict
    resumen_futbol: dict
    mensaje: str


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


class PeticionEvaluarAlertasCalibracion(BaseModel):
    """Parámetros para evaluar alertas de calibración."""

    mercado: str = Field(pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$")
    origen: str
    fecha_inicio: date
    fecha_fin: date
    modelo_version_id: Optional[int] = None


class RespuestaAlertasCalibracion(BaseModel):
    """Respuesta del evaluador de alertas."""

    exito: bool
    alertas: List[dict]
    mensaje: str


class PeticionSugerirRecalibracion(BaseModel):
    """Parámetros para sugerir recalibración."""

    mercado: str = Field(pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$")
    origen: str
    periodo_fin: date
    modelo_version_id: Optional[int] = None


class PeticionRecalibracion(BaseModel):
    """Parámetros para ejecutar recalibración."""

    mercado: str = Field(pattern="^(Q1|Q2|Q3|Q4|COMPLETO)$")
    origen: str
    cutoff_datos: date
    modelo_version_id: Optional[int] = None
    metodo: str = Field(default="platt")
    min_muestras: int = Field(default=100, ge=10)


class RespuestaRecalibracion(BaseModel):
    """Respuesta de recalibración."""

    exito: bool
    calibrador_id: Optional[str]
    creado: bool
    mensaje: str
    detalle: dict


class RespuestaSugerenciaRecalibracion(BaseModel):
    """Respuesta para sugerencias de recalibración."""

    exito: bool
    sugerida: bool
    motivo: str
    alertas: List[str]


class RespuestaListadoAlertas(BaseModel):
    """Listado de alertas."""

    exito: bool
    alertas: List[dict]


class PeticionResolverAlerta(BaseModel):
    """Parámetros para resolver una alerta de calibración."""

    alerta_id: str
    nota: Optional[str] = None


class RespuestaResolverAlerta(BaseModel):
    """Respuesta de resolver alerta."""

    exito: bool
    alerta_id: Optional[str]
    resuelta: bool
    mensaje: str


class RespuestaListadoCalibradores(BaseModel):
    """Listado de calibradores."""

    exito: bool
    calibradores: List[dict]


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


@router.post(
    "/resolver-predicciones-futbol",
    response_model=RespuestaResolucion,
    summary="Resolver predicciones pendientes (fútbol)",
    description="""
    Resuelve `predicciones_futbol` pendientes usando resultados reales de `partidos_futbol`.

    Reglas:
    - Solo resuelve partidos FINALIZADO.
    - Calcula valor_real por mercado (goles/corners/disparos).
    - outcome_binario = OVER/UNDER contra la línea.
    - PUSH cuando valor_real == línea.
    """,
)
async def resolver_predicciones_futbol_endpoint(
    peticion: PeticionResolverPrediccionesFutbol,
) -> RespuestaResolucion:
    logger.info(
        "Iniciando resolución fútbol: limite=%d mercado=%s hasta=%s force=%s",
        peticion.limite,
        peticion.mercado,
        peticion.solo_hasta_fecha,
        peticion.force,
    )

    try:
        resumen = resolver_predicciones_futbol(
            limite=peticion.limite,
            mercado=peticion.mercado,
            solo_hasta_fecha=peticion.solo_hasta_fecha,
            force=peticion.force,
        )

        mensaje = f"Resolución fútbol completada: {resumen.resueltas} resueltas"
        if resumen.push > 0:
            mensaje += f", {resumen.push} PUSH"
        if resumen.pendientes > 0:
            mensaje += f", {resumen.pendientes} pendientes"
        if resumen.sin_datos_partido > 0:
            mensaje += f", {resumen.sin_datos_partido} sin datos"
        if resumen.errores > 0:
            mensaje += f", {resumen.errores} errores"

        return RespuestaResolucion(
            exito=True,
            resumen=resumen.to_dict(),
            mensaje=mensaje,
        )
    except Exception as e:
        logger.exception("Error en resolución de predicciones fútbol")
        return RespuestaResolucion(
            exito=False,
            resumen={},
            mensaje=f"Error: {str(e)}",
        )


@router.post(
    "/ciclo-calidad",
    response_model=RespuestaCicloCalidad,
    summary="Ejecutar ciclo de calidad (resolver baloncesto + fútbol)",
)
async def ejecutar_ciclo_calidad(
    limite_baloncesto: int = Query(1000, ge=1, le=20000),
    limite_futbol: int = Query(2000, ge=1, le=20000),
) -> RespuestaCicloCalidad:
    try:
        resumen_b = resolver_predicciones(limite=limite_baloncesto)
        resumen_f = resolver_predicciones_futbol(limite=limite_futbol)

        mensaje = (
            f"Ciclo OK | baloncesto: {resumen_b.resueltas} resueltas "
            f"| futbol: {resumen_f.resueltas} resueltas"
        )
        return RespuestaCicloCalidad(
            exito=True,
            resumen_baloncesto=resumen_b.to_dict(),
            resumen_futbol=resumen_f.to_dict(),
            mensaje=mensaje,
        )
    except Exception as e:
        logger.exception("Error ejecutando ciclo de calidad")
        return RespuestaCicloCalidad(
            exito=False,
            resumen_baloncesto={},
            resumen_futbol={},
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


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE ALERTAS Y RECALIBRACIÓN
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/evaluar-alertas-calibracion",
    response_model=RespuestaAlertasCalibracion,
    summary="Evaluar alertas de calibración",
)
async def evaluar_alertas_calibracion_endpoint(
    peticion: PeticionEvaluarAlertasCalibracion,
) -> RespuestaAlertasCalibracion:
    try:
        alertas = evaluar_alertas_calibracion(
            mercado=peticion.mercado,
            origen=peticion.origen,
            fecha_inicio=peticion.fecha_inicio,
            fecha_fin=peticion.fecha_fin,
            modelo_version_id=peticion.modelo_version_id,
        )
        return RespuestaAlertasCalibracion(
            exito=True,
            alertas=alertas,
            mensaje=f"Se generaron {len(alertas)} alertas.",
        )
    except Exception as exc:
        logger.exception("Error evaluando alertas de calibración")
        return RespuestaAlertasCalibracion(
            exito=False,
            alertas=[],
            mensaje=f"Error: {str(exc)}",
        )


@router.get(
    "/alertas-calibracion",
    response_model=RespuestaListadoAlertas,
    summary="Listar alertas de calibración",
)
async def listar_alertas_calibracion_endpoint(
    mercado: Optional[str] = Query(default=None),
    origen: Optional[str] = Query(default=None),
    severidad: Optional[str] = Query(default=None),
    resuelta: Optional[bool] = Query(default=None),
) -> RespuestaListadoAlertas:
    try:
        alertas = listar_alertas_calibracion(
            mercado=mercado,
            origen=origen,
            severidad=severidad,
            resuelta=resuelta,
        )
        return RespuestaListadoAlertas(exito=True, alertas=alertas)
    except Exception as exc:
        logger.exception("Error listando alertas de calibración")
        return RespuestaListadoAlertas(exito=False, alertas=[])


@router.post(
    "/alertas-calibracion/resolver",
    response_model=RespuestaResolverAlerta,
    summary="Resolver alerta de calibración",
)
async def resolver_alerta_calibracion_endpoint(
    peticion: PeticionResolverAlerta,
) -> RespuestaResolverAlerta:
    try:
        resultado = resolver_alerta_calibracion(
            obtener_pool(),
            alerta_id=peticion.alerta_id,
            nota=peticion.nota,
        )
        return RespuestaResolverAlerta(
            exito=True,
            alerta_id=str(resultado["alerta_id"]),
            resuelta=bool(resultado["resuelta"]),
            mensaje="Alerta resuelta.",
        )
    except Exception as exc:
        logger.exception("Error resolviendo alerta de calibración")
        return RespuestaResolverAlerta(
            exito=False,
            alerta_id=None,
            resuelta=False,
            mensaje=f"Error: {str(exc)}",
        )


@router.post(
    "/sugerir-recalibracion",
    response_model=RespuestaSugerenciaRecalibracion,
    summary="Sugerir recalibración por alertas",
)
async def sugerir_recalibracion_endpoint(
    peticion: PeticionSugerirRecalibracion,
) -> RespuestaSugerenciaRecalibracion:
    try:
        resultado = sugerir_recalibracion(
            mercado=peticion.mercado,
            origen=peticion.origen,
            periodo_fin=peticion.periodo_fin,
            modelo_version_id=peticion.modelo_version_id,
        )
        return RespuestaSugerenciaRecalibracion(
            exito=True,
            sugerida=resultado["sugerida"],
            motivo=resultado["motivo"],
            alertas=resultado["alertas"],
        )
    except Exception as exc:
        logger.exception("Error sugiriendo recalibración")
        return RespuestaSugerenciaRecalibracion(
            exito=False,
            sugerida=False,
            motivo=f"Error: {str(exc)}",
            alertas=[],
        )


@router.post(
    "/recalibrar",
    response_model=RespuestaRecalibracion,
    summary="Ejecutar recalibración",
)
async def recalibrar_endpoint(peticion: PeticionRecalibracion) -> RespuestaRecalibracion:
    try:
        resultado = recalibrar_mercado(
            mercado=peticion.mercado,
            origen=peticion.origen,
            cutoff_datos=peticion.cutoff_datos,
            modelo_version_id=peticion.modelo_version_id,
            metodo=peticion.metodo,
            min_muestras=peticion.min_muestras,
        )
        return RespuestaRecalibracion(
            exito=True,
            calibrador_id=str(resultado.calibrador_id) if resultado.calibrador_id else None,
            creado=resultado.creado,
            mensaje=resultado.mensaje,
            detalle=resultado.detalle,
        )
    except Exception as exc:
        logger.exception("Error ejecutando recalibración")
        return RespuestaRecalibracion(
            exito=False,
            calibrador_id=None,
            creado=False,
            mensaje=f"Error: {str(exc)}",
            detalle={},
        )


@router.get(
    "/calibradores",
    response_model=RespuestaListadoCalibradores,
    summary="Listar calibradores",
)
async def listar_calibradores_endpoint(
    mercado: Optional[str] = Query(default=None),
    activo: Optional[bool] = Query(default=None),
) -> RespuestaListadoCalibradores:
    try:
        calibradores = listar_calibradores(mercado=mercado, activo=activo)
        return RespuestaListadoCalibradores(exito=True, calibradores=calibradores)
    except Exception as exc:
        logger.exception("Error listando calibradores")
        return RespuestaListadoCalibradores(exito=False, calibradores=[])

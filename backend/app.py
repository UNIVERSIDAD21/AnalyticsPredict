# -*- coding: utf-8 -*-
"""
app.py — Punto de entrada FastAPI; serving y entrenamiento NBA separados.

El arranque solo carga un artefacto explícito. No entrena ni registra versiones.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from time import perf_counter
from uuid import uuid4
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from configuracion import CONFIGURACION
from api.rutas_analisis import router as router_analisis
from api.rutas_bitacora import router as router_bitacora
from api.rutas_equipos import router as router_equipos
from api.rutas_metricas import router as router_metricas
from api.rutas_partidos import router as router_partidos
from api.rutas_predicciones import router as router_predicciones
from api.rutas_backtest import router as router_backtest
from api.rutas_internas import router as router_interno
from api.rutas_combinadas import router as router_combinadas
from api.rutas_calidad import router as router_calidad
from api.rutas_explicabilidad import router as router_explicabilidad
from api.rutas_match_analysis_nba import router as router_match_analysis_nba

# Routers de Fútbol
from api.rutas_competiciones_futbol import router as router_competiciones_futbol
from api.rutas_equipos_futbol import router as router_equipos_futbol
from api.rutas_partidos_futbol import router as router_partidos_futbol
from api.rutas_analisis_futbol import router as router_analisis_futbol
from api.rutas_apuestas_futbol import router as router_apuestas_futbol
from api.rutas_metricas_futbol import router as router_metricas_futbol
from api.excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion
from db import cerrar_pool
from observabilidad_http import ObservabilidadHTTP

# ═══════════════════════════════════════════════════════════════════════════════
# Serving NBA y entrenamiento explícito
# ═══════════════════════════════════════════════════════════════════════════════
from motor_autoentrenamiento import (
    GestorModelo,
    obtener_modelo,
    obtener_metricas_modelo,
)

# Variable global para el gestor
_gestor_modelo = None
logger = logging.getLogger(__name__)
observabilidad_http = ObservabilidadHTTP()


def _respuesta_error(request: Request, status_code: int, codigo: str, mensaje: str, detalle=None):
    """Formato estándar de error para toda la API."""
    trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": codigo,
                "message": mensaje,
                "detail": detalle,
                "trace_id": trace_id,
            },
        },
    )


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    global _gestor_modelo
    
    print("=" * 60)
    print("🏀 ANALIZADOR NBA - Iniciando servidor...")
    print("=" * 60)
    print(f"   Entorno:     {CONFIGURACION.entorno}")
    print(f"   Debug:       {CONFIGURACION.debug}")
    print(f"   Host:        {CONFIGURACION.host}")
    print(f"   Puerto:      {CONFIGURACION.puerto}")
    print("=" * 60)
    print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Cargar artefacto local sin BD, entrenamiento ni escritura.
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        print("📦 Cargando artefacto NBA activo (sin entrenamiento)...")
        _gestor_modelo = GestorModelo.obtener_instancia()
        await _gestor_modelo.inicializar_async()
        if _gestor_modelo.esta_inicializado:
            modelo = obtener_modelo()
            print(f"✅ Modelo NBA cargado: ID {modelo.version}, {modelo.cantidad_equipos} equipos")
        else:
            print("⚠️ Sin artefacto NBA: API activa; análisis NBA no disponible hasta entrenamiento explícito")
    except Exception as e:
        logger.exception("No se pudo cargar el artefacto NBA: %s", e)
        print("⚠️ Artefacto NBA no disponible; API activa en modo degradado")

    print()
    print("🚀 Servidor listo para recibir peticiones")
    print(f"   Documentación: http://{CONFIGURACION.host}:{CONFIGURACION.puerto}/docs")
    print(f"   Estado modelo: http://{CONFIGURACION.host}:{CONFIGURACION.puerto}/api/modelo/estado")
    print()

    try:
        yield
    finally:
        cerrar_pool()
        print()
        print("👋 Cerrando servidor...")
        print("   Hasta pronto!")


app = FastAPI(
    title="Analizador NBA API",
    description="""
## 🏀 Sistema de Análisis de Apuestas NBA

Esta API permite analizar partidos de NBA y calcular probabilidades
de Over/Under para mercados por cuarto y juego completo.

**Características:**
- 📦 Serving desde artefacto versionado; entrenamiento solo explícito
- 📊 30 equipos NBA soportados
- ⚡ Modelo en memoria para respuestas rápidas
""",
    version="2.0.0",
    contact={
        "name": "Soporte",
        "email": "soporte@ejemplo.com",
    },
    license_info={
        "name": "Privado",
    },
    lifespan=ciclo_de_vida,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIGURACION.origenes_cors,
    # Hardening local DX: aceptar localhost/127.0.0.1 en cualquier puerto
    # para evitar bloqueos CORS intermitentes por cambio de host/puerto en frontend.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def middleware_trace_id(request: Request, call_next):
    """Asigna trace_id y captura métricas HTTP operativas mínimas."""
    trace_id = str(uuid4())
    request.state.trace_id = trace_id

    inicio = perf_counter()
    response = await call_next(request)
    latencia_ms = (perf_counter() - inicio) * 1000.0

    observabilidad_http.registrar(
        latencia_ms=latencia_ms,
        status_code=response.status_code,
    )
    response.headers["X-Trace-Id"] = trace_id
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# MANEJADORES DE ERRORES
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(ErrorEquipoNoEncontrado)
async def manejador_equipo_no_encontrado(request: Request, exc: ErrorEquipoNoEncontrado):
    """Maneja errores cuando un equipo no existe en el modelo."""
    detalle = {
        "equipo": exc.equipo,
        "sugerencia": "Usa GET /api/equipos para ver la lista de equipos válidos.",
    }
    return _respuesta_error(
        request,
        status_code=400,
        codigo="EQUIPO_NO_ENCONTRADO",
        mensaje=str(exc),
        detalle=detalle,
    )


@app.exception_handler(ErrorValidacion)
async def manejador_error_validacion(request: Request, exc: ErrorValidacion):
    """Maneja errores de validación de datos de entrada."""
    detalle = {"campo": exc.campo if hasattr(exc, "campo") else None}
    return _respuesta_error(
        request,
        status_code=422,
        codigo="ERROR_VALIDACION",
        mensaje=str(exc),
        detalle=detalle,
    )


@app.exception_handler(ErrorAnalisis)
async def manejador_error_analisis(request: Request, exc: ErrorAnalisis):
    """Maneja errores durante el análisis."""
    return _respuesta_error(
        request,
        status_code=500,
        codigo="ERROR_ANALISIS",
        mensaje=str(exc),
    )


@app.exception_handler(Exception)
async def manejador_error_general(request: Request, exc: Exception):
    """Maneja cualquier error no capturado."""
    trace_id = getattr(request.state, "trace_id", "sin-trace")
    logger.exception("Error interno no controlado trace_id=%s", trace_id)

    detalle = traceback.format_exc() if CONFIGURACION.debug else None
    return _respuesta_error(
        request,
        status_code=500,
        codigo="ERROR_INTERNO",
        mensaje="Ocurrió un error inesperado en el servidor.",
        detalle=detalle,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS
# ═══════════════════════════════════════════════════════════════════════════════

app.include_router(router_analisis)
app.include_router(router_equipos)
app.include_router(router_bitacora)
app.include_router(router_partidos)
app.include_router(router_interno)
app.include_router(router_metricas)
app.include_router(router_backtest)
app.include_router(router_predicciones)
app.include_router(router_combinadas)
app.include_router(router_calidad)
app.include_router(router_explicabilidad)
app.include_router(router_match_analysis_nba)

# Routers de Fútbol
app.include_router(router_competiciones_futbol)
app.include_router(router_equipos_futbol)
app.include_router(router_partidos_futbol)
app.include_router(router_analisis_futbol)
app.include_router(router_apuestas_futbol)
app.include_router(router_metricas_futbol)


@app.get(
    "/",
    tags=["Sistema"],
    summary="Información del servidor",
    description="Retorna información básica del servidor y links útiles.",
)
async def raiz():
    """Endpoint raíz que retorna información del servidor."""
    return {
        "nombre": "Analizador NBA API",
        "version": "2.0.0",
        "descripcion": "API para análisis de apuestas deportivas NBA",
        "estado": "activo",
        "timestamp": datetime.now().isoformat(),
        "enlaces": {
            "documentacion_swagger": "/docs",
            "documentacion_redoc": "/redoc",
            "health_check": "/salud",
            "equipos": "/api/equipos",
            "estado_modelo": "/api/modelo/estado",
        },
    }


@app.get(
    "/salud",
    tags=["Sistema"],
    summary="Verificación de salud",
    description="Endpoint para verificar que todos los servicios están funcionando.",
)
async def verificar_salud():
    """Health check del servidor."""
    try:
        modelo = obtener_modelo()
        modelo_ok = True
        equipos = modelo.cantidad_equipos
    except:
        modelo_ok = False
        equipos = 0

    return {
        "estado": "saludable" if modelo_ok else "degradado",
        "timestamp": datetime.now().isoformat(),
        "servicios": {
            "api": "activo",
            "modelo": "disponible" if modelo_ok else "NO DISPONIBLE",
            "equipos_en_modelo": equipos,
        },
        "configuracion": {
            "entorno": CONFIGURACION.entorno,
            "debug": CONFIGURACION.debug,
        },
    }


@app.get(
    "/api/interno/observabilidad-http",
    tags=["Interno"],
    summary="Resumen HTTP operativo mínimo",
    description=(
        "Entrega p95 de latencia, error rate 5xx y uptime del proceso. "
        "Sirve como dashboard técnico mínimo del bloque A5."
    ),
)
async def obtener_observabilidad_http(
    umbral_p95_ms: float = 800.0,
    umbral_error_rate: float = 0.05,
):
    return observabilidad_http.resumen(
        umbral_p95_ms=umbral_p95_ms,
        umbral_error_rate=umbral_error_rate,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# NUEVOS ENDPOINTS DE MODELO
# ═══════════════════════════════════════════════════════════════════════════════

@app.get(
    "/api/modelo/estado",
    tags=["Modelo"],
    summary="Estado del modelo",
    description="Retorna información detallada del modelo de predicción.",
)
async def estado_modelo():
    """Obtiene el estado actual del modelo."""
    try:
        metricas = obtener_metricas_modelo()
        modelo = obtener_modelo()
        
        return {
            "exito": True,
            "modelo": {
                "version": modelo.version,
                "equipos": modelo.cantidad_equipos,
                "fecha_entrenamiento": modelo.fecha_entrenamiento.isoformat(),
                "metricas": metricas,
            }
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
        }


@app.get(
    "/api/modelo/equipos",
    tags=["Modelo"],
    summary="Equipos en el modelo",
    description="Lista todos los equipos que el modelo puede analizar.",
)
async def equipos_modelo():
    """Lista los equipos del modelo."""
    try:
        modelo = obtener_modelo()
        equipos = modelo.obtener_equipos()
        
        return {
            "exito": True,
            "cantidad": len(equipos),
            "equipos": sorted(equipos),
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
        }


@app.post(
    "/api/modelo/cargar",
    tags=["Modelo"],
    summary="Cargar artefacto NBA ya publicado",
    description="Recarga un artefacto versionado sin entrenar ni escribir en la base de datos.",
)
async def cargar_modelo_publicado():
    """Activa en memoria una versión publicada por el comando explícito."""
    global _gestor_modelo
    try:
        if _gestor_modelo is None:
            _gestor_modelo = GestorModelo.obtener_instancia()
        modelo = _gestor_modelo.cargar_modelo_publicado()
        return {"exito": True, "modelo_version_id": modelo.version,
                "fecha_entrenamiento": modelo.fecha_entrenamiento.isoformat()}
    except Exception as e:
        return {"exito": False, "error": str(e)}


@app.post(
    "/api/modelo/reentrenar",
    tags=["Modelo"],
    summary="Forzar reentrenamiento",
    description="Fuerza el reentrenamiento del modelo desde la base de datos.",
)
async def reentrenar_modelo():
    """Fuerza el reentrenamiento del modelo."""
    global _gestor_modelo
    
    try:
        if _gestor_modelo is None:
            _gestor_modelo = GestorModelo.obtener_instancia()

        await _gestor_modelo.reentrenar_async()
        modelo = obtener_modelo()
        
        return {
            "exito": True,
            "mensaje": "Modelo reentrenado exitosamente",
            "modelo": {
                "version": modelo.version,
                "equipos": modelo.cantidad_equipos,
                "fecha_entrenamiento": modelo.fecha_entrenamiento.isoformat(),
            }
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=CONFIGURACION.host,
        port=CONFIGURACION.puerto,
        reload=CONFIGURACION.debug,
    )

# -*- coding: utf-8 -*-
"""
app.py — Punto de entrada de la aplicación FastAPI.
"""

from contextlib import asynccontextmanager
from datetime import datetime
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from configuracion import CONFIGURACION
from api.rutas_analisis import router as router_analisis
from api.rutas_equipos import router as router_equipos
from api.excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    print("=" * 60)
    print("🏀 ANALIZADOR NBA - Iniciando servidor...")
    print("=" * 60)
    print(f"   Entorno:     {CONFIGURACION.entorno}")
    print(f"   Debug:       {CONFIGURACION.debug}")
    print(f"   Host:        {CONFIGURACION.host}")
    print(f"   Puerto:      {CONFIGURACION.puerto}")
    print(f"   Modelo:      {CONFIGURACION.ruta_modelo}")
    print("=" * 60)

    if not os.path.exists(CONFIGURACION.ruta_modelo):
        print(f"⚠️  ADVERTENCIA: No se encontró el modelo en {CONFIGURACION.ruta_modelo}")
        print("   El servidor arrancará pero /api/analizar fallará.")
    else:
        print(f"✅ Modelo encontrado: {CONFIGURACION.ruta_modelo}")

    print("")
    print("🚀 Servidor listo para recibir peticiones")
    print(f"   Documentación: http://{CONFIGURACION.host}:{CONFIGURACION.puerto}/docs")
    print("")

    yield

    print("")
    print("👋 Cerrando servidor...")
    print("   Hasta pronto!")


app = FastAPI(
    title="Analizador NBA API",
    description="""
## 🏀 Sistema de Análisis de Apuestas NBA

Esta API permite analizar partidos de NBA y calcular probabilidades
de Over/Under para mercados por cuarto y juego completo.
""",
    version="1.0.0",
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErrorEquipoNoEncontrado)
async def manejador_equipo_no_encontrado(request: Request, exc: ErrorEquipoNoEncontrado):
    """Maneja errores cuando un equipo no existe en el modelo."""
    return JSONResponse(
        status_code=400,
        content={
            "exito": False,
            "error": {
                "tipo": "EQUIPO_NO_ENCONTRADO",
                "mensaje": str(exc),
                "equipo": exc.equipo,
            },
            "sugerencia": "Usa GET /api/equipos para ver la lista de equipos válidos.",
        },
    )


@app.exception_handler(ErrorValidacion)
async def manejador_error_validacion(request: Request, exc: ErrorValidacion):
    """Maneja errores de validación de datos de entrada."""
    return JSONResponse(
        status_code=422,
        content={
            "exito": False,
            "error": {
                "tipo": "ERROR_VALIDACION",
                "mensaje": str(exc),
                "campo": exc.campo if hasattr(exc, "campo") else None,
            },
        },
    )


@app.exception_handler(ErrorAnalisis)
async def manejador_error_analisis(request: Request, exc: ErrorAnalisis):
    """Maneja errores durante el análisis."""
    return JSONResponse(
        status_code=500,
        content={
            "exito": False,
            "error": {
                "tipo": "ERROR_ANALISIS",
                "mensaje": str(exc),
            },
        },
    )


@app.exception_handler(Exception)
async def manejador_error_general(request: Request, exc: Exception):
    """Maneja cualquier error no capturado."""
    if CONFIGURACION.debug:
        import traceback
        detalle = traceback.format_exc()
    else:
        detalle = "Contacta al administrador si el problema persiste."

    return JSONResponse(
        status_code=500,
        content={
            "exito": False,
            "error": {
                "tipo": "ERROR_INTERNO",
                "mensaje": "Ocurrió un error inesperado en el servidor.",
                "detalle": detalle if CONFIGURACION.debug else None,
            },
        },
    )


app.include_router(router_analisis)
app.include_router(router_equipos)


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
        "version": "1.0.0",
        "descripcion": "API para análisis de apuestas deportivas NBA",
        "estado": "activo",
        "timestamp": datetime.now().isoformat(),
        "enlaces": {
            "documentacion_swagger": "/docs",
            "documentacion_redoc": "/redoc",
            "health_check": "/salud",
            "equipos": "/api/equipos",
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
    modelo_existe = os.path.exists(CONFIGURACION.ruta_modelo)
    equipos_existe = os.path.exists(CONFIGURACION.ruta_equipos)

    servicios_ok = modelo_existe

    return {
        "estado": "saludable" if servicios_ok else "degradado",
        "timestamp": datetime.now().isoformat(),
        "servicios": {
            "api": "activo",
            "modelo": "disponible" if modelo_existe else "NO ENCONTRADO",
            "datos_equipos": "disponible" if equipos_existe else "no encontrado",
        },
        "configuracion": {
            "entorno": CONFIGURACION.entorno,
            "debug": CONFIGURACION.debug,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=CONFIGURACION.host,
        port=CONFIGURACION.puerto,
        reload=CONFIGURACION.debug,
    )

# -*- coding: utf-8 -*-
"""
app.py — Punto de entrada de la aplicación FastAPI con AUTO-ENTRENAMIENTO.

CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
- Integra el sistema de auto-entrenamiento desde base de datos
- El modelo se entrena automáticamente al iniciar
- Se reentrena cuando hay cambios en la tabla partidos
"""

from contextlib import asynccontextmanager
from datetime import datetime
import os

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
from api.excepciones import ErrorAnalisis, ErrorEquipoNoEncontrado, ErrorValidacion
from db import obtener_pool, cerrar_pool

# ═══════════════════════════════════════════════════════════════════════════════
# NUEVO: Importar sistema de auto-entrenamiento
# ═══════════════════════════════════════════════════════════════════════════════
from motor_autoentrenamiento import (
    GestorModelo,
    obtener_modelo,
    obtener_metricas_modelo,
)

# Variable global para el gestor
_gestor_modelo = None


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
    # NUEVO: Inicializar auto-entrenamiento desde BD
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        print("🔄 Inicializando modelo desde base de datos...")
        pool = obtener_pool()
        
        # Crear gestor y entrenar modelo
        _gestor_modelo = GestorModelo.obtener_instancia(pool)
        await _gestor_modelo.inicializar_async()
        
        # Mostrar info del modelo
        modelo = obtener_modelo()
        print()
        print("=" * 60)
        print("✅ MODELO ENTRENADO DESDE BASE DE DATOS")
        print("=" * 60)
        print(f"   Equipos en modelo: {modelo.cantidad_equipos}")
        print(f"   Versión: {modelo.version}")
        print(f"   Fecha entrenamiento: {modelo.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if modelo.cantidad_equipos < 30:
            print()
            print(f"⚠️  ADVERTENCIA: Solo {modelo.cantidad_equipos} equipos en el modelo")
            print("   La tabla 'partidos' puede no tener datos de todos los equipos.")
            print("   Ejecuta 'python poblar_partidos_completo.py' para solucionarlo.")
        
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR INICIALIZANDO MODELO")
        print("=" * 60)
        print(f"   Error: {e}")
        print()
        print("   Posibles causas:")
        print("   1. La tabla 'partidos' está vacía")
        print("   2. No hay conexión a la base de datos")
        print("   3. Las tablas no están creadas correctamente")
        print()
        print("   El servidor arrancará pero /api/analizar fallará.")
        print("=" * 60)

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
- 🔄 Auto-entrenamiento desde base de datos
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# MANEJADORES DE ERRORES
# ═══════════════════════════════════════════════════════════════════════════════

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
            return {
                "exito": False,
                "error": "Gestor de modelo no inicializado",
            }
        
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

# -*- coding: utf-8 -*-
"""
integracion_fastapi.py — Ejemplo de integración con FastAPI.

Este archivo muestra EXACTAMENTE cómo modificar tu app.py existente
para usar el sistema de auto-entrenamiento.

CAMBIOS NECESARIOS EN TU CÓDIGO:
================================

1. En app.py - Añadir imports y eventos de startup/shutdown
2. En rutas_analisis.py - Usar obtener_modelo() en lugar de cargar_modelo()
3. Ejecutar el SQL de triggers una vez en tu BD

"""

# ══════════════════════════════════════════════════════════════════════════════
# EJEMPLO: MODIFICACIONES PARA app.py
# ══════════════════════════════════════════════════════════════════════════════

EJEMPLO_APP_PY = '''
# -*- coding: utf-8 -*-
"""
app.py — Aplicación FastAPI con auto-entrenamiento de modelo.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import obtener_pool, cerrar_pool
from configuracion import CONFIGURACION

# NUEVO: Importar el sistema de auto-entrenamiento
from motor_autoentrenamiento import AutoReentrenador, obtener_modelo


# Variable global para el auto-reentrenador
_auto_reentrenador = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    
    - startup: Inicializa el pool de BD y el modelo
    - shutdown: Limpia recursos
    """
    global _auto_reentrenador
    
    # ═══════════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════════
    print("🚀 Iniciando servidor...")
    
    # 1. Obtener pool de conexiones
    pool = obtener_pool()
    
    # 2. NUEVO: Inicializar auto-reentrenamiento
    # Esto entrena el modelo desde la BD al iniciar y configura
    # la escucha de eventos para reentrenar automáticamente
    _auto_reentrenador = AutoReentrenador(pool)
    await _auto_reentrenador.iniciar()
    
    print("✅ Servidor listo")
    
    yield  # Aquí corre la aplicación
    
    # ═══════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ═══════════════════════════════════════════════════════════════════
    print("⏹️ Deteniendo servidor...")
    
    # Detener auto-reentrenamiento
    if _auto_reentrenador:
        await _auto_reentrenador.detener()
    
    # Cerrar pool de conexiones
    cerrar_pool()
    
    print("✅ Servidor detenido")


# Crear aplicación
app = FastAPI(
    title="Analizador NBA",
    description="API de predicción de partidos NBA con auto-entrenamiento",
    version="2.0.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIGURACION.origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
from rutas_analisis import router as router_analisis
from rutas_equipos import router as router_equipos
from rutas_bitacora import router as router_bitacora

app.include_router(router_analisis)
app.include_router(router_equipos)
app.include_router(router_bitacora)


# ═══════════════════════════════════════════════════════════════════════════
# NUEVOS ENDPOINTS DE DIAGNÓSTICO
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/modelo/estado")
async def obtener_estado_modelo():
    """
    Retorna el estado actual del modelo.
    
    Útil para verificar:
    - Cuántos equipos tiene el modelo
    - Cuándo se entrenó por última vez
    - Métricas de entrenamiento
    """
    from motor_autoentrenamiento import obtener_metricas_modelo
    return obtener_metricas_modelo()


@app.post("/api/modelo/reentrenar")
async def forzar_reentrenamiento_modelo():
    """
    Fuerza el reentrenamiento del modelo.
    
    Usar cuando se han insertado datos manualmente y se quiere
    actualizar el modelo inmediatamente sin esperar al trigger.
    """
    from motor_autoentrenamiento import GestorModelo
    
    gestor = GestorModelo.obtener_instancia()
    await gestor.reentrenar_async()
    
    return {
        "mensaje": "Modelo reentrenado exitosamente",
        "estado": gestor.obtener_estado(),
    }


@app.get("/api/modelo/equipos")
async def listar_equipos_modelo():
    """
    Lista todos los equipos que el modelo reconoce.
    
    Útil para verificar que todos los equipos están incluidos.
    """
    modelo = obtener_modelo()
    return {
        "cantidad": modelo.cantidad_equipos,
        "equipos": modelo.obtener_equipos(),
    }
'''


# ══════════════════════════════════════════════════════════════════════════════
# EJEMPLO: MODIFICACIONES PARA rutas_analisis.py
# ══════════════════════════════════════════════════════════════════════════════

EJEMPLO_RUTAS_ANALISIS_PY = '''
# -*- coding: utf-8 -*-
"""
rutas_analisis.py — Rutas de análisis MODIFICADAS para usar auto-entrenamiento.
"""

from fastapi import APIRouter, HTTPException

from modelos_peticion import PeticionAnalisis
from modelos_respuesta import RespuestaAnalisis

# CAMBIO: En lugar de importar cargar_modelo, usar obtener_modelo
# ANTES:  from nba_predictor_cuartos import cargar_modelo, analizar_partido
# AHORA:
from motor_autoentrenamiento import obtener_modelo
from nba_predictor_cuartos import analizar_partido, resultado_a_dict

from tipos import Ubicacion

router = APIRouter(prefix="/api", tags=["analisis"])


@router.post("/analizar", response_model=RespuestaAnalisis)
async def analizar(peticion: PeticionAnalisis):
    """
    Analiza un partido y genera predicciones.
    """
    try:
        # CAMBIO: Obtener modelo desde memoria (siempre actualizado)
        # ANTES:  modelo = cargar_modelo(CONFIGURACION.ruta_modelo)
        # AHORA:
        modelo = obtener_modelo()
        
        # Verificar que los equipos existen en el modelo
        if not modelo.contiene_equipo(peticion.equipo):
            raise HTTPException(
                status_code=400,
                detail=f"Equipo '{peticion.equipo}' no encontrado en el modelo. "
                       f"Equipos disponibles: {modelo.cantidad_equipos}"
            )
        
        if not modelo.contiene_equipo(peticion.rival):
            raise HTTPException(
                status_code=400,
                detail=f"Rival '{peticion.rival}' no encontrado en el modelo."
            )
        
        # Ejecutar análisis
        ubicacion = Ubicacion.LOCAL if peticion.es_local else Ubicacion.VISITANTE
        
        resultado = analizar_partido(
            modelo=modelo,
            equipo=peticion.equipo,
            rival=peticion.rival,
            ubicacion=ubicacion,
            mercado=peticion.mercado,
            linea=peticion.linea,
            cuota=peticion.cuota,
            marcador_q1=peticion.marcador_q1,
            marcador_q2=peticion.marcador_q2,
            marcador_q3=peticion.marcador_q3,
        )
        
        return resultado_a_dict(resultado)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
'''


# ══════════════════════════════════════════════════════════════════════════════
# SQL PARA EJECUTAR EN LA BASE DE DATOS (UNA SOLA VEZ)
# ══════════════════════════════════════════════════════════════════════════════

SQL_TRIGGERS = '''
-- ═══════════════════════════════════════════════════════════════════════════════
-- TRIGGERS PARA AUTO-REENTRENAMIENTO DEL MODELO NBA
-- ═══════════════════════════════════════════════════════════════════════════════
-- 
-- Ejecutar UNA SOLA VEZ en tu base de datos PostgreSQL.
-- Esto permite que el backend sea notificado cuando hay cambios en partidos.
-- ═══════════════════════════════════════════════════════════════════════════════

-- 1. Crear función de notificación
CREATE OR REPLACE FUNCTION notificar_cambio_partidos()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'partidos_actualizados',
        json_build_object(
            'operacion', TG_OP,
            'tabla', TG_TABLE_NAME,
            'timestamp', NOW()::text,
            'partido_id', COALESCE(NEW.id::text, OLD.id::text)
        )::text
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 2. Crear trigger
DROP TRIGGER IF EXISTS trigger_notificar_partidos ON partidos;

CREATE TRIGGER trigger_notificar_partidos
    AFTER INSERT OR UPDATE OR DELETE ON partidos
    FOR EACH ROW
    EXECUTE FUNCTION notificar_cambio_partidos();

-- 3. Verificar que se creó correctamente
SELECT 'Trigger creado exitosamente' as resultado
WHERE EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_notificar_partidos'
);
'''


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT DE VERIFICACIÓN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("GUÍA DE INTEGRACIÓN - AUTO-ENTRENAMIENTO NBA")
    print("=" * 70)
    print()
    print("PASO 1: Copiar archivos del motor")
    print("-" * 70)
    print("Copia la carpeta 'motor_autoentrenamiento' a tu proyecto backend/")
    print()
    print("PASO 2: Modificar app.py")
    print("-" * 70)
    print("Ver EJEMPLO_APP_PY arriba para los cambios necesarios")
    print()
    print("PASO 3: Modificar rutas_analisis.py")
    print("-" * 70)
    print("Ver EJEMPLO_RUTAS_ANALISIS_PY arriba para los cambios necesarios")
    print()
    print("PASO 4: Ejecutar SQL en la base de datos")
    print("-" * 70)
    print("Ejecuta el SQL de triggers UNA SOLA VEZ en tu BD PostgreSQL")
    print()
    print("=" * 70)
    print("SQL A EJECUTAR:")
    print("=" * 70)
    print(SQL_TRIGGERS)
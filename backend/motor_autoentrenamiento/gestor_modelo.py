# -*- coding: utf-8 -*-
"""
gestor_modelo.py — Gestor singleton del modelo con auto-reentrenamiento.

Este módulo gestiona el ciclo de vida del modelo de predicción:
- Carga inicial desde BD
- Reentrenamiento automático cuando hay cambios
- Acceso thread-safe al modelo
- Integración con el sistema de eventos

ARQUITECTURA:
El sistema usa el patrón Singleton para garantizar una única instancia del modelo
en memoria, y un sistema de versiones para detectar cuándo reentrenar.

Flujo de auto-reentrenamiento:
1. Al iniciar el servidor → entrenar desde BD si no hay modelo
2. Cada N minutos → verificar si hay partidos nuevos
3. Si hay cambios → reentrenar en background
4. Trigger de BD → notificar cuando se inserta partido (opcional)

Uso:
    from gestor_modelo import GestorModelo, obtener_modelo
    
    # Inicializar (una vez al inicio del servidor)
    gestor = GestorModelo.obtener_instancia(pool)
    gestor.inicializar()
    
    # Obtener modelo para predicciones
    modelo = obtener_modelo()
"""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TYPE_CHECKING

from .entrenador_bd import EntrenadorBD

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# TIPOS PARA EL MODELO EN MEMORIA
# ══════════════════════════════════════════════════════════════════════════════

class ModeloEnMemoria:
    """
    Wrapper del modelo Ridge que vive en memoria.
    
    Proporciona la misma interfaz que ModeloRidge pero sin necesidad
    de cargar desde archivo .npz.
    
    Attributes:
        alfa: Parámetro de regularización usado
        entidad_a_indice: Mapeo nombre_equipo -> índice
        pesos_equipo: Matriz de pesos para predicción del equipo
        pesos_rival: Matriz de pesos para predicción del rival
        desviacion_equipo: Desviación estándar por cuarto del equipo
        desviacion_rival: Desviación estándar por cuarto del rival
        version: Número de versión del modelo (incrementa en cada reentrenamiento)
        fecha_entrenamiento: Fecha del último entrenamiento
    """
    
    def __init__(self, datos: Dict[str, Any], version: int = 1):
        self.alfa: float = datos["alpha"]
        self.entidad_a_indice: Dict[str, int] = datos["entidad_a_indice"]
        self.pesos_equipo = datos["pesos_equipo"]
        self.pesos_rival = datos["pesos_rival"]
        self.desviacion_equipo = datos["desviacion_equipo"]
        self.desviacion_rival = datos["desviacion_rival"]
        self.version: int = version
        self.fecha_entrenamiento: datetime = datetime.now()
        self.metricas: Dict[str, Any] = datos.get("metricas", {})
    
    def contiene_equipo(self, nombre: str) -> bool:
        """Verifica si un equipo está en el modelo."""
        from .entrenador_bd import normalizar_nombre
        nombre_norm = normalizar_nombre(nombre)
        return nombre_norm in self.entidad_a_indice
    
    @property
    def cantidad_equipos(self) -> int:
        """Retorna la cantidad de equipos en el modelo."""
        return len(self.entidad_a_indice)
    
    def obtener_equipos(self) -> list:
        """Retorna lista de nombres de equipos en el modelo."""
        return list(self.entidad_a_indice.keys())


# ══════════════════════════════════════════════════════════════════════════════
# GESTOR SINGLETON
# ══════════════════════════════════════════════════════════════════════════════

class GestorModelo:
    """
    Gestor singleton del modelo de predicción.
    
    Esta clase garantiza que solo exista una instancia del modelo en memoria
    y maneja el reentrenamiento automático.
    
    Características:
    - Singleton thread-safe
    - Auto-reentrenamiento cuando hay cambios en la BD
    - Verificación periódica de datos nuevos
    - Métricas y logging detallado
    
    Configuración:
    - INTERVALO_VERIFICACION: Cada cuánto verificar datos nuevos (minutos)
    - REENTRENAR_AL_INICIAR: Si reentrenar aunque exista modelo previo
    
    Ejemplo:
        # Inicialización (al arrancar FastAPI)
        @app.on_event("startup")
        async def startup():
            gestor = GestorModelo.obtener_instancia(obtener_pool())
            await gestor.inicializar_async()
        
        # En los endpoints
        modelo = obtener_modelo()
        resultado = analizar_partido(modelo, ...)
    """
    
    _instancia: Optional["GestorModelo"] = None
    _lock = threading.Lock()
    
    # Configuración
    INTERVALO_VERIFICACION_MINUTOS: int = 30  # Verificar cada 30 minutos
    REENTRENAR_AL_INICIAR: bool = True  # Siempre reentrenar al iniciar
    
    def __init__(self, pool: "ConnectionPool"):
        """
        Constructor privado - usar obtener_instancia().
        
        Args:
            pool: ConnectionPool de psycopg para la base de datos
        """
        self._pool = pool
        self._entrenador = EntrenadorBD(pool)
        self._modelo: Optional[ModeloEnMemoria] = None
        self._version: int = 0
        self._inicializado: bool = False
        self._tarea_verificacion: Optional[asyncio.Task] = None
        self._ultimo_conteo_partidos: int = 0
    
    @classmethod
    def obtener_instancia(cls, pool: Optional["ConnectionPool"] = None) -> "GestorModelo":
        """
        Obtiene la instancia singleton del gestor.
        
        Args:
            pool: ConnectionPool (requerido en la primera llamada)
            
        Returns:
            La instancia única del GestorModelo
            
        Raises:
            RuntimeError: Si se llama sin pool y no existe instancia previa
        """
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    if pool is None:
                        raise RuntimeError(
                            "GestorModelo no inicializado. "
                            "La primera llamada debe incluir el pool de conexiones."
                        )
                    cls._instancia = cls(pool)
        
        return cls._instancia
    
    @classmethod
    def reiniciar(cls) -> None:
        """
        Reinicia el singleton (útil para tests).
        
        ADVERTENCIA: Solo usar en tests o al reiniciar la aplicación.
        """
        with cls._lock:
            if cls._instancia and cls._instancia._tarea_verificacion:
                cls._instancia._tarea_verificacion.cancel()
            cls._instancia = None
    
    def inicializar(self) -> None:
        """
        Inicializa el gestor entrenando el modelo desde la BD.
        
        Este método es síncrono y bloquea hasta que el modelo esté listo.
        Para uso en FastAPI, preferir inicializar_async().
        """
        if self._inicializado and self._modelo is not None:
            logger.info("✅ Gestor ya inicializado, modelo en memoria")
            return
        
        logger.info("🚀 Inicializando GestorModelo...")
        self._entrenar_modelo()
        self._inicializado = True
        logger.info(f"✅ GestorModelo listo - Modelo v{self._version} con {self._modelo.cantidad_equipos} equipos")
    
    async def inicializar_async(self) -> None:
        """
        Inicializa el gestor de forma asíncrona.
        
        Entrena el modelo en un thread separado para no bloquear el event loop.
        También inicia la tarea de verificación periódica.
        """
        if self._inicializado and self._modelo is not None:
            logger.info("✅ Gestor ya inicializado")
            return
        
        logger.info("🚀 Inicializando GestorModelo (async)...")
        
        # Entrenar en thread separado
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._entrenar_modelo)
        
        self._inicializado = True
        
        # Iniciar verificación periódica
        self._tarea_verificacion = asyncio.create_task(self._verificar_periodicamente())
        
        logger.info(f"✅ GestorModelo listo - Modelo v{self._version}")
    
    def _entrenar_modelo(self) -> None:
        """
        Entrena o reentrena el modelo desde la BD.
        
        Este método es thread-safe y puede ser llamado concurrentemente.
        """
        with self._lock:
            try:
                logger.info("🔄 Entrenando modelo desde BD...")
                datos_modelo = self._entrenador.entrenar()
                
                self._version += 1
                self._modelo = ModeloEnMemoria(datos_modelo, self._version)
                self._ultimo_conteo_partidos = datos_modelo["metricas"].get("partidos_entrenamiento", 0)
                
                logger.info(
                    f"✅ Modelo v{self._version} entrenado: "
                    f"{self._modelo.cantidad_equipos} equipos, "
                    f"{self._ultimo_conteo_partidos} partidos"
                )
                
            except Exception as e:
                logger.error(f"❌ Error entrenando modelo: {e}")
                raise
    
    async def _verificar_periodicamente(self) -> None:
        """
        Tarea que verifica periódicamente si hay datos nuevos.
        
        Corre en background y reentrena automáticamente cuando detecta
        partidos nuevos en la BD.
        """
        while True:
            try:
                await asyncio.sleep(self.INTERVALO_VERIFICACION_MINUTOS * 60)
                
                logger.debug("🔍 Verificando datos nuevos...")
                
                if self._entrenador.hay_datos_nuevos():
                    logger.info("📊 Detectados datos nuevos, reentrenando...")
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._entrenar_modelo)
                else:
                    logger.debug("✓ No hay datos nuevos")
                    
            except asyncio.CancelledError:
                logger.info("⏹️ Verificación periódica cancelada")
                break
            except Exception as e:
                logger.error(f"❌ Error en verificación periódica: {e}")
                await asyncio.sleep(60)  # Esperar antes de reintentar
    
    def reentrenar(self) -> None:
        """
        Fuerza el reentrenamiento del modelo.
        
        Útil cuando se sabe que hay datos nuevos (ej: después de insertar
        partidos manualmente).
        """
        logger.info("🔄 Reentrenamiento forzado solicitado")
        self._entrenar_modelo()
    
    async def reentrenar_async(self) -> None:
        """Versión asíncrona de reentrenar()."""
        logger.info("🔄 Reentrenamiento forzado solicitado (async)")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._entrenar_modelo)
    
    @property
    def modelo(self) -> ModeloEnMemoria:
        """
        Obtiene el modelo actual.
        
        Returns:
            El modelo de predicción en memoria
            
        Raises:
            RuntimeError: Si el gestor no está inicializado
        """
        if self._modelo is None:
            raise RuntimeError(
                "Modelo no disponible. "
                "Asegúrate de llamar inicializar() primero."
            )
        return self._modelo
    
    @property
    def version(self) -> int:
        """Retorna la versión actual del modelo."""
        return self._version
    
    @property
    def esta_inicializado(self) -> bool:
        """Indica si el gestor está inicializado."""
        return self._inicializado and self._modelo is not None
    
    @property
    def metricas(self) -> Dict[str, Any]:
        """Retorna métricas del último entrenamiento."""
        if self._modelo is None:
            return {}
        return {
            "version": self._version,
            "equipos": self._modelo.cantidad_equipos,
            "fecha_entrenamiento": self._modelo.fecha_entrenamiento.isoformat(),
            **self._modelo.metricas,
        }
    
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo del gestor.
        
        Útil para endpoints de diagnóstico/health check.
        """
        return {
            "inicializado": self._inicializado,
            "version_modelo": self._version,
            "equipos_en_modelo": self._modelo.cantidad_equipos if self._modelo else 0,
            "partidos_entrenamiento": self._ultimo_conteo_partidos,
            "fecha_ultimo_entrenamiento": (
                self._modelo.fecha_entrenamiento.isoformat() 
                if self._modelo else None
            ),
            "intervalo_verificacion_minutos": self.INTERVALO_VERIFICACION_MINUTOS,
            "verificacion_activa": self._tarea_verificacion is not None and not self._tarea_verificacion.done(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════════════════════

def obtener_modelo() -> ModeloEnMemoria:
    """
    Obtiene el modelo actual para usar en predicciones.
    
    Esta es la función principal que deben usar los endpoints.
    
    Returns:
        El modelo de predicción listo para usar
        
    Raises:
        RuntimeError: Si el gestor no está inicializado
        
    Ejemplo:
        modelo = obtener_modelo()
        if modelo.contiene_equipo("Los Angeles Lakers"):
            resultado = analizar_partido(modelo, ...)
    """
    return GestorModelo.obtener_instancia().modelo


def obtener_metricas_modelo() -> Dict[str, Any]:
    """
    Obtiene las métricas del modelo actual.
    
    Returns:
        Diccionario con métricas de entrenamiento y estado
    """
    return GestorModelo.obtener_instancia().metricas


def forzar_reentrenamiento() -> None:
    """
    Fuerza el reentrenamiento del modelo.
    
    Usar cuando se han insertado datos manualmente y se quiere
    actualizar el modelo inmediatamente.
    """
    GestorModelo.obtener_instancia().reentrenar()
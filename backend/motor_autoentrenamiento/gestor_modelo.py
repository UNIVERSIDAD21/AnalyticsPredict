# -*- coding: utf-8 -*-
"""
gestor_modelo.py — Gestor singleton del modelo NBA para serving y entrenamiento explícito.

Este módulo gestiona el ciclo de vida del modelo de predicción:
- Carga inicial de un artefacto versionado, sin BD ni entrenamiento
- Reentrenamiento únicamente mediante operación explícita
- Acceso thread-safe al modelo
- Integración con el sistema de eventos

ARQUITECTURA:
El sistema usa el patrón Singleton para garantizar una única instancia del modelo
en memoria, y un sistema de versiones para detectar cuándo reentrenar.

El startup y las lecturas no crean versiones del modelo. Una ingesta tampoco
entrena: el operador debe ejecutar el comando o endpoint explícito.

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
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from .entrenador_bd import EntrenadorBD
from .artefacto_nba import cargar_artefacto, guardar_artefacto

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
        version: ID real de modelo_versiones en BD (FK válida)
        fecha_entrenamiento: Fecha del último entrenamiento

    IMPORTANTE: `version` es el ID real de modelo_versiones (modelo_version_id),
    NO un contador interno. Esto garantiza que sea una FK válida para
    predicciones_registradas.modelo_version_id.
    """

    def __init__(self, datos: Dict[str, Any], version: int = 1):
        self.alfa: float = datos["alpha"]
        self.entidad_a_indice: Dict[str, int] = datos["entidad_a_indice"]
        self.pesos_equipo = datos["pesos_equipo"]
        self.pesos_rival = datos["pesos_rival"]
        self.desviacion_equipo = datos["desviacion_equipo"]
        self.desviacion_rival = datos["desviacion_rival"]
        # CAMBIO: Usar modelo_version_id real de BD si está disponible
        self.version: int = datos.get("modelo_version_id", version)
        fecha = datos.get("fecha_entrenamiento") or datos.get("metricas", {}).get("fecha_entrenamiento")
        self.fecha_entrenamiento: datetime = datetime.fromisoformat(fecha) if fecha else datetime.now()
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
    y solo entrena por una operación explícita.
    
    Características:
    - Singleton thread-safe
    - Carga de artefacto en startup sin BD ni entrenamiento
    - Entrenamiento explícito con publicación atómica de artefacto
    - Métricas y logging detallado
    
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
    
    INTERVALO_VERIFICACION_MINUTOS: int = 0
    REENTRENAR_AL_INICIAR: bool = False
    
    def __init__(self, pool: Optional["ConnectionPool"] = None):
        """
        Constructor privado - usar obtener_instancia().
        
        Args:
            pool: ConnectionPool de psycopg para la base de datos
        """
        self._pool = pool
        self._entrenador = EntrenadorBD(pool) if pool is not None else None
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
                    cls._instancia = cls(pool)
        elif pool is not None and cls._instancia._pool is None:
            cls._instancia._pool = pool
            cls._instancia._entrenador = EntrenadorBD(pool)
        
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
        Carga el artefacto existente sin consultar BD ni crear versiones.
        """
        if self._inicializado and self._modelo is not None:
            logger.info("✅ Gestor ya inicializado, modelo en memoria")
            return
        datos = cargar_artefacto()
        if datos is None:
            logger.warning("No hay artefacto NBA activo; API disponible, análisis NBA degradado")
            return
        self.cargar_modelo_publicado(datos)
        logger.info("Modelo NBA versionado cargado sin entrenamiento: id=%s", self._version)

    def cargar_modelo_publicado(self, datos: Optional[Dict[str, Any]] = None) -> ModeloEnMemoria:
        """Recarga explícita del artefacto ya publicado; no consulta ni escribe BD."""
        datos = datos if datos is not None else cargar_artefacto()
        if datos is None:
            raise RuntimeError("No existe artefacto NBA activo")
        modelo = ModeloEnMemoria(datos)
        with self._lock:
            self._modelo = modelo
            self._version = modelo.version
            self._ultimo_conteo_partidos = int(modelo.metricas.get("partidos_entrenamiento", 0))
            self._inicializado = True
        return modelo
    
    async def inicializar_async(self) -> None:
        """
        Carga el artefacto sin lanzar jobs automáticos ni entrenar.
        """
        if self._inicializado and self._modelo is not None:
            logger.info("✅ Gestor ya inicializado")
            return
        
        self.inicializar()
    
    def _entrenar_modelo(self) -> None:
        """
        Entrena o reentrena el modelo desde la BD.
        
        Este método es thread-safe y puede ser llamado concurrentemente.
        """
        with self._lock:
            try:
                logger.info("🔄 Entrenando modelo desde BD...")
                if self._entrenador is None:
                    from db import obtener_pool
                    self._pool = obtener_pool()
                    self._entrenador = EntrenadorBD(self._pool)
                datos_modelo = self._entrenador.entrenar()
                guardar_artefacto(datos_modelo)

                self._modelo = ModeloEnMemoria(datos_modelo)
                self._version = self._modelo.version
                self._inicializado = True
                self._ultimo_conteo_partidos = datos_modelo["metricas"].get("partidos_entrenamiento", 0)
                
                logger.info(
                    f"✅ Modelo v{self._version} entrenado: "
                    f"{self._modelo.cantidad_equipos} equipos, "
                    f"{self._ultimo_conteo_partidos} partidos"
                )
                
            except Exception as e:
                logger.error(f"❌ Error entrenando modelo: {e}")
                raise
    
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

# -*- coding: utf-8 -*-
"""
eventos_modelo.py — Sistema de eventos para auto-reentrenamiento.

Este módulo implementa la notificación en tiempo real de cambios en la BD
usando PostgreSQL LISTEN/NOTIFY para reentrenar el modelo automáticamente.

ARQUITECTURA:
PostgreSQL tiene un sistema de pub/sub incorporado (LISTEN/NOTIFY) que permite
notificar a clientes conectados cuando ocurren eventos. Usamos esto para:

1. Crear un trigger en la tabla `partidos` que envía NOTIFY al insertar/actualizar
2. Un listener en Python que escucha estas notificaciones
3. Cuando llega una notificación, se programa el reentrenamiento

Esto es más eficiente que polling porque:
- No hay consultas periódicas a la BD
- El reentrenamiento ocurre inmediatamente después del cambio
- Menor carga en la BD

Uso:
    # En startup de FastAPI
    listener = EscuchaEventosPartidos(pool)
    await listener.iniciar()
    
    # En shutdown
    await listener.detener()
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SQL PARA CREAR TRIGGERS
# ══════════════════════════════════════════════════════════════════════════════

SQL_CREAR_FUNCION_NOTIFICACION = """
-- Función que envía notificación cuando cambian los partidos
CREATE OR REPLACE FUNCTION notificar_cambio_partidos()
RETURNS TRIGGER AS $$
BEGIN
    -- Enviar notificación con información básica del cambio
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
"""

SQL_CREAR_TRIGGER = """
-- Trigger que se dispara en INSERT, UPDATE o DELETE
DROP TRIGGER IF EXISTS trigger_notificar_partidos ON partidos;

CREATE TRIGGER trigger_notificar_partidos
    AFTER INSERT OR UPDATE OR DELETE ON partidos
    FOR EACH ROW
    EXECUTE FUNCTION notificar_cambio_partidos();
"""

SQL_VERIFICAR_TRIGGER = """
SELECT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'trigger_notificar_partidos'
);
"""


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class EscuchaEventosPartidos:
    """
    Escucha eventos de cambios en la tabla partidos.
    
    Usa PostgreSQL LISTEN/NOTIFY para recibir notificaciones en tiempo real
    cuando se insertan, actualizan o eliminan partidos.
    
    Características:
    - Debouncing: Agrupa múltiples cambios rápidos en un solo reentrenamiento
    - Reconexión automática si se pierde la conexión
    - Callbacks personalizables para reaccionar a cambios
    
    Ejemplo:
        listener = EscuchaEventosPartidos(pool)
        listener.al_cambiar(mi_callback)  # Opcional
        await listener.iniciar()
    """
    
    # Tiempo de debounce en segundos
    # Si hay múltiples cambios rápidos, espera este tiempo antes de reentrenar
    DEBOUNCE_SEGUNDOS: float = 10.0
    
    def __init__(self, pool: "ConnectionPool"):
        """
        Inicializa el listener.
        
        Args:
            pool: ConnectionPool de psycopg
        """
        self._pool = pool
        self._activo: bool = False
        self._tarea_escucha: Optional[asyncio.Task] = None
        self._callbacks: list[Callable] = []
        self._ultimo_cambio: Optional[datetime] = None
        self._tarea_debounce: Optional[asyncio.Task] = None
        self._cambios_pendientes: int = 0
    
    def al_cambiar(self, callback: Callable) -> None:
        """
        Registra un callback para cuando hay cambios.
        
        El callback se llamará después del período de debounce,
        con el número de cambios acumulados.
        
        Args:
            callback: Función a llamar (puede ser async)
        """
        self._callbacks.append(callback)
    
    async def iniciar(self) -> None:
        """
        Inicia la escucha de eventos.
        
        Crea los triggers en la BD si no existen y comienza a escuchar.
        """
        if self._activo:
            logger.warning("⚠️ Listener ya está activo")
            return
        
        logger.info("🎧 Iniciando escucha de eventos de partidos...")
        
        # Crear triggers si no existen
        await self._asegurar_triggers()
        
        self._activo = True
        self._tarea_escucha = asyncio.create_task(self._escuchar())
        
        logger.info("✅ Escucha de eventos iniciada")
    
    async def detener(self) -> None:
        """Detiene la escucha de eventos."""
        logger.info("⏹️ Deteniendo escucha de eventos...")
        
        self._activo = False
        
        if self._tarea_escucha:
            self._tarea_escucha.cancel()
            try:
                await self._tarea_escucha
            except asyncio.CancelledError:
                pass
        
        if self._tarea_debounce:
            self._tarea_debounce.cancel()
            try:
                await self._tarea_debounce
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Escucha de eventos detenida")
    
    async def _asegurar_triggers(self) -> None:
        """Crea los triggers en la BD si no existen."""
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                # Verificar si el trigger existe
                cursor.execute(SQL_VERIFICAR_TRIGGER)
                existe = cursor.fetchone()[0]
                
                if not existe:
                    logger.info("📝 Creando triggers de notificación...")
                    cursor.execute(SQL_CREAR_FUNCION_NOTIFICACION)
                    cursor.execute(SQL_CREAR_TRIGGER)
                    conn.commit()
                    logger.info("✅ Triggers creados")
                else:
                    logger.debug("✓ Triggers ya existen")
    
    async def _escuchar(self) -> None:
        """Loop principal de escucha de notificaciones."""
        import select
        
        while self._activo:
            try:
                with self._pool.connection() as conn:
                    # Suscribirse al canal
                    with conn.cursor() as cursor:
                        cursor.execute("LISTEN partidos_actualizados")
                    conn.commit()
                    
                    logger.info("📡 Escuchando canal 'partidos_actualizados'")
                    
                    # Obtener el file descriptor de la conexión
                    fd = conn.fileno()
                    
                    while self._activo:
                        # Esperar notificaciones con timeout
                        readable, _, _ = select.select([fd], [], [], 5.0)
                        
                        if readable:
                            conn.poll()
                            while conn.notifies:
                                notify = conn.notifies.pop(0)
                                await self._procesar_notificacion(notify)
                        
                        # Yield control al event loop
                        await asyncio.sleep(0)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en escucha: {e}")
                if self._activo:
                    logger.info("🔄 Reconectando en 5 segundos...")
                    await asyncio.sleep(5)
    
    async def _procesar_notificacion(self, notify) -> None:
        """
        Procesa una notificación de cambio.
        
        Implementa debouncing para agrupar cambios rápidos.
        """
        import json
        
        try:
            payload = json.loads(notify.payload) if notify.payload else {}
            operacion = payload.get("operacion", "UNKNOWN")
            
            logger.info(f"📬 Notificación recibida: {operacion} en partidos")
            
            self._cambios_pendientes += 1
            self._ultimo_cambio = datetime.now()
            
            # Cancelar debounce anterior si existe
            if self._tarea_debounce and not self._tarea_debounce.done():
                self._tarea_debounce.cancel()
            
            # Programar nuevo debounce
            self._tarea_debounce = asyncio.create_task(self._debounce())
            
        except Exception as e:
            logger.error(f"❌ Error procesando notificación: {e}")
    
    async def _debounce(self) -> None:
        """
        Espera el período de debounce y luego ejecuta callbacks.
        
        Esto agrupa múltiples cambios rápidos en una sola acción.
        """
        await asyncio.sleep(self.DEBOUNCE_SEGUNDOS)
        
        cambios = self._cambios_pendientes
        self._cambios_pendientes = 0
        
        logger.info(f"🔔 Ejecutando callbacks después de {cambios} cambios")
        
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(cambios)
                else:
                    callback(cambios)
            except Exception as e:
                logger.error(f"❌ Error en callback: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN CON GESTOR DE MODELO
# ══════════════════════════════════════════════════════════════════════════════

class AutoReentrenador:
    """
    Integra el listener de eventos con el gestor de modelo.
    
    Esta clase conecta las piezas para que el modelo se reentrene
    automáticamente cuando hay cambios en la BD.
    
    Uso:
        auto = AutoReentrenador(pool)
        await auto.iniciar()
        
        # El modelo se reentrenará automáticamente cuando se 
        # inserten nuevos partidos
    """
    
    def __init__(self, pool: "ConnectionPool"):
        """
        Inicializa el auto-reentrenador.
        
        Args:
            pool: ConnectionPool de psycopg
        """
        from .gestor_modelo import GestorModelo
        
        self._pool = pool
        self._gestor = GestorModelo.obtener_instancia(pool)
        self._listener = EscuchaEventosPartidos(pool)
        
        # Registrar callback de reentrenamiento
        self._listener.al_cambiar(self._al_cambiar_partidos)
    
    async def _al_cambiar_partidos(self, cantidad_cambios: int) -> None:
        """Callback cuando cambian los partidos."""
        logger.info(f"🔄 Reentrenando modelo por {cantidad_cambios} cambios en BD...")
        
        try:
            await self._gestor.reentrenar_async()
            logger.info("✅ Modelo reentrenado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error reentrenando: {e}")
    
    async def iniciar(self) -> None:
        """
        Inicia el sistema completo de auto-reentrenamiento.
        
        1. Inicializa el gestor de modelo
        2. Inicia la escucha de eventos
        """
        logger.info("🚀 Iniciando sistema de auto-reentrenamiento...")
        
        # Inicializar gestor (entrena modelo inicial)
        await self._gestor.inicializar_async()
        
        # Iniciar escucha de eventos
        await self._listener.iniciar()
        
        logger.info("✅ Sistema de auto-reentrenamiento activo")
    
    async def detener(self) -> None:
        """Detiene el sistema de auto-reentrenamiento."""
        await self._listener.detener()
    
    @property
    def estado(self) -> dict:
        """Obtiene el estado del sistema."""
        return {
            "gestor": self._gestor.obtener_estado(),
            "listener_activo": self._listener._activo,
        }


# ══════════════════════════════════════════════════════════════════════════════
# SCRIPT DE CONFIGURACIÓN DE TRIGGERS
# ══════════════════════════════════════════════════════════════════════════════

def crear_triggers_sql() -> str:
    """
    Retorna el SQL necesario para crear los triggers.
    
    Útil para ejecutar manualmente o incluir en migraciones.
    """
    return f"""
-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGERS PARA AUTO-REENTRENAMIENTO DEL MODELO NBA
-- ═══════════════════════════════════════════════════════════════════════════
-- 
-- Este SQL crea los triggers necesarios para notificar al backend cuando
-- hay cambios en la tabla de partidos, permitiendo el reentrenamiento
-- automático del modelo de predicción.
--
-- Ejecutar una sola vez en la base de datos.
-- ═══════════════════════════════════════════════════════════════════════════

{SQL_CREAR_FUNCION_NOTIFICACION}

{SQL_CREAR_TRIGGER}

-- Verificar que el trigger se creó correctamente
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing
FROM information_schema.triggers
WHERE trigger_name = 'trigger_notificar_partidos';
"""


if __name__ == "__main__":
    # Si se ejecuta directamente, imprime el SQL
    print(crear_triggers_sql())
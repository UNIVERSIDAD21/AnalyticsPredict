# -*- coding: utf-8 -*-
"""
Motor de Auto-Entrenamiento NBA
===============================

Este paquete proporciona entrenamiento automático del modelo de predicción
NBA desde la base de datos PostgreSQL.

Componentes principales:
- EntrenadorBD: Entrena el modelo directamente desde la tabla `partidos`
- GestorModelo: Singleton que gestiona el modelo en memoria
- EscuchaEventosPartidos: Escucha cambios en BD para reentrenar
- AutoReentrenador: Integra todo para reentrenamiento automático

Uso básico:
-----------

    from motor_autoentrenamiento import (
        GestorModelo,
        obtener_modelo,
        AutoReentrenador,
    )
    
    # Inicializar con tu pool de conexiones
    gestor = GestorModelo.obtener_instancia(pool)
    gestor.inicializar()
    
    # Usar el modelo para predicciones
    modelo = obtener_modelo()
    print(f"Equipos: {modelo.cantidad_equipos}")

Uso con FastAPI:
----------------

    from motor_autoentrenamiento import AutoReentrenador
    
    auto_reentrenador = None
    
    @app.on_event("startup")
    async def startup():
        global auto_reentrenador
        auto_reentrenador = AutoReentrenador(obtener_pool())
        await auto_reentrenador.iniciar()
    
    @app.on_event("shutdown")
    async def shutdown():
        if auto_reentrenador:
            await auto_reentrenador.detener()

El modelo se reentrenará automáticamente cuando:
1. Se inicia el servidor
2. Se insertan nuevos partidos en la BD
3. Se actualiza/elimina un partido existente
"""

from .entrenador_bd import EntrenadorBD, normalizar_nombre
from .gestor_modelo import (
    GestorModelo,
    ModeloEnMemoria,
    obtener_modelo,
    obtener_modelo_por_temporadas,
    obtener_metricas_modelo,
    forzar_reentrenamiento,
)
from .eventos_modelo import (
    EscuchaEventosPartidos,
    AutoReentrenador,
    crear_triggers_sql,
)

__all__ = [
    # Entrenador
    "EntrenadorBD",
    "normalizar_nombre",
    
    # Gestor de modelo
    "GestorModelo",
    "ModeloEnMemoria",
    "obtener_modelo",
    "obtener_modelo_por_temporadas",
    "obtener_metricas_modelo",
    "forzar_reentrenamiento",
    
    # Eventos
    "EscuchaEventosPartidos",
    "AutoReentrenador",
    "crear_triggers_sql",
]

__version__ = "1.0.0"

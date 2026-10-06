# -*- coding: utf-8 -*-
"""
Motor NBA de serving y entrenamiento explícito
==============================================

El startup solo carga un artefacto versionado; la BD se usa para entrenar
únicamente desde una operación explícita del operador.

Componentes principales:
- EntrenadorBD: Entrena el modelo directamente desde la tabla `partidos`
- GestorModelo: Singleton que sirve el modelo en memoria
- EscuchaEventosPartidos/AutoReentrenador: compatibilidad legacy sin arranque automático

Uso básico:
-----------

    from motor_autoentrenamiento import (
        GestorModelo,
        obtener_modelo,
        AutoReentrenador,
    )
    
    # Inicializar con tu pool de conexiones
    gestor = GestorModelo.obtener_instancia()
    gestor.inicializar()
    
    # Usar el modelo para predicciones
    modelo = obtener_modelo()
    print(f"Equipos: {modelo.cantidad_equipos}")

Uso con FastAPI:
----------------

    from motor_autoentrenamiento import GestorModelo
    
    @app.on_event("startup")
    async def startup():
        await GestorModelo.obtener_instancia().inicializar_async()

Una ingesta o un reload no entrenan. Usar
`python scripts/entrenar_modelo_nba_explicito.py --entrenar` de forma deliberada.
"""

from .entrenador_bd import EntrenadorBD, normalizar_nombre
from .gestor_modelo import (
    GestorModelo,
    ModeloEnMemoria,
    obtener_modelo,
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
    "obtener_metricas_modelo",
    "forzar_reentrenamiento",
    
    # Eventos
    "EscuchaEventosPartidos",
    "AutoReentrenador",
    "crear_triggers_sql",
]

__version__ = "1.0.0"

# -*- coding: utf-8 -*-
"""
configuracion.py — Configuración central del sistema.

Este archivo contiene todas las variables de configuración del backend.
Los valores se pueden sobrescribir con variables de entorno.

Uso:
    from configuracion import CONFIGURACION
    print(CONFIGURACION.puerto)
"""

from dataclasses import dataclass, field
from typing import List
import os


@dataclass
class Configuracion:
    """
    Configuración central de la aplicación.

    Todos los valores tienen defaults sensatos para desarrollo local.
    En producción, se sobrescriben con variables de entorno.
    """

    # ══════════════════════════════════════════════════════════
    # ENTORNO
    # ══════════════════════════════════════════════════════════

    entorno: str = field(default_factory=lambda: os.getenv("ENTORNO", "desarrollo"))
    """Entorno de ejecución: 'desarrollo', 'pruebas', 'produccion'"""

    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    """Modo debug: activa logs detallados y recarga automática"""

    # ══════════════════════════════════════════════════════════
    # SERVIDOR
    # ══════════════════════════════════════════════════════════

    host: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    """Host donde corre el servidor"""

    puerto: int = field(default_factory=lambda: int(os.getenv("PUERTO", "8000")))
    """Puerto del servidor"""

    # ══════════════════════════════════════════════════════════
    # CORS (Cross-Origin Resource Sharing)
    # ══════════════════════════════════════════════════════════

    origenes_cors: List[str] = field(default_factory=list)
    """Orígenes permitidos para peticiones CORS"""

    # ══════════════════════════════════════════════════════════
    # RUTAS DE ARCHIVOS
    # ══════════════════════════════════════════════════════════

    ruta_modelo: str = field(
        default_factory=lambda: os.getenv("RUTA_MODELO", "datos/modelo_entrenado.npz")
    )
    """Ruta al archivo del modelo entrenado"""

    ruta_equipos: str = field(
        default_factory=lambda: os.getenv("RUTA_EQUIPOS", "datos/equipos_nba.json")
    )
    """Ruta al archivo JSON con información de equipos"""

    ruta_estadisticas_equipos: str = field(
        default_factory=lambda: os.getenv("RUTA_ESTADISTICAS_EQUIPOS", "datos/estadisticas_equipos.json")
    )
    """Ruta al archivo JSON con estadísticas de equipos"""

    # ══════════════════════════════════════════════════════════
    # MODELO
    # ══════════════════════════════════════════════════════════

    probabilidad_minima_recomendacion: float = field(
        default_factory=lambda: float(os.getenv("PROB_MIN_RECOMENDACION", "0.55"))
    )
    """Probabilidad mínima para considerar una apuesta 'recomendable'"""

    edge_minimo_valor: float = field(
        default_factory=lambda: float(os.getenv("EDGE_MIN_VALOR", "0.10"))
    )
    """Edge mínimo para considerar que hay 'valor' en una apuesta"""

    # ══════════════════════════════════════════════════════════
    # INGESTIÓN
    # ══════════════════════════════════════════════════════════

    ingestion_api_enabled: bool = field(
        default_factory=lambda: os.getenv("INGESTION_API_ENABLED", "false").lower() == "true"
    )
    """Habilita el endpoint de sincronización de partidos"""

    ingestion_api_key: str = field(default_factory=lambda: os.getenv("INGESTION_API_KEY", ""))
    """API key simple para proteger la sincronización"""

    def __post_init__(self):
        """Inicialización posterior: configura valores que dependen del entorno."""

        # Configurar CORS según entorno
        if not self.origenes_cors:
            if self.entorno == "desarrollo":
                self.origenes_cors = [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                ]
            elif self.entorno == "produccion":
                # En producción, los orígenes vienen de variable de entorno
                origenes_env = os.getenv("ORIGENES_CORS", "")
                self.origenes_cors = [o.strip() for o in origenes_env.split(",") if o.strip()]
            else:
                self.origenes_cors = ["*"]  # Pruebas: permitir todo

    def __str__(self) -> str:
        """Representación legible de la configuración."""
        return (
            "Configuración(\n"
            f"  entorno={self.entorno},\n"
            f"  debug={self.debug},\n"
            f"  host={self.host},\n"
            f"  puerto={self.puerto},\n"
            f"  ruta_modelo={self.ruta_modelo}\n"
            ")"
        )


# Instancia global de configuración
CONFIGURACION = Configuracion()


# ══════════════════════════════════════════════════════════════
# CONSTANTES DEL SISTEMA
# ══════════════════════════════════════════════════════════════

# Identificadores de cuartos
CUARTOS = ("Q1", "Q2", "Q3", "Q4")
INDICE_CUARTOS = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}

# Mercados soportados
MERCADOS_SOPORTADOS = ("Q1", "Q2", "Q3", "Q4", "COMPLETO")

# Niveles de confianza
NIVELES_CONFIANZA = ("ALTA", "MEDIA", "BAJA")

# Recomendaciones de mercado
RECOMENDACIONES = ("VALOR", "JUSTO", "EVITAR")

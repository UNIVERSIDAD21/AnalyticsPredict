# -*- coding: utf-8 -*-
"""
Módulo de scraping de Sofascore para datos de fútbol.

Este paquete proporciona herramientas para extraer datos de partidos de fútbol
desde la API de Sofascore, incluyendo:

- Información de temporadas y competiciones
- Datos de equipos
- Partidos históricos y futuros
- Estadísticas detalladas (corners, disparos, posesión, xG)

Componentes principales:
- SofascoreClient: Cliente HTTP con rate limiting y reintentos
- Extractores: temporadas, equipos, partidos, estadisticas
- Sincronizador: Persistencia a base de datos PostgreSQL
- Monitoreo: Sistema de logging y métricas

Uso básico:
    from scrapers.sofascore import SofascoreClient
    from scrapers.sofascore.partidos import obtener_partidos_pasados

    cliente = SofascoreClient()
    partidos = obtener_partidos_pasados(cliente, liga_id=8, temporada_id=12345)
"""

from .cliente import SofascoreClient
from .excepciones import (
    SofascoreError,
    RateLimitError,
    RecursoNoEncontrado,
    ErrorDeRed,
    DatosIncompletos,
)

__all__ = [
    'SofascoreClient',
    'SofascoreError',
    'RateLimitError',
    'RecursoNoEncontrado',
    'ErrorDeRed',
    'DatosIncompletos',
]

__version__ = '1.0.0'

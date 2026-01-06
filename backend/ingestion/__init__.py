# -*- coding: utf-8 -*-
"""Paquete de ingestión incremental de partidos."""

from .sync_partidos import SyncConfig, SyncResult, sync_partidos_recientes, formatear_resumen

__all__ = [
    "SyncConfig",
    "SyncResult",
    "sync_partidos_recientes",
    "formatear_resumen",
]

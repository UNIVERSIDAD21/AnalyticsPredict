# -*- coding: utf-8 -*-
"""
db.py — Utilidades de conexión a PostgreSQL.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# Cargar variables de entorno desde .env
load_dotenv()

_pool: Optional[ConnectionPool] = None


def _asegurar_ssl(url: str) -> str:
    """Asegura que la URL tenga sslmode=require."""
    if "sslmode=" in url:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}sslmode=require"


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos desde variables de entorno."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada. "
            "Crea un archivo .env con DATABASE_URL=tu_cadena_de_conexion"
        )
    return _asegurar_ssl(url)


def obtener_pool() -> ConnectionPool:
    """Obtiene el pool de conexiones, creándolo si no existe."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=obtener_database_url(),
            min_size=1,
            max_size=5,
            max_idle=300,
            max_lifetime=1800,
            check=ConnectionPool.check_connection,
            open=True  # Abrir inmediatamente al crear
        )
    return _pool


def cerrar_pool() -> None:
    """Cierra el pool de conexiones si está abierto."""
    global _pool
    if _pool is not None:
        try:
            _pool.close()
        except Exception:
            pass
        _pool = None

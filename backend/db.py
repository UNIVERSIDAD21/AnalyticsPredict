# -*- coding: utf-8 -*-
"""
db.py — Utilidades de conexión a PostgreSQL.
"""

from __future__ import annotations

import os
from typing import Optional

from psycopg_pool import ConnectionPool


_pool: Optional[ConnectionPool] = None


def _asegurar_ssl(url: str) -> str:
    if "sslmode=" in url:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}sslmode=require"


def obtener_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurada.")
    return _asegurar_ssl(url)


def obtener_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(conninfo=obtener_database_url(), min_size=1, max_size=5, open=False)
    if not _pool.opened:
        _pool.open()
    return _pool


def cerrar_pool() -> None:
    global _pool
    if _pool and _pool.opened:
        _pool.close()

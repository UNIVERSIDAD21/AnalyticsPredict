# -*- coding: utf-8 -*-
"""
db.py — Utilidades de conexión a PostgreSQL.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Optional

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from lecturas_http import solo_lectura_http, en_peticion_http


class PoolAplicacion(ConnectionPool):
    """Toda conexión abierta desde GET/HEAD opera en transacción READ ONLY.

    La propiedad de conexión también protege transacciones que un consumidor
    cierre/reabra explícitamente. Se restaura antes de devolverla al pool; POST y
    tareas explícitas ajenas al contexto HTTP mantienen su comportamiento.
    """

    @contextmanager
    def connection(self, timeout=None):
        with super().connection(timeout=timeout) as conn:
            # Un socket perdido no debe dejar una ventana esperando indefinidamente.
            # SET LOCAL funciona también con el pooler transaccional de Neon;
            # sus parámetros de startup no admiten statement_timeout.
            if not solo_lectura_http.get():
                if en_peticion_http.get():
                    conn.execute("SET LOCAL statement_timeout = '15s'; SET LOCAL lock_timeout = '5s'")
                yield conn
                return
            anterior = conn.read_only
            conn.read_only = True
            try:
                with conn.transaction():
                    conn.execute("SET TRANSACTION READ ONLY; SET LOCAL statement_timeout = '15s'; SET LOCAL lock_timeout = '5s'"
                                 if en_peticion_http.get() else 'SET TRANSACTION READ ONLY')
                    yield conn
            finally:
                # transaction() ya dejó la conexión en reposo incluso ante error.
                conn.read_only = anterior

# Cargar variables de entorno desde .env
# 1) intento estándar (cwd/parents)
load_dotenv()
# 2) fallback robusto: backend/.env relativo a este archivo
_ENV_BACKEND = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_ENV_BACKEND):
    load_dotenv(_ENV_BACKEND, override=False)

_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


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
    with _pool_lock:
        if _pool is None:
            _pool = PoolAplicacion(
                conninfo=obtener_database_url(),
                min_size=1,
                max_size=5,
                timeout=8,
                max_idle=300,
                max_lifetime=1800,
                kwargs={"connect_timeout": 5, "keepalives_idle": 10,
                        "keepalives_interval": 5, "keepalives_count": 3,
                        "tcp_user_timeout": 15000},
                check=ConnectionPool.check_connection,
                open=True,
            )
    return _pool


def cerrar_pool() -> None:
    """Cierra el pool de conexiones si está abierto."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool = None

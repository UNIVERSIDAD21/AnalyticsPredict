# -*- coding: utf-8 -*-
"""Rutas de operación C2: observabilidad mínima de componentes críticos."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter

from db import obtener_pool
from servicios.auth_store import obtener_auth_store

router = APIRouter(prefix="/api/operacion", tags=["Operacion-C2"])


def _db_info(path_env: str, default_path: str, checks: dict[str, str]) -> dict:
    db_path = os.getenv(path_env, default_path)
    exists = os.path.exists(db_path)
    info: dict[str, object] = {
        "path": db_path,
        "exists": exists,
        "size_bytes": os.path.getsize(db_path) if exists else 0,
        "checks": {},
        "status": "ok" if exists else "missing",
    }

    if not exists:
        return info

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        for key, sql in checks.items():
            row = conn.execute(sql).fetchone()
            value = 0
            if row is not None:
                first_key = row.keys()[0]
                value = row[first_key]
            info["checks"][key] = value
        conn.close()
    except Exception as exc:  # pragma: no cover
        info["status"] = "error"
        info["error"] = str(exc)

    return info


@router.get("/c2/health-auth")
def health_auth_store():
    """Diagnóstico explícito del driver auth y su fuente de verdad."""
    store = obtener_auth_store()
    driver = "postgres" if "Postgres" in type(store).__name__ else "sqlite"

    info: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "driver": driver,
        "store_class": type(store).__name__,
        "expected_source_table": "usuarios",
        "database_url_present": bool(os.getenv("DATABASE_URL")),
        "auth_store_driver_env": os.getenv("AUTH_STORE_DRIVER"),
    }

    if driver == "sqlite":
        info["warning"] = "Auth está usando SQLite. Si quieres Postgres, define AUTH_STORE_DRIVER=postgres o DATABASE_URL."
        info["db_path"] = getattr(store, "db_path", None)
        return {"ok": True, "data": info}

    # Verificación operativa en Postgres
    try:
        with obtener_pool().connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM usuarios")
                usuarios_count = cur.fetchone()[0]
                cur.execute("SELECT to_regclass('public.auth_users')")
                auth_users_table = cur.fetchone()[0]
        info["usuarios_count"] = usuarios_count
        info["auth_users_table_exists"] = bool(auth_users_table)
        info["status"] = "ok"
    except Exception as exc:  # pragma: no cover
        info["status"] = "error"
        info["error"] = str(exc)

    return {"ok": True, "data": info}


@router.get("/c2/health-critical")
def health_critical_components():
    now = datetime.now(timezone.utc).isoformat()

    pagos_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "pagos.db"))
    auth_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "auth.db"))

    pagos = _db_info(
        "PAGOS_DB_PATH",
        pagos_default,
        {
            "payment_intents": "SELECT COUNT(*) as n FROM payment_intents",
            "subscriptions": "SELECT COUNT(*) as n FROM subscriptions",
            "payment_events": "SELECT COUNT(*) as n FROM payment_events",
        },
    )
    auth = _db_info(
        "AUTH_DB_PATH",
        auth_default,
        {
            "usuarios": "SELECT COUNT(*) as n FROM usuarios",
            "tokens_revocados": "SELECT COUNT(*) as n FROM tokens_revocados",
        },
    )

    overall = "ok"
    if pagos.get("status") != "ok" or auth.get("status") != "ok":
        overall = "degraded"

    return {
        "ok": True,
        "data": {
            "timestamp": now,
            "overall": overall,
            "components": {
                "pagos_store": pagos,
                "auth_store": auth,
            },
        },
    }

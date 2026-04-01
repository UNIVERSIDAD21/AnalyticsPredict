# -*- coding: utf-8 -*-
"""Ingesta simple de eventos de producto (Fase F)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime

from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/product-analytics", tags=["ProductAnalytics"])


class ProductAnalyticsStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS product_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert(self, name: str, payload: dict | None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO product_events (name, payload_json, created_at) VALUES (?, ?, ?)",
                (name, json.dumps(payload or {}, ensure_ascii=False), datetime.utcnow().isoformat()),
            )
            conn.commit()


def _resolver_ruta_store(path_env: str | None, nombre_archivo_default: str) -> str:
    base_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if path_env and path_env.strip():
        candidata = path_env.strip()
        if not os.path.isabs(candidata):
            normalizada = candidata.replace("\\", "/")
            if normalizada.startswith("backend/"):
                candidata = normalizada[len("backend/"):]
            return os.path.abspath(os.path.join(base_backend, candidata))
        return candidata
    return os.path.join(base_backend, "data", nombre_archivo_default)


def _store() -> ProductAnalyticsStore:
    path = _resolver_ruta_store(os.getenv("PRODUCT_ANALYTICS_DB_PATH"), "product_analytics.db")
    return ProductAnalyticsStore(path)


@router.post("/events")
def ingest_event(
    name: str = Body(..., embed=True),
    payload: dict | None = Body(default=None, embed=True),
):
    _store().insert(name=name, payload=payload)
    return {"ok": True, "data": {"stored": True}}

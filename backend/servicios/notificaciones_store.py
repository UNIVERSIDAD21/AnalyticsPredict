# -*- coding: utf-8 -*-
"""Persistencia B4 de preferencias e historial de notificaciones."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Protocol


class NotificacionesStore(Protocol):
    def obtener_preferencias(self, user_id: str) -> dict: ...
    def guardar_preferencias(self, user_id: str, preferencias: dict) -> dict: ...
    def registrar_envio(self, user_id: str, canal: str, tipo: str, estado: str, detalle: str | None = None) -> dict: ...
    def listar_envios(self, user_id: str, limit: int = 20) -> list[dict]: ...


_PREFS_DEFAULT = {
    "email_habilitado": True,
    "alertas_partidos": True,
    "alertas_suscripcion": True,
    "resumen_semanal": False,
}


class SQLiteNotificacionesStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._inicializar()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _inicializar(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notificaciones_preferencias (
                  user_id TEXT PRIMARY KEY,
                  prefs_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notificaciones_envios (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  canal TEXT NOT NULL,
                  tipo TEXT NOT NULL,
                  estado TEXT NOT NULL,
                  detalle TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )

    def obtener_preferencias(self, user_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT prefs_json, updated_at FROM notificaciones_preferencias WHERE user_id=?",
                (user_id,),
            ).fetchone()

        if not row:
            return {"preferencias": dict(_PREFS_DEFAULT), "updated_at": None}

        prefs = json.loads(row["prefs_json"])
        merged = {**_PREFS_DEFAULT, **prefs}
        return {"preferencias": merged, "updated_at": row["updated_at"]}

    def guardar_preferencias(self, user_id: str, preferencias: dict) -> dict:
        merged = {**_PREFS_DEFAULT, **preferencias}
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO notificaciones_preferencias(user_id, prefs_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  prefs_json=excluded.prefs_json,
                  updated_at=excluded.updated_at
                """,
                (user_id, json.dumps(merged, ensure_ascii=False), updated_at),
            )
        return {"preferencias": merged, "updated_at": updated_at}

    def registrar_envio(self, user_id: str, canal: str, tipo: str, estado: str, detalle: str | None = None) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO notificaciones_envios(user_id, canal, tipo, estado, detalle, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, canal, tipo, estado, detalle, created_at),
            )
            envio_id = int(cur.lastrowid)
        return {
            "id": envio_id,
            "user_id": user_id,
            "canal": canal,
            "tipo": tipo,
            "estado": estado,
            "detalle": detalle,
            "created_at": created_at,
        }

    def listar_envios(self, user_id: str, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, canal, tipo, estado, detalle, created_at
                FROM notificaciones_envios
                WHERE user_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def obtener_notificaciones_store() -> NotificacionesStore:
    db_path = os.getenv(
        "NOTIFICACIONES_DB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "notificaciones.db")),
    )
    return SQLiteNotificacionesStore(db_path)

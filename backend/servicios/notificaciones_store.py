# -*- coding: utf-8 -*-
"""Persistencia B4 de preferencias, historial y cola de notificaciones."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator, Protocol


class NotificacionesStore(Protocol):
    def obtener_preferencias(self, user_id: str) -> dict: ...
    def guardar_preferencias(self, user_id: str, preferencias: dict) -> dict: ...
    def listar_usuarios_con_preferencias(self) -> list[dict]: ...
    def registrar_envio(self, user_id: str, canal: str, tipo: str, estado: str, detalle: str | None = None) -> dict: ...
    def listar_envios(self, user_id: str, limit: int = 20) -> list[dict]: ...
    def resumen_envios(self, user_id: str, horas: int = 24) -> dict: ...
    def encolar_notificacion(self, user_id: str, email: str, tipo: str, asunto: str, mensaje: str, max_intentos: int = 3) -> dict: ...
    def obtener_pendientes(self, user_id: str | None = None, limit: int = 20) -> list[dict]: ...
    def marcar_procesada(self, queue_id: int) -> None: ...
    def marcar_fallida(self, queue_id: int, intentos: int, max_intentos: int, detalle: str) -> str: ...


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notificaciones_cola (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT NOT NULL,
                  email TEXT NOT NULL,
                  tipo TEXT NOT NULL,
                  asunto TEXT NOT NULL,
                  mensaje TEXT NOT NULL,
                  estado TEXT NOT NULL,
                  intentos INTEGER NOT NULL DEFAULT 0,
                  max_intentos INTEGER NOT NULL DEFAULT 3,
                  proximo_intento_at TEXT NOT NULL,
                  last_error TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
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

    def listar_usuarios_con_preferencias(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT user_id, prefs_json, updated_at FROM notificaciones_preferencias"
            ).fetchall()

        users: list[dict] = []
        for row in rows:
            prefs = json.loads(row["prefs_json"])
            users.append(
                {
                    "user_id": row["user_id"],
                    "preferencias": {**_PREFS_DEFAULT, **prefs},
                    "updated_at": row["updated_at"],
                }
            )
        return users

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

    def resumen_envios(self, user_id: str, horas: int = 24) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT tipo, estado, COUNT(*) as total
                FROM notificaciones_envios
                WHERE user_id=?
                GROUP BY tipo, estado
                """,
                (user_id,),
            ).fetchall()

        por_tipo: dict[str, dict[str, int]] = {}
        total_enviados = 0
        total_fallidos = 0
        total_omitidos = 0
        total_reprogramados = 0

        for row in rows:
            tipo = str(row["tipo"])
            estado = str(row["estado"])
            total = int(row["total"] or 0)
            bucket = por_tipo.setdefault(tipo, {"enviado": 0, "fallido": 0, "omitido": 0, "pendiente": 0})
            bucket[estado] = bucket.get(estado, 0) + total

            if estado == "enviado":
                total_enviados += total
            elif estado == "fallido":
                total_fallidos += total
            elif estado == "omitido":
                total_omitidos += total
            elif estado == "pendiente":
                total_reprogramados += total

        total_intentos = total_enviados + total_fallidos
        tasa_entrega = (total_enviados / total_intentos * 100.0) if total_intentos > 0 else None

        return {
            "ventana_horas": int(horas),
            "totales": {
                "enviados": total_enviados,
                "fallidos": total_fallidos,
                "omitidos": total_omitidos,
                "reprogramados": total_reprogramados,
            },
            "tasa_entrega_pct": round(tasa_entrega, 2) if tasa_entrega is not None else None,
            "por_tipo": por_tipo,
        }

    def encolar_notificacion(self, user_id: str, email: str, tipo: str, asunto: str, mensaje: str, max_intentos: int = 3) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO notificaciones_cola(
                  user_id, email, tipo, asunto, mensaje, estado,
                  intentos, max_intentos, proximo_intento_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'pendiente', 0, ?, ?, ?, ?)
                """,
                (user_id, email, tipo, asunto, mensaje, max_intentos, now, now, now),
            )
            queue_id = int(cur.lastrowid)
        return {
            "id": queue_id,
            "user_id": user_id,
            "email": email,
            "tipo": tipo,
            "estado": "pendiente",
            "intentos": 0,
            "max_intentos": max_intentos,
            "proximo_intento_at": now,
        }

    def obtener_pendientes(self, user_id: str | None = None, limit: int = 20) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            if user_id:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM notificaciones_cola
                    WHERE user_id=? AND estado='pendiente' AND proximo_intento_at <= ?
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (user_id, now, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM notificaciones_cola
                    WHERE estado='pendiente' AND proximo_intento_at <= ?
                    ORDER BY id ASC
                    LIMIT ?
                    """,
                    (now, limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def marcar_procesada(self, queue_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "UPDATE notificaciones_cola SET estado='enviado', updated_at=? WHERE id=?",
                (now, queue_id),
            )

    def marcar_fallida(self, queue_id: int, intentos: int, max_intentos: int, detalle: str) -> str:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()

        if intentos >= max_intentos:
            nuevo_estado = "fallido"
            proximo = now
        else:
            nuevo_estado = "pendiente"
            backoff_min = min(30, 2 ** max(1, intentos))
            proximo = (now_dt + timedelta(minutes=backoff_min)).isoformat()

        with self._conn() as conn:
            conn.execute(
                """
                UPDATE notificaciones_cola
                SET estado=?, intentos=?, last_error=?, proximo_intento_at=?, updated_at=?
                WHERE id=?
                """,
                (nuevo_estado, intentos, detalle, proximo, now, queue_id),
            )
        return nuevo_estado


def obtener_notificaciones_store() -> NotificacionesStore:
    db_path = os.getenv(
        "NOTIFICACIONES_DB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "notificaciones.db")),
    )
    return SQLiteNotificacionesStore(db_path)

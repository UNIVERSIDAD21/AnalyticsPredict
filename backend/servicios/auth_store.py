# -*- coding: utf-8 -*-
"""Persistencia simple de autenticación sobre SQLite para staging/desarrollo."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator


class AuthStore:
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
                CREATE TABLE IF NOT EXISTS auth_users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_reset_tokens (
                  token TEXT PRIMARY KEY,
                  user_id INTEGER NOT NULL,
                  expires_at TEXT NOT NULL,
                  used INTEGER NOT NULL DEFAULT 0,
                  FOREIGN KEY(user_id) REFERENCES auth_users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_revoked_tokens (
                  jti TEXT PRIMARY KEY,
                  revoked_at TEXT NOT NULL
                )
                """
            )

    def crear_usuario(self, email: str, password_hash: str) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO auth_users(email, password_hash, created_at) VALUES (?, ?, ?)",
                (email.lower().strip(), password_hash, created_at),
            )
            user_id = cur.lastrowid
        return {"id": user_id, "email": email.lower().strip(), "created_at": created_at}

    def obtener_usuario_por_email(self, email: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash, created_at FROM auth_users WHERE email=?",
                (email.lower().strip(),),
            ).fetchone()
        return dict(row) if row else None

    def obtener_usuario_por_id(self, user_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash, created_at FROM auth_users WHERE id=?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def guardar_reset_token(self, user_id: int, token: str, expires_at: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO auth_reset_tokens(token, user_id, expires_at, used) VALUES (?, ?, ?, 0)",
                (token, user_id, expires_at),
            )

    def validar_reset_token(self, token: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT token, user_id, expires_at, used FROM auth_reset_tokens WHERE token=?",
                (token,),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        if data["used"]:
            return None
        exp = datetime.fromisoformat(data["expires_at"])
        if exp < datetime.now(timezone.utc):
            return None
        return data

    def marcar_reset_token_usado(self, token: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE auth_reset_tokens SET used=1 WHERE token=?", (token,))

    def actualizar_password(self, user_id: int, password_hash: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE auth_users SET password_hash=? WHERE id=?",
                (password_hash, user_id),
            )

    def revocar_jti(self, jti: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO auth_revoked_tokens(jti, revoked_at) VALUES (?, ?)",
                (jti, datetime.now(timezone.utc).isoformat()),
            )

    def token_revocado(self, jti: str) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT jti FROM auth_revoked_tokens WHERE jti=?", (jti,)).fetchone()
        return row is not None


def obtener_auth_store() -> AuthStore:
    db_path = os.getenv("AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "auth.db"))
    db_path = os.path.abspath(db_path)
    return AuthStore(db_path)

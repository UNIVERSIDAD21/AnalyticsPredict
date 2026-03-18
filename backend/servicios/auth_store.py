# -*- coding: utf-8 -*-
"""Persistencia de autenticación (SQLite para dev y PostgreSQL para staging/prod)."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Protocol


class AuthStore(Protocol):
    def crear_usuario(self, email: str, password_hash: str, legal_version: str | None = None) -> dict: ...
    def obtener_usuario_por_email(self, email: str) -> dict | None: ...
    def obtener_usuario_por_id(self, user_id: int) -> dict | None: ...
    def guardar_reset_token(self, user_id: int, token: str, expires_at: str) -> None: ...
    def validar_reset_token(self, token: str) -> dict | None: ...
    def marcar_reset_token_usado(self, token: str) -> None: ...
    def actualizar_password(self, user_id: int, password_hash: str) -> None: ...
    def revocar_jti(self, jti: str) -> None: ...
    def token_revocado(self, jti: str) -> bool: ...


class SQLiteAuthStore:
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

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        names = {row[1] for row in cols}
        if column not in names:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _inicializar(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  legal_accepted_version TEXT,
                  legal_accepted_at TEXT
                )
                """
            )
            self._ensure_column(conn, "auth_users", "legal_accepted_version", "TEXT")
            self._ensure_column(conn, "auth_users", "legal_accepted_at", "TEXT")
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

    def crear_usuario(self, email: str, password_hash: str, legal_version: str | None = None) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        normalized_email = email.lower().strip()
        legal_accepted_at = created_at if legal_version else None
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO auth_users(email, password_hash, created_at, legal_accepted_version, legal_accepted_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (normalized_email, password_hash, created_at, legal_version, legal_accepted_at),
            )
            user_id = cur.lastrowid
        return {
            "id": user_id,
            "email": normalized_email,
            "created_at": created_at,
            "legal_accepted_version": legal_version,
            "legal_accepted_at": legal_accepted_at,
        }

    def obtener_usuario_por_email(self, email: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash, created_at, legal_accepted_version, legal_accepted_at FROM auth_users WHERE email=?",
                (email.lower().strip(),),
            ).fetchone()
        return dict(row) if row else None

    def obtener_usuario_por_id(self, user_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, email, password_hash, created_at, legal_accepted_version, legal_accepted_at FROM auth_users WHERE id=?",
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


class PostgresAuthStore:
    def __init__(self):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool
        from db import obtener_database_url

        self._dict_row = dict_row
        self._pool = ConnectionPool(
            conninfo=obtener_database_url(),
            min_size=1,
            max_size=5,
            max_idle=300,
            max_lifetime=1800,
            open=True,
        )
        self._inicializar()

    @contextmanager
    def _conn(self):
        with self._pool.connection() as conn:
            conn.row_factory = self._dict_row
            with conn.cursor() as cur:
                yield conn, cur
            conn.commit()

    def _inicializar(self) -> None:
        with self._conn() as (_, cur):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                  id BIGSERIAL PRIMARY KEY,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  legal_accepted_version TEXT,
                  legal_accepted_at TIMESTAMPTZ
                )
                """
            )
            cur.execute("ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS legal_accepted_version TEXT")
            cur.execute("ALTER TABLE auth_users ADD COLUMN IF NOT EXISTS legal_accepted_at TIMESTAMPTZ")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_reset_tokens (
                  token TEXT PRIMARY KEY,
                  user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
                  expires_at TIMESTAMPTZ NOT NULL,
                  used BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_revoked_tokens (
                  jti TEXT PRIMARY KEY,
                  revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

    def crear_usuario(self, email: str, password_hash: str, legal_version: str | None = None) -> dict:
        normalized_email = email.lower().strip()
        with self._conn() as (_, cur):
            cur.execute(
                """
                INSERT INTO auth_users(email, password_hash, legal_accepted_version, legal_accepted_at)
                VALUES (%s, %s, %s, CASE WHEN %s IS NULL THEN NULL ELSE NOW() END)
                RETURNING id, email, password_hash, created_at, legal_accepted_version, legal_accepted_at
                """,
                (normalized_email, password_hash, legal_version, legal_version),
            )
            row = cur.fetchone()
        return dict(row)

    def obtener_usuario_por_email(self, email: str) -> dict | None:
        with self._conn() as (_, cur):
            cur.execute(
                "SELECT id, email, password_hash, created_at, legal_accepted_version, legal_accepted_at FROM auth_users WHERE email=%s",
                (email.lower().strip(),),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    def obtener_usuario_por_id(self, user_id: int) -> dict | None:
        with self._conn() as (_, cur):
            cur.execute(
                "SELECT id, email, password_hash, created_at, legal_accepted_version, legal_accepted_at FROM auth_users WHERE id=%s",
                (user_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    def guardar_reset_token(self, user_id: int, token: str, expires_at: str) -> None:
        with self._conn() as (_, cur):
            cur.execute(
                """
                INSERT INTO auth_reset_tokens(token, user_id, expires_at, used)
                VALUES (%s, %s, %s, FALSE)
                """,
                (token, user_id, expires_at),
            )

    def validar_reset_token(self, token: str) -> dict | None:
        with self._conn() as (_, cur):
            cur.execute(
                "SELECT token, user_id, expires_at, used FROM auth_reset_tokens WHERE token=%s",
                (token,),
            )
            row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        if data["used"]:
            return None
        exp = data["expires_at"]
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
        return data

    def marcar_reset_token_usado(self, token: str) -> None:
        with self._conn() as (_, cur):
            cur.execute("UPDATE auth_reset_tokens SET used=TRUE WHERE token=%s", (token,))

    def actualizar_password(self, user_id: int, password_hash: str) -> None:
        with self._conn() as (_, cur):
            cur.execute("UPDATE auth_users SET password_hash=%s WHERE id=%s", (password_hash, user_id))

    def revocar_jti(self, jti: str) -> None:
        with self._conn() as (_, cur):
            cur.execute(
                """
                INSERT INTO auth_revoked_tokens(jti, revoked_at)
                VALUES (%s, NOW())
                ON CONFLICT (jti) DO UPDATE SET revoked_at=EXCLUDED.revoked_at
                """,
                (jti,),
            )

    def token_revocado(self, jti: str) -> bool:
        with self._conn() as (_, cur):
            cur.execute("SELECT jti FROM auth_revoked_tokens WHERE jti=%s", (jti,))
            row = cur.fetchone()
        return row is not None


def obtener_auth_store() -> AuthStore:
    driver = os.getenv("AUTH_STORE_DRIVER", "sqlite").strip().lower()

    if driver == "postgres":
        return PostgresAuthStore()

    db_path = os.getenv("AUTH_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "auth.db"))
    db_path = os.path.abspath(db_path)
    return SQLiteAuthStore(db_path)

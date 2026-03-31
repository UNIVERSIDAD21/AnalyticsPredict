# -*- coding: utf-8 -*-
"""Persistencia B2 para onboarding y eventos de conversión."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Protocol


class OnboardingStore(Protocol):
    def guardar_onboarding(self, user_id: int, perfil: dict) -> dict: ...
    def obtener_onboarding(self, user_id: int) -> dict | None: ...
    def registrar_evento(self, user_id: int, event_name: str, event_ts: str, metadata: dict | None = None) -> None: ...
    def obtener_kpis_conversion(self) -> dict: ...


class SQLiteOnboardingStore:
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
                CREATE TABLE IF NOT EXISTS onboarding_profiles (
                  user_id INTEGER PRIMARY KEY,
                  nombre TEXT NOT NULL,
                  objetivo_principal TEXT NOT NULL,
                  deporte_preferido TEXT NOT NULL,
                  frecuencia TEXT NOT NULL,
                  bankroll_referencial REAL,
                  completado INTEGER NOT NULL DEFAULT 1,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS onboarding_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  event_name TEXT NOT NULL,
                  event_ts TEXT NOT NULL,
                  metadata_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )

    def guardar_onboarding(self, user_id: int, perfil: dict) -> dict:
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO onboarding_profiles(
                  user_id, nombre, objetivo_principal, deporte_preferido, frecuencia,
                  bankroll_referencial, completado, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  nombre=excluded.nombre,
                  objetivo_principal=excluded.objetivo_principal,
                  deporte_preferido=excluded.deporte_preferido,
                  frecuencia=excluded.frecuencia,
                  bankroll_referencial=excluded.bankroll_referencial,
                  completado=1,
                  updated_at=excluded.updated_at
                """,
                (
                    user_id,
                    perfil["nombre"],
                    perfil["objetivo_principal"],
                    perfil["deporte_preferido"],
                    perfil["frecuencia"],
                    perfil.get("bankroll_referencial"),
                    updated_at,
                ),
            )

        return self.obtener_onboarding(user_id) or {
            "completado": True,
            "updated_at": updated_at,
            "perfil": perfil,
        }

    def obtener_onboarding(self, user_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT user_id, nombre, objetivo_principal, deporte_preferido,
                       frecuencia, bankroll_referencial, completado, updated_at
                FROM onboarding_profiles
                WHERE user_id=?
                """,
                (user_id,),
            ).fetchone()

        if not row:
            return None

        return {
            "completado": bool(row["completado"]),
            "updated_at": row["updated_at"],
            "perfil": {
                "nombre": row["nombre"],
                "objetivo_principal": row["objetivo_principal"],
                "deporte_preferido": row["deporte_preferido"],
                "frecuencia": row["frecuencia"],
                "bankroll_referencial": row["bankroll_referencial"],
            },
        }

    def registrar_evento(self, user_id: int, event_name: str, event_ts: str, metadata: dict | None = None) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO onboarding_events(user_id, event_name, event_ts, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    event_name,
                    event_ts,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def obtener_kpis_conversion(self) -> dict:
        with self._conn() as conn:
            iniciados = conn.execute(
                "SELECT COUNT(DISTINCT user_id) AS total FROM onboarding_events WHERE event_name='onboarding_started'"
            ).fetchone()["total"]
            completados_evento = conn.execute(
                "SELECT COUNT(DISTINCT user_id) AS total FROM onboarding_events WHERE event_name='onboarding_completed'"
            ).fetchone()["total"]
            completados_perfil = conn.execute(
                "SELECT COUNT(*) AS total FROM onboarding_profiles WHERE completado=1"
            ).fetchone()["total"]

            completados = max(int(completados_evento or 0), int(completados_perfil or 0))
            iniciados = int(iniciados or 0)
            completion_rate = (completados / iniciados * 100.0) if iniciados > 0 else 0.0

            rows = conn.execute(
                """
                SELECT user_id, event_name, event_ts
                FROM onboarding_events
                WHERE event_name IN ('onboarding_completed', 'dashboard_viewed')
                ORDER BY user_id, event_ts ASC
                """
            ).fetchall()

        por_usuario: dict[int, dict[str, str | None]] = {}
        for row in rows:
            uid = int(row["user_id"])
            data = por_usuario.setdefault(uid, {"onboarding_completed": None, "dashboard_viewed": None})
            event_name = row["event_name"]
            if data.get(event_name) is None:
                data[event_name] = row["event_ts"]

        deltas_min = []
        for data in por_usuario.values():
            start = data.get("onboarding_completed")
            end = data.get("dashboard_viewed")
            if not start or not end:
                continue
            try:
                dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                delta = (dt_end - dt_start).total_seconds() / 60.0
                if delta >= 0:
                    deltas_min.append(delta)
            except Exception:
                continue

        ttv_avg = sum(deltas_min) / len(deltas_min) if deltas_min else None

        return {
            "started_users": iniciados,
            "completed_users": completados,
            "completion_rate_pct": round(completion_rate, 2),
            "time_to_value_minutes_avg": round(ttv_avg, 2) if ttv_avg is not None else None,
            "ttv_sample_size": len(deltas_min),
        }


class PostgresOnboardingStore:
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
                CREATE TABLE IF NOT EXISTS onboarding_profiles (
                  user_id BIGINT PRIMARY KEY,
                  nombre TEXT NOT NULL,
                  objetivo_principal TEXT NOT NULL,
                  deporte_preferido TEXT NOT NULL,
                  frecuencia TEXT NOT NULL,
                  bankroll_referencial DOUBLE PRECISION,
                  completado BOOLEAN NOT NULL DEFAULT TRUE,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS onboarding_events (
                  id BIGSERIAL PRIMARY KEY,
                  user_id BIGINT NOT NULL,
                  event_name TEXT NOT NULL,
                  event_ts TIMESTAMPTZ NOT NULL,
                  metadata_json JSONB,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

    def guardar_onboarding(self, user_id: int, perfil: dict) -> dict:
        with self._conn() as (_, cur):
            cur.execute(
                """
                INSERT INTO onboarding_profiles(
                  user_id, nombre, objetivo_principal, deporte_preferido,
                  frecuencia, bankroll_referencial, completado, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                  nombre=EXCLUDED.nombre,
                  objetivo_principal=EXCLUDED.objetivo_principal,
                  deporte_preferido=EXCLUDED.deporte_preferido,
                  frecuencia=EXCLUDED.frecuencia,
                  bankroll_referencial=EXCLUDED.bankroll_referencial,
                  completado=TRUE,
                  updated_at=NOW()
                """,
                (
                    user_id,
                    perfil["nombre"],
                    perfil["objetivo_principal"],
                    perfil["deporte_preferido"],
                    perfil["frecuencia"],
                    perfil.get("bankroll_referencial"),
                ),
            )
        return self.obtener_onboarding(user_id) or {"completado": True, "updated_at": None, "perfil": perfil}

    def obtener_onboarding(self, user_id: int) -> dict | None:
        with self._conn() as (_, cur):
            cur.execute(
                """
                SELECT user_id, nombre, objetivo_principal, deporte_preferido,
                       frecuencia, bankroll_referencial, completado, updated_at
                FROM onboarding_profiles
                WHERE user_id=%s
                """,
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        return {
            "completado": bool(row["completado"]),
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "perfil": {
                "nombre": row["nombre"],
                "objetivo_principal": row["objetivo_principal"],
                "deporte_preferido": row["deporte_preferido"],
                "frecuencia": row["frecuencia"],
                "bankroll_referencial": row["bankroll_referencial"],
            },
        }

    def registrar_evento(self, user_id: int, event_name: str, event_ts: str, metadata: dict | None = None) -> None:
        with self._conn() as (_, cur):
            cur.execute(
                """
                INSERT INTO onboarding_events(user_id, event_name, event_ts, metadata_json)
                VALUES (%s, %s, %s, %s::jsonb)
                """,
                (user_id, event_name, event_ts, json.dumps(metadata or {}, ensure_ascii=False)),
            )

    def obtener_kpis_conversion(self) -> dict:
        with self._conn() as (_, cur):
            cur.execute("SELECT COUNT(DISTINCT user_id) AS total FROM onboarding_events WHERE event_name='onboarding_started'")
            iniciados = int((cur.fetchone() or {}).get("total", 0) or 0)

            cur.execute("SELECT COUNT(DISTINCT user_id) AS total FROM onboarding_events WHERE event_name='onboarding_completed'")
            completados_evento = int((cur.fetchone() or {}).get("total", 0) or 0)

            cur.execute("SELECT COUNT(*) AS total FROM onboarding_profiles WHERE completado=TRUE")
            completados_perfil = int((cur.fetchone() or {}).get("total", 0) or 0)

            completados = max(completados_evento, completados_perfil)
            completion_rate = (completados / iniciados * 100.0) if iniciados > 0 else 0.0

            cur.execute(
                """
                SELECT user_id, event_name, event_ts
                FROM onboarding_events
                WHERE event_name IN ('onboarding_completed', 'dashboard_viewed')
                ORDER BY user_id, event_ts ASC
                """
            )
            rows = cur.fetchall() or []

        por_usuario: dict[int, dict[str, datetime | None]] = {}
        for row in rows:
            uid = int(row["user_id"])
            data = por_usuario.setdefault(uid, {"onboarding_completed": None, "dashboard_viewed": None})
            event_name = row["event_name"]
            if data.get(event_name) is None:
                data[event_name] = row["event_ts"]

        deltas_min = []
        for data in por_usuario.values():
            start = data.get("onboarding_completed")
            end = data.get("dashboard_viewed")
            if not start or not end:
                continue
            delta = (end - start).total_seconds() / 60.0
            if delta >= 0:
                deltas_min.append(delta)

        ttv_avg = sum(deltas_min) / len(deltas_min) if deltas_min else None

        return {
            "started_users": iniciados,
            "completed_users": completados,
            "completion_rate_pct": round(completion_rate, 2),
            "time_to_value_minutes_avg": round(ttv_avg, 2) if ttv_avg is not None else None,
            "ttv_sample_size": len(deltas_min),
        }


def obtener_onboarding_store() -> OnboardingStore:
    driver_raw = os.getenv("ONBOARDING_STORE_DRIVER")
    if driver_raw and driver_raw.strip():
        driver = driver_raw.strip().lower()
    else:
        # Si onboarding no está definido, heredar driver de auth para evitar desalineación.
        driver = os.getenv("AUTH_STORE_DRIVER", "sqlite").strip().lower()

    if driver == "postgres":
        return PostgresOnboardingStore()

    default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "onboarding.db"))
    db_path = os.getenv("ONBOARDING_DB_PATH")
    if not db_path:
        auth_path = os.getenv("AUTH_DB_PATH")
        if auth_path:
            auth_dir = os.path.dirname(os.path.abspath(auth_path))
            db_path = os.path.join(auth_dir, "onboarding.db")
        else:
            db_path = default_path
    return SQLiteOnboardingStore(db_path)

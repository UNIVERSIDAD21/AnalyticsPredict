# -*- coding: utf-8 -*-
"""Store de pagos/suscripciones con idempotencia de webhook y trazabilidad."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator


TERMINAL_PAYMENT_STATUSES = {"approved", "rejected", "cancelled", "refunded", "charged_back"}


class PagosStore:
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
                CREATE TABLE IF NOT EXISTS payment_intents (
                  external_reference TEXT PRIMARY KEY,
                  user_id INTEGER NOT NULL,
                  plan_id TEXT NOT NULL,
                  amount_cents INTEGER NOT NULL,
                  currency TEXT NOT NULL,
                  status TEXT NOT NULL,
                  payment_id TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                  user_id INTEGER PRIMARY KEY,
                  plan_id TEXT NOT NULL,
                  status TEXT NOT NULL,
                  activated_at TEXT NOT NULL,
                  expires_at TEXT NOT NULL,
                  source_payment_id TEXT,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  external_reference TEXT NOT NULL,
                  payment_id TEXT NOT NULL,
                  status TEXT NOT NULL,
                  payload_json TEXT,
                  processed_at TEXT NOT NULL,
                  UNIQUE(external_reference, payment_id, status)
                )
                """
            )

    def crear_checkout(self, *, user_id: int, plan_id: str, amount_cents: int, currency: str, external_reference: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO payment_intents(
                    external_reference, user_id, plan_id, amount_cents, currency, status, payment_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
                """,
                (external_reference, user_id, plan_id, amount_cents, currency.upper(), now, now),
            )
        return {
            "external_reference": external_reference,
            "status": "pending",
        }

    def registrar_evento_webhook(
        self,
        *,
        external_reference: str,
        payment_id: str,
        status: str,
        payload_json: str | None,
    ) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """
                    INSERT INTO payment_events(external_reference, payment_id, status, payload_json, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (external_reference, payment_id, status.lower(), payload_json, now),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def marcar_pago(self, *, external_reference: str, payment_id: str, status: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()
        status = status.lower().strip()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT external_reference, user_id, plan_id, amount_cents, currency, status, payment_id FROM payment_intents WHERE external_reference=?",
                (external_reference,),
            ).fetchone()
            if not row:
                return None

            current_status = (row["status"] or "").lower()
            current_payment_id = row["payment_id"]

            if current_status in TERMINAL_PAYMENT_STATUSES and current_payment_id == payment_id:
                data = dict(row)
                data["idempotent"] = True
                return data

            conn.execute(
                """
                UPDATE payment_intents
                SET payment_id=?, status=?, updated_at=?
                WHERE external_reference=?
                """,
                (payment_id, status, now, external_reference),
            )

        data = dict(row)
        data["status"] = status
        data["payment_id"] = payment_id
        data["idempotent"] = False
        return data

    def activar_suscripcion(self, *, user_id: int, plan_id: str, payment_id: str, duracion_dias: int = 30) -> dict:
        activated_at = datetime.now(timezone.utc)
        expires_at = activated_at + timedelta(days=duracion_dias)
        now = activated_at.isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO subscriptions(user_id, plan_id, status, activated_at, expires_at, source_payment_id, updated_at)
                VALUES (?, ?, 'active', ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  plan_id=excluded.plan_id,
                  status='active',
                  activated_at=excluded.activated_at,
                  expires_at=excluded.expires_at,
                  source_payment_id=excluded.source_payment_id,
                  updated_at=excluded.updated_at
                """,
                (user_id, plan_id, activated_at.isoformat(), expires_at.isoformat(), payment_id, now),
            )
        return {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "activated_at": activated_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "source_payment_id": payment_id,
            "updated_at": now,
        }

    def actualizar_estado_suscripcion_por_evento(self, *, user_id: int, plan_id: str, payment_status: str, payment_id: str) -> dict:
        status = payment_status.lower().strip()
        now = datetime.now(timezone.utc).isoformat()

        if status == "approved":
            return self.activar_suscripcion(user_id=user_id, plan_id=plan_id, payment_id=payment_id)

        mapped = "past_due" if status in {"in_process", "pending"} else "inactive"

        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id, plan_id, status, activated_at, expires_at, source_payment_id FROM subscriptions WHERE user_id=?",
                (user_id,),
            ).fetchone()

            if row:
                conn.execute(
                    """
                    UPDATE subscriptions
                    SET status=?, source_payment_id=?, updated_at=?
                    WHERE user_id=?
                    """,
                    (mapped, payment_id, now, user_id),
                )
                base = dict(row)
                base["status"] = mapped
                base["source_payment_id"] = payment_id
                base["updated_at"] = now
                return base

            activated_at = now
            expires_at = now
            conn.execute(
                """
                INSERT INTO subscriptions(user_id, plan_id, status, activated_at, expires_at, source_payment_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, plan_id, mapped, activated_at, expires_at, payment_id, now),
            )
            return {
                "user_id": user_id,
                "plan_id": plan_id,
                "status": mapped,
                "activated_at": activated_at,
                "expires_at": expires_at,
                "source_payment_id": payment_id,
                "updated_at": now,
            }

    def obtener_suscripcion(self, user_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id, plan_id, status, activated_at, expires_at, source_payment_id, updated_at FROM subscriptions WHERE user_id=?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return dict(row)



def obtener_pagos_store() -> PagosStore:
    path = os.getenv("PAGOS_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "pagos.db")))
    return PagosStore(path)

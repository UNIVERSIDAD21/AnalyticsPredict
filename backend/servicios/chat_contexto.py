# -*- coding: utf-8 -*-
"""B5: chat contextual local con ventana deslizante y guardrails."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Protocol


DISCLAIMER_B5 = (
    "⚠️ Este asistente ofrece información orientativa y educativa. "
    "No garantiza resultados ni constituye asesoría financiera profesional."
)


class ChatContextoStore(Protocol):
    def registrar_mensaje(self, user_id: int, role: str, contenido: str) -> dict: ...
    def obtener_ventana(self, user_id: int, limit: int = 12) -> list[dict]: ...
    def limpiar(self, user_id: int) -> None: ...


class SQLiteChatContextoStore:
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
                CREATE TABLE IF NOT EXISTS chat_contexto (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  role TEXT NOT NULL,
                  contenido TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )

    def registrar_mensaje(self, user_id: int, role: str, contenido: str) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO chat_contexto(user_id, role, contenido, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, contenido, created_at),
            )
            mensaje_id = int(cur.lastrowid)
        return {
            "id": mensaje_id,
            "user_id": user_id,
            "role": role,
            "contenido": contenido,
            "created_at": created_at,
        }

    def obtener_ventana(self, user_id: int, limit: int = 12) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, role, contenido, created_at
                FROM chat_contexto
                WHERE user_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, int(limit)),
            ).fetchall()
        data = [dict(r) for r in rows]
        data.reverse()
        return data

    def limpiar(self, user_id: int) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM chat_contexto WHERE user_id=?", (user_id,))


def _contiene_advice_sensible(texto: str) -> bool:
    t = (texto or "").lower()
    claves = [
        "garantizado",
        "apuesta segura",
        "mete todo",
        "endeud",
        "préstamo para apostar",
        "recuperar pérdidas",
        "doblar para recuperar",
        "all in",
    ]
    return any(c in t for c in claves)


def _resumen_contexto(ventana: list[dict]) -> str:
    if len(ventana) <= 12:
        return ""
    recortados = len(ventana) - 12
    return f"Se resumieron {recortados} mensajes previos para mantener foco y costo controlado."


def _respuesta_mock_inteligente(mensaje: str, ventana: list[dict]) -> str:
    texto = (mensaje or "").strip()
    lower = texto.lower()

    if _contiene_advice_sensible(lower):
        return (
            "No puedo ayudar con estrategias de riesgo extremo o recuperación compulsiva de pérdidas. "
            "Si quieres, te propongo un plan disciplinado de gestión de riesgo (stake, límites diarios y revisión de edge)."
        )

    if any(k in lower for k in ["hola", "buenas", "hey"]):
        return (
            "¡Listo! Puedo ayudarte con métricas, revisión de picks y plan de acción por riesgo. "
            "Dime si quieres enfoque en rendimiento, disciplina o aprendizaje."
        )

    if any(k in lower for k in ["win rate", "brier", "métrica", "metricas", "kpi"]):
        return (
            "Para evaluar calidad, prioriza: 1) tasa de entrega/ejecución, 2) calibración (Brier), "
            "3) estabilidad por liga y 4) disciplina de stake. Si quieres, te armo checklist de revisión diaria."
        )

    if any(k in lower for k in ["recomend", "pick", "apuesta", "partido"]):
        return (
            "Te recomiendo usar un filtro base: edge mínimo, contexto suficiente y límite de exposición por día. "
            "Puedo convertir eso en una rutina rápida por partido para decidir si entrar o pasar."
        )

    contexto = _resumen_contexto(ventana)
    base = (
        "Entendido. Tomo tu contexto y te propongo un siguiente paso accionable: "
        "define objetivo del bloque (rentabilidad, disciplina o aprendizaje), límite de riesgo y criterio de salida."
    )
    return f"{base} {contexto}".strip()


def generar_respuesta_local(mensaje_usuario: str, ventana: list[dict]) -> str:
    respuesta = _respuesta_mock_inteligente(mensaje_usuario, ventana)
    return f"{respuesta}\n\n{DISCLAIMER_B5}"


def obtener_chat_contexto_store() -> ChatContextoStore:
    db_path = os.getenv(
        "CHAT_CONTEXTO_DB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chat_contexto.db")),
    )
    return SQLiteChatContextoStore(db_path)

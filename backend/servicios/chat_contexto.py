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


def compactar_ventana_con_resumen(ventana_completa: list[dict], limite: int = 12) -> tuple[list[dict], str]:
    limite = max(4, int(limite))
    if len(ventana_completa) <= limite:
        return ventana_completa, ""

    antiguos = ventana_completa[:-limite]
    recientes = ventana_completa[-limite:]

    palabras_clave: list[str] = []
    for msg in antiguos:
        texto = str(msg.get("contenido") or "").lower()
        for k in ["riesgo", "stake", "kpi", "brier", "notificaciones", "onboarding", "partido", "apuesta"]:
            if k in texto and k not in palabras_clave:
                palabras_clave.append(k)

    recortados = len(antiguos)
    if palabras_clave:
        return (
            recientes,
            f"Se resumieron {recortados} mensajes previos. Temas detectados: {', '.join(palabras_clave[:4])}.",
        )

    return recientes, f"Se resumieron {recortados} mensajes previos para mantener foco y costo controlado."


def _plan_por_objetivo(objetivo: str, resumen_contexto: str = "") -> str:
    objetivo = (objetivo or "").lower().strip()

    if objetivo == "rentabilidad":
        plan = (
            "Plan rentabilidad (48h):\n"
            "1) Filtra picks con edge mínimo y contexto suficiente.\n"
            "2) Prioriza mercados con mejor calibración histórica.\n"
            "3) Limita exposición diaria y evita correlación alta entre picks.\n"
            "4) Cierre del día: revisa EV esperado vs resultado real."
        )
    elif objetivo == "disciplina":
        plan = (
            "Plan disciplina (48h):\n"
            "1) Define stake fijo por operación y no lo rompas.\n"
            "2) Activa stop-loss diario y stop-win moderado.\n"
            "3) Registra cada decisión en bitácora antes de ejecutar.\n"
            "4) Cierre del día: audita si seguiste reglas, no solo PnL."
        )
    elif objetivo == "aprendizaje":
        plan = (
            "Plan aprendizaje (48h):\n"
            "1) Selecciona 3 picks y documenta hipótesis previa.\n"
            "2) Compara hipótesis vs outcome y causas de error.\n"
            "3) Revisa 2 métricas clave (Brier, win-rate por contexto).\n"
            "4) Cierra con una lección accionable para la próxima jornada."
        )
    else:
        plan = (
            "Plan base sugerido:\n"
            "1) Define objetivo principal (rentabilidad/disciplina/aprendizaje).\n"
            "2) Define límite de riesgo diario.\n"
            "3) Ejecuta solo picks con criterios explícitos.\n"
            "4) Cierra el día con revisión corta y mejoras."
        )

    return f"{plan}\n{resumen_contexto}".strip()


def _respuesta_mock_inteligente(mensaje: str, ventana: list[dict], contexto_negocio: dict | None = None) -> str:
    texto = (mensaje or "").strip()
    lower = texto.lower()
    contexto_negocio = contexto_negocio or {}

    tasa_entrega = contexto_negocio.get("tasa_entrega_pct")
    completion_rate = contexto_negocio.get("completion_rate_pct")
    ttv = contexto_negocio.get("time_to_value_minutes_avg")
    resumen_contexto = str(contexto_negocio.get("resumen_contexto") or "").strip()

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
        partes = [
            "Para evaluar calidad, prioriza: 1) tasa de entrega/ejecución, 2) calibración (Brier), "
            "3) estabilidad por liga y 4) disciplina de stake."
        ]
        if isinstance(tasa_entrega, (int, float)):
            partes.append(f"Entrega notificaciones actual: {float(tasa_entrega):.1f}%.")
        if isinstance(completion_rate, (int, float)):
            partes.append(f"Completion onboarding: {float(completion_rate):.1f}%.")
        if isinstance(ttv, (int, float)):
            partes.append(f"Time-to-value promedio: {float(ttv):.1f} min.")
        partes.append("Si quieres, te armo checklist de revisión diaria con estos datos.")
        if resumen_contexto:
            partes.append(resumen_contexto)
        return " ".join(partes)

    if "rentabilidad" in lower:
        return _plan_por_objetivo("rentabilidad", resumen_contexto)

    if "disciplina" in lower:
        return _plan_por_objetivo("disciplina", resumen_contexto)

    if "aprendizaje" in lower:
        return _plan_por_objetivo("aprendizaje", resumen_contexto)

    if any(k in lower for k in ["recomend", "pick", "apuesta", "partido"]):
        base = (
            "Te recomiendo usar un filtro base: edge mínimo, contexto suficiente y límite de exposición por día. "
            "Si me dices el objetivo (rentabilidad, disciplina o aprendizaje), te doy plan 48h específico."
        )
        return f"{base} {resumen_contexto}".strip()

    base = (
        "Entendido. Tomo tu contexto y te propongo un siguiente paso accionable: "
        "define objetivo del bloque (rentabilidad, disciplina o aprendizaje), límite de riesgo y criterio de salida."
    )
    return f"{base} {resumen_contexto}".strip()


def generar_respuesta_local(mensaje_usuario: str, ventana: list[dict], contexto_negocio: dict | None = None) -> str:
    respuesta = _respuesta_mock_inteligente(mensaje_usuario, ventana, contexto_negocio=contexto_negocio)
    return f"{respuesta}\n\n{DISCLAIMER_B5}"


def obtener_chat_contexto_store() -> ChatContextoStore:
    db_path = os.getenv(
        "CHAT_CONTEXTO_DB_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chat_contexto.db")),
    )
    return SQLiteChatContextoStore(db_path)

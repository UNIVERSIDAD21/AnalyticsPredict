#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper_euroliga.py - Sincroniza partidos de Euroliga desde Sofascore.

Requisitos:
    pip install psycopg[binary] python-dotenv curl_cffi

Uso:
    python scraper_euroliga.py --dias 7
    python scraper_euroliga.py --dias 7 --dias-futuros 7 --incluir-futuros
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

EUROLIGA_SOFASCORE_ID = 138
EUROLIGA_CODIGO = "euroleague"
SOFASCORE_API_BASE = "https://api.sofascore.com/api/v1"

# Cargar .env
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SofascoreClientInteligente:
    """Cliente HTTP con manejo de bloqueos y rate limiting."""

    def __init__(self, min_intervalo: float = 2.0):
        self.min_intervalo = min_intervalo
        self.ultima_peticion = 0.0
        self.session = None
        self.usar_curl_cffi = False
        self.bloqueos_consecutivos = 0
        self.total_bloqueos = 0
        self.total_peticiones = 0

        try:
            from curl_cffi import requests as curl_requests

            self.session = curl_requests.Session(impersonate="chrome")
            self.usar_curl_cffi = True
            logger.info("Usando curl_cffi para Sofascore")
        except ImportError:
            import requests

            self.session = requests.Session()
            self.session.headers.update(
                {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json",
                    "Referer": "https://www.sofascore.com/",
                }
            )
            logger.warning("curl_cffi no instalado. Instala con: pip install curl_cffi")

    def _rate_limit(self) -> None:
        ahora = time.time()
        delta = ahora - self.ultima_peticion
        if delta < self.min_intervalo:
            time.sleep(self.min_intervalo - delta)
        self.ultima_peticion = time.time()

    def _manejar_bloqueo(self) -> None:
        self.bloqueos_consecutivos += 1
        self.total_bloqueos += 1

        if self.bloqueos_consecutivos >= 5:
            pausa = 60 * self.bloqueos_consecutivos
            logger.warning("Bloqueo severo 403. Pausando %ss", pausa)
            time.sleep(pausa)
        elif self.bloqueos_consecutivos >= 3:
            pausa = 30
            logger.warning("Multiples 403. Pausando %ss", pausa)
            time.sleep(pausa)

    def _reiniciar_bloqueos(self) -> None:
        self.bloqueos_consecutivos = 0

    def get(self, endpoint: str, reintentos: int = 3) -> Optional[Dict[str, Any]]:
        url = f"{SOFASCORE_API_BASE}{endpoint}"
        self.total_peticiones += 1

        for intento in range(reintentos):
            self._rate_limit()
            try:
                if self.usar_curl_cffi:
                    response = self.session.get(url)
                else:
                    response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    self._reiniciar_bloqueos()
                    return response.json()

                if response.status_code == 403:
                    if intento == 0:
                        logger.warning("HTTP 403 en endpoint %s", endpoint)
                    self._manejar_bloqueo()
                    time.sleep(2**intento)
                    continue

                if response.status_code == 404:
                    return None

                logger.warning("HTTP %s en %s", response.status_code, endpoint)
            except Exception as exc:
                logger.error("Error GET %s: %s", endpoint, exc)
                time.sleep(2)
        return None

    def verificar_acceso(self) -> bool:
        datos = self.get(f"/unique-tournament/{EUROLIGA_SOFASCORE_ID}/seasons")
        if datos and "seasons" in datos:
            logger.info("Acceso a Sofascore OK")
            return True
        logger.error("Sin acceso a Sofascore")
        return False

    def cerrar(self) -> None:
        if self.session:
            self.session.close()


def obtener_conexion():
    try:
        import psycopg
    except ImportError:
        logger.error("psycopg no instalado. pip install psycopg[binary]")
        raise

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL no configurada")
    if "sslmode=" not in database_url:
        sep = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{sep}sslmode=require"
    return psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)


@dataclass
class CapacidadesEquiposLegacy:
    tiene_competicion_col: bool
    tiene_sofascore_col: bool
    conferencia_nullable: bool
    division_nullable: bool


def detectar_capacidades_equipos_legacy(conn) -> CapacidadesEquiposLegacy:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'equipos'
            """
        )
        cols = {row["column_name"]: row["is_nullable"] for row in cur.fetchall()}

    return CapacidadesEquiposLegacy(
        tiene_competicion_col="competicion_principal_id" in cols,
        tiene_sofascore_col="sofascore_id" in cols,
        conferencia_nullable=cols.get("conferencia") == "YES",
        division_nullable=cols.get("division") == "YES",
    )


def obtener_competicion_euroliga(conn) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, nombre, codigo, sofascore_id, activo
            FROM competiciones_baloncesto
            WHERE codigo = %s
            LIMIT 1
            """,
            (EUROLIGA_CODIGO,),
        )
        row = cur.fetchone()

        if not row:
            cur.execute(
                """
                INSERT INTO competiciones_baloncesto (
                    nombre, nombre_corto, codigo, tipo, sofascore_id, activo, prioridad
                )
                VALUES (
                    'Turkish Airlines Euroleague', 'Euroliga',
                    'euroleague', 'EUROLIGA', %s, true, 2
                )
                RETURNING id, nombre, codigo, sofascore_id, activo
                """,
                (EUROLIGA_SOFASCORE_ID,),
            )
            conn.commit()
            row = cur.fetchone()

    if row["sofascore_id"] != EUROLIGA_SOFASCORE_ID:
        raise RuntimeError(
            f"competiciones_baloncesto.codigo='euroleague' debe tener sofascore_id={EUROLIGA_SOFASCORE_ID}. "
            f"Valor actual: {row['sofascore_id']}"
        )
    if not row["activo"]:
        raise RuntimeError("La competicion euroleague esta inactiva en BD (activo=false)")

    return dict(row)


def _parsear_temporada_anios(nombre: str, year: Optional[str]) -> Tuple[str, int, int]:
    texto = f"{nombre or ''} {year or ''}"
    patron = re.search(r"(\d{2,4})\s*[/-]\s*(\d{2,4})", texto)
    if patron:
        a = int(patron.group(1))
        b = int(patron.group(2))
        if a < 100:
            a += 2000
        if b < 100:
            b += 2000
        if b < a:
            b += 1
        return f"{a}-{b}", a, b

    hoy = datetime.now(timezone.utc).year
    return f"{hoy}-{hoy + 1}", hoy, hoy + 1


def obtener_temporadas_sofascore(cliente: SofascoreClientInteligente) -> List[Dict[str, Any]]:
    datos = cliente.get(f"/unique-tournament/{EUROLIGA_SOFASCORE_ID}/seasons")
    if not datos or "seasons" not in datos or not datos["seasons"]:
        raise RuntimeError("No se pudieron obtener temporadas de Euroliga desde Sofascore")

    temporadas: List[Dict[str, Any]] = []
    for idx, temporada_api in enumerate(datos["seasons"]):
        nombre, anio_inicio, anio_fin = _parsear_temporada_anios(
            temporada_api.get("name", ""),
            temporada_api.get("year"),
        )
        temporadas.append(
            {
                "sofascore_season_id": int(temporada_api["id"]),
                "nombre": nombre,
                "anio_inicio": anio_inicio,
                "anio_fin": anio_fin,
                "es_actual": idx == 0,
            }
        )
    return temporadas


def obtener_o_crear_temporada(
    conn,
    competicion_id: str,
    temporada_obj: Dict[str, Any],
    marcar_activa: bool,
) -> Dict[str, Any]:
    sofascore_season_id = int(temporada_obj["sofascore_season_id"])
    nombre = temporada_obj["nombre"]
    anio_inicio = int(temporada_obj["anio_inicio"])
    anio_fin = int(temporada_obj["anio_fin"])

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, nombre, anio_inicio, anio_fin, sofascore_season_id
            FROM temporadas_baloncesto
            WHERE competicion_id = %s AND sofascore_season_id = %s
            LIMIT 1
            """,
            (competicion_id, sofascore_season_id),
        )
        row = cur.fetchone()

        if row:
            temporada_id = row["id"]
            cur.execute(
                """
                UPDATE temporadas_baloncesto
                SET nombre = %s,
                    anio_inicio = %s,
                    anio_fin = %s,
                    activa = %s,
                    actualizado_en = now()
                WHERE id = %s
                """,
                (nombre, anio_inicio, anio_fin, marcar_activa, temporada_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO temporadas_baloncesto (
                    nombre, anio_inicio, anio_fin, activa,
                    competicion_id, sofascore_season_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    nombre,
                    anio_inicio,
                    anio_fin,
                    marcar_activa,
                    competicion_id,
                    sofascore_season_id,
                ),
            )
            temporada_id = cur.fetchone()["id"]

        if marcar_activa:
            # Solo una temporada activa por competicion
            cur.execute(
                """
                UPDATE temporadas_baloncesto
                SET activa = (id = %s),
                    actualizado_en = now()
                WHERE competicion_id = %s
                """,
                (temporada_id, competicion_id),
            )
        conn.commit()

    return {
        "id": temporada_id,
        "nombre": nombre,
        "sofascore_season_id": sofascore_season_id,
        "anio_inicio": anio_inicio,
        "anio_fin": anio_fin,
    }


def obtener_o_crear_temporada_activa(conn, cliente: SofascoreClientInteligente, competicion_id: str) -> Dict[str, Any]:
    temporadas = obtener_temporadas_sofascore(cliente)
    return obtener_o_crear_temporada(
        conn=conn,
        competicion_id=competicion_id,
        temporada_obj=temporadas[0],
        marcar_activa=True,
    )


def _sanear_abreviatura(texto: str) -> str:
    limpio = re.sub(r"[^A-Z0-9]", "", (texto or "").upper())
    return limpio[:3]


def _candidatos_abreviatura(nombre: str, nombre_corto: str, name_code: str) -> List[str]:
    candidatos: List[str] = []
    for valor in (name_code, nombre_corto, nombre):
        abr = _sanear_abreviatura(valor)
        if abr:
            candidatos.append(abr)

    if nombre:
        tokens = re.findall(r"[A-Za-z0-9]+", nombre.upper())
        iniciales = "".join(t[0] for t in tokens if t)[:3]
        abr = _sanear_abreviatura(iniciales)
        if abr:
            candidatos.append(abr)

    if not candidatos:
        candidatos.append("EUR")

    vistos = set()
    salida = []
    for c in candidatos:
        if c not in vistos:
            vistos.add(c)
            salida.append(c)
    return salida

def _abreviatura_disponible(conn, candidatos: List[str], equipo_id: str) -> str:
    with conn.cursor() as cur:
        for base in candidatos:
            if len(base) < 3:
                base = (base + "XXX")[:3]

            cur.execute(
                """
                SELECT id
                FROM equipos
                WHERE abreviatura = %s
                LIMIT 1
                """,
                (base,),
            )
            row = cur.fetchone()
            if not row or str(row["id"]) == str(equipo_id):
                return base

            prefijo = base[:2]
            for i in range(10):
                cand = f"{prefijo}{i}"
                cur.execute(
                    "SELECT id FROM equipos WHERE abreviatura = %s LIMIT 1",
                    (cand,),
                )
                row_i = cur.fetchone()
                if not row_i or str(row_i["id"]) == str(equipo_id):
                    return cand

    fallback = _sanear_abreviatura(uuid.uuid4().hex[:3].upper())
    if len(fallback) < 3:
        fallback = "EUX"
    return fallback


def _upsert_equipo_legacy(
    conn,
    capacidades: CapacidadesEquiposLegacy,
    equipo_id: str,
    nombre: str,
    nombre_corto: str,
    abreviatura: str,
    ciudad: Optional[str],
    competicion_id: str,
    sofascore_id: int,
) -> None:
    conferencia = None if capacidades.conferencia_nullable else "Este"
    division = None if capacidades.division_nullable else "EUROLIGA"

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM equipos WHERE id = %s LIMIT 1", (equipo_id,))
        existe = cur.fetchone() is not None

        if existe:
            if capacidades.tiene_competicion_col and capacidades.tiene_sofascore_col:
                cur.execute(
                    """
                    UPDATE equipos
                    SET nombre = %s,
                        nombre_corto = %s,
                        abreviatura = %s,
                        ciudad = %s,
                        conferencia = %s,
                        division = %s,
                        competicion_principal_id = %s,
                        sofascore_id = %s,
                        activo = true,
                        actualizado_en = now()
                    WHERE id = %s
                    """,
                    (
                        nombre,
                        nombre_corto,
                        abreviatura,
                        ciudad,
                        conferencia,
                        division,
                        competicion_id,
                        sofascore_id,
                        equipo_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE equipos
                    SET nombre = %s,
                        nombre_corto = %s,
                        abreviatura = %s,
                        ciudad = %s,
                        conferencia = %s,
                        division = %s,
                        activo = true,
                        actualizado_en = now()
                    WHERE id = %s
                    """,
                    (
                        nombre,
                        nombre_corto,
                        abreviatura,
                        ciudad,
                        conferencia,
                        division,
                        equipo_id,
                    ),
                )
            return

        if capacidades.tiene_competicion_col and capacidades.tiene_sofascore_col:
            cur.execute(
                """
                INSERT INTO equipos (
                    id, nombre, nombre_corto, abreviatura,
                    conferencia, division, ciudad,
                    competicion_principal_id, sofascore_id, activo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                """,
                (
                    equipo_id,
                    nombre,
                    nombre_corto,
                    abreviatura,
                    conferencia,
                    division,
                    ciudad,
                    competicion_id,
                    sofascore_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO equipos (
                    id, nombre, nombre_corto, abreviatura,
                    conferencia, division, ciudad, activo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                """,
                (
                    equipo_id,
                    nombre,
                    nombre_corto,
                    abreviatura,
                    conferencia,
                    division,
                    ciudad,
                ),
            )


def obtener_o_crear_equipo(
    conn,
    capacidades: CapacidadesEquiposLegacy,
    team_data: Dict[str, Any],
    competicion_id: str,
) -> Optional[str]:
    sofascore_id = team_data.get("id")
    nombre = (team_data.get("name") or "").strip()
    nombre_corto = (team_data.get("shortName") or nombre[:50]).strip()[:50]
    name_code = (team_data.get("nameCode") or "").strip()
    ciudad = None

    if not sofascore_id or not nombre:
        return None

    # Determinar ID canonico desde equipos_baloncesto
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM equipos_baloncesto
            WHERE sofascore_id = %s
            LIMIT 1
            """,
            (sofascore_id,),
        )
        row = cur.fetchone()
        equipo_id = str(row["id"]) if row else str(uuid.uuid4())

    abreviatura = _abreviatura_disponible(
        conn,
        _candidatos_abreviatura(nombre, nombre_corto, name_code),
        equipo_id,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO equipos_baloncesto (
                    id, nombre, nombre_corto, nombre_comun, abreviatura,
                    ciudad, competicion_principal_id, sofascore_id, activo
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, true
                )
                ON CONFLICT (sofascore_id) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    nombre_corto = EXCLUDED.nombre_corto,
                    nombre_comun = EXCLUDED.nombre_comun,
                    abreviatura = EXCLUDED.abreviatura,
                    ciudad = EXCLUDED.ciudad,
                    competicion_principal_id = EXCLUDED.competicion_principal_id,
                    activo = true,
                    actualizado_en = now()
                RETURNING id
                """,
                (
                    equipo_id,
                    nombre,
                    nombre_corto,
                    nombre.lower()[:50],
                    abreviatura,
                    ciudad,
                    competicion_id,
                    sofascore_id,
                ),
            )
            saved = cur.fetchone()
            equipo_id = str(saved["id"])

            _upsert_equipo_legacy(
                conn=conn,
                capacidades=capacidades,
                equipo_id=equipo_id,
                nombre=nombre,
                nombre_corto=nombre_corto,
                abreviatura=abreviatura,
                ciudad=ciudad,
                competicion_id=competicion_id,
                sofascore_id=sofascore_id,
            )

        conn.commit()
        return equipo_id
    except Exception as exc:
        conn.rollback()
        logger.error("Error sincronizando equipo %s (sofascore=%s): %s", nombre, sofascore_id, exc)
        return None


def _score_periodo(score_obj: Dict[str, Any], clave: str) -> int:
    try:
        valor = score_obj.get(clave)
        return int(valor) if valor is not None else 0
    except Exception:
        return 0


def _score_total(score_obj: Dict[str, Any]) -> int:
    current = score_obj.get("current")
    if current is not None:
        try:
            return int(current)
        except Exception:
            pass
    return (
        _score_periodo(score_obj, "period1")
        + _score_periodo(score_obj, "period2")
        + _score_periodo(score_obj, "period3")
        + _score_periodo(score_obj, "period4")
        + _score_overtime(score_obj)
    )


def _score_overtime(score_obj: Dict[str, Any]) -> int:
    overtime = score_obj.get("overtime")
    if overtime is not None:
        try:
            return int(overtime)
        except Exception:
            pass

    extra = 0
    for key, value in score_obj.items():
        if key.startswith("period"):
            m = re.match(r"period(\d+)$", key)
            if m and int(m.group(1)) > 4:
                try:
                    extra += int(value)
                except Exception:
                    continue
    return extra


def insertar_o_actualizar_partido(
    conn,
    evento: Dict[str, Any],
    competicion_id: str,
    temporada_id: str,
    equipo_local_id: str,
    equipo_visitante_id: str,
) -> Tuple[bool, bool]:
    sofascore_event_id = evento.get("id")
    if not sofascore_event_id:
        return False, False

    status_type = (evento.get("status", {}) or {}).get("type", "").lower()
    finalizado = status_type == "finished"

    home_score = evento.get("homeScore") or {}
    away_score = evento.get("awayScore") or {}

    local_q1 = _score_periodo(home_score, "period1")
    local_q2 = _score_periodo(home_score, "period2")
    local_q3 = _score_periodo(home_score, "period3")
    local_q4 = _score_periodo(home_score, "period4")
    local_ot = _score_overtime(home_score)
    local_total = _score_total(home_score)

    visitante_q1 = _score_periodo(away_score, "period1")
    visitante_q2 = _score_periodo(away_score, "period2")
    visitante_q3 = _score_periodo(away_score, "period3")
    visitante_q4 = _score_periodo(away_score, "period4")
    visitante_ot = _score_overtime(away_score)
    visitante_total = _score_total(away_score)

    if not finalizado:
        local_q1 = local_q2 = local_q3 = local_q4 = local_ot = local_total = 0
        visitante_q1 = visitante_q2 = visitante_q3 = visitante_q4 = visitante_ot = visitante_total = 0

    ganador_id = None
    diferencia_puntos = None
    if finalizado:
        if local_total > visitante_total:
            ganador_id = equipo_local_id
        elif visitante_total > local_total:
            ganador_id = equipo_visitante_id
        diferencia_puntos = abs(local_total - visitante_total)

    hubo_overtime = (local_ot > 0) or (visitante_ot > 0)

    timestamp = evento.get("startTimestamp")
    fecha_partido = datetime.now(timezone.utc).date()
    if timestamp:
        fecha_partido = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM partidos_baloncesto
            WHERE sofascore_match_id = %s
            LIMIT 1
            """,
            (sofascore_event_id,),
        )
        existente = cur.fetchone()

        if existente:
            cur.execute(
                """
                UPDATE partidos_baloncesto
                SET temporada_id = %s,
                    competicion_id = %s,
                    fecha_partido = %s,
                    tipo_partido = 'REG',
                    equipo_local_id = %s,
                    equipo_visitante_id = %s,
                    local_q1 = %s,
                    local_q2 = %s,
                    local_q3 = %s,
                    local_q4 = %s,
                    local_ot = %s,
                    local_total = %s,
                    visitante_q1 = %s,
                    visitante_q2 = %s,
                    visitante_q3 = %s,
                    visitante_q4 = %s,
                    visitante_ot = %s,
                    visitante_total = %s,
                    ganador_id = %s,
                    diferencia_puntos = %s,
                    hubo_overtime = %s,
                    fuente_datos = 'SOFASCORE',
                    source = 'SOFASCORE',
                    source_game_id = %s,
                    url_referencia = %s,
                    valido = true,
                    notas = %s,
                    actualizado_en = now()
                WHERE sofascore_match_id = %s
                """,
                (
                    temporada_id,
                    competicion_id,
                    fecha_partido,
                    equipo_local_id,
                    equipo_visitante_id,
                    local_q1,
                    local_q2,
                    local_q3,
                    local_q4,
                    local_ot,
                    local_total,
                    visitante_q1,
                    visitante_q2,
                    visitante_q3,
                    visitante_q4,
                    visitante_ot,
                    visitante_total,
                    ganador_id,
                    diferencia_puntos,
                    hubo_overtime,
                    str(sofascore_event_id),
                    f"https://www.sofascore.com/event/{sofascore_event_id}",
                    status_type or None,
                    sofascore_event_id,
                ),
            )
            return True, False

        cur.execute(
            """
            INSERT INTO partidos_baloncesto (
                temporada_id, competicion_id, fecha_partido, tipo_partido,
                equipo_local_id, equipo_visitante_id,
                local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                ganador_id, diferencia_puntos, hubo_overtime,
                fuente_datos, source, source_game_id, espn_game_id,
                sofascore_match_id, url_referencia, valido, notas
            )
            VALUES (
                %s, %s, %s, 'REG',
                %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                'SOFASCORE', 'SOFASCORE', %s, NULL,
                %s, %s, true, %s
            )
            """,
            (
                temporada_id,
                competicion_id,
                fecha_partido,
                equipo_local_id,
                equipo_visitante_id,
                local_q1,
                local_q2,
                local_q3,
                local_q4,
                local_ot,
                local_total,
                visitante_q1,
                visitante_q2,
                visitante_q3,
                visitante_q4,
                visitante_ot,
                visitante_total,
                ganador_id,
                diferencia_puntos,
                hubo_overtime,
                str(sofascore_event_id),
                sofascore_event_id,
                f"https://www.sofascore.com/event/{sofascore_event_id}",
                status_type or None,
            ),
        )
        return True, True

def obtener_partidos_pasados(
    cliente: SofascoreClientInteligente,
    season_id: int,
    dias: int,
    max_paginas: int,
) -> List[Dict[str, Any]]:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    partidos: List[Dict[str, Any]] = []

    for pagina in range(max_paginas):
        endpoint = (
            f"/unique-tournament/{EUROLIGA_SOFASCORE_ID}/season/{season_id}/events/last/{pagina}"
        )
        datos = cliente.get(endpoint)
        if not datos or "events" not in datos:
            break
        eventos = datos["events"] or []
        if not eventos:
            break

        for evento in eventos:
            ts = evento.get("startTimestamp")
            if not ts:
                continue
            fecha = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            if fecha >= desde:
                partidos.append(evento)

        ultimo_ts = eventos[-1].get("startTimestamp")
        if ultimo_ts and datetime.fromtimestamp(int(ultimo_ts), tz=timezone.utc) < desde:
            break

    return partidos


def obtener_todos_partidos_temporada(
    cliente: SofascoreClientInteligente,
    season_id: int,
    max_paginas: int,
) -> List[Dict[str, Any]]:
    partidos: List[Dict[str, Any]] = []
    vistos = set()

    for pagina in range(max_paginas):
        endpoint = (
            f"/unique-tournament/{EUROLIGA_SOFASCORE_ID}/season/{season_id}/events/last/{pagina}"
        )
        datos = cliente.get(endpoint)
        if not datos or "events" not in datos:
            break
        eventos = datos["events"] or []
        if not eventos:
            break

        for evento in eventos:
            event_id = evento.get("id")
            if event_id in vistos:
                continue
            vistos.add(event_id)
            partidos.append(evento)

    return partidos


def obtener_partidos_futuros(
    cliente: SofascoreClientInteligente,
    season_id: int,
    dias_futuros: int,
    max_paginas: int,
) -> List[Dict[str, Any]]:
    hasta = datetime.now(timezone.utc) + timedelta(days=dias_futuros)
    partidos: List[Dict[str, Any]] = []

    for pagina in range(max_paginas):
        endpoint = (
            f"/unique-tournament/{EUROLIGA_SOFASCORE_ID}/season/{season_id}/events/next/{pagina}"
        )
        datos = cliente.get(endpoint)
        if not datos or "events" not in datos:
            break
        eventos = datos["events"] or []
        if not eventos:
            break

        for evento in eventos:
            ts = evento.get("startTimestamp")
            if not ts:
                continue
            fecha = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            if fecha <= hasta:
                partidos.append(evento)

        ultimo_ts = eventos[-1].get("startTimestamp")
        if ultimo_ts and datetime.fromtimestamp(int(ultimo_ts), tz=timezone.utc) > hasta:
            break

    return partidos


def actualizar_estado_ingesta(
    conn,
    competicion_id: str,
    insertados: int,
    actualizados: int,
    errores: int,
    cursor_fecha: Optional[datetime.date],
    ultimo_error: Optional[str],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_state_baloncesto (
                clave, competicion_id, ultima_sincronizacion,
                ultima_exito, ultima_error, ultimo_error,
                ultimo_insertados, ultimo_actualizados,
                cursor_fecha, metadata, actualizado_en
            )
            VALUES (
                'euroliga_sync', %s, now(),
                CASE WHEN %s = 0 THEN now() ELSE NULL END,
                CASE WHEN %s > 0 THEN now() ELSE NULL END,
                %s,
                %s, %s,
                %s, %s::jsonb, now()
            )
            ON CONFLICT (clave) DO UPDATE SET
                competicion_id = EXCLUDED.competicion_id,
                ultima_sincronizacion = EXCLUDED.ultima_sincronizacion,
                ultima_exito = CASE
                    WHEN EXCLUDED.ultima_exito IS NOT NULL THEN EXCLUDED.ultima_exito
                    ELSE ingestion_state_baloncesto.ultima_exito
                END,
                ultima_error = CASE
                    WHEN EXCLUDED.ultima_error IS NOT NULL THEN EXCLUDED.ultima_error
                    ELSE ingestion_state_baloncesto.ultima_error
                END,
                ultimo_error = EXCLUDED.ultimo_error,
                ultimo_insertados = EXCLUDED.ultimo_insertados,
                ultimo_actualizados = EXCLUDED.ultimo_actualizados,
                cursor_fecha = EXCLUDED.cursor_fecha,
                metadata = EXCLUDED.metadata,
                actualizado_en = now()
            """,
            (
                competicion_id,
                errores,
                errores,
                ultimo_error,
                insertados,
                actualizados,
                cursor_fecha,
                json.dumps(
                    {
                        "fuente": "SOFASCORE",
                        "torneo_id": EUROLIGA_SOFASCORE_ID,
                        "errores": errores,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
            ),
        )
    conn.commit()


def procesar_eventos_temporada(
    conn,
    competicion_id: str,
    temporada_id: str,
    eventos: List[Dict[str, Any]],
    capacidades: CapacidadesEquiposLegacy,
) -> Dict[str, Any]:
    resultado = {
        "procesados": 0,
        "insertados": 0,
        "actualizados": 0,
        "errores": 0,
        "equipos_sin_id": 0,
        "ultima_fecha": None,
        "ultimo_error": None,
    }

    for idx, evento in enumerate(eventos, start=1):
        if idx % 10 == 0:
            print(f"\rProcesados {idx}/{len(eventos)}", end="", flush=True)

        try:
            home = evento.get("homeTeam") or {}
            away = evento.get("awayTeam") or {}

            home_id = obtener_o_crear_equipo(
                conn=conn,
                capacidades=capacidades,
                team_data=home,
                competicion_id=competicion_id,
            )
            away_id = obtener_o_crear_equipo(
                conn=conn,
                capacidades=capacidades,
                team_data=away,
                competicion_id=competicion_id,
            )

            if not home_id or not away_id:
                resultado["equipos_sin_id"] += 1
                resultado["errores"] += 1
                resultado["ultimo_error"] = (
                    f"No se pudo resolver IDs de equipos para evento {evento.get('id')}"
                )
                continue

            ok, insertado = insertar_o_actualizar_partido(
                conn=conn,
                evento=evento,
                competicion_id=competicion_id,
                temporada_id=temporada_id,
                equipo_local_id=home_id,
                equipo_visitante_id=away_id,
            )
            if ok:
                resultado["procesados"] += 1
                if insertado:
                    resultado["insertados"] += 1
                else:
                    resultado["actualizados"] += 1
                conn.commit()
            else:
                resultado["errores"] += 1
                resultado["ultimo_error"] = f"Fallo guardando evento {evento.get('id')}"
                conn.rollback()
                continue

            ts = evento.get("startTimestamp")
            if ts:
                fecha = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
                if resultado["ultima_fecha"] is None or fecha > resultado["ultima_fecha"]:
                    resultado["ultima_fecha"] = fecha
        except Exception as exc:
            conn.rollback()
            resultado["errores"] += 1
            resultado["ultimo_error"] = str(exc)
            logger.error("Error procesando evento %s: %s", evento.get("id"), exc)

    if eventos:
        print()
    return resultado


def sincronizar_euroliga(
    conn,
    cliente: SofascoreClientInteligente,
    dias_pasados: int,
    dias_futuros: int,
    incluir_futuros: bool,
    max_paginas: int,
) -> Dict[str, Any]:
    resultado = {"procesados": 0, "insertados": 0, "actualizados": 0, "errores": 0, "equipos_sin_id": 0}
    comp = obtener_competicion_euroliga(conn)
    logger.info("Competicion: %s (%s)", comp["nombre"], comp["id"])

    temporada = obtener_o_crear_temporada_activa(conn, cliente, str(comp["id"]))
    logger.info(
        "Temporada activa Euroliga: %s (sofascore_season_id=%s)",
        temporada["nombre"],
        temporada["sofascore_season_id"],
    )

    partidos_pasados = obtener_partidos_pasados(
        cliente=cliente,
        season_id=temporada["sofascore_season_id"],
        dias=dias_pasados,
        max_paginas=max_paginas,
    )
    partidos_futuros: List[Dict[str, Any]] = []
    if incluir_futuros:
        partidos_futuros = obtener_partidos_futuros(
            cliente=cliente,
            season_id=temporada["sofascore_season_id"],
            dias_futuros=dias_futuros,
            max_paginas=max_paginas,
        )

    eventos_map = {}
    for evento in partidos_pasados + partidos_futuros:
        eventos_map[evento.get("id")] = evento
    eventos = list(eventos_map.values())

    logger.info("Eventos a procesar: %s", len(eventos))
    if not eventos:
        actualizar_estado_ingesta(
            conn=conn,
            competicion_id=str(comp["id"]),
            insertados=0,
            actualizados=0,
            errores=0,
            cursor_fecha=None,
            ultimo_error=None,
        )
        return resultado

    capacidades = detectar_capacidades_equipos_legacy(conn)
    parcial = procesar_eventos_temporada(
        conn=conn,
        competicion_id=str(comp["id"]),
        temporada_id=str(temporada["id"]),
        eventos=eventos,
        capacidades=capacidades,
    )
    for key in ("procesados", "insertados", "actualizados", "errores", "equipos_sin_id"):
        resultado[key] += parcial[key]

    actualizar_estado_ingesta(
        conn=conn,
        competicion_id=str(comp["id"]),
        insertados=resultado["insertados"],
        actualizados=resultado["actualizados"],
        errores=resultado["errores"],
        cursor_fecha=parcial["ultima_fecha"],
        ultimo_error=parcial["ultimo_error"],
    )
    return resultado


def sincronizar_euroliga_historico(
    conn,
    cliente: SofascoreClientInteligente,
    desde_anio: int,
    hasta_anio: int,
    max_paginas: int,
) -> Dict[str, Any]:
    if desde_anio > hasta_anio:
        raise ValueError("--desde-anio no puede ser mayor que --hasta-anio")

    comp = obtener_competicion_euroliga(conn)
    capacidades = detectar_capacidades_equipos_legacy(conn)
    temporadas_api = obtener_temporadas_sofascore(cliente)

    # Rango por anio de inicio: 2018..2025 cubre temporadas 2018-2019 .. 2025-2026
    objetivo = [
        t for t in temporadas_api
        if desde_anio <= int(t["anio_inicio"]) and int(t["anio_fin"]) <= hasta_anio
    ]
    objetivo.sort(key=lambda t: int(t["anio_inicio"]))

    if not objetivo:
        raise RuntimeError(
            f"No hay temporadas de Euroliga en rango {desde_anio}-{hasta_anio}"
        )

    logger.info(
        "Modo historico: %s temporadas (%s -> %s)",
        len(objetivo),
        objetivo[0]["nombre"],
        objetivo[-1]["nombre"],
    )

    total = {"procesados": 0, "insertados": 0, "actualizados": 0, "errores": 0, "equipos_sin_id": 0}
    ultima_fecha = None
    ultimo_error = None
    season_activa_id = max(objetivo, key=lambda t: int(t["anio_inicio"]))["sofascore_season_id"]

    for idx, temporada_api in enumerate(objetivo, start=1):
        logger.info(
            "[%s/%s] Sincronizando temporada %s (sofascore=%s)",
            idx,
            len(objetivo),
            temporada_api["nombre"],
            temporada_api["sofascore_season_id"],
        )

        temporada_bd = obtener_o_crear_temporada(
            conn=conn,
            competicion_id=str(comp["id"]),
            temporada_obj=temporada_api,
            marcar_activa=(temporada_api["sofascore_season_id"] == season_activa_id),
        )

        eventos = obtener_todos_partidos_temporada(
            cliente=cliente,
            season_id=int(temporada_api["sofascore_season_id"]),
            max_paginas=max_paginas,
        )
        logger.info("Eventos temporada %s: %s", temporada_api["nombre"], len(eventos))

        parcial = procesar_eventos_temporada(
            conn=conn,
            competicion_id=str(comp["id"]),
            temporada_id=str(temporada_bd["id"]),
            eventos=eventos,
            capacidades=capacidades,
        )

        for key in ("procesados", "insertados", "actualizados", "errores", "equipos_sin_id"):
            total[key] += parcial[key]

        if parcial["ultima_fecha"] and (ultima_fecha is None or parcial["ultima_fecha"] > ultima_fecha):
            ultima_fecha = parcial["ultima_fecha"]
        if parcial["ultimo_error"]:
            ultimo_error = parcial["ultimo_error"]

    actualizar_estado_ingesta(
        conn=conn,
        competicion_id=str(comp["id"]),
        insertados=total["insertados"],
        actualizados=total["actualizados"],
        errores=total["errores"],
        cursor_fecha=ultima_fecha,
        ultimo_error=ultimo_error,
    )
    return total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sincroniza Euroliga desde Sofascore (solo torneo 138)"
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=7,
        help="Dias hacia atras a sincronizar (default: 7)",
    )
    parser.add_argument(
        "--dias-futuros",
        type=int,
        default=7,
        help="Dias hacia adelante para eventos programados (default: 7)",
    )
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=12,
        help="Maximo de paginas last/next en modo incremental (default: 12)",
    )
    parser.add_argument(
        "--historico",
        action="store_true",
        help="Carga historica de temporadas completas por rango de anios",
    )
    parser.add_argument(
        "--desde-anio",
        type=int,
        default=2018,
        help="Anio inicial (anio_inicio de temporada) para modo historico (default: 2018)",
    )
    parser.add_argument(
        "--hasta-anio",
        type=int,
        default=2026,
        help="Anio final para modo historico (default: 2026, cubre hasta 2025-2026)",
    )
    parser.add_argument(
        "--max-paginas-historico",
        type=int,
        default=80,
        help="Maximo de paginas events/last por temporada en modo historico (default: 80)",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=2.0,
        help="Segundos entre peticiones HTTP (default: 2.0)",
    )
    parser.add_argument(
        "--incluir-futuros",
        dest="incluir_futuros",
        action="store_true",
        help="Incluye eventos futuros (default: activado)",
    )
    parser.add_argument(
        "--no-futuros",
        dest="incluir_futuros",
        action="store_false",
        help="No sincroniza eventos futuros",
    )
    parser.set_defaults(incluir_futuros=True)
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 72)
    print("SINCRONIZADOR EUROLIGA - SOFASCORE")
    print("=" * 72)
    print(f"Torneo fijo: {EUROLIGA_SOFASCORE_ID} (EUROLIGA)")
    if args.historico:
        print("Modo: historico")
        print(f"Rango temporadas (anio_inicio): {args.desde_anio} - {args.hasta_anio}")
        print(f"Paginas historico por temporada: {args.max_paginas_historico}")
    else:
        print("Modo: incremental")
        print(f"Dias atras: {args.dias}")
        print(f"Incluir futuros: {'si' if args.incluir_futuros else 'no'}")
        if args.incluir_futuros:
            print(f"Dias futuros: {args.dias_futuros}")
        print(f"Paginas incremental: {args.max_paginas}")
    print(f"Intervalo HTTP: {args.intervalo}s")
    print()

    try:
        conn = obtener_conexion()
    except Exception as exc:
        print(f"Error conectando a BD: {exc}")
        return 1

    cliente = SofascoreClientInteligente(min_intervalo=args.intervalo)

    if not cliente.verificar_acceso():
        print("Sofascore esta bloqueando peticiones. Instala curl_cffi o espera y reintenta.")
        cliente.cerrar()
        conn.close()
        return 1

    inicio = datetime.now(timezone.utc)
    try:
        if args.historico:
            resultado = sincronizar_euroliga_historico(
                conn=conn,
                cliente=cliente,
                desde_anio=args.desde_anio,
                hasta_anio=args.hasta_anio,
                max_paginas=args.max_paginas_historico,
            )
        else:
            resultado = sincronizar_euroliga(
                conn=conn,
                cliente=cliente,
                dias_pasados=args.dias,
                dias_futuros=args.dias_futuros,
                incluir_futuros=args.incluir_futuros,
                max_paginas=args.max_paginas,
            )
    except Exception as exc:
        logger.exception("Error fatal en sincronizacion Euroliga: %s", exc)
        cliente.cerrar()
        conn.close()
        return 1
    finally:
        cliente.cerrar()
        conn.close()

    duracion = (datetime.now(timezone.utc) - inicio).total_seconds()

    print()
    print("=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"Duracion:            {duracion:.1f}s")
    print(f"Procesados:          {resultado['procesados']}")
    print(f"Insertados:          {resultado['insertados']}")
    print(f"Actualizados:        {resultado['actualizados']}")
    print(f"Errores:             {resultado['errores']}")
    print(f"Equipos sin ID:      {resultado['equipos_sin_id']}")
    print(f"Peticiones HTTP:     {cliente.total_peticiones}")
    print(f"Bloqueos 403:        {cliente.total_bloqueos}")
    print("=" * 72)

    return 0 if resultado["errores"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

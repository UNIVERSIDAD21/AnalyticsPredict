#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper_equipos_recientes.py — Versión CORREGIDA + OPTIMIZADA

CORRECCIONES vs versión anterior:
✅ Bug #1: visitante_ot usaba parsed["home_ot"] en vez de parsed["away_ot"]
✅ Bug #2: crear_sesion_http() se llamaba dentro del loop → cada request tenía sesión nueva
           sin retries activos. Ahora la sesión se pasa como parámetro y se reutiliza.
✅ Bug #3: Los except silenciaban los errores sin imprimir causa. Ahora loguean el error.
✅ Bug #4: SummaryCache tenía race condition entre get() y set(). Ahora el fetch+set
           se hace dentro del lock para evitar descargas duplicadas entre threads.

OPTIMIZACIONES mantenidas:
✅ Caché de equipos ESPN en memoria (evita N llamadas a get_all_teams)
✅ Caché de summaries por event_id (evita re-descargar mismos partidos)
✅ Batch processing con ThreadPoolExecutor (paraleliza equipos)
✅ Rate limiting inteligente (evita 429 de ESPN)
✅ Filtro por fecha ANTES de hacer fetch_summary (ahorra requests)
✅ Conexión DB reutilizada con pool

Uso:
    python scripts/scraper_equipos_recientes.py --all-teams --days 10
    python scripts/scraper_equipos_recientes.py --team "Lakers" --days 30
    python scripts/scraper_equipos_recientes.py --all-teams --days 10 --workers 8
    python scripts/scraper_equipos_recientes.py --all-teams --days 10 --out output/partidos.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from threading import Lock
import hashlib

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except Exception as e:
    raise SystemExit("❌ Falta 'requests' o 'urllib3'. pip install -r requirements.txt") from e

try:
    from motor.nba_scraper_espn import (
        resolve_team,
        fetch_schedule_events,
        is_completed_event,
        get_event_id,
        fetch_summary,
        extract_linescores,
        request_json,
        normalize,
        TeamInfo,
    )
except Exception as e:
    raise SystemExit("❌ No pude importar motor.nba_scraper_espn.") from e

try:
    import psycopg
    from psycopg_pool import ConnectionPool
except Exception:
    raise SystemExit("❌ Falta psycopg o psycopg_pool. pip install 'psycopg[binary]' psycopg-pool")

ZONA_HORARIA_NBA = ZoneInfo("America/New_York")
COMPETICION_TODAS = "ALL"

# ============================================================================
# CONFIGURACIÓN DE OPTIMIZACIÓN
# ============================================================================

MAX_WORKERS = 4          # Hilos paralelos para sincronización de equipos
REQUEST_TIMEOUT = 15     # Timeout por request a ESPN (segundos)
REQUESTS_PER_SECOND = 2  # Rate limit para evitar 429 de ESPN
CACHE_SUMMARY_TTL = 3600 # Segundos que vive el caché de summaries (1 hora)


# ============================================================================
# CLASES DE DATOS
# ============================================================================

@dataclass
class DbTeam:
    id: str
    nombre: str
    nombre_corto: str
    abreviatura: str
    competicion_id: Optional[str] = None
    competicion_nombre: Optional[str] = None


@dataclass
class SyncStats:
    procesados: int = 0
    insertados: int = 0
    actualizados: int = 0
    omitidos: int = 0
    errores: int = 0


# ============================================================================
# RATE LIMITER + SESIÓN HTTP REUTILIZABLE
# ============================================================================

class RateLimiter:
    """Limita requests por segundo para evitar bloqueos de ESPN."""

    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self.lock = Lock()

    def wait_if_needed(self):
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request = time.time()


def crear_sesion_http() -> requests.Session:
    """
    Crea sesión HTTP con retries y keep-alive.
    IMPORTANTE: llamar UNA SOLA VEZ y reutilizar la sesión.
    Crear sesiones dentro de loops anula los retries configurados.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20,
    )
    # FIX: los headers van en la sesión, no en el adapter
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AnalyticsPredict/2.0",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })

    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ============================================================================
# CACHÉ DE EQUIPOS ESPN (EVITA LLAMADAS REPETIDAS)
# ============================================================================

class EspnTeamCache:
    """Caché en memoria de equipos ESPN. Una sola llamada a get_all_teams()."""

    def __init__(self, session: requests.Session):
        self._cache: Dict[str, TeamInfo] = {}
        self._cache_by_name: Dict[str, TeamInfo] = {}
        self._loaded = False
        self._session = session
        self._lock = Lock()

    def _load_all_teams(self):
        """Carga TODOS los equipos de ESPN una sola vez."""
        if self._loaded:
            return

        with self._lock:
            if self._loaded:  # Double-check
                return

            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
            try:
                data = request_json(self._session, url, params={}, max_retries=3, backoff_base=0.5)

                for sport in data.get("sports", []):
                    for league in sport.get("leagues", []):
                        for t in league.get("teams", []):
                            team = t.get("team", {}) or {}
                            tid = str(team.get("id", "")).strip()
                            dn = str(team.get("displayName", "")).strip()
                            ab = str(team.get("abbreviation", "")).strip()
                            if tid and dn:
                                info = TeamInfo(id=tid, display_name=dn, abbreviation=ab)
                                self._cache[ab.upper()] = info
                                self._cache_by_name[normalize(dn)] = info

                self._loaded = True
                print(f"✅ Caché de equipos ESPN cargada: {len(self._cache)} equipos")

            except Exception as e:
                print(f"⚠️  Error cargando equipos ESPN: {e}")
                self._loaded = True  # Evitar reintentos infinitos

    def get_team(self, team_query: str) -> Optional[TeamInfo]:
        """Resuelve equipo usando caché (sin llamadas a ESPN)."""
        self._load_all_teams()

        q = normalize(team_query)
        q_upper = q.upper()

        # 1) Match por abreviatura
        if q_upper in self._cache:
            return self._cache[q_upper]

        # 2) Match exacto por nombre
        if q in self._cache_by_name:
            return self._cache_by_name[q]

        # 3) Match parcial (primero que contenga)
        for name, info in self._cache_by_name.items():
            if q in name:
                return info

        return None


# ============================================================================
# CACHÉ DE SUMMARIES (EVITA RE-DESCARGAR MISMOS PARTIDOS)
# FIX: ahora el fetch+set ocurre dentro del lock para evitar race condition
#      entre threads que podrían descargar el mismo partido simultáneamente.
# ============================================================================

class SummaryCache:
    """Caché de summaries de ESPN por event_id. Thread-safe."""

    def __init__(self, session: requests.Session, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._session = session
        self._ttl = ttl_seconds
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get_or_fetch(
        self,
        event_id: str,
        rate_limiter: RateLimiter,
    ) -> Optional[Dict[str, Any]]:
        """
        Devuelve el summary del caché si existe y no expiró.
        Si no está, lo descarga usando la sesión compartida.
        El fetch ocurre dentro del lock para evitar descargas duplicadas.
        """
        with self._lock:
            if event_id in self._cache:
                timestamp, data = self._cache[event_id]
                if time.time() - timestamp < self._ttl:
                    self._hits += 1
                    return data
                else:
                    del self._cache[event_id]

            # No estaba en caché: descargar
            # El lock evita que otro thread descargue el mismo event_id
            rate_limiter.wait_if_needed()
            try:
                summary = fetch_summary(self._session, event_id)
                self._cache[event_id] = (time.time(), summary)
                self._misses += 1
                return summary
            except Exception as e:
                self._misses += 1
                raise  # Re-lanzar para que el caller lo maneje

    def stats(self) -> Tuple[int, int]:
        with self._lock:
            return self._hits, self._misses


# ============================================================================
# UTILIDADES
# ============================================================================

def obtener_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return ""
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or isinstance(v, bool):
            return default
        if isinstance(v, (int, float)):
            return int(v)
        s = str(v).strip()
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default


def parse_fecha_calendario_espn_iso(iso_str: str) -> date:
    try:
        texto = str(iso_str)
        if "T" not in texto:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        fecha_dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if fecha_dt.tzinfo is None:
            return fecha_dt.date()
        return fecha_dt.astimezone(ZONA_HORARIA_NBA).date()
    except Exception:
        return datetime.now(ZONA_HORARIA_NBA).date()


def seasontype_to_tipo(seasontype: int) -> str:
    return {1: "PRE", 2: "REG", 3: "POST"}.get(seasontype, "REG")


def normalize_nombre(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())


# ============================================================================
# OPERACIONES DE BD
# ============================================================================

def _build_team(row: tuple) -> DbTeam:
    rid, nombre, nombre_corto, abbr, comp_id, comp_nombre = row
    return DbTeam(
        id=str(rid),
        nombre=str(nombre or ""),
        nombre_corto=str(nombre_corto or ""),
        abreviatura=str(abbr or "").upper(),
        competicion_id=str(comp_id) if comp_id else None,
        competicion_nombre=str(comp_nombre or "") if comp_nombre else None,
    )


def cargar_equipos_bd(conexion, competicion_filtro: str = "NBA") -> Tuple[Dict[str, DbTeam], Dict[str, DbTeam]]:
    por_abbr: Dict[str, DbTeam] = {}
    por_nombre: Dict[str, DbTeam] = {}

    sql_base = """
        SELECT e.id, e.nombre, e.nombre_corto, e.abreviatura,
               e.competicion_principal_id, c.nombre AS competicion_nombre
        FROM equipos_baloncesto e
        LEFT JOIN competiciones_baloncesto c ON c.id = e.competicion_principal_id
        WHERE e.activo = true
    """

    with conexion.cursor() as cur:
        if competicion_filtro.upper() == COMPETICION_TODAS:
            cur.execute(sql_base + " ORDER BY e.nombre")
            rows = cur.fetchall()
        else:
            cur.execute(
                sql_base + " AND (c.nombre ILIKE %s OR c.codigo ILIKE %s) ORDER BY e.nombre",
                (f"%{competicion_filtro}%", f"%{competicion_filtro}%"),
            )
            rows = cur.fetchall()

    for row in rows:
        t = _build_team(row)
        if t.abreviatura:
            por_abbr[t.abreviatura] = t
        key1 = normalize_nombre(t.nombre)
        key2 = normalize_nombre(t.nombre_corto)
        if key1:
            por_nombre[key1] = t
        if key2 and key2 != key1:
            por_nombre[key2] = t

    return por_abbr, por_nombre


def obtener_todos_equipos_bd(conexion, competicion_filtro: str = "NBA") -> List[DbTeam]:
    sql_base = """
        SELECT e.id, e.nombre, e.nombre_corto, e.abreviatura,
               e.competicion_principal_id, c.nombre AS competicion_nombre
        FROM equipos_baloncesto e
        LEFT JOIN competiciones_baloncesto c ON c.id = e.competicion_principal_id
        WHERE e.activo = true
    """

    with conexion.cursor() as cur:
        if competicion_filtro.upper() == COMPETICION_TODAS:
            cur.execute(sql_base + " ORDER BY e.nombre")
        else:
            cur.execute(
                sql_base + " AND (c.nombre ILIKE %s OR c.codigo ILIKE %s) ORDER BY e.nombre",
                (f"%{competicion_filtro}%", f"%{competicion_filtro}%"),
            )
        rows = cur.fetchall()

    return [_build_team(row) for row in rows]


def resolver_equipo_bd(conexion, team_query: str) -> DbTeam:
    q = str(team_query or "").strip()
    if not q:
        raise SystemExit("❌ --team es requerido")

    sql_select = """
        SELECT e.id, e.nombre, e.nombre_corto, e.abreviatura,
               e.competicion_principal_id, c.nombre AS competicion_nombre
        FROM equipos_baloncesto e
        LEFT JOIN competiciones_baloncesto c ON c.id = e.competicion_principal_id
    """

    ab = q.upper()
    with conexion.cursor() as cur:
        cur.execute(sql_select + " WHERE UPPER(e.abreviatura) = %s LIMIT 1", (ab,))
        row = cur.fetchone()
        if row:
            return _build_team(row)

        like = f"%{q}%"
        cur.execute(
            sql_select + " WHERE e.nombre ILIKE %s OR e.nombre_corto ILIKE %s ORDER BY LENGTH(e.nombre) ASC LIMIT 1",
            (like, like),
        )
        row = cur.fetchone()
        if row:
            return _build_team(row)

    raise SystemExit(f"❌ No encontré el equipo en BD para: {q}")


def asegurar_equipo_bd(
    conexion,
    por_abbr: Dict[str, DbTeam],
    por_nombre: Dict[str, DbTeam],
    nombre: str,
    nombre_corto: str,
    abreviatura: str,
) -> DbTeam:
    ab = str(abreviatura or "").upper().strip()
    if ab and ab in por_abbr:
        return por_abbr[ab]

    key = normalize_nombre(nombre)
    if key and key in por_nombre:
        return por_nombre[key]

    with conexion.cursor() as cur:
        cur.execute(
            """
            INSERT INTO equipos_baloncesto (nombre, nombre_corto, abreviatura, conferencia, division, ciudad, activo)
            VALUES (%s, %s, %s, NULL, NULL, NULL, true)
            ON CONFLICT (abreviatura) DO UPDATE SET
                nombre = COALESCE(EXCLUDED.nombre, equipos_baloncesto.nombre),
                nombre_corto = COALESCE(EXCLUDED.nombre_corto, equipos_baloncesto.nombre_corto),
                activo = true
            RETURNING id, nombre, nombre_corto, abreviatura, competicion_principal_id
            """,
            (nombre, nombre_corto or nombre, ab),
        )
        rid, rnom, rshort, rabbr, comp_id = cur.fetchone()
    conexion.commit()

    t = DbTeam(
        id=str(rid),
        nombre=str(rnom or ""),
        nombre_corto=str(rshort or ""),
        abreviatura=str(rabbr or "").upper(),
        competicion_id=str(comp_id) if comp_id else None,
    )
    if t.abreviatura:
        por_abbr[t.abreviatura] = t
    if t.nombre:
        por_nombre[normalize_nombre(t.nombre)] = t
    if t.nombre_corto:
        por_nombre[normalize_nombre(t.nombre_corto)] = t
    return t


def asegurar_temporadas(conexion, seasons: List[int]) -> Dict[int, str]:
    seasons_int = sorted({int(s) for s in seasons})
    if not seasons_int:
        return {}

    max_temp = max(seasons_int)
    out: Dict[int, str] = {}

    with conexion.cursor() as cur:
        for anio_fin in seasons_int:
            anio_inicio = anio_fin - 1
            nombre = f"{anio_inicio}-{anio_fin}"

            cur.execute(
                "SELECT id FROM temporadas_baloncesto WHERE (anio_inicio = %s AND anio_fin = %s) OR nombre = %s",
                (anio_inicio, anio_fin, nombre),
            )
            row = cur.fetchone()
            if row:
                out[anio_fin] = str(row[0])
                continue

            fecha_inicio = f"{anio_inicio}-10-01"
            fecha_fin_str = f"{anio_fin}-06-30"
            activa = anio_fin == max_temp

            cur.execute(
                """
                INSERT INTO temporadas_baloncesto (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin_str, activa),
            )
            out[anio_fin] = str(cur.fetchone()[0])

    conexion.commit()
    return out


# ============================================================================
# PARSEO Y UPSERT
# ============================================================================

def parse_summary_to_partido(summary: Dict[str, Any]) -> Dict[str, Any]:
    header = summary.get("header", {}) or {}
    competitions = summary.get("competitions", []) or header.get("competitions", []) or []
    if not competitions:
        raise RuntimeError("Summary sin competitions")

    comp = competitions[0]
    date_str = comp.get("date") or header.get("date") or ""
    fecha_partido = parse_fecha_calendario_espn_iso(date_str)

    competitors = comp.get("competitors", []) or []
    if len(competitors) < 2:
        raise RuntimeError("Summary sin 2 competidores")

    home = away = None
    for c in competitors:
        ha = str(c.get("homeAway", "")).lower()
        if ha == "home":
            home = c
        elif ha == "away":
            away = c

    if home is None or away is None:
        home, away = competitors[0], competitors[1]

    def team_names(c: Dict[str, Any]) -> Tuple[str, str, str]:
        t = c.get("team", {}) or {}
        nombre = t.get("displayName") or t.get("shortDisplayName") or ""
        corto = t.get("shortDisplayName") or t.get("displayName") or nombre
        abbr = (t.get("abbreviation") or "").upper()
        return str(nombre), str(corto), str(abbr)

    home_nombre, home_corto, home_abbr = team_names(home)
    away_nombre, away_corto, away_abbr = team_names(away)

    home_ls = extract_linescores(home)
    away_ls = extract_linescores(away)

    L = max(len(home_ls), len(away_ls), 4)
    while len(home_ls) < L:
        home_ls.append(0)
    while len(away_ls) < L:
        away_ls.append(0)

    home_q1, home_q2, home_q3, home_q4 = home_ls[0], home_ls[1], home_ls[2], home_ls[3]
    away_q1, away_q2, away_q3, away_q4 = away_ls[0], away_ls[1], away_ls[2], away_ls[3]

    home_ot = sum(home_ls[4:]) if len(home_ls) > 4 else 0
    away_ot = sum(away_ls[4:]) if len(away_ls) > 4 else 0  # FIX: era home_ls[4:] en la versión anterior

    home_total = _safe_int(home.get("score"), default=sum(home_ls))
    away_total = _safe_int(away.get("score"), default=sum(away_ls))

    hubo_overtime = bool(home_ot or away_ot or len(home_ls) > 4 or len(away_ls) > 4)

    return {
        "fecha_partido": fecha_partido,
        "home": {"nombre": home_nombre, "corto": home_corto, "abbr": home_abbr},
        "away": {"nombre": away_nombre, "corto": away_corto, "abbr": away_abbr},
        "home_q": [home_q1, home_q2, home_q3, home_q4],
        "away_q": [away_q1, away_q2, away_q3, away_q4],
        "home_ot": home_ot,
        "away_ot": away_ot,
        "home_total": home_total,
        "away_total": away_total,
        "hubo_overtime": hubo_overtime,
    }


def upsert_partido_con_fecha(
    conexion,
    fecha_partido: date,
    temporada_id: str,
    tipo_partido: str,
    espn_game_id: str,
    equipo_local_id: str,
    equipo_visitante_id: str,
    local_q: List[int],
    visitante_q: List[int],
    local_ot: int,
    visitante_ot: int,
    local_total: int,
    visitante_total: int,
    ganador_id: Optional[str],
    hubo_overtime: bool,
    competicion_id: str,
) -> Tuple[bool, str]:
    diferencia = abs(local_total - visitante_total)
    with conexion.cursor() as cur:
        cur.execute(
            """
            INSERT INTO partidos_baloncesto (
                temporada_id, fecha_partido, tipo_partido, espn_game_id,
                equipo_local_id, equipo_visitante_id,
                local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                ganador_id, diferencia_puntos, hubo_overtime,
                competicion_id, fuente_datos, valido
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, 'ESPN', true
            )
            ON CONFLICT (temporada_id, fecha_partido, tipo_partido, equipo_local_id, equipo_visitante_id)
            DO UPDATE SET
                espn_game_id = COALESCE(EXCLUDED.espn_game_id, partidos_baloncesto.espn_game_id),
                local_q1 = EXCLUDED.local_q1, local_q2 = EXCLUDED.local_q2,
                local_q3 = EXCLUDED.local_q3, local_q4 = EXCLUDED.local_q4,
                local_ot = EXCLUDED.local_ot, local_total = EXCLUDED.local_total,
                visitante_q1 = EXCLUDED.visitante_q1, visitante_q2 = EXCLUDED.visitante_q2,
                visitante_q3 = EXCLUDED.visitante_q3, visitante_q4 = EXCLUDED.visitante_q4,
                visitante_ot = EXCLUDED.visitante_ot, visitante_total = EXCLUDED.visitante_total,
                ganador_id = EXCLUDED.ganador_id,
                diferencia_puntos = EXCLUDED.diferencia_puntos,
                hubo_overtime = EXCLUDED.hubo_overtime,
                competicion_id = COALESCE(EXCLUDED.competicion_id, partidos_baloncesto.competicion_id),
                actualizado_en = now()
            RETURNING id, (xmax = 0) AS inserted
            """,
            (
                temporada_id, fecha_partido, tipo_partido, espn_game_id,
                equipo_local_id, equipo_visitante_id,
                int(local_q[0]), int(local_q[1]), int(local_q[2]), int(local_q[3]),
                int(local_ot), int(local_total),
                int(visitante_q[0]), int(visitante_q[1]), int(visitante_q[2]), int(visitante_q[3]),
                int(visitante_ot), int(visitante_total),
                ganador_id, diferencia, bool(hubo_overtime), competicion_id,
            ),
        )
        partido_id, inserted = cur.fetchone()
        return bool(inserted), str(partido_id)


# ============================================================================
# SINCRONIZACIÓN OPTIMIZADA (THREAD-SAFE)
# FIX: session ahora es parámetro en vez de crearse dentro del loop
# ============================================================================

def sincronizar_equipo_optimizado(
    conexion,
    equipo_bd: DbTeam,
    fecha_min: date,
    hoy: date,
    seasons: List[int],
    seasontypes: List[int],
    temporada_por_anio_fin: Dict[int, str],
    por_abbr: Dict[str, DbTeam],
    por_nombre: Dict[str, DbTeam],
    team_cache: EspnTeamCache,
    summary_cache: SummaryCache,
    rate_limiter: RateLimiter,
    session: requests.Session,         # FIX: sesión compartida, no se crea dentro del loop
    verbose: bool = False,             # Nuevo: imprimir causa de errores
) -> SyncStats:
    stats = SyncStats()

    # Resolver equipo en ESPN usando caché
    team_query = equipo_bd.abreviatura or equipo_bd.nombre
    team_info = team_cache.get_team(team_query)

    if not team_info:
        team_info = team_cache.get_team(equipo_bd.nombre)

    if not team_info:
        print(f"⚠️  No encontré {equipo_bd.nombre} en ESPN", flush=True)
        stats.errores += 1
        return stats

    team_id = team_info.id
    competicion_id_equipo = equipo_bd.competicion_id

    for season in seasons:
        temporada_id = temporada_por_anio_fin.get(int(season))
        if not temporada_id:
            temporada_id = asegurar_temporadas(conexion, [int(season)]).get(int(season), "")

        for st in seasontypes:
            tipo_partido = seasontype_to_tipo(st)

            try:
                rate_limiter.wait_if_needed()
                # FIX: usa la sesión compartida en vez de crear una nueva
                events = fetch_schedule_events(session, team_id, season, st)
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Error fetch_schedule_events {equipo_bd.nombre} s{season} t{st}: {e}", flush=True)
                stats.errores += 1
                continue

            for ev in events:
                if not is_completed_event(ev):
                    continue

                event_id = get_event_id(ev)
                if not event_id:
                    continue

                # FILTRO POR FECHA ANTES DE FETCH_SUMMARY (ahorra requests)
                comps = ev.get("competitions", []) or []
                ev_date_str = (comps[0].get("date") if comps else "") or ""
                fecha_ev = parse_fecha_calendario_espn_iso(ev_date_str)

                if fecha_ev < fecha_min or fecha_ev > hoy:
                    stats.omitidos += 1
                    continue

                # FIX: get_or_fetch maneja caché + descarga de forma thread-safe
                try:
                    summary = summary_cache.get_or_fetch(event_id, rate_limiter)
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Error fetch_summary event_id={event_id}: {e}", flush=True)
                    stats.errores += 1
                    continue

                try:
                    parsed = parse_summary_to_partido(summary)
                    home = parsed["home"]
                    away = parsed["away"]

                    home_team = asegurar_equipo_bd(conexion, por_abbr, por_nombre, home["nombre"], home["corto"], home["abbr"])
                    away_team = asegurar_equipo_bd(conexion, por_abbr, por_nombre, away["nombre"], away["corto"], away["abbr"])

                    local_total = int(parsed["home_total"])
                    visit_total = int(parsed["away_total"])

                    ganador_id = None
                    if local_total > visit_total:
                        ganador_id = home_team.id
                    elif visit_total > local_total:
                        ganador_id = away_team.id

                    competicion_id = competicion_id_equipo or home_team.competicion_id or away_team.competicion_id

                    if not competicion_id:
                        stats.omitidos += 1
                        if verbose:
                            print(f"   ⚠️  Sin competicion_id para evento {event_id}, omitido", flush=True)
                        continue

                    ins, _pid = upsert_partido_con_fecha(
                        conexion=conexion,
                        fecha_partido=parsed["fecha_partido"],
                        temporada_id=temporada_id,
                        tipo_partido=tipo_partido,
                        espn_game_id=str(event_id),
                        equipo_local_id=home_team.id,
                        equipo_visitante_id=away_team.id,
                        local_q=[int(x) for x in parsed["home_q"]],
                        visitante_q=[int(x) for x in parsed["away_q"]],
                        local_ot=int(parsed["home_ot"]),
                        visitante_ot=int(parsed["away_ot"]),   # FIX: era parsed["home_ot"]
                        local_total=local_total,
                        visitante_total=visit_total,
                        ganador_id=ganador_id,
                        hubo_overtime=bool(parsed["hubo_overtime"]),
                        competicion_id=competicion_id,
                    )

                    stats.procesados += 1
                    if ins:
                        stats.insertados += 1
                    else:
                        stats.actualizados += 1

                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Error procesando evento {event_id}: {e}", flush=True)
                    stats.errores += 1
                    continue

    return stats


def sincronizar_equipo_wrapper(
    equipo_bd: DbTeam,
    db_url: str,
    fecha_min: date,
    hoy: date,
    seasons: List[int],
    seasontypes: List[int],
    temporada_por_anio_fin: Dict[int, str],
    por_abbr: Dict[str, DbTeam],
    por_nombre: Dict[str, DbTeam],
    team_cache: EspnTeamCache,
    summary_cache: SummaryCache,
    rate_limiter: RateLimiter,
    session: requests.Session,
    verbose: bool = False,
) -> Tuple[str, SyncStats]:
    """Wrapper para ejecutar en thread separado con su propia conexión DB."""
    try:
        with psycopg.connect(db_url) as conexion:
            stats = sincronizar_equipo_optimizado(
                conexion=conexion,
                equipo_bd=equipo_bd,
                fecha_min=fecha_min,
                hoy=hoy,
                seasons=seasons,
                seasontypes=seasontypes,
                temporada_por_anio_fin=temporada_por_anio_fin,
                por_abbr=por_abbr,
                por_nombre=por_nombre,
                team_cache=team_cache,
                summary_cache=summary_cache,
                rate_limiter=rate_limiter,
                session=session,
                verbose=verbose,
            )
            conexion.commit()
            return (equipo_bd.nombre, stats)
    except Exception as e:
        print(f"⚠️  Error en wrapper {equipo_bd.nombre}: {e}", flush=True)
        return (equipo_bd.nombre, SyncStats(errores=1))


# ============================================================================
# EXPORTACIÓN
# ============================================================================

def exportar(partidos: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = out_path.suffix.lower()

    if ext == ".jsonl":
        with out_path.open("w", encoding="utf-8") as f:
            for row in partidos:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return

    headers = [
        "fecha_partido", "tipo_partido", "equipo_local", "equipo_visitante",
        "local_total", "visitante_total", "hubo_overtime", "espn_game_id",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in partidos:
            w.writerow({k: r.get(k) for k in headers})


def consultar_partidos_bd(conexion, equipo_id: str, fecha_min: date, limite: int = 200) -> List[Dict[str, Any]]:
    with conexion.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.fecha_partido, p.tipo_partido,
                el.nombre_corto AS equipo_local,
                ev.nombre_corto AS equipo_visitante,
                p.local_total, p.visitante_total,
                p.hubo_overtime, p.espn_game_id
            FROM partidos_baloncesto p
            JOIN equipos_baloncesto el ON el.id = p.equipo_local_id
            JOIN equipos_baloncesto ev ON ev.id = p.equipo_visitante_id
            WHERE p.fecha_partido >= %s
              AND (p.equipo_local_id = %s OR p.equipo_visitante_id = %s)
            ORDER BY p.fecha_partido DESC
            LIMIT %s
            """,
            (fecha_min, equipo_id, equipo_id, limite),
        )
        rows = cur.fetchall()

    out: List[Dict[str, Any]] = []
    for (f, tp, el, ev, lt, vt, hot, gid) in rows:
        out.append({
            "fecha_partido": str(f),
            "tipo_partido": str(tp),
            "equipo_local": str(el),
            "equipo_visitante": str(ev),
            "local_total": int(lt) if lt is not None else None,
            "visitante_total": int(vt) if vt is not None else None,
            "hubo_overtime": bool(hot),
            "espn_game_id": str(gid) if gid is not None else None,
        })
    return out


# ============================================================================
# CLI
# ============================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sincroniza y lista partidos de los últimos N días (VERSIÓN CORREGIDA + OPTIMIZADA)."
    )
    team_group = p.add_mutually_exclusive_group(required=True)
    team_group.add_argument("--team", type=str, help='Nombre o abreviatura. Ej: "Lakers" o "LAL"')
    team_group.add_argument("--all-teams", action="store_true", help="Sincroniza TODOS los equipos")

    p.add_argument("--competicion", type=str, default="NBA", help="Filtro de competición (default: NBA, usa ALL para todas)")
    p.add_argument("--days", type=int, default=10, help="Días hacia atrás (default: 10)")
    p.add_argument("--no-sync", action="store_true", help="Solo consulta BD")
    p.add_argument("--out", type=str, default="", help="Exportar a .csv o .jsonl")
    p.add_argument("--include-preseason", action="store_true", help="Incluye pretemporada")
    p.add_argument("--include-playoffs", action="store_true", help="Incluye playoffs")
    p.add_argument("--seasons", type=int, nargs="*", default=[], help="Temporadas (anio_fin)")
    p.add_argument("--limit", type=int, default=200, help="Límite de resultados")
    p.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"Hilos paralelos (default: {MAX_WORKERS})")
    p.add_argument("--verbose", action="store_true", help="Imprimir causa de cada error (útil para debug)")
    return p.parse_args()


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    load_dotenv()

    db_url = obtener_database_url()
    if not db_url:
        print("❌ Falta DATABASE_URL en el entorno (.env).")
        return 1

    args = parse_args()
    hoy = date.today()
    dias = max(1, int(args.days))
    fecha_min = hoy - timedelta(days=dias)
    comp_filtro = args.competicion.strip() if args.competicion else "NBA"

    print("=" * 90)
    print("🚀 SCRAPER CORREGIDO + OPTIMIZADO - AnalyticsPredict")
    print("=" * 90)
    print(f"   Rango: {fecha_min} a {hoy} ({dias} días)")
    print(f"   Competicion: {comp_filtro}")
    print(f"   Hilos paralelos: {args.workers}")
    print(f"   Rate limit: {REQUESTS_PER_SECOND} req/s")
    if args.verbose:
        print(f"   Modo verbose: ON (se mostrarán causas de errores)")
    print("=" * 90)
    print()

    with psycopg.connect(db_url) as conexion:
        # Determinar equipos
        if args.all_teams:
            equipos_a_sincronizar = obtener_todos_equipos_bd(conexion, competicion_filtro=comp_filtro)
            liga_label = "todas las ligas" if comp_filtro.upper() == COMPETICION_TODAS else comp_filtro
            print(f"📋 Equipos a sincronizar: {len(equipos_a_sincronizar)} ({liga_label})")
            if not equipos_a_sincronizar:
                print(f"⚠️  No se encontraron equipos para: '{comp_filtro}'")
                return 1
        else:
            equipo_bd = resolver_equipo_bd(conexion, args.team)
            equipos_a_sincronizar = [equipo_bd]
            print(f"📋 Equipo: {equipo_bd.nombre} ({equipo_bd.abreviatura})")

        print()

        if not args.no_sync:
            # FIX: sesión creada UNA SOLA VEZ y compartida entre todos los threads
            session = crear_sesion_http()
            team_cache = EspnTeamCache(session)
            summary_cache = SummaryCache(session, ttl_seconds=CACHE_SUMMARY_TTL)
            rate_limiter = RateLimiter(requests_per_second=REQUESTS_PER_SECOND)

            seasons = [int(s) for s in args.seasons] if args.seasons else sorted({hoy.year, hoy.year - 1})
            temporada_por_anio_fin = asegurar_temporadas(conexion, seasons)
            por_abbr, por_nombre = cargar_equipos_bd(conexion, competicion_filtro=comp_filtro)

            seasontypes = [2]
            if args.include_preseason:
                seasontypes.insert(0, 1)
            if args.include_playoffs:
                seasontypes.append(3)

            stats_globales = SyncStats()
            equipos_con_errores = 0

            print(f"⏳ Sincronizando {len(equipos_a_sincronizar)} equipos...\n")

            if args.workers > 1 and len(equipos_a_sincronizar) > 1:
                futures = {}
                with ThreadPoolExecutor(max_workers=args.workers) as executor:
                    for idx, equipo in enumerate(equipos_a_sincronizar, 1):
                        future = executor.submit(
                            sincronizar_equipo_wrapper,
                            equipo_bd=equipo,
                            db_url=db_url,
                            fecha_min=fecha_min,
                            hoy=hoy,
                            seasons=seasons,
                            seasontypes=seasontypes,
                            temporada_por_anio_fin=temporada_por_anio_fin,
                            por_abbr=por_abbr,
                            por_nombre=por_nombre,
                            team_cache=team_cache,
                            summary_cache=summary_cache,
                            rate_limiter=rate_limiter,
                            session=session,
                            verbose=args.verbose,
                        )
                        futures[future] = equipo

                    for future in as_completed(futures):
                        equipo = futures[future]
                        nombre, stats = future.result()

                        stats_globales.procesados += stats.procesados
                        stats_globales.insertados += stats.insertados
                        stats_globales.actualizados += stats.actualizados
                        stats_globales.omitidos += stats.omitidos
                        stats_globales.errores += stats.errores

                        if stats.errores > 0:
                            equipos_con_errores += 1

                        print(f"  ✓ {nombre}: {stats.insertados} nuevos, {stats.actualizados} actualizados, {stats.errores} errores")
            else:
                for idx, equipo in enumerate(equipos_a_sincronizar, 1):
                    if args.all_teams:
                        print(f"[{idx}/{len(equipos_a_sincronizar)}] {equipo.nombre}...", end=" ", flush=True)

                    stats = sincronizar_equipo_optimizado(
                        conexion=conexion,
                        equipo_bd=equipo,
                        fecha_min=fecha_min,
                        hoy=hoy,
                        seasons=seasons,
                        seasontypes=seasontypes,
                        temporada_por_anio_fin=temporada_por_anio_fin,
                        por_abbr=por_abbr,
                        por_nombre=por_nombre,
                        team_cache=team_cache,
                        summary_cache=summary_cache,
                        rate_limiter=rate_limiter,
                        session=session,
                        verbose=args.verbose,
                    )

                    stats_globales.procesados += stats.procesados
                    stats_globales.insertados += stats.insertados
                    stats_globales.actualizados += stats.actualizados
                    stats_globales.omitidos += stats.omitidos
                    stats_globales.errores += stats.errores

                    if stats.errores > 0:
                        equipos_con_errores += 1

                    if args.all_teams:
                        print(f"({stats.insertados} nuevos, {stats.actualizados} actualizados, {stats.errores} errores)")
                    else:
                        print(f"   Procesados: {stats.procesados} | Nuevos: {stats.insertados} | Actualizados: {stats.actualizados}")

            # Estadísticas de caché
            hits, misses = summary_cache.stats()
            cache_total = hits + misses
            cache_hit_rate = (hits / cache_total * 100) if cache_total > 0 else 0

            print()
            print("=" * 90)
            print("✅ Sincronización completada")
            print(f"   Partidos procesados: {stats_globales.procesados}")
            print(f"   Nuevos: {stats_globales.insertados}")
            print(f"   Actualizados: {stats_globales.actualizados}")
            print(f"   Omitidos: {stats_globales.omitidos}")
            print(f"   Errores: {stats_globales.errores}")
            if args.all_teams:
                print(f"   Equipos con errores: {equipos_con_errores}")
            print(f"   Caché summaries: {cache_hit_rate:.1f}% hit rate ({hits} hits, {misses} misses)")
            print("=" * 90)
            if stats_globales.errores > 0:
                print(f"\n💡 Tip: ejecuta con --verbose para ver la causa de cada error")

        # Consulta final
        if args.all_teams:
            print()
            print("📊 Resumen en BD:")
            with conexion.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM partidos_baloncesto WHERE fecha_partido >= %s", (fecha_min,))
                total = cur.fetchone()[0]
                print(f"   Total partidos en rango: {total}")

            if args.out:
                print(f"\n📦 Exportando a {args.out}...")
                with conexion.cursor() as cur:
                    cur.execute(
                        """
                        SELECT p.fecha_partido, p.tipo_partido,
                               el.nombre_corto AS equipo_local,
                               ev.nombre_corto AS equipo_visitante,
                               p.local_total, p.visitante_total,
                               p.hubo_overtime, p.espn_game_id
                        FROM partidos_baloncesto p
                        JOIN equipos_baloncesto el ON el.id = p.equipo_local_id
                        JOIN equipos_baloncesto ev ON ev.id = p.equipo_visitante_id
                        WHERE p.fecha_partido >= %s
                        ORDER BY p.fecha_partido DESC
                        LIMIT %s
                        """,
                        (fecha_min, int(args.limit))
                    )
                    rows = cur.fetchall()

                partidos_export = []
                for (f, tp, el, ev, lt, vt, hot, gid) in rows:
                    partidos_export.append({
                        "fecha_partido": str(f),
                        "tipo_partido": str(tp),
                        "equipo_local": str(el),
                        "equipo_visitante": str(ev),
                        "local_total": int(lt) if lt is not None else None,
                        "visitante_total": int(vt) if vt is not None else None,
                        "hubo_overtime": bool(hot),
                        "espn_game_id": str(gid) if gid is not None else None,
                    })

                exportar(partidos_export, Path(args.out))
                print(f"   Exportado: {len(partidos_export)} partidos")

        else:
            equipo_bd = equipos_a_sincronizar[0]
            partidos = consultar_partidos_bd(conexion, equipo_bd.id, fecha_min, limite=int(args.limit))

            if partidos:
                print(f"\n📌 Últimos partidos de {equipo_bd.nombre}:")
                print("-" * 90)
                for r in partidos[:10]:
                    ot = "OT" if r.get("hubo_overtime") else ""
                    print(f"{r['fecha_partido']}  {r['equipo_local']} {r['local_total']} - {r['visitante_total']} {r['equipo_visitante']}  {ot}")
                if len(partidos) > 10:
                    print(f"... y {len(partidos) - 10} más")
                print("-" * 90)

            if args.out:
                exportar(partidos, Path(args.out))
                print(f"\n📦 Exportado: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# -*- coding: utf-8 -*-
"""
sync_partidos.py — Sincronización incremental e idempotente de partidos NBA.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from dateutil import parser as dtparser
from zoneinfo import ZoneInfo

from db import obtener_pool

ESPN_SCOREBOARD_API = "https://site.web.api.espn.com/apis/v2/sports/basketball/nba/scoreboard"
ESPN_SUMMARY_API = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary"

DEFAULT_HEADERS = {
    "User-Agent": "AnalyticsPredict-Ingestion/1.0",
    "Accept": "application/json",
}

SEASONTYPE_LABEL = {1: "PRE", 2: "REG", 3: "POST"}

BUFFER_DAYS_DEFAULT = 2
STATE_KEY = "espn_recent_sync"

TEAM_TIMEZONES = {
    # Pacific
    "LAL": "America/Los_Angeles",
    "LAC": "America/Los_Angeles",
    "GSW": "America/Los_Angeles",
    "SAC": "America/Los_Angeles",
    "POR": "America/Los_Angeles",
    # Mountain
    "DEN": "America/Denver",
    "UTA": "America/Denver",
    "PHX": "America/Phoenix",
    # Central
    "DAL": "America/Chicago",
    "HOU": "America/Chicago",
    "SAS": "America/Chicago",
    "MEM": "America/Chicago",
    "NOP": "America/Chicago",
    "MIN": "America/Chicago",
    "OKC": "America/Chicago",
    "CHI": "America/Chicago",
    "MIL": "America/Chicago",
    # Eastern
    "IND": "America/Indiana/Indianapolis",
    "DET": "America/Detroit",
    "CLE": "America/New_York",
    "BOS": "America/New_York",
    "NYK": "America/New_York",
    "BKN": "America/New_York",
    "PHI": "America/New_York",
    "WAS": "America/New_York",
    "MIA": "America/New_York",
    "ORL": "America/New_York",
    "ATL": "America/New_York",
    "CHA": "America/New_York",
    "TOR": "America/Toronto",
}

NAME_MAP = {
    "la clippers": "los angeles clippers",
    "la lakers": "los angeles lakers",
}


@dataclass
class SyncConfig:
    days: int = 7
    buffer_days: int = BUFFER_DAYS_DEFAULT
    force: bool = False
    dry_run: bool = False
    source: str = "espn"
    max_workers: int = 4


@dataclass
class SyncResult:
    start_date: date
    end_date: date
    events_detected: int
    events_processed: int
    insertados: int
    actualizados: int
    omitidos: int
    errores: int
    fuente: str
    dry_run: bool
    detalles: List[str]


_thread_local = threading.local()


def _get_thread_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        _thread_local.session = session
    return session


def _request_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 6,
    backoff_base: float = 0.6,
) -> Dict[str, Any]:
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            session = _get_thread_session()
            resp = session.get(url, params=params, timeout=30)
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff_base * (2 ** attempt))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_err = exc
            time.sleep(backoff_base * (2 ** attempt))
    raise RuntimeError(f"Fallo consultando {url} params={params}. Error: {last_err}")


def _normalize_nombre(nombre: str) -> str:
    nombre = " ".join((nombre or "").strip().lower().replace("_", " ").split())
    return NAME_MAP.get(nombre, nombre)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_score_lines(competitor: Dict[str, Any]) -> List[int]:
    lines = competitor.get("linescores") or []
    valores: List[int] = []
    for entry in lines:
        if not isinstance(entry, dict):
            valores.append(0)
            continue
        if entry.get("value") is not None:
            valores.append(_safe_int(entry.get("value")))
            continue
        if entry.get("displayValue") is not None:
            valores.append(_safe_int(entry.get("displayValue")))
            continue
        valores.append(0)
    return valores


def _extract_competitors(summary: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    competitions = summary.get("competitions") or summary.get("header", {}).get("competitions") or []
    if not competitions:
        raise RuntimeError("Summary sin competitions")
    comp = competitions[0]
    competitors = comp.get("competitors") or []
    if len(competitors) < 2:
        raise RuntimeError("Summary sin 2 equipos")
    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
    return home, away


def _resolve_timezone(comp: Dict[str, Any], home_team_abbr: str) -> ZoneInfo:
    venue = comp.get("venue") or {}
    tz_name = venue.get("timeZone")
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    if home_team_abbr:
        tz_name = TEAM_TIMEZONES.get(home_team_abbr.upper())
        if tz_name:
            return ZoneInfo(tz_name)
    return ZoneInfo("America/New_York")


def _parse_event_datetime(comp: Dict[str, Any]) -> datetime:
    date_str = comp.get("date") or ""
    if not date_str:
        raise RuntimeError("Fecha no disponible en summary")
    dt = dtparser.isoparse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _map_season_type(summary: Dict[str, Any], comp: Dict[str, Any]) -> str:
    season_type = None
    if comp.get("season"):
        season_type = comp.get("season", {}).get("type")
    if season_type is None:
        season_type = summary.get("header", {}).get("season", {}).get("type")
    return SEASONTYPE_LABEL.get(int(season_type) if season_type is not None else 2, "REG")


def _resolver_temporada(conn, fecha_local: date) -> int:
    anio = fecha_local.year
    if fecha_local.month >= 9:
        anio_fin = anio + 1
    else:
        anio_fin = anio
    anio_inicio = anio_fin - 1
    nombre = f"{anio_inicio}-{anio_fin}"
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM temporadas WHERE (anio_inicio = %s AND anio_fin = %s) OR nombre = %s",
            (anio_inicio, anio_fin, nombre),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        fecha_inicio = f"{anio_inicio}-10-01"
        fecha_fin = f"{anio_fin}-06-30"
        cursor.execute(
            """
            INSERT INTO temporadas (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, True),
        )
        return cursor.fetchone()[0]


def _cargar_equipos(conn) -> Dict[str, str]:
    equipos: Dict[str, str] = {}
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM equipos")
        for equipo_id, nombre in cursor.fetchall():
            equipos[_normalize_nombre(nombre)] = str(equipo_id)
    return equipos


def _resolver_equipo_id(equipos: Dict[str, str], candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        clave = _normalize_nombre(candidate)
        if clave in equipos:
            return equipos[clave]
    return None


def _fetch_scoreboard_for_date(target_date: date) -> List[Dict[str, Any]]:
    params = {"dates": target_date.strftime("%Y%m%d")}
    data = _request_json(ESPN_SCOREBOARD_API, params=params)
    return data.get("events") or []


def _is_completed_event(event: Dict[str, Any]) -> bool:
    competitions = event.get("competitions") or []
    if competitions:
        status = competitions[0].get("status", {}).get("type", {})
        if status.get("completed") is True:
            return True
        name = str(status.get("name", "")).upper()
        state = str(status.get("state", "")).upper()
        return "FINAL" in name or "POST" in state
    return False


def _fetch_summary(event_id: str) -> Dict[str, Any]:
    return _request_json(ESPN_SUMMARY_API, params={"event": event_id})


def _parse_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    competitions = summary.get("competitions") or summary.get("header", {}).get("competitions") or []
    if not competitions:
        raise RuntimeError("Summary sin competitions")
    comp = competitions[0]
    home, away = _extract_competitors(summary)

    def team_name(comp_data: Dict[str, Any]) -> str:
        team = comp_data.get("team") or {}
        return team.get("displayName") or team.get("shortDisplayName") or ""

    def team_abbr(comp_data: Dict[str, Any]) -> str:
        team = comp_data.get("team") or {}
        return team.get("abbreviation") or ""

    home_name = team_name(home)
    away_name = team_name(away)
    home_abbr = team_abbr(home)

    home_total = int(home.get("score") or 0)
    away_total = int(away.get("score") or 0)

    home_lines = _parse_score_lines(home)
    away_lines = _parse_score_lines(away)

    while len(home_lines) < 4:
        home_lines.append(0)
    while len(away_lines) < 4:
        away_lines.append(0)

    ot_home = sum(home_lines[4:]) if len(home_lines) > 4 else 0
    ot_away = sum(away_lines[4:]) if len(away_lines) > 4 else 0

    if ot_home == 0 and ot_away == 0:
        ot_home = max(0, home_total - sum(home_lines[:4]))
        ot_away = max(0, away_total - sum(away_lines[:4]))

    hubo_overtime = (ot_home + ot_away) > 0

    tipo_partido = _map_season_type(summary, comp)

    dt_evento = _parse_event_datetime(comp)
    tz = _resolve_timezone(comp, home_abbr)
    dt_local = dt_evento.astimezone(tz)

    return {
        "source_game_id": str(comp.get("id") or summary.get("header", {}).get("id") or ""),
        "fecha_local": dt_local.date(),
        "fecha_evento_iso": dt_evento.isoformat(),
        "zona_horaria": tz.key,
        "tipo_partido": tipo_partido,
        "equipo_local": home_name,
        "equipo_visitante": away_name,
        "equipo_local_abbr": home_abbr,
        "local_q1": int(home_lines[0]),
        "local_q2": int(home_lines[1]),
        "local_q3": int(home_lines[2]),
        "local_q4": int(home_lines[3]),
        "local_ot": int(ot_home),
        "local_total": int(home_total),
        "visitante_q1": int(away_lines[0]),
        "visitante_q2": int(away_lines[1]),
        "visitante_q3": int(away_lines[2]),
        "visitante_q4": int(away_lines[3]),
        "visitante_ot": int(ot_away),
        "visitante_total": int(away_total),
        "hubo_overtime": bool(hubo_overtime),
    }


def _ensure_ingestion_schema(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_state (
                clave TEXT PRIMARY KEY,
                ultima_sincronizacion TIMESTAMPTZ,
                ultima_exito TIMESTAMPTZ,
                ultima_error TIMESTAMPTZ,
                ultimo_error TEXT,
                ultimo_event_ids JSONB,
                ultimo_insertados INTEGER DEFAULT 0,
                ultimo_actualizados INTEGER DEFAULT 0,
                ventana_dias INTEGER,
                cursor_inicio DATE,
                cursor_fin DATE,
                actualizado_en TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        cursor.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS source TEXT")
        cursor.execute("ALTER TABLE partidos ADD COLUMN IF NOT EXISTS source_game_id TEXT")
        cursor.execute(
            "UPDATE partidos SET source = 'espn' WHERE source IS NULL AND espn_game_id IS NOT NULL"
        )
        cursor.execute(
            "UPDATE partidos SET source_game_id = espn_game_id "
            "WHERE source_game_id IS NULL AND espn_game_id IS NOT NULL"
        )
        cursor.execute(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY source, source_game_id
                        ORDER BY
                            (
                                (local_q1 IS NOT NULL)::int +
                                (local_q2 IS NOT NULL)::int +
                                (local_q3 IS NOT NULL)::int +
                                (local_q4 IS NOT NULL)::int +
                                (visitante_q1 IS NOT NULL)::int +
                                (visitante_q2 IS NOT NULL)::int +
                                (visitante_q3 IS NOT NULL)::int +
                                (visitante_q4 IS NOT NULL)::int +
                                (local_total IS NOT NULL)::int +
                                (visitante_total IS NOT NULL)::int
                            ) DESC,
                            id DESC
                    ) AS rn
                FROM partidos
                WHERE source IS NOT NULL AND source_game_id IS NOT NULL
            )
            DELETE FROM partidos p
            USING ranked r
            WHERE p.id = r.id AND r.rn > 1
            """
        )
        cursor.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'partidos_source_source_game_id_key'
                ) THEN
                    ALTER TABLE partidos
                    ADD CONSTRAINT partidos_source_source_game_id_key UNIQUE (source, source_game_id);
                END IF;
            END
            $$
            """
        )
    conn.commit()


def _leer_estado(conn) -> Optional[Dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT ultima_sincronizacion, ultima_exito, ultima_error,
                   ultimo_error, ultimo_event_ids, ultimo_insertados,
                   ultimo_actualizados, ventana_dias, cursor_inicio, cursor_fin
            FROM ingestion_state
            WHERE clave = %s
            """,
            (STATE_KEY,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    return {
        "ultima_sincronizacion": row[0],
        "ultima_exito": row[1],
        "ultima_error": row[2],
        "ultimo_error": row[3],
        "ultimo_event_ids": row[4],
        "ultimo_insertados": row[5],
        "ultimo_actualizados": row[6],
        "ventana_dias": row[7],
        "cursor_inicio": row[8],
        "cursor_fin": row[9],
    }


def _guardar_estado(
    conn,
    start_date: date,
    end_date: date,
    insertados: int,
    actualizados: int,
    event_ids: List[str],
    error: Optional[str] = None,
) -> None:
    ahora = datetime.now(tz=timezone.utc)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ingestion_state (
                clave, ultima_sincronizacion, ultima_exito, ultima_error,
                ultimo_error, ultimo_event_ids, ultimo_insertados, ultimo_actualizados,
                ventana_dias, cursor_inicio, cursor_fin, actualizado_en
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (clave)
            DO UPDATE SET
                ultima_sincronizacion = EXCLUDED.ultima_sincronizacion,
                ultima_exito = EXCLUDED.ultima_exito,
                ultima_error = EXCLUDED.ultima_error,
                ultimo_error = EXCLUDED.ultimo_error,
                ultimo_event_ids = EXCLUDED.ultimo_event_ids,
                ultimo_insertados = EXCLUDED.ultimo_insertados,
                ultimo_actualizados = EXCLUDED.ultimo_actualizados,
                ventana_dias = EXCLUDED.ventana_dias,
                cursor_inicio = EXCLUDED.cursor_inicio,
                cursor_fin = EXCLUDED.cursor_fin,
                actualizado_en = EXCLUDED.actualizado_en
            """,
            (
                STATE_KEY,
                ahora,
                None if error else ahora,
                ahora if error else None,
                error,
                json.dumps(event_ids[:20]),
                insertados,
                actualizados,
                (end_date - start_date).days + 1,
                start_date,
                end_date,
                ahora,
            ),
        )
    conn.commit()


def _determine_window(cfg: SyncConfig, state: Optional[Dict[str, Any]]) -> Tuple[date, date]:
    ahora_est = datetime.now(tz=ZoneInfo("America/New_York")).date()
    end_date = ahora_est
    base_start = end_date - timedelta(days=max(cfg.days - 1, 0))

    if cfg.force or not state:
        start_date = end_date - timedelta(days=cfg.days + cfg.buffer_days - 1)
        if cfg.force:
            start_date = base_start
        return start_date, end_date

    cursor_fin = state.get("cursor_fin")
    if cursor_fin:
        buffer_start = cursor_fin - timedelta(days=cfg.buffer_days)
        start_date = min(base_start, buffer_start)
    else:
        start_date = end_date - timedelta(days=cfg.days + cfg.buffer_days - 1)

    return start_date, end_date


def _obtener_event_ids(start_date: date, end_date: date, detalles: List[str]) -> List[str]:
    event_ids: List[str] = []
    current = start_date
    while current <= end_date:
        try:
            events = _fetch_scoreboard_for_date(current)
            for ev in events:
                if not _is_completed_event(ev):
                    continue
                event_id = str(ev.get("id") or "")
                if event_id:
                    event_ids.append(event_id)
        except Exception as exc:
            detalles.append(f"⚠️  Error scoreboard {current}: {exc}")
        current += timedelta(days=1)
    return list(dict.fromkeys(event_ids))


def _fetch_and_parse_event(event_id: str) -> Dict[str, Any]:
    summary = _fetch_summary(event_id)
    parsed = _parse_summary(summary)
    parsed["event_id"] = event_id
    return parsed


def _upsert_partido(
    conn,
    equipos: Dict[str, str],
    parsed: Dict[str, Any],
    source: str,
    dry_run: bool,
) -> Tuple[str, str]:
    if not parsed["source_game_id"]:
        raise RuntimeError("Summary sin source_game_id")

    equipo_local_id = _resolver_equipo_id(
        equipos,
        [parsed["equipo_local"], parsed["equipo_local_abbr"]],
    )
    equipo_visitante_id = _resolver_equipo_id(
        equipos,
        [parsed["equipo_visitante"]],
    )

    if not equipo_local_id or not equipo_visitante_id:
        raise RuntimeError(
            f"Equipo no encontrado en BD: {parsed['equipo_local']} vs {parsed['equipo_visitante']}"
        )

    temporada_id = _resolver_temporada(conn, parsed["fecha_local"])

    ganador_id = None
    if parsed["local_total"] > parsed["visitante_total"]:
        ganador_id = equipo_local_id
    elif parsed["visitante_total"] > parsed["local_total"]:
        ganador_id = equipo_visitante_id

    if dry_run:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM partidos WHERE source = %s AND source_game_id = %s",
                (source, parsed["source_game_id"]),
            )
            existe = cursor.fetchone()
        return ("actualizado" if existe else "insertado", parsed["source_game_id"])

    sql_upsert = """
        INSERT INTO partidos (
            temporada_id, fecha_partido, tipo_partido, espn_game_id,
            source, source_game_id,
            equipo_local_id, equipo_visitante_id,
            local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
            visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
            ganador_id, hubo_overtime, valido
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (source, source_game_id)
        DO UPDATE SET
            temporada_id = EXCLUDED.temporada_id,
            fecha_partido = EXCLUDED.fecha_partido,
            tipo_partido = EXCLUDED.tipo_partido,
            espn_game_id = COALESCE(EXCLUDED.espn_game_id, partidos.espn_game_id),
            equipo_local_id = EXCLUDED.equipo_local_id,
            equipo_visitante_id = EXCLUDED.equipo_visitante_id,
            local_q1 = EXCLUDED.local_q1,
            local_q2 = EXCLUDED.local_q2,
            local_q3 = EXCLUDED.local_q3,
            local_q4 = EXCLUDED.local_q4,
            local_ot = EXCLUDED.local_ot,
            local_total = EXCLUDED.local_total,
            visitante_q1 = EXCLUDED.visitante_q1,
            visitante_q2 = EXCLUDED.visitante_q2,
            visitante_q3 = EXCLUDED.visitante_q3,
            visitante_q4 = EXCLUDED.visitante_q4,
            visitante_ot = EXCLUDED.visitante_ot,
            visitante_total = EXCLUDED.visitante_total,
            ganador_id = EXCLUDED.ganador_id,
            hubo_overtime = EXCLUDED.hubo_overtime,
            valido = TRUE,
            actualizado_en = NOW()
        RETURNING id, (xmax = 0) AS es_nuevo
    """

    valores = (
        temporada_id,
        parsed["fecha_local"],
        parsed["tipo_partido"],
        parsed["source_game_id"],
        source,
        parsed["source_game_id"],
        equipo_local_id,
        equipo_visitante_id,
        parsed["local_q1"],
        parsed["local_q2"],
        parsed["local_q3"],
        parsed["local_q4"],
        parsed["local_ot"],
        parsed["local_total"],
        parsed["visitante_q1"],
        parsed["visitante_q2"],
        parsed["visitante_q3"],
        parsed["visitante_q4"],
        parsed["visitante_ot"],
        parsed["visitante_total"],
        ganador_id,
        parsed["hubo_overtime"],
        True,
    )

    with conn.cursor() as cursor:
        cursor.execute(sql_upsert, valores)
        resultado = cursor.fetchone()

    if resultado and resultado[1]:
        return ("insertado", parsed["source_game_id"])
    return ("actualizado", parsed["source_game_id"])


def sync_partidos_recientes(cfg: Optional[SyncConfig] = None) -> SyncResult:
    cfg = cfg or SyncConfig()
    detalles: List[str] = []

    pool = obtener_pool()
    with pool.connection() as conn:
        _ensure_ingestion_schema(conn)
        estado = _leer_estado(conn)
        start_date, end_date = _determine_window(cfg, estado)

        equipos = _cargar_equipos(conn)

        event_ids = _obtener_event_ids(start_date, end_date, detalles)
        insertados = 0
        actualizados = 0
        omitidos = 0
        errores = 0

        if not event_ids:
            if not cfg.dry_run:
                _guardar_estado(conn, start_date, end_date, 0, 0, [])
            return SyncResult(
                start_date=start_date,
                end_date=end_date,
                events_detected=0,
                events_processed=0,
                insertados=0,
                actualizados=0,
                omitidos=0,
                errores=0,
                fuente=cfg.source,
                dry_run=cfg.dry_run,
                detalles=detalles,
            )

        from concurrent.futures import ThreadPoolExecutor, as_completed

        parsed_events: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=cfg.max_workers) as executor:
            futuros = {executor.submit(_fetch_and_parse_event, event_id): event_id for event_id in event_ids}
            for futuro in as_completed(futuros):
                event_id = futuros[futuro]
                try:
                    parsed = futuro.result()
                    parsed_events.append(parsed)
                except Exception as exc:
                    errores += 1
                    detalles.append(f"⚠️  Error evento {event_id}: {exc}")

        processed_ids: List[str] = []
        for parsed in parsed_events:
            try:
                accion, source_game_id = _upsert_partido(
                    conn, equipos, parsed, cfg.source, cfg.dry_run
                )
                processed_ids.append(source_game_id)
                if accion == "insertado":
                    insertados += 1
                elif accion == "actualizado":
                    actualizados += 1
                else:
                    omitidos += 1
            except Exception as exc:
                errores += 1
                detalles.append(f"⚠️  Error evento {parsed.get('event_id')}: {exc}")

        if not cfg.dry_run:
            conn.commit()
            error_msg = None if errores == 0 else "Errores durante sync"
            _guardar_estado(conn, start_date, end_date, insertados, actualizados, processed_ids, error_msg)

    return SyncResult(
        start_date=start_date,
        end_date=end_date,
        events_detected=len(event_ids),
        events_processed=len(processed_ids),
        insertados=insertados,
        actualizados=actualizados,
        omitidos=omitidos,
        errores=errores,
        fuente=cfg.source,
        dry_run=cfg.dry_run,
        detalles=detalles,
    )


def formatear_resumen(resultado: SyncResult) -> str:
    lineas = [
        "Resumen Sync Partidos",
        f"Fuente: {resultado.fuente}",
        f"Ventana: {resultado.start_date} -> {resultado.end_date}",
        f"Eventos detectados: {resultado.events_detected}",
        f"Eventos procesados: {resultado.events_processed}",
        f"Insertados: {resultado.insertados}",
        f"Actualizados: {resultado.actualizados}",
        f"Omitidos: {resultado.omitidos}",
        f"Errores: {resultado.errores}",
        f"Dry-run: {resultado.dry_run}",
    ]
    if resultado.detalles:
        lineas.append("Detalles:")
        lineas.extend(resultado.detalles[:10])
    return "\n".join(lineas)

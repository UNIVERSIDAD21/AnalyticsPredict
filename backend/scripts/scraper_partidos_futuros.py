#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sincroniza el calendario NBA de ESPN sin convertir fixtures en resultados.

El modo predeterminado es solo lectura. Para escribir se requiere ``--apply`` y
``--evidence-dir``; todas las altas se hacen en una única transacción. Nunca se
actualizan filas ya existentes. ``--rollback-file`` elimina únicamente las altas
de un manifiesto de aplicación que sigan intactas y con todos sus puntos en cero.

Ejemplos:
    python scripts/scraper_partidos_futuros.py --days 14 --evidence-dir /ruta/privada/evidencia
    python scripts/scraper_partidos_futuros.py --input-json calendario.json
    python scripts/scraper_partidos_futuros.py --input-json calendario.json \
        --apply --evidence-dir /ruta/privada/evidencia
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
import requests
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
NY = ZoneInfo("America/New_York")
SOURCE = "ESPN"
PHASE_BY_TYPE = {1: "PRE", 2: "REG", 3: "POST", 5: "POST"}
# Variantes oficiales literales del displayName de ESPN; no se usa fuzzy matching.
ESPN_NAME_ALIASES = {"la clippers": "los angeles clippers"}
ZERO_COLUMNS = (
    "local_q1", "local_q2", "local_q3", "local_q4", "local_ot", "local_total",
    "visitante_q1", "visitante_q2", "visitante_q3", "visitante_q4", "visitante_ot", "visitante_total",
)


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL no está configurada")
    if "sslmode=" not in value:
        value += ("&" if "?" in value else "?") + "sslmode=require"
    return value


def parse_nba_date(value: str) -> date:
    """Convierte fecha/hora acreditada a la fecha civil de Nueva York."""
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("ESPN entregó una fecha sin zona horaria")
    return parsed.astimezone(NY).date()


def _type_code(raw: Any) -> int:
    if isinstance(raw, dict):
        raw = raw.get("type")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("fase ESPN ausente o inválida") from exc


def parse_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Normaliza un evento ESPN crudo o el resumen de evidencia guardado.

    Devuelve None para eventos no programados (live/final). Estados desconocidos
    fallan cerrados para evitar registrar un fixture ambiguo.
    """
    if "home" in event and "away" in event:
        event_id = str(event.get("id") or "").strip()
        event_date = event.get("date_utc") or event.get("date")
        home = event.get("home") or {}
        away = event.get("away") or {}
        state = str(event.get("state") or "").lower()
        completed = bool(event.get("completed", False))
        type_code = _type_code(event.get("season_type"))
    else:
        competitions = event.get("competitions") or []
        if not competitions:
            raise ValueError("evento ESPN sin competitions")
        comp = competitions[0]
        competitors = comp.get("competitors") or []
        home_raw = next((x for x in competitors if x.get("homeAway") == "home"), None)
        away_raw = next((x for x in competitors if x.get("homeAway") == "away"), None)
        if not home_raw or not away_raw:
            raise ValueError("evento ESPN sin local/visitante inequívocos")
        event_id = str(event.get("id") or "").strip()
        event_date = event.get("date") or comp.get("date")
        status = comp.get("status") or event.get("status") or {}
        status_type = status.get("type") or status
        state = str(status_type.get("state") or "").lower()
        completed = bool(status_type.get("completed", False))
        home_team = home_raw.get("team") or {}
        away_team = away_raw.get("team") or {}
        home = {"abbr": home_team.get("abbreviation"), "name": home_team.get("displayName") or home_team.get("name")}
        away = {"abbr": away_team.get("abbreviation"), "name": away_team.get("displayName") or away_team.get("name")}
        type_code = _type_code(event.get("season") or event.get("season_type"))

    if completed or state in {"post", "in"}:
        return None
    if state not in {"pre"}:
        raise ValueError(f"estado ESPN no reconocido como fixture: {state or 'vacío'}")
    if not event_id or not event_date:
        raise ValueError("evento sin ID o fecha")
    if type_code not in PHASE_BY_TYPE:
        raise ValueError(f"fase ESPN no permitida: {type_code}")

    home_abbr = str(home.get("abbr") or "").strip().upper()
    away_abbr = str(away.get("abbr") or "").strip().upper()
    home_name = str(home.get("name") or "").strip()
    away_name = str(away.get("name") or "").strip()
    if not all((home_abbr, away_abbr, home_name, away_name)) or home_abbr == away_abbr:
        raise ValueError(f"equipos ESPN incompletos/ambiguos para {event_id}")

    return {
        "espn_game_id": event_id,
        "fecha_partido": parse_nba_date(str(event_date)).isoformat(),
        "tipo_partido": PHASE_BY_TYPE[type_code],
        "home_abbr": home_abbr,
        "home_name": home_name,
        "away_abbr": away_abbr,
        "away_name": away_name,
        "season_type": type_code,
        "state": state,
    }


def normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        record = parse_event(event)
        if record is None:
            continue
        event_id = record["espn_game_id"]
        prior = by_id.get(event_id)
        if prior is not None and prior != record:
            raise ValueError(f"ESPN repitió ID con payload distinto: {event_id}")
        by_id[event_id] = record

    records = list(by_id.values())
    natural_keys = [
        (r["fecha_partido"], r["tipo_partido"], r["home_abbr"], r["away_abbr"])
        for r in records
    ]
    if len(set(natural_keys)) != len(natural_keys):
        raise ValueError("el lote contiene una llave natural duplicada")
    return sorted(records, key=lambda row: (row["fecha_partido"], row["espn_game_id"]))


def load_input(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events") if isinstance(payload, dict) else payload
    if not isinstance(events, list):
        raise ValueError("el JSON debe ser una lista de eventos o contener 'events'")
    return events, {k: payload.get(k) for k in ("source", "start", "end", "summary") if isinstance(payload, dict) and k in payload}


def fetch_events(
    start: date, end: date, pacing_seconds: float = 1.25
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Obtiene scoreboards con ritmo fijo y conserva cada respuesta cruda.

    No reintenta bloqueos HTTP, valida que cada fecha tenga una lista de eventos
    completa respecto al límite solicitado y falla si ESPN alcanza ese límite.
    El cuerpo se conserva como texto UTF-8 y se acompaña con su SHA-256 exacto.
    """
    events: dict[str, dict[str, Any]] = {}
    responses: list[dict[str, Any]] = []
    with requests.Session() as session:
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            requested_at = datetime.now(timezone.utc).isoformat()
            response = session.get(ESPN_SCOREBOARD, params={"dates": day.strftime("%Y%m%d"), "limit": 500}, timeout=(10, 30))
            if response.status_code in {401, 403}:
                raise RuntimeError(f"ESPN rechazó la consulta HTTP {response.status_code}; no se reintentó")
            if response.status_code == 429:
                raise RuntimeError(f"ESPN limitó el ritmo HTTP 429; respeta Retry-After={response.headers.get('Retry-After', 'no indicado')}")
            response.raise_for_status()
            body_text = response.content.decode("utf-8")
            try:
                data = json.loads(body_text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"ESPN devolvió JSON inválido para {day}") from exc
            day_events = data.get("events")
            if not isinstance(day_events, list):
                raise ValueError(f"ESPN no devolvió una lista de eventos para {day}")
            if len(day_events) >= 500:
                raise ValueError(f"ESPN alcanzó el límite de 500 eventos para {day}; posible truncamiento")
            responses.append({
                "requested_day": day.isoformat(),
                "requested_at_utc": requested_at,
                "request_url": response.url,
                "http_status": response.status_code,
                "response_headers": {
                    key: response.headers[key]
                    for key in ("Date", "Content-Type", "ETag", "Last-Modified", "Retry-After")
                    if key in response.headers
                },
                "body_sha256": hashlib.sha256(response.content).hexdigest(),
                "body_text_utf8": body_text,
                "event_count": len(day_events),
            })
            for event in day_events:
                key = str(event.get("id") or "")
                if not key:
                    raise ValueError(f"evento sin id en la respuesta {day}")
                previous = events.get(key)
                if previous is not None and previous != event:
                    raise ValueError(f"ESPN entregó payloads distintos para ID {key}")
                events[key] = event
            if offset + 1 < (end - start).days + 1:
                time.sleep(pacing_seconds)
    capture = {
        "source": "ESPN NBA public scoreboard",
        "scoreboard_url": ESPN_SCOREBOARD,
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "request_count": len(responses),
        "event_count_unique": len(events),
        "pacing_seconds_between_requests": pacing_seconds,
        "responses": responses,
    }
    return list(events.values()), capture


def load_db_context(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM competiciones_baloncesto WHERE lower(codigo)='nba' AND activo IS TRUE")
        comps = cur.fetchall()
        if len(comps) != 1:
            raise RuntimeError(f"se requiere exactamente una competición NBA activa; encontradas={len(comps)}")
        competition_id = str(comps[0][0])
        cur.execute(
            """SELECT id,nombre FROM temporadas_baloncesto
               WHERE competicion_id=%s AND activa IS TRUE ORDER BY anio_fin DESC""",
            (competition_id,),
        )
        seasons = cur.fetchall()
        if len(seasons) != 1:
            raise RuntimeError(f"se requiere exactamente una temporada NBA activa; encontradas={len(seasons)}")
        cur.execute(
            """SELECT id,abreviatura,nombre FROM equipos
               WHERE activo IS TRUE AND competicion_principal_id=%s""",
            (competition_id,),
        )
        teams = cur.fetchall()
    by_abbr: dict[str, str] = {}
    by_name: dict[str, str] = {}
    for team_id, abbreviation, name in teams:
        key = str(abbreviation or "").strip().upper()
        if not key or key in by_abbr:
            raise RuntimeError(f"abreviatura NBA vacía o duplicada: {key!r}")
        by_abbr[key] = str(team_id)
        name_key = str(name or "").strip().casefold()
        if not name_key or name_key in by_name:
            raise RuntimeError(f"nombre NBA vacío o duplicado: {name_key!r}")
        by_name[name_key] = str(team_id)
    if len(by_abbr) != 30:
        raise RuntimeError(f"catálogo NBA debe tener 30 equipos activos; encontrados={len(by_abbr)}")
    return {
        "competicion_id": competition_id,
        "temporada_id": str(seasons[0][0]),
        "temporada_nombre": str(seasons[0][1]),
        "equipos_por_abrev": by_abbr,
        "equipos_por_nombre": by_name,
    }


def attach_db_ids(records: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    teams = context["equipos_por_abrev"]
    names = context["equipos_por_nombre"]
    for raw in records:
        home_key = ESPN_NAME_ALIASES.get(raw["home_name"].strip().casefold(), raw["home_name"].strip().casefold())
        away_key = ESPN_NAME_ALIASES.get(raw["away_name"].strip().casefold(), raw["away_name"].strip().casefold())
        home_id = names.get(home_key)
        away_id = names.get(away_key)
        if not home_id or not away_id:
            raise ValueError(f"nombre completo ESPN no coincide exactamente con catálogo NBA: {raw['home_name']} vs {raw['away_name']}")
        if raw["home_abbr"] in teams and teams[raw["home_abbr"]] != home_id:
            raise ValueError(f"abreviatura/nombre local ESPN discrepan: {raw['home_abbr']} / {raw['home_name']}")
        if raw["away_abbr"] in teams and teams[raw["away_abbr"]] != away_id:
            raise ValueError(f"abreviatura/nombre visitante ESPN discrepan: {raw['away_abbr']} / {raw['away_name']}")
        row = dict(raw)
        row.update({
            "competicion_id": context["competicion_id"],
            "temporada_id": context["temporada_id"],
            "equipo_local_id": home_id,
            "equipo_visitante_id": away_id,
            "source": SOURCE,
            "source_game_id": raw["espn_game_id"],
            "fuente_datos": SOURCE,
        })
        if row["equipo_local_id"] == row["equipo_visitante_id"]:
            raise ValueError(f"evento asigna el mismo equipo a ambos lados: {raw['espn_game_id']}")
        result.append(row)
    return result


def _identity(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row["temporada_id"]), str(row["fecha_partido"]), str(row["tipo_partido"]),
        str(row["equipo_local_id"]), str(row["equipo_visitante_id"]),
    )


def inspect_existing(conn, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Classifica claves existentes sin escritura; cualquier colisión ambigua aborta."""
    existing: list[dict[str, Any]] = []
    new: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    with conn.cursor() as cur:
        for candidate in records:
            cur.execute(
                """SELECT id::text, temporada_id::text, competicion_id::text, fecha_partido,
                          tipo_partido, equipo_local_id::text, equipo_visitante_id::text,
                          espn_game_id, source, source_game_id, local_total, visitante_total,
                          local_q1,local_q2,local_q3,local_q4,local_ot,
                          visitante_q1,visitante_q2,visitante_q3,visitante_q4,visitante_ot
                   FROM partidos_baloncesto
                   WHERE espn_game_id=%s OR (source=%s AND source_game_id=%s)
                      OR (temporada_id=%s AND fecha_partido=%s AND tipo_partido=%s
                          AND equipo_local_id=%s AND equipo_visitante_id=%s)""",
                (
                    candidate["espn_game_id"], SOURCE, candidate["source_game_id"],
                    candidate["temporada_id"], candidate["fecha_partido"], candidate["tipo_partido"],
                    candidate["equipo_local_id"], candidate["equipo_visitante_id"],
                ),
            )
            rows = cur.fetchall()
            if not rows:
                new.append(candidate)
                continue
            seen = [dict(zip(("id","temporada_id","competicion_id","fecha_partido","tipo_partido",
                              "equipo_local_id","equipo_visitante_id","espn_game_id","source","source_game_id",
                              "local_total","visitante_total","local_q1","local_q2","local_q3","local_q4","local_ot",
                              "visitante_q1","visitante_q2","visitante_q3","visitante_q4","visitante_ot"), row)) for row in rows]
            matches = len(seen) == 1 and (
                str(seen[0]["temporada_id"]) == candidate["temporada_id"]
                and str(seen[0]["competicion_id"]) == candidate["competicion_id"]
                and str(seen[0]["fecha_partido"]) == candidate["fecha_partido"]
                and str(seen[0]["tipo_partido"]) == candidate["tipo_partido"]
                and str(seen[0]["equipo_local_id"]) == candidate["equipo_local_id"]
                and str(seen[0]["equipo_visitante_id"]) == candidate["equipo_visitante_id"]
                and str(seen[0]["espn_game_id"] or candidate["espn_game_id"]) == candidate["espn_game_id"]
                and seen[0]["source"] in (None, SOURCE)
                and str(seen[0]["source_game_id"] or candidate["source_game_id"]) == candidate["source_game_id"]
            )
            is_pending = all(int(seen[0][col] or 0) == 0 for col in ZERO_COLUMNS) if len(seen) == 1 else False
            if matches and is_pending:
                existing.append({"candidate_id": candidate["espn_game_id"], "row": seen[0]})
            else:
                conflicts.append({"candidate_id": candidate["espn_game_id"], "rows": seen})
    return {"new": new, "existing": existing, "conflicts": conflicts}


def evidence_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def insert_batch(conn, records: list[dict[str, Any]]) -> list[dict[str, str]]:
    inserted = []
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:NBA:fixture-import'))")
        # Reclassify after acquiring the cooperative importer lock. Conflicts are
        # never silently converted into updates; a uniqueness race rolls back all.
        state = inspect_existing(conn, records)
        if state["conflicts"]:
            raise RuntimeError(f"colisiones detectadas bajo lock: {len(state['conflicts'])}")
        already = {item["candidate_id"] for item in state["existing"]}
        for row in records:
            if row["espn_game_id"] in already:
                continue
            cur.execute(
                """INSERT INTO partidos_baloncesto (
                       temporada_id,competicion_id,fecha_partido,tipo_partido,
                       equipo_local_id,equipo_visitante_id,
                       local_q1,local_q2,local_q3,local_q4,local_ot,local_total,
                       visitante_q1,visitante_q2,visitante_q3,visitante_q4,visitante_ot,visitante_total,
                       diferencia_puntos,hubo_overtime,fuente_datos,source,source_game_id,espn_game_id
                   ) VALUES (
                       %(temporada_id)s,%(competicion_id)s,%(fecha_partido)s,%(tipo_partido)s,
                       %(equipo_local_id)s,%(equipo_visitante_id)s,
                       0,0,0,0,0,0,0,0,0,0,0,0,0,false,%(fuente_datos)s,%(source)s,%(source_game_id)s,%(espn_game_id)s
                   ) ON CONFLICT DO NOTHING RETURNING id::text""",
                row,
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError(f"conflicto de unicidad durante alta {row['espn_game_id']}; lote revertido")
            inserted.append({"id": str(result[0]), "espn_game_id": row["espn_game_id"]})
        ids = [row["id"] for row in inserted]
        if ids:
            cur.execute(
                """SELECT count(*) FROM partidos_baloncesto
                   WHERE id = ANY(%s::uuid[]) AND source=%s AND source_game_id=espn_game_id
                     AND local_total=0 AND visitante_total=0
                     AND local_q1=0 AND local_q2=0 AND local_q3=0 AND local_q4=0 AND local_ot=0
                     AND visitante_q1=0 AND visitante_q2=0 AND visitante_q3=0 AND visitante_q4=0 AND visitante_ot=0""",
                (ids, SOURCE),
            )
            verified = int(cur.fetchone()[0])
            if verified != len(inserted):
                raise RuntimeError(f"postflight transaccional NBA {verified}/{len(inserted)}; lote revertido")
    return inserted


def rollback_batch(conn, manifest: dict[str, Any]) -> list[str]:
    if manifest.get("status") != "applied" or not manifest.get("inserted"):
        raise ValueError("el manifiesto no contiene altas aplicadas")
    ids = [str(item["id"]) for item in manifest["inserted"]]
    event_ids = [str(item["espn_game_id"]) for item in manifest["inserted"]]
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:NBA:fixture-import'))")
        cur.execute(
            f"""SELECT id::text FROM partidos_baloncesto WHERE id = ANY(%s::uuid[])
                AND source=%s AND espn_game_id = ANY(%s) AND source_game_id=espn_game_id
                AND {' AND '.join(f'{col}=0' for col in ZERO_COLUMNS)} FOR UPDATE""",
            (ids, SOURCE, event_ids),
        )
        rows = {str(row[0]) for row in cur.fetchall()}
        if rows != set(ids):
            raise RuntimeError("rollback detenido: alguna fila falta, cambió o ya tiene puntos; no se eliminó ninguna")
        cur.execute("DELETE FROM partidos_baloncesto WHERE id = ANY(%s::uuid[]) RETURNING id::text", (ids,))
        deleted = [str(row[0]) for row in cur.fetchall()]
        if set(deleted) != set(ids):
            raise RuntimeError("rollback incompleto; transacción revertida")
    return deleted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sincroniza fixtures NBA desde ESPN; modo seco por defecto")
    parser.add_argument("--days", type=int, default=14, help="días adelante, inclusivo desde hoy en Nueva York")
    parser.add_argument("--input-json", type=Path, help="captura de ESPN con events para reproducción")
    parser.add_argument("--pacing-seconds", type=float, default=1.25, help="pausa entre consultas ESPN (mínimo 1,25 s)")
    parser.add_argument("--apply", action="store_true", help="aplicar únicamente altas de fixtures; requiere evidencia")
    parser.add_argument("--evidence-dir", type=Path, help="directorio privado para preflight/manifiesto")
    parser.add_argument("--rollback-file", type=Path, help="manifiesto aplicado a revertir con guardas de filas intactas")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.days < 0 or args.days > 90:
        raise SystemExit("--days debe estar entre 0 y 90")
    if args.pacing_seconds < 1.25:
        raise SystemExit("--pacing-seconds no puede ser menor a 1,25")
    if args.rollback_file:
        if args.apply:
            raise SystemExit("--rollback-file y --apply son excluyentes")
        manifest = json.loads(args.rollback_file.read_text(encoding="utf-8"))
        with psycopg.connect(database_url()) as conn:
            deleted = rollback_batch(conn, manifest)
        print(json.dumps({"rolled_back": len(deleted), "ids": deleted}, ensure_ascii=False))
        return 0
    if args.apply and not args.evidence_dir:
        raise SystemExit("--apply requiere --evidence-dir para crear preflight antes de escribir")

    metadata: dict[str, Any] = {}
    if args.input_json:
        raw_events, metadata = load_input(args.input_json)
    else:
        if not args.evidence_dir:
            raise SystemExit("la consulta de red requiere --evidence-dir para conservar respuestas crudas")
        start = datetime.now(NY).date()
        end = start + timedelta(days=args.days)
        raw_events, raw_capture = fetch_events(start, end, pacing_seconds=args.pacing_seconds)
        capture_path = args.evidence_dir / "CAPTURA_ESPN_BRUTA.json"
        evidence_write(capture_path, raw_capture)
        metadata = {
            "source": "ESPN NBA scoreboard",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "capture_file": capture_path.name,
            "capture_sha256": file_sha256(capture_path),
            "request_count": raw_capture["request_count"],
            "event_count_unique": raw_capture["event_count_unique"],
        }
    normalized = normalize_events(raw_events)

    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        context = load_db_context(conn)
        records = attach_db_ids(normalized, context)
        state = inspect_existing(conn, records)

    report = {
        "status": "preflight",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": metadata,
        "competition_id": context["competicion_id"],
        "season_id": context["temporada_id"],
        "season_name": context["temporada_nombre"],
        "candidate_count": len(records),
        "new_count": len(state["new"]),
        "already_pending_count": len(state["existing"]),
        "conflict_count": len(state["conflicts"]),
        "candidates": records,
        "new": state["new"],
        "already_pending": state["existing"],
        "conflicts": state["conflicts"],
        "inserted": [],
    }
    if args.evidence_dir:
        evidence_write(args.evidence_dir / "PREFLIGHT_CALENDARIO_NBA.json", report)
    print(json.dumps({k: report[k] for k in ("candidate_count", "new_count", "already_pending_count", "conflict_count", "season_name")}, ensure_ascii=False))
    if state["conflicts"]:
        raise RuntimeError(f"se detectaron {len(state['conflicts'])} colisiones; no se aplicó el lote")
    if not args.apply:
        print("modo READ ONLY; no se hicieron escrituras")
        return 0

    with psycopg.connect(database_url()) as conn:
        inserted = insert_batch(conn, records)
    applied = dict(report)
    applied.update({"status": "applied", "applied_at_utc": datetime.now(timezone.utc).isoformat(), "inserted": inserted})
    evidence_write(args.evidence_dir / "RESULTADO_APLICACION_NBA.json", applied)
    print(json.dumps({"status": "applied", "inserted": len(inserted), "already_pending": len(state["existing"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # sanitized: never print DATABASE_URL or driver DSN details
        print(f"Error de sincronización NBA: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)

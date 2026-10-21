#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Importa fixtures EuroLeague desde capturas del Game Center oficial.

Por defecto es READ ONLY. Las altas requieren ``--apply`` y se realizan en una
única transacción. Se exige coincidencia exacta de ID, temporada, competición,
local, visitante y fecha del calendario oficial. Nunca se completan estadísticas
ni se convierten capturas web en resultados.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import psycopg
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

SOURCE = "EUROLEAGUE"
SOURCE_PAGE = "https://www.euroleaguebasketball.net/en/euroleague/game-center/"
BOGOTA = ZoneInfo("America/Bogota")
DATE_RE = re.compile(r"^(\d{1,2} (?:October|November) 2026)$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
SOURCE_ID_RE = re.compile(r"/E2026/(\d+)/?$")
ZERO_COLUMNS = (
    "local_q1", "local_q2", "local_q3", "local_q4", "local_ot", "local_total",
    "visitante_q1", "visitante_q2", "visitante_q3", "visitante_q4", "visitante_ot", "visitante_total",
)

# Crosswalk explícito de nombres visibles oficiales a nombres canónicos del catálogo.
# No se normaliza por similitud y cualquier nombre no listado aborta el lote.
TEAM_ALIASES = {
    "anadolu efes istanbul": "Anadolu Efes",
    "armani olimpia milan": "EA7 Emporio Armani Milano",
    "besiktas istanbul": "Besiktas Istanbul",
    "crvena zvezda meridianbet belgrade": "KK Crvena zvezda",
    "dubai basketball": "BC Dubai",
    "fc barcelona": "Barça Basket",
    "fc bayern munich": "Bayern München",
    "fenerbahce tarfin istanbul": "Fenerbahçe Beko",
    "hapoel ibi tel aviv": "Hapoel Tel-Aviv",
    "kosner baskonia vitoria-gasteiz": "Kosner Baskonia",
    "ldlc asvel villeurbanne": "LDLC ASVEL Lyon-Villeurbanne",
    "maccabi rapyd tel aviv": "Maccabi Tel Aviv",
    "olympiacos piraeus": "Olympiacos BC",
    "panathinaikos aktor athens": "Panathinaikos BC",
    "paris basketball": "Paris Basketball",
    "partizan mozzart bet belgrade": "KK Partizan Mozzart Bet",
    "real madrid": "Real Madrid",
    "valencia basket": "Valencia Basket",
    "virtus bologna": "Virtus Bologna",
    "zalgiris kaunas": "Kauno Žalgiris",
}


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL no está configurada")
    if "sslmode=" not in value:
        value += ("&" if "?" in value else "?") + "sslmode=require"
    return value


def _next_nonempty(lines: list[str], start: int) -> tuple[int, str]:
    for index in range(start, len(lines)):
        if lines[index].strip():
            return index, lines[index].strip()
    raise ValueError("bloque de partido truncado en el calendario oficial")


def parse_round_capture(capture_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extrae juegos PRE de texto renderizado y enlaces de partido oficiales."""
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture.get("source_url") != SOURCE_PAGE:
        raise ValueError(f"captura de origen inesperado: {capture_path.name}")
    round_number = int(capture.get("round") or 0)
    links = capture.get("game_links")
    if not isinstance(links, list) or len(links) != 10:
        raise ValueError(f"la ronda {round_number} debe contener exactamente 10 enlaces")
    lines = [line.strip() for line in str(capture.get("schedule_text") or "").splitlines()]
    current_date: date | None = None
    games: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    link_index = 0

    for index, line in enumerate(lines):
        date_match = DATE_RE.fullmatch(line)
        if date_match:
            current_date = datetime.strptime(date_match.group(1), "%d %B %Y").date()
            continue
        if not line.startswith("game "):
            continue
        if current_date is None:
            raise ValueError(f"partido sin fecha previa en ronda {round_number}")
        if link_index >= len(links):
            raise ValueError(f"la ronda {round_number} contiene más juegos que enlaces")
        link = links[link_index]
        link_index += 1
        source_match = SOURCE_ID_RE.search(str(link.get("url") or ""))
        if not source_match:
            raise ValueError(f"URL oficial sin ID E2026: {link.get('url')}")
        source_game_id = f"E2026/{source_match.group(1)}"
        label = line.removeprefix("game ").strip()

        time_index, time_value = _next_nonempty(lines, index + 1)
        if not TIME_RE.fullmatch(time_value):
            observations.append({
                "source_game_id": source_game_id,
                "label": label,
                "date": current_date.isoformat(),
                "status_observed": time_value,
                "reason": "no es una hora de partido programado; excluido del lote PRE",
            })
            continue

        venue_index, venue = _next_nonempty(lines, time_index + 1)
        home_index, home_name = _next_nonempty(lines, venue_index + 1)
        rank_index, home_rank = _next_nonempty(lines, home_index + 1)
        vs_index, versus = _next_nonempty(lines, rank_index + 1)
        away_index, away_name = _next_nonempty(lines, vs_index + 1)
        if not re.fullmatch(r"\(\d+\)", home_rank) or versus != "VS":
            raise ValueError(f"estructura local/visitante inválida para {source_game_id}")
        _, away_rank = _next_nonempty(lines, away_index + 1)
        if not re.fullmatch(r"\(\d+\)", away_rank):
            raise ValueError(f"segunda identidad de equipo inválida para {source_game_id}")
        link_label = str(link.get("label") or "")
        # En el calendario público el enlace muestra visitante vs local; la tarjeta
        # de juego (local VS visitante) es la fuente para asignar la localía.
        if link_label.casefold() != f"{away_name} vs {home_name}".casefold():
            raise ValueError(
                f"la tarjeta y el enlace discrepan en localía para {source_game_id}: "
                f"card={home_name} vs {away_name}; link={link_label}"
            )
        games.append({
            "source_game_id": source_game_id,
            "source_url": str(link["url"]),
            "source_label": link_label,
            "fecha_partido": current_date.isoformat(),
            "tipo_partido": "REG",
            "jornada_observada": round_number,
            "hora_renderizada": time_value,
            "sede": venue,
            "equipo_local_fuente": home_name,
            "equipo_visitante_fuente": away_name,
        })

    if link_index != len(links):
        raise ValueError(f"la ronda {round_number} tiene {len(links)} enlaces y {link_index} tarjetas")
    if len(games) + len(observations) != 10:
        raise ValueError(f"la ronda {round_number} no produjo 10 observaciones")
    return games, observations


def load_db_context(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("SELECT id,nombre,codigo FROM competiciones_baloncesto WHERE lower(codigo)='euroleague' AND activo IS TRUE")
        competitions = cur.fetchall()
        if len(competitions) != 1:
            raise RuntimeError(f"se requiere una competición EuroLeague activa; encontradas={len(competitions)}")
        competition_id = str(competitions[0][0])
        cur.execute(
            """SELECT id,nombre,anio_inicio,anio_fin FROM temporadas_baloncesto
               WHERE competicion_id=%s AND activa IS TRUE""",
            (competition_id,),
        )
        seasons = cur.fetchall()
        if len(seasons) != 1:
            raise RuntimeError(f"se requiere una temporada EuroLeague activa; encontradas={len(seasons)}")
        season_id, season_name, year_start, year_end = seasons[0]
        if int(year_start) != 2026 or int(year_end) != 2027:
            raise RuntimeError(f"capturas 2026-27 y temporada activa difieren: {year_start}-{year_end}")
        cur.execute(
            """SELECT id,nombre FROM equipos
               WHERE activo IS TRUE AND competicion_principal_id=%s""",
            (competition_id,),
        )
        teams = cur.fetchall()
    by_name = {str(name).strip().casefold(): str(team_id) for team_id, name in teams}
    if len(by_name) != len(teams):
        raise RuntimeError("el catálogo EuroLeague tiene nombres canónicos duplicados")
    if len(TEAM_ALIASES) != 20:
        raise RuntimeError("el crosswalk explícito debe describir los 20 equipos 2026-27")
    return {
        "competition_id": competition_id,
        "competition_name": str(competitions[0][1]),
        "season_id": str(season_id),
        "season_name": str(season_name),
        "teams_by_name": by_name,
    }


def attach_db_ids(events: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for event in events:
        home_canonical = TEAM_ALIASES.get(event["equipo_local_fuente"].strip().casefold())
        away_canonical = TEAM_ALIASES.get(event["equipo_visitante_fuente"].strip().casefold())
        if not home_canonical or not away_canonical:
            raise ValueError(
                "equipo oficial no registrado en el crosswalk exacto: "
                f"{event['equipo_local_fuente']} vs {event['equipo_visitante_fuente']}"
            )
        home_id = context["teams_by_name"].get(home_canonical.casefold())
        away_id = context["teams_by_name"].get(away_canonical.casefold())
        if not home_id or not away_id:
            raise ValueError(f"el crosswalk no llega al catálogo activo: {home_canonical} vs {away_canonical}")
        if home_id == away_id:
            raise ValueError(f"mismo equipo local y visitante: {event['source_game_id']}")
        row = dict(event)
        row.update({
            "competicion_id": context["competition_id"],
            "temporada_id": context["season_id"],
            "equipo_local_id": home_id,
            "equipo_visitante_id": away_id,
            "equipo_local_canonico": home_canonical,
            "equipo_visitante_canonico": away_canonical,
            "source": SOURCE,
            "fuente_datos": SOURCE,
        })
        result.append(row)
    ids = [row["source_game_id"] for row in result]
    natural = [(row["fecha_partido"], row["equipo_local_id"], row["equipo_visitante_id"], row["tipo_partido"]) for row in result]
    if len(ids) != len(set(ids)) or len(natural) != len(set(natural)):
        raise ValueError("ID externo o llave natural duplicada dentro del lote")
    return result


def inspect_existing(conn, records: list[dict[str, Any]]) -> dict[str, Any]:
    new, existing, conflicts = [], [], []
    columns = (
        "id", "temporada_id", "competicion_id", "fecha_partido", "tipo_partido",
        "equipo_local_id", "equipo_visitante_id", "source", "source_game_id",
        "local_total", "visitante_total", "local_q1", "local_q2", "local_q3", "local_q4", "local_ot",
        "visitante_q1", "visitante_q2", "visitante_q3", "visitante_q4", "visitante_ot",
    )
    with conn.cursor() as cur:
        for candidate in records:
            cur.execute(
                """SELECT id::text,temporada_id::text,competicion_id::text,fecha_partido,tipo_partido,
                          equipo_local_id::text,equipo_visitante_id::text,source,source_game_id,
                          local_total,visitante_total,local_q1,local_q2,local_q3,local_q4,local_ot,
                          visitante_q1,visitante_q2,visitante_q3,visitante_q4,visitante_ot
                   FROM partidos_baloncesto
                   WHERE (source=%s AND source_game_id=%s)
                      OR (temporada_id=%s AND fecha_partido=%s AND tipo_partido=%s
                          AND equipo_local_id=%s AND equipo_visitante_id=%s)""",
                (
                    SOURCE, candidate["source_game_id"], candidate["temporada_id"],
                    candidate["fecha_partido"], candidate["tipo_partido"],
                    candidate["equipo_local_id"], candidate["equipo_visitante_id"],
                ),
            )
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            if not rows:
                new.append(candidate)
                continue
            exact = len(rows) == 1 and all((
                str(rows[0]["temporada_id"]) == candidate["temporada_id"],
                str(rows[0]["competicion_id"]) == candidate["competicion_id"],
                str(rows[0]["fecha_partido"]) == candidate["fecha_partido"],
                str(rows[0]["tipo_partido"]) == candidate["tipo_partido"],
                str(rows[0]["equipo_local_id"]) == candidate["equipo_local_id"],
                str(rows[0]["equipo_visitante_id"]) == candidate["equipo_visitante_id"],
                rows[0]["source"] == SOURCE,
                rows[0]["source_game_id"] == candidate["source_game_id"],
            ))
            pending = len(rows) == 1 and all(int(rows[0][col] or 0) == 0 for col in ZERO_COLUMNS)
            item = {"source_game_id": candidate["source_game_id"], "rows": rows}
            if exact and pending:
                existing.append(item)
            else:
                conflicts.append(item)
    return {"new": new, "existing": existing, "conflicts": conflicts}


def evidence_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def insert_batch(conn, records: list[dict[str, Any]]) -> list[dict[str, str]]:
    inserted = []
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:EuroLeague:fixture-import'))")
        state = inspect_existing(conn, records)
        if state["conflicts"]:
            raise RuntimeError(f"colisiones bajo lock: {len(state['conflicts'])}; lote revertido")
        already = {item["source_game_id"] for item in state["existing"]}
        for row in records:
            if row["source_game_id"] in already:
                continue
            cur.execute(
                """INSERT INTO partidos_baloncesto(
                       temporada_id,competicion_id,fecha_partido,tipo_partido,equipo_local_id,equipo_visitante_id,
                       local_q1,local_q2,local_q3,local_q4,local_ot,local_total,
                       visitante_q1,visitante_q2,visitante_q3,visitante_q4,visitante_ot,visitante_total,
                       diferencia_puntos,hubo_overtime,fuente_datos,url_referencia,source,source_game_id
                   ) VALUES (
                       %(temporada_id)s,%(competicion_id)s,%(fecha_partido)s,%(tipo_partido)s,
                       %(equipo_local_id)s,%(equipo_visitante_id)s,
                       0,0,0,0,0,0,0,0,0,0,0,0,0,false,%(fuente_datos)s,%(source_url)s,%(source)s,%(source_game_id)s
                   ) ON CONFLICT DO NOTHING RETURNING id::text""",
                row,
            )
            saved = cur.fetchone()
            if saved is None:
                raise RuntimeError(f"conflicto de unicidad en {row['source_game_id']}; lote revertido")
            inserted.append({"id": str(saved[0]), "source_game_id": row["source_game_id"]})
        if inserted:
            ids = [row["id"] for row in inserted]
            cur.execute(
                """SELECT count(*) FROM partidos_baloncesto WHERE id=ANY(%s::uuid[])
                   AND source=%s AND fuente_datos=%s AND source_game_id IS NOT NULL
                   AND local_total=0 AND visitante_total=0
                   AND local_q1=0 AND local_q2=0 AND local_q3=0 AND local_q4=0 AND local_ot=0
                   AND visitante_q1=0 AND visitante_q2=0 AND visitante_q3=0 AND visitante_q4=0 AND visitante_ot=0""",
                (ids, SOURCE, SOURCE),
            )
            verified = int(cur.fetchone()[0])
            if verified != len(inserted):
                raise RuntimeError(f"postflight dentro de transacción {verified}/{len(inserted)}; lote revertido")
    return inserted


def rollback_batch(conn, manifest: dict[str, Any]) -> list[str]:
    if manifest.get("status") != "applied" or not manifest.get("inserted"):
        raise ValueError("manifiesto sin lote aplicado")
    ids = [str(row["id"]) for row in manifest["inserted"]]
    source_ids = [str(row["source_game_id"]) for row in manifest["inserted"]]
    zero_sql = " AND ".join(f"{column}=0" for column in ZERO_COLUMNS)
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('AnalyticsPredict:EuroLeague:fixture-import'))")
        cur.execute(
            f"""SELECT id::text FROM partidos_baloncesto
                WHERE id=ANY(%s::uuid[]) AND source=%s AND fuente_datos=%s
                  AND source_game_id=ANY(%s) AND {zero_sql} FOR UPDATE""",
            (ids, SOURCE, SOURCE, source_ids),
        )
        found = {str(row[0]) for row in cur.fetchall()}
        if found != set(ids):
            raise RuntimeError("rollback detenido: filas cambiaron; ninguna se eliminó")
        cur.execute("DELETE FROM partidos_baloncesto WHERE id=ANY(%s::uuid[]) RETURNING id::text", (ids,))
        deleted = [str(row[0]) for row in cur.fetchall()]
        if set(deleted) != set(ids):
            raise RuntimeError("rollback incompleto; transacción revertida")
    return deleted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sincroniza fixtures EuroLeague; READ ONLY por defecto")
    parser.add_argument("--source-dir", type=Path, required=True, help="capturas EUROLeague_RONDA_07..13")
    parser.add_argument("--evidence-dir", type=Path, required=True, help="salida privada de preflight/aplicación")
    parser.add_argument("--days", type=int, default=30, help="horizonte desde hoy en Bogotá (1–90)")
    parser.add_argument("--apply", action="store_true", help="aplica solo altas PRE después del preflight")
    parser.add_argument("--rollback-file", type=Path, help="revierte un manifiesto aplicado si todas las filas siguen intactas")
    return parser


def build_records(source_dir: Path, days: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], date, date]:
    events, observations = [], []
    for round_number in range(7, 14):
        path = source_dir / f"EUROLEAGUE_RONDA_{round_number:02d}.json"
        parsed, excluded = parse_round_capture(path)
        events.extend(parsed)
        observations.extend(excluded)
    ids = [row["source_game_id"] for row in events + observations]
    if len(ids) != 70 or len(ids) != len(set(ids)):
        raise ValueError(f"rondas 7–13 deben cubrir 70 IDs oficiales únicos; recibidos={len(ids)}")
    start = datetime.now(BOGOTA).date()
    end = start + timedelta(days=days)
    selected = [row for row in events if start <= date.fromisoformat(row["fecha_partido"]) <= end]
    return selected, observations, start, end


def main() -> int:
    args = build_parser().parse_args()
    if args.days < 1 or args.days > 90:
        raise SystemExit("--days debe estar entre 1 y 90")
    if args.rollback_file:
        if args.apply:
            raise SystemExit("--rollback-file y --apply son excluyentes")
        manifest = json.loads(args.rollback_file.read_text(encoding="utf-8"))
        with psycopg.connect(database_url()) as conn:
            deleted = rollback_batch(conn, manifest)
        print(json.dumps({"rolled_back": len(deleted)}, ensure_ascii=False))
        return 0

    raw_records, excluded, horizon_start, horizon_end = build_records(args.source_dir, args.days)
    if not raw_records:
        raise RuntimeError("no hay fixtures oficiales PRE dentro del horizonte solicitado")
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        context = load_db_context(conn)
        records = attach_db_ids(raw_records, context)
        state = inspect_existing(conn, records)

    report = {
        "status": "preflight",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE,
        "source_calendar_url": SOURCE_PAGE,
        "source_captures": [f"EUROLEAGUE_RONDA_{n:02d}.json" for n in range(7, 14)],
        "horizon_start_bogota": horizon_start.isoformat(),
        "horizon_end_bogota": horizon_end.isoformat(),
        "competition_id": context["competition_id"],
        "competition_name": context["competition_name"],
        "season_id": context["season_id"],
        "season_name": context["season_name"],
        "candidate_count": len(records),
        "new_count": len(state["new"]),
        "already_pending_count": len(state["existing"]),
        "conflict_count": len(state["conflicts"]),
        "excluded_observations": excluded,
        "candidates": records,
        "new": state["new"],
        "already_pending": state["existing"],
        "conflicts": state["conflicts"],
        "inserted": [],
    }
    evidence_write(args.evidence_dir / "PREFLIGHT_EUROLEAGUE.json", report)
    print(json.dumps({key: report[key] for key in ("candidate_count", "new_count", "already_pending_count", "conflict_count", "horizon_start_bogota", "horizon_end_bogota", "season_name")}, ensure_ascii=False))
    if state["conflicts"]:
        raise RuntimeError(f"colisiones detectadas: {len(state['conflicts'])}; no se escribió")
    if not args.apply:
        print("modo READ ONLY; no se hicieron escrituras")
        return 0

    with psycopg.connect(database_url()) as conn:
        inserted = insert_batch(conn, records)
    applied = dict(report)
    applied.update({"status": "applied", "applied_at_utc": datetime.now(timezone.utc).isoformat(), "inserted": inserted})
    evidence_write(args.evidence_dir / "RESULTADO_APLICACION_EUROLEAGUE.json", applied)
    print(json.dumps({"status": "applied", "inserted": len(inserted), "already_pending": len(state["existing"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # Sanitiza cualquier excepción: nunca imprime el DSN.
        print(f"Error calendario EuroLeague: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Actualiza partidos NBA recientes desde ESPN Scoreboard hacia PostgreSQL.

Diseño:
- Idempotente: usa source='ESPN' + source_game_id=event_id y llave natural de partido.
- Seguro: soporta --dry-run, no borra datos y valida cuartos/totales antes de escribir.
- Reutilizable: detecta competición/temporada/equipos desde la BD.

Ejemplos:
  backend/.venv/bin/python backend/scripts/actualizar_partidos_nba.py --days-back 45 --dry-run
  backend/.venv/bin/python backend/scripts/actualizar_partidos_nba.py --from-date 2026-04-13 --to-date 2026-05-06
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
HEADERS = {"User-Agent": "AnalyticsPredict-NBA-Ingestion/1.0", "Accept": "application/json"}
SOURCE = "ESPN"


@dataclass(frozen=True)
class DbContext:
    competicion_id: str
    temporada_id: str
    temporada_nombre: str
    equipos_por_abrev: dict[str, str]
    equipos_por_nombre: dict[str, str]


def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurada en backend/.env")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def daterange_chunks(start: date, end: date, chunk_days: int = 30):
    cur = start
    while cur <= end:
        chunk_end = min(end, cur + timedelta(days=chunk_days - 1))
        yield cur, chunk_end
        cur = chunk_end + timedelta(days=1)


def request_json(url: str, params: dict[str, Any], retries: int = 5, sleep: float = 0.8) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if resp.status_code in {429, 500, 502, 503, 504}:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else sleep * (2 ** attempt)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(sleep * (2 ** attempt))
    raise RuntimeError(f"Fallo consultando ESPN params={params}: {last}")


def safe_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def linescores(competitor: dict[str, Any]) -> list[int]:
    vals = [safe_int(x.get("value", x.get("displayValue", 0))) for x in competitor.get("linescores", [])]
    while len(vals) < 4:
        vals.append(0)
    return vals


def is_completed(event: dict[str, Any]) -> bool:
    st = event.get("status", {}).get("type", {})
    return bool(st.get("completed")) or str(st.get("state", "")).lower() == "post"


def season_type(event: dict[str, Any]) -> str:
    raw = event.get("season", {}).get("type")
    return {1: "PRE", 2: "REG", 3: "POST"}.get(safe_int(raw), "REG")


def event_to_record(event: dict[str, Any], ctx: DbContext) -> dict[str, Any]:
    comps = event.get("competitions") or []
    if not comps:
        raise ValueError("evento sin competitions")
    competitors = comps[0].get("competitors") or []
    if len(competitors) != 2:
        raise ValueError("evento sin dos competidores")
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        raise ValueError("no se pudo determinar local/visitante")

    def team_id(c: dict[str, Any]) -> str | None:
        team = c.get("team") or {}
        abbr = str(team.get("abbreviation") or "").upper()
        name = str(team.get("displayName") or team.get("name") or "")
        return ctx.equipos_por_abrev.get(abbr) or ctx.equipos_por_nombre.get(name.lower())

    home_id = team_id(home)
    away_id = team_id(away)
    if not home_id or not away_id:
        hn = (home.get("team") or {}).get("displayName")
        an = (away.get("team") or {}).get("displayName")
        raise ValueError(f"equipo no existe en BD: {hn} vs {an}")

    home_ls = linescores(home)
    away_ls = linescores(away)
    home_total = safe_int(home.get("score"))
    away_total = safe_int(away.get("score"))
    home_ot = max(0, home_total - sum(home_ls[:4]))
    away_ot = max(0, away_total - sum(away_ls[:4]))
    if sum(home_ls[:4]) + home_ot != home_total or sum(away_ls[:4]) + away_ot != away_total:
        raise ValueError("cuartos/totales inconsistentes")

    event_date = datetime.fromisoformat(str(event["date"]).replace("Z", "+00:00")).date()
    winner_id = home_id if home_total > away_total else away_id if away_total > home_total else None
    event_id = str(event.get("id") or comps[0].get("id") or "").strip()
    if not event_id:
        raise ValueError("evento sin id ESPN")

    links = event.get("links") or []
    url = next((x.get("href") for x in links if isinstance(x, dict) and x.get("href")), None)

    return {
        "temporada_id": ctx.temporada_id,
        "competicion_id": ctx.competicion_id,
        "fecha_partido": event_date,
        "tipo_partido": season_type(event),
        "equipo_local_id": home_id,
        "equipo_visitante_id": away_id,
        "local_q1": home_ls[0], "local_q2": home_ls[1], "local_q3": home_ls[2], "local_q4": home_ls[3],
        "local_ot": home_ot, "local_total": home_total,
        "visitante_q1": away_ls[0], "visitante_q2": away_ls[1], "visitante_q3": away_ls[2], "visitante_q4": away_ls[3],
        "visitante_ot": away_ot, "visitante_total": away_total,
        "ganador_id": winner_id,
        "diferencia_puntos": home_total - away_total,
        "hubo_overtime": home_ot > 0 or away_ot > 0,
        "fuente_datos": SOURCE,
        "source": SOURCE,
        "source_game_id": event_id,
        "espn_game_id": event_id,
        "url_referencia": url,
    }


def load_context(conn, season_year: int | None) -> DbContext:
    with conn.cursor() as cur:
        cur.execute("select id from competiciones_baloncesto where lower(codigo)='nba' and activo=true")
        row = cur.fetchone()
        if not row:
            raise RuntimeError("No existe competición NBA activa en competiciones_baloncesto")
        comp_id = str(row[0])

        if season_year:
            cur.execute(
                """
                select id,nombre from temporadas_baloncesto
                where competicion_id=%s and anio_fin=%s
                order by activa desc, anio_fin desc limit 1
                """,
                (comp_id, season_year),
            )
        else:
            cur.execute(
                """
                select id,nombre from temporadas_baloncesto
                where competicion_id=%s and activa=true
                order by anio_fin desc limit 1
                """,
                (comp_id,),
            )
        season = cur.fetchone()
        if not season:
            raise RuntimeError("No existe temporada NBA activa/solicitada en temporadas_baloncesto")

        cur.execute(
            """
            select id, abreviatura, nombre
            from equipos
            where activo=true and competicion_principal_id=%s
            """,
            (comp_id,),
        )
        equipos = cur.fetchall()
        if len(equipos) < 30:
            raise RuntimeError(f"Catálogo NBA incompleto: {len(equipos)} equipos")
        return DbContext(
            competicion_id=comp_id,
            temporada_id=str(season[0]),
            temporada_nombre=str(season[1]),
            equipos_por_abrev={str(a).upper(): str(i) for i, a, _ in equipos if a},
            equipos_por_nombre={str(n).lower(): str(i) for i, _, n in equipos if n},
        )


def fetch_events(start: date, end: date) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for a, b in daterange_chunks(start, end):
        params = {"dates": f"{a:%Y%m%d}-{b:%Y%m%d}", "limit": 500}
        data = request_json(ESPN_SCOREBOARD, params)
        for ev in data.get("events", []) or []:
            if is_completed(ev):
                out[str(ev.get("id"))] = ev
    return sorted(out.values(), key=lambda e: e.get("date", ""))


def existing_keys(conn, records: list[dict[str, Any]]) -> tuple[set[str], set[tuple[Any, ...]]]:
    source_ids = [r["source_game_id"] for r in records]
    exacts = [(r["temporada_id"], r["fecha_partido"], r["tipo_partido"], r["equipo_local_id"], r["equipo_visitante_id"]) for r in records]
    existing_source: set[str] = set()
    existing_exact: set[tuple[Any, ...]] = set()
    if not records:
        return existing_source, existing_exact
    with conn.cursor() as cur:
        cur.execute("select source_game_id from partidos_baloncesto where source=%s and source_game_id = any(%s)", (SOURCE, source_ids))
        existing_source = {str(x[0]) for x in cur.fetchall()}
        cur.execute(
            """
            select temporada_id::text, fecha_partido, tipo_partido, equipo_local_id::text, equipo_visitante_id::text
            from partidos_baloncesto
            where (temporada_id, fecha_partido, tipo_partido, equipo_local_id, equipo_visitante_id) in (
            """
            + ",".join(["(%s,%s,%s,%s,%s)"] * len(exacts))
            + ")",
            [item for tup in exacts for item in tup],
        )
        existing_exact = set(cur.fetchall())
    return existing_source, existing_exact


def upsert_records(conn, records: list[dict[str, Any]], dry_run: bool) -> dict[str, int]:
    existing_source, existing_exact = existing_keys(conn, records)
    stats = {"found": len(records), "inserted": 0, "existing": 0, "updated": 0, "failed": 0}
    if dry_run:
        stats["existing"] = sum(1 for r in records if r["source_game_id"] in existing_source)
        stats["inserted"] = len(records) - stats["existing"]
        return stats

    sql = """
    INSERT INTO partidos_baloncesto (
      temporada_id, competicion_id, fecha_partido, tipo_partido,
      equipo_local_id, equipo_visitante_id,
      local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
      visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
      ganador_id, diferencia_puntos, hubo_overtime,
      fuente_datos, source, source_game_id, espn_game_id, url_referencia, actualizado_en
    ) VALUES (
      %(temporada_id)s, %(competicion_id)s, %(fecha_partido)s, %(tipo_partido)s,
      %(equipo_local_id)s, %(equipo_visitante_id)s,
      %(local_q1)s, %(local_q2)s, %(local_q3)s, %(local_q4)s, %(local_ot)s, %(local_total)s,
      %(visitante_q1)s, %(visitante_q2)s, %(visitante_q3)s, %(visitante_q4)s, %(visitante_ot)s, %(visitante_total)s,
      %(ganador_id)s, %(diferencia_puntos)s, %(hubo_overtime)s,
      %(fuente_datos)s, %(source)s, %(source_game_id)s, %(espn_game_id)s, %(url_referencia)s, now()
    )
    ON CONFLICT (source, source_game_id) DO UPDATE SET
      fecha_partido=EXCLUDED.fecha_partido,
      tipo_partido=EXCLUDED.tipo_partido,
      equipo_local_id=EXCLUDED.equipo_local_id,
      equipo_visitante_id=EXCLUDED.equipo_visitante_id,
      local_q1=EXCLUDED.local_q1, local_q2=EXCLUDED.local_q2, local_q3=EXCLUDED.local_q3, local_q4=EXCLUDED.local_q4,
      local_ot=EXCLUDED.local_ot, local_total=EXCLUDED.local_total,
      visitante_q1=EXCLUDED.visitante_q1, visitante_q2=EXCLUDED.visitante_q2, visitante_q3=EXCLUDED.visitante_q3, visitante_q4=EXCLUDED.visitante_q4,
      visitante_ot=EXCLUDED.visitante_ot, visitante_total=EXCLUDED.visitante_total,
      ganador_id=EXCLUDED.ganador_id,
      diferencia_puntos=EXCLUDED.diferencia_puntos,
      hubo_overtime=EXCLUDED.hubo_overtime,
      fuente_datos=EXCLUDED.fuente_datos,
      espn_game_id=EXCLUDED.espn_game_id,
      url_referencia=EXCLUDED.url_referencia,
      actualizado_en=now()
    """
    with conn.cursor() as cur:
        for r in records:
            try:
                natural = (r["temporada_id"], r["fecha_partido"], r["tipo_partido"], r["equipo_local_id"], r["equipo_visitante_id"])
                existed = r["source_game_id"] in existing_source or natural in existing_exact
                cur.execute(sql, r)
                if existed:
                    stats["existing"] += 1
                    stats["updated"] += 1
                else:
                    stats["inserted"] += 1
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                stats["failed"] += 1
                print(f"ERROR event={r.get('source_game_id')}: {exc}", file=sys.stderr)
            else:
                conn.commit()
    return stats


def update_ingestion_state(conn, ctx: DbContext, stats: dict[str, int], start: date, end: date, dry_run: bool) -> None:
    if dry_run:
        return
    ok = stats["failed"] == 0
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_state_baloncesto (
              clave, competicion_id, ultima_sincronizacion, ultima_exito, ultima_error,
              ultimo_error, ultimo_insertados, ultimo_actualizados, cursor_fecha, ventana_dias, metadata, actualizado_en
            ) VALUES (%s,%s,now(),CASE WHEN %s THEN now() ELSE NULL END,CASE WHEN %s THEN NULL ELSE now() END,%s,%s,%s,%s,%s,%s::jsonb,now())
            ON CONFLICT (clave) DO UPDATE SET
              competicion_id=EXCLUDED.competicion_id,
              ultima_sincronizacion=EXCLUDED.ultima_sincronizacion,
              ultima_exito=CASE WHEN %s THEN EXCLUDED.ultima_exito ELSE ingestion_state_baloncesto.ultima_exito END,
              ultima_error=CASE WHEN %s THEN ingestion_state_baloncesto.ultima_error ELSE EXCLUDED.ultima_error END,
              ultimo_error=EXCLUDED.ultimo_error,
              ultimo_insertados=EXCLUDED.ultimo_insertados,
              ultimo_actualizados=EXCLUDED.ultimo_actualizados,
              cursor_fecha=EXCLUDED.cursor_fecha,
              ventana_dias=EXCLUDED.ventana_dias,
              metadata=EXCLUDED.metadata,
              actualizado_en=now()
            """,
            (
                "nba_partidos", ctx.competicion_id, ok, ok, None if ok else "fallos en ingesta",
                stats["inserted"], stats["updated"], end, (end - start).days + 1,
                json.dumps({"fuente": SOURCE, "from": str(start), "to": str(end), **stats}), ok, ok,
            ),
        )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--from-date", type=parse_date)
    parser.add_argument("--to-date", type=parse_date, default=date.today())
    parser.add_argument("--days-back", type=int, default=45)
    parser.add_argument("--season", type=int, help="Año final ESPN/NBA, ej. 2026 para 2025-2026")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    start = args.from_date or (args.to_date - timedelta(days=args.days_back))
    end = args.to_date
    if start > end:
        raise SystemExit("--from-date no puede ser mayor que --to-date")

    import psycopg

    with psycopg.connect(db_url()) as conn:
        ctx = load_context(conn, args.season)
        print(f"NBA {ctx.temporada_nombre}: consultando ESPN {start} → {end} (dry_run={args.dry_run})")
        events = fetch_events(start, end)
        records: list[dict[str, Any]] = []
        failed_parse = 0
        for ev in events:
            try:
                records.append(event_to_record(ev, ctx))
            except Exception as exc:  # noqa: BLE001
                failed_parse += 1
                print(f"WARN event={ev.get('id')}: {exc}", file=sys.stderr)
        stats = upsert_records(conn, records, args.dry_run)
        stats["failed"] += failed_parse
        update_ingestion_state(conn, ctx, stats, start, end, args.dry_run)
        print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
        return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

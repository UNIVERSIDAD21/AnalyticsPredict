#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper_equipos_recientes.py — Sincroniza e imprime los partidos terminados de los últimos N días para 1 equipo o TODOS.

Objetivo:
- Ejecutar un script y traer los últimos partidos (últimos N días) de un equipo o todos los equipos.
- Sin CSV, incremental e idempotente (UPSERT), BD como fuente de verdad.

Uso recomendado (desde carpeta backend):
    # Un solo equipo:
    python scripts/scraper_equipos_recientes.py --team "Los Angeles Lakers" --days 10

    # TODOS los equipos:
    python scripts/scraper_equipos_recientes.py --all-teams --days 10

Opciones útiles:
    --all-teams          Sincroniza TODOS los equipos activos en la BD
    --no-sync            Solo consulta en BD (no llama a ESPN)
    --out <ruta>         Exporta a CSV o JSONL según extensión (.csv o .jsonl)
    --include-preseason  Incluye pretemporada (seasontype=1)
    --include-playoffs   Incluye playoffs (seasontype=3)
    --seasons 2025 2026  Fuerza temporadas ESPN (anio_fin) a consultar
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Asegurar imports del paquete backend cuando se ejecuta desde /backend o /backend/scripts
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    import requests
except Exception as e:
    raise SystemExit("❌ Falta 'requests'. Instala dependencias: pip install -r requirements.txt") from e

try:
    from motor.nba_scraper_espn import (
        resolve_team,
        fetch_schedule_events,
        is_completed_event,
        get_event_id,
        fetch_summary,
        extract_linescores,
    )
except Exception as e:
    raise SystemExit("❌ No pude importar motor.nba_scraper_espn. Ejecuta desde carpeta backend.") from e

ZONA_HORARIA_NBA = ZoneInfo("America/New_York")


@dataclass
class DbTeam:
    id: str
    nombre: str
    nombre_corto: str
    abreviatura: str


def obtener_database_url() -> str:
    """Obtiene la URL de la base de datos. Fuerza sslmode=require si no viene."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return ""
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return default
        if isinstance(v, bool):
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
    """
    Convierte una fecha ISO a fecha NBA (America/New_York).
    """
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
    if seasontype == 1:
        return "PRE"
    if seasontype == 3:
        return "POST"
    return "REG"


def normalize_nombre(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())


def cargar_equipos_bd(conexion) -> Tuple[Dict[str, DbTeam], Dict[str, DbTeam]]:
    """Devuelve (por_abreviatura, por_nombre_normalizado)."""
    por_abbr: Dict[str, DbTeam] = {}
    por_nombre: Dict[str, DbTeam] = {}
    with conexion.cursor() as cur:
        cur.execute("SELECT id, nombre, nombre_corto, abreviatura FROM equipos WHERE activo = true")
        for rid, nombre, nombre_corto, abbr in cur.fetchall():
            t = DbTeam(
                id=str(rid),
                nombre=str(nombre or ""),
                nombre_corto=str(nombre_corto or ""),
                abreviatura=str(abbr or "").upper(),
            )
            if t.abreviatura:
                por_abbr[t.abreviatura] = t
            key1 = normalize_nombre(t.nombre)
            key2 = normalize_nombre(t.nombre_corto)
            if key1:
                por_nombre[key1] = t
            if key2:
                por_nombre[key2] = t
    return por_abbr, por_nombre


def obtener_todos_equipos_bd(conexion) -> List[DbTeam]:
    """Retorna lista de todos los equipos activos."""
    equipos: List[DbTeam] = []
    with conexion.cursor() as cur:
        cur.execute("""
            SELECT id, nombre, nombre_corto, abreviatura 
            FROM equipos 
            WHERE activo = true 
            ORDER BY nombre
        """)
        for rid, nombre, nombre_corto, abbr in cur.fetchall():
            equipos.append(DbTeam(
                id=str(rid),
                nombre=str(nombre or ""),
                nombre_corto=str(nombre_corto or ""),
                abreviatura=str(abbr or "").upper(),
            ))
    return equipos


def asegurar_equipo_bd(
    conexion,
    por_abbr: Dict[str, DbTeam],
    por_nombre: Dict[str, DbTeam],
    nombre: str,
    nombre_corto: str,
    abreviatura: str,
) -> DbTeam:
    """
    Asegura que el equipo exista en BD; si no, lo inserta con lo mínimo.
    Mantiene mapeos en memoria actualizados.
    """
    ab = str(abreviatura or "").upper().strip()
    if ab and ab in por_abbr:
        return por_abbr[ab]

    key = normalize_nombre(nombre)
    if key and key in por_nombre:
        return por_nombre[key]

    # Insert mínimo: nombre, nombre_corto, abreviatura, activo=true; conferencia/division/ciudad NULL
    with conexion.cursor() as cur:
        cur.execute(
            """
            INSERT INTO equipos (nombre, nombre_corto, abreviatura, conferencia, division, ciudad, activo)
            VALUES (%s, %s, %s, NULL, NULL, NULL, true)
            ON CONFLICT (abreviatura) DO UPDATE SET
                nombre = COALESCE(EXCLUDED.nombre, equipos.nombre),
                nombre_corto = COALESCE(EXCLUDED.nombre_corto, equipos.nombre_corto),
                activo = true
            RETURNING id, nombre, nombre_corto, abreviatura
            """,
            (nombre, nombre_corto or nombre, ab),
        )
        rid, rnom, rshort, rabbr = cur.fetchone()
    conexion.commit()

    t = DbTeam(id=str(rid), nombre=str(rnom or ""), nombre_corto=str(rshort or ""), abreviatura=str(rabbr or "").upper())
    if t.abreviatura:
        por_abbr[t.abreviatura] = t
    if t.nombre:
        por_nombre[normalize_nombre(t.nombre)] = t
    if t.nombre_corto:
        por_nombre[normalize_nombre(t.nombre_corto)] = t
    return t


def asegurar_temporadas(conexion, seasons: List[int]) -> Dict[int, str]:
    """
    Asegura temporadas en tabla temporadas.
    seasons: lista de anio_fin (ej 2026 => temporada 2025-2026)
    Retorna dict {anio_fin: temporada_id}
    """
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
            fecha_fin = f"{anio_fin}-06-30"
            activa = True if anio_fin == max_temp else False

            cur.execute(
                """
                INSERT INTO temporadas_baloncesto (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (nombre, anio_inicio, anio_fin, fecha_inicio, fecha_fin, activa),
            )
            out[anio_fin] = str(cur.fetchone()[0])

    conexion.commit()
    return out


def parse_summary_to_partido(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte un summary ESPN a un dict con:
    - fecha_partido (date)
    - home/away nombres y abreviaturas
    - q1..q4, ot_sum, totales
    """
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

    home = None
    away = None
    for c in competitors:
        ha = str(c.get("homeAway", "")).lower()
        if ha == "home":
            home = c
        elif ha == "away":
            away = c
    if home is None or away is None:
        # fallback por orden, si ESPN cambia
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

    # Normalizar longitudes
    L = max(len(home_ls), len(away_ls))
    while len(home_ls) < L:
        home_ls.append(0)
    while len(away_ls) < L:
        away_ls.append(0)

    while len(home_ls) < 4:
        home_ls.append(0)
    while len(away_ls) < 4:
        away_ls.append(0)

    home_q1, home_q2, home_q3, home_q4 = home_ls[0], home_ls[1], home_ls[2], home_ls[3]
    away_q1, away_q2, away_q3, away_q4 = away_ls[0], away_ls[1], away_ls[2], away_ls[3]

    home_ot = sum(home_ls[4:]) if len(home_ls) > 4 else 0
    away_ot = sum(away_ls[4:]) if len(away_ls) > 4 else 0

    # Totales
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
) -> Tuple[bool, str]:
    """UPSERT idempotente en tabla partidos. Retorna (insertado, partido_id)."""
    with conexion.cursor() as cur:
        cur.execute(
            """
            INSERT INTO partidos_baloncesto (
                temporada_id, fecha_partido, tipo_partido, espn_game_id,
                equipo_local_id, equipo_visitante_id,
                local_q1, local_q2, local_q3, local_q4, local_ot, local_total,
                visitante_q1, visitante_q2, visitante_q3, visitante_q4, visitante_ot, visitante_total,
                ganador_id, hubo_overtime
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (temporada_id, fecha_partido, tipo_partido, equipo_local_id, equipo_visitante_id)
            DO UPDATE SET
                espn_game_id = COALESCE(EXCLUDED.espn_game_id, partidos_baloncesto.espn_game_id),
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
                hubo_overtime = EXCLUDED.hubo_overtime
            RETURNING id, (xmax = 0) AS inserted
            """,
            (
                temporada_id,
                fecha_partido,
                tipo_partido,
                espn_game_id,
                equipo_local_id,
                equipo_visitante_id,
                int(local_q[0]), int(local_q[1]), int(local_q[2]), int(local_q[3]),
                int(local_ot), int(local_total),
                int(visitante_q[0]), int(visitante_q[1]), int(visitante_q[2]), int(visitante_q[3]),
                int(visitante_ot), int(visitante_total),
                ganador_id,
                bool(hubo_overtime),
            ),
        )
        partido_id, inserted = cur.fetchone()
        return bool(inserted), str(partido_id)


def exportar(partidos: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = out_path.suffix.lower()

    if ext == ".jsonl":
        with out_path.open("w", encoding="utf-8") as f:
            for row in partidos:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return

    # default CSV
    headers = [
        "fecha_partido",
        "tipo_partido",
        "equipo_local",
        "equipo_visitante",
        "local_total",
        "visitante_total",
        "hubo_overtime",
        "espn_game_id",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in partidos:
            w.writerow({k: r.get(k) for k in headers})


def imprimir_resumen(partidos: List[Dict[str, Any]], equipo_nombre: str = "") -> None:
    if not partidos:
        titulo = f"⚠️  No hay partidos en el rango{' para ' + equipo_nombre if equipo_nombre else ''}."
        print(titulo)
        return

    print()
    titulo = f"📌 Partidos encontrados{' para ' + equipo_nombre if equipo_nombre else ''} (más recientes primero):"
    print(titulo)
    print("-" * 90)
    for r in partidos:
        fecha = r.get("fecha_partido")
        tp = r.get("tipo_partido")
        el = r.get("equipo_local")
        ev = r.get("equipo_visitante")
        lt = r.get("local_total")
        vt = r.get("visitante_total")
        ot = "OT" if r.get("hubo_overtime") else ""
        print(f"{fecha}  [{tp}]  {el} {lt} - {vt} {ev}  {ot}".rstrip())
    print("-" * 90)
    print(f"Total: {len(partidos)}")


def consultar_partidos_bd(conexion, equipo_id: str, fecha_min: date, limite: int = 200) -> List[Dict[str, Any]]:
    with conexion.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.fecha_partido,
                p.tipo_partido,
                el.nombre_corto AS equipo_local,
                ev.nombre_corto AS equipo_visitante,
                p.local_total,
                p.visitante_total,
                p.hubo_overtime,
                p.espn_game_id
            FROM partidos_baloncesto p
            JOIN equipos el ON el.id = p.equipo_local_id
            JOIN equipos ev ON ev.id = p.equipo_visitante_id
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


def resolver_equipo_bd(conexion, team_query: str) -> DbTeam:
    q = str(team_query or "").strip()
    if not q:
        raise SystemExit("❌ --team es requerido")

    ab = q.upper()
    with conexion.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, nombre_corto, abreviatura FROM equipos WHERE UPPER(abreviatura) = %s LIMIT 1",
            (ab,),
        )
        row = cur.fetchone()
        if row:
            return DbTeam(id=str(row[0]), nombre=str(row[1] or ""), nombre_corto=str(row[2] or ""), abreviatura=str(row[3] or "").upper())

        like = f"%{q}%"
        cur.execute(
            """
            SELECT id, nombre, nombre_corto, abreviatura
            FROM equipos
            WHERE nombre ILIKE %s OR nombre_corto ILIKE %s
            ORDER BY LENGTH(nombre) ASC
            LIMIT 1
            """,
            (like, like),
        )
        row = cur.fetchone()
        if row:
            return DbTeam(id=str(row[0]), nombre=str(row[1] or ""), nombre_corto=str(row[2] or ""), abreviatura=str(row[3] or "").upper())

    raise SystemExit(f"❌ No encontré el equipo en BD para: {q}")


def sincronizar_equipo(
    conexion,
    session: requests.Session,
    equipo_bd: DbTeam,
    fecha_min: date,
    hoy: date,
    seasons: List[int],
    seasontypes: List[int],
    temporada_por_anio_fin: Dict[int, str],
    por_abbr: Dict[str, DbTeam],
    por_nombre: Dict[str, DbTeam],
) -> Dict[str, int]:
    """
    Sincroniza un equipo y retorna estadísticas.
    Retorna: {"procesados": int, "insertados": int, "actualizados": int, "omitidos": int, "errores": int}
    
    CORRECCIÓN: Intenta primero con abreviatura, luego con nombre completo si falla.
    """
    stats = {"procesados": 0, "insertados": 0, "actualizados": 0, "omitidos": 0, "errores": 0}

    try:
        # 🔧 CORRECCIÓN: Intentar primero con abreviatura, luego con nombre completo
        team_query = equipo_bd.abreviatura or equipo_bd.nombre
        try:
            team_info = resolve_team(session, team_query)
        except Exception:
            # Si falla con abreviatura, intentar con nombre completo
            team_info = resolve_team(session, equipo_bd.nombre)
        
        team_id = str(team_info.id)
    except Exception as e:
        print(f"⚠️  No pude resolver equipo {equipo_bd.nombre} en ESPN: {e}")
        stats["errores"] += 1
        return stats

    for season in seasons:
        temporada_id = temporada_por_anio_fin.get(int(season)) or ""
        if not temporada_id:
            temporada_id = asegurar_temporadas(conexion, [int(season)]).get(int(season), "")

        for st in seasontypes:
            tipo_partido = seasontype_to_tipo(st)

            try:
                events = fetch_schedule_events(session, team_id, season, st)
            except Exception as e:
                stats["errores"] += 1
                continue

            for ev in events:
                try:
                    if not is_completed_event(ev):
                        continue
                    event_id = get_event_id(ev)
                    if not event_id:
                        continue

                    # Filtrar por fecha de evento
                    comps = ev.get("competitions", []) or []
                    ev_date_str = (comps[0].get("date") if comps else "") or ""
                    fecha_ev = parse_fecha_calendario_espn_iso(ev_date_str)
                    if fecha_ev < fecha_min or fecha_ev > hoy:
                        stats["omitidos"] += 1
                        continue

                    summary = fetch_summary(session, event_id)
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
                        visitante_ot=int(parsed["away_ot"]),
                        local_total=local_total,
                        visitante_total=visit_total,
                        ganador_id=ganador_id,
                        hubo_overtime=bool(parsed["hubo_overtime"]),
                    )

                    stats["procesados"] += 1
                    if ins:
                        stats["insertados"] += 1
                    else:
                        stats["actualizados"] += 1

                except Exception as e:
                    stats["errores"] += 1
                    try:
                        conexion.rollback()
                    except Exception:
                        pass
                    if stats["errores"] <= 3:  # Limitar mensajes de error por equipo
                        print(f"⚠️  Error en evento {equipo_bd.abreviatura}: {e}")

    return stats


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sincroniza y lista partidos de los últimos N días para 1 equipo o TODOS.")
    
    # Grupo mutuamente exclusivo: --team o --all-teams
    team_group = p.add_mutually_exclusive_group(required=True)
    team_group.add_argument("--team", type=str, help='Nombre o abreviatura. Ej: "Los Angeles Lakers" o "LAL"')
    team_group.add_argument("--all-teams", action="store_true", help="Sincroniza TODOS los equipos activos")
    
    p.add_argument("--days", type=int, default=10, help="Cantidad de días hacia atrás (default: 10)")
    p.add_argument("--no-sync", action="store_true", help="No llama a ESPN; solo consulta BD")
    p.add_argument("--out", type=str, default="", help="Ruta para exportar (.csv o .jsonl)")
    p.add_argument("--include-preseason", action="store_true", help="Incluye pretemporada (seasontype=1)")
    p.add_argument("--include-playoffs", action="store_true", help="Incluye playoffs (seasontype=3)")
    p.add_argument("--seasons", type=int, nargs="*", default=[], help="Años anio_fin a consultar en ESPN (ej: 2025 2026)")
    p.add_argument("--limit", type=int, default=200, help="Límite de resultados impresos/exportados (default: 200)")
    return p.parse_args()


def main() -> int:
    load_dotenv()

    db_url = obtener_database_url()
    if not db_url:
        print("❌ Falta DATABASE_URL en el entorno (.env).")
        return 1

    try:
        import psycopg
    except Exception:
        print("❌ Falta psycopg. Instala con: pip install psycopg[binary]")
        return 1

    args = parse_args()
    hoy = date.today()
    dias = max(1, int(args.days))
    fecha_min = hoy - timedelta(days=dias)

    with psycopg.connect(db_url) as conexion:
        # Determinar qué equipos sincronizar
        if args.all_teams:
            equipos_a_sincronizar = obtener_todos_equipos_bd(conexion)
            print(f"🔄 Sincronizando TODOS los equipos ({len(equipos_a_sincronizar)} equipos activos)")
            print(f"   Rango de fechas: {fecha_min} a {hoy} ({dias} días)")
            print()
        else:
            equipo_bd = resolver_equipo_bd(conexion, args.team)
            equipos_a_sincronizar = [equipo_bd]
            print(f"🔄 Sincronizando: {equipo_bd.nombre} ({equipo_bd.abreviatura})")
            print(f"   Rango de fechas: {fecha_min} a {hoy} ({dias} días)")
            print()

        # Sincronización (opcional)
        stats_globales = {
            "equipos_procesados": 0,
            "equipos_con_errores": 0,
            "total_procesados": 0,
            "total_insertados": 0,
            "total_actualizados": 0,
            "total_omitidos": 0,
            "total_errores": 0,
        }

        if not args.no_sync:
            # Preparar temporadas y seasontypes
            if args.seasons:
                seasons = [int(s) for s in args.seasons]
            else:
                seasons = sorted({hoy.year, hoy.year - 1})  # cubre cambio de año

            temporada_por_anio_fin = asegurar_temporadas(conexion, seasons)
            por_abbr, por_nombre = cargar_equipos_bd(conexion)

            seasontypes = [2]  # regular
            if args.include_preseason:
                seasontypes.insert(0, 1)
            if args.include_playoffs:
                seasontypes.append(3)

            session = requests.Session()

            # Sincronizar cada equipo
            for idx, equipo in enumerate(equipos_a_sincronizar, 1):
                if args.all_teams:
                    print(f"[{idx}/{len(equipos_a_sincronizar)}] Sincronizando {equipo.nombre} ({equipo.abreviatura})...", end=" ", flush=True)
                
                stats = sincronizar_equipo(
                    conexion=conexion,
                    session=session,
                    equipo_bd=equipo,
                    fecha_min=fecha_min,
                    hoy=hoy,
                    seasons=seasons,
                    seasontypes=seasontypes,
                    temporada_por_anio_fin=temporada_por_anio_fin,
                    por_abbr=por_abbr,
                    por_nombre=por_nombre,
                )

                # Actualizar estadísticas globales
                stats_globales["equipos_procesados"] += 1
                if stats["errores"] > 0:
                    stats_globales["equipos_con_errores"] += 1
                stats_globales["total_procesados"] += stats["procesados"]
                stats_globales["total_insertados"] += stats["insertados"]
                stats_globales["total_actualizados"] += stats["actualizados"]
                stats_globales["total_omitidos"] += stats["omitidos"]
                stats_globales["total_errores"] += stats["errores"]

                if args.all_teams:
                    print(f"✓ ({stats['insertados']} nuevos, {stats['actualizados']} actualizados)")
                else:
                    print(f"   Procesados:  {stats['procesados']}")
                    print(f"   Nuevos:      {stats['insertados']}")
                    print(f"   Actualizados:{stats['actualizados']}")
                    print(f"   Omitidos (fuera de rango): {stats['omitidos']}")
                    print(f"   Errores:     {stats['errores']}")

            conexion.commit()

            print()
            print("=" * 90)
            print("✅ Sincronización completada")
            if args.all_teams:
                print(f"   Equipos sincronizados:     {stats_globales['equipos_procesados']}")
                print(f"   Equipos con errores:       {stats_globales['equipos_con_errores']}")
            print(f"   Total partidos procesados: {stats_globales['total_procesados']}")
            print(f"   Total nuevos:              {stats_globales['total_insertados']}")
            print(f"   Total actualizados:        {stats_globales['total_actualizados']}")
            print(f"   Total omitidos:            {stats_globales['total_omitidos']}")
            print(f"   Total errores:             {stats_globales['total_errores']}")
            print("=" * 90)

        # Consulta final a BD y mostrar resultados
        if args.all_teams:
            # Para --all-teams, mostrar resumen general sin detalles de cada partido
            print()
            print("📊 Resumen de partidos en BD (últimos días):")
            with conexion.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM partidos_baloncesto p
                    WHERE p.fecha_partido >= %s
                    """,
                    (fecha_min,)
                )
                total = cur.fetchone()[0]
                print(f"   Total de partidos en rango: {total}")
            
            if args.out:
                # Exportar todos los partidos del rango
                print()
                print("📦 Exportando todos los partidos del rango...")
                with conexion.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            p.fecha_partido,
                            p.tipo_partido,
                            el.nombre_corto AS equipo_local,
                            ev.nombre_corto AS equipo_visitante,
                            p.local_total,
                            p.visitante_total,
                            p.hubo_overtime,
                            p.espn_game_id
                        FROM partidos_baloncesto p
                        JOIN equipos el ON el.id = p.equipo_local_id
                        JOIN equipos ev ON ev.id = p.equipo_visitante_id
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
                
                out_path = Path(args.out)
                exportar(partidos_export, out_path)
                print(f"📦 Exportado: {out_path.resolve()} ({len(partidos_export)} partidos)")
        else:
            # Para un solo equipo, mostrar detalle
            equipo_bd = equipos_a_sincronizar[0]
            partidos = consultar_partidos_bd(conexion, equipo_bd.id, fecha_min, limite=int(args.limit))
            imprimir_resumen(partidos, equipo_bd.nombre)

            if args.out:
                out_path = Path(args.out)
                exportar(partidos, out_path)
                print(f"📦 Exportado: {out_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NBAscript.py — ESPN NBA -> CSV con puntos por cuarto (Q1-Q4 + OT)

Qué hace:
- Tú pones el nombre del equipo (ej: "Orlando Magic" o "NYK")
- Descarga partidos terminados de temporadas que indiques
- Incluye pretemporada, regular y playoffs (configurable)
- Extrae Q1-Q4 (+ OT) y totales
- Valida que suma de cuartos = total
- Exporta un CSV con columnas simples para análisis/modelado

Requisitos:
    pip install requests python-dateutil

Ejemplos:
    python NBAscript.py --team "Orlando Magic" --seasons 2024 2025 --out orlando.csv
    python NBAscript.py --team "New York Knicks" --seasons 2024 2025 --out knicks.csv
    python NBAscript.py --team "NYK" --seasons 2024 2025 --include-preseason --out knicks_pre.csv
"""

import argparse
import csv
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from dateutil import parser as dtparser


ESPN_SITE_API = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_SITE_WEB_API = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NBAscript/2.0",
    "Accept": "application/json,text/plain,*/*",
}

# ESPN:
# 1 = Preseason, 2 = Regular Season, 3 = Postseason (Playoffs)
SEASONTYPE_LABEL = {1: "PRE", 2: "REG", 3: "POST"}


@dataclass
class TeamInfo:
    id: str
    display_name: str
    abbreviation: str


# -------------------------
# Helpers HTTP
# -------------------------
def request_json(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 7,
    backoff_base: float = 0.7,
) -> Dict[str, Any]:
    """GET JSON con reintentos/backoff (maneja 429/5xx)."""
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=30)
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff_base * (2 ** attempt))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            time.sleep(backoff_base * (2 ** attempt))
    raise RuntimeError(f"Fallo consultando {url} params={params}. Último error: {last_err}")


def normalize(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# -------------------------
# Resolución de equipo
# -------------------------
def get_all_teams(session: requests.Session) -> List[TeamInfo]:
    url = f"{ESPN_SITE_API}/teams"
    data = request_json(session, url)

    teams: List[TeamInfo] = []

    # Estructura típica: sports -> leagues -> teams -> team
    for sport in data.get("sports", []):
        for league in sport.get("leagues", []):
            for t in league.get("teams", []):
                team = t.get("team", {}) or {}
                tid = str(team.get("id", "")).strip()
                dn = str(team.get("displayName", "")).strip()
                ab = str(team.get("abbreviation", "")).strip()
                if tid and dn:
                    teams.append(TeamInfo(id=tid, display_name=dn, abbreviation=ab))

    # Fallback si la estructura cambia
    if not teams:
        for t in data.get("teams", []):
            team = t.get("team", {}) or {}
            tid = str(team.get("id", "")).strip()
            dn = str(team.get("displayName", "")).strip()
            ab = str(team.get("abbreviation", "")).strip()
            if tid and dn:
                teams.append(TeamInfo(id=tid, display_name=dn, abbreviation=ab))

    if not teams:
        raise RuntimeError("No pude leer la lista de equipos desde ESPN.")
    return teams


def resolve_team(session: requests.Session, team_query: str) -> TeamInfo:
    q = normalize(team_query)
    teams = get_all_teams(session)

    # 1) match exact abbreviation
    for t in teams:
        if normalize(t.abbreviation) == q and t.abbreviation:
            return t

    # 2) match exact display name
    for t in teams:
        if normalize(t.display_name) == q:
            return t

    # 3) contains
    contains = [t for t in teams if q and q in normalize(t.display_name)]
    if len(contains) == 1:
        return contains[0]

    # 4) token overlap scoring
    q_tokens = set(q.split())
    scored: List[Tuple[int, TeamInfo]] = []
    for t in teams:
        tokens = set(normalize(t.display_name).split())
        score = len(q_tokens & tokens)
        if score > 0:
            scored.append((score, t))
    scored.sort(key=lambda x: x[0], reverse=True)

    if scored:
        top_score = scored[0][0]
        top = [t for s, t in scored if s == top_score]
        if len(top) == 1:
            return top[0]
        opts = ", ".join([f"{x.display_name}({x.abbreviation})" for x in top[:10]])
        raise RuntimeError(f"Ambiguo: '{team_query}'. Opciones: {opts}")

    raise RuntimeError(f"No encontré el equipo '{team_query}'. Prueba con nombre completo (ej: 'Orlando Magic') o abreviación (ej: 'ORL').")


# -------------------------
# Schedule y eventos
# -------------------------
def fetch_schedule_events(session: requests.Session, team_id: str, season: int, seasontype: int) -> List[Dict[str, Any]]:
    """
    ESPN schedule:
    /teams/{team_id}/schedule?season=YYYY&seasontype=1|2|3
    """
    url = f"{ESPN_SITE_API}/teams/{team_id}/schedule"
    params = {"season": season, "seasontype": seasontype}
    data = request_json(session, url, params=params)
    events = data.get("events", []) or []

    # Fallback: a veces ESPN indexa distinto (probar season-1)
    if not events and season > 1900:
        params2 = {"season": season - 1, "seasontype": seasontype}
        data2 = request_json(session, url, params=params2)
        events = data2.get("events", []) or []

    return events


def is_completed_event(ev: Dict[str, Any]) -> bool:
    comps = ev.get("competitions", []) or []
    if not comps:
        return False
    st = comps[0].get("status", {}).get("type", {}) or {}
    if st.get("completed") is True:
        return True
    # fallback
    name = str(st.get("name", "")).upper()
    state = str(st.get("state", "")).upper()
    return ("STATUS_FINAL" in name) or ("POST" in state)


def get_event_id(ev: Dict[str, Any]) -> Optional[str]:
    if ev.get("id"):
        return str(ev["id"])
    comps = ev.get("competitions", []) or []
    if comps and comps[0].get("id"):
        return str(comps[0]["id"])
    return None


# -------------------------
# Summary -> parsing cuartos
# -------------------------
def fetch_summary(session: requests.Session, event_id: str) -> Dict[str, Any]:
    # Summary endpoint (JSON)
    url = f"{ESPN_SITE_WEB_API}/summary"
    return request_json(session, url, params={"event": event_id})


def _safe_int_from_any(x: Any) -> int:
    if x is None:
        return 0
    if isinstance(x, (int, float)):
        return int(x)
    s = str(x)
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else 0


def extract_linescores(competitor: Dict[str, Any]) -> List[int]:
    """
    ESPN puede enviar linescores así:
      [{"value": 30}, {"value": 28}, ...]
    o así:
      [{"displayValue": "30"}, ...]
    """
    ls = competitor.get("linescores") or []
    out: List[int] = []
    for p in ls:
        if not isinstance(p, dict):
            out.append(0)
            continue

        if "value" in p and p.get("value") is not None:
            out.append(_safe_int_from_any(p.get("value")))
            continue

        if "displayValue" in p and p.get("displayValue") is not None:
            out.append(_safe_int_from_any(p.get("displayValue")))
            continue

        # fallback: algunos payloads usan "display" u otro campo
        out.append(_safe_int_from_any(p.get("display") if isinstance(p, dict) else 0))

    return out


def parse_game_record(summary: Dict[str, Any], target_team_name: str) -> Dict[str, Any]:
    """
    Devuelve un record en formato "TEAM vs OPP" y Q1-Q4 (+OT).
    """
    header = summary.get("header", {}) or {}
    competitions = summary.get("competitions", []) or header.get("competitions", []) or []
    if not competitions:
        raise RuntimeError("Summary sin competitions.")

    comp = competitions[0]
    competitors = comp.get("competitors", []) or []
    if len(competitors) < 2:
        raise RuntimeError("No hay 2 equipos en competitors.")

    # date
    date_str = comp.get("date") or header.get("date") or ""
    try:
        dt = dtparser.isoparse(date_str)
        date_iso = dt.isoformat()
    except Exception:
        date_iso = date_str

    def team_display_name(c: Dict[str, Any]) -> str:
        t = c.get("team", {}) or {}
        return t.get("displayName") or t.get("shortDisplayName") or ""

    def team_abbr(c: Dict[str, Any]) -> str:
        t = c.get("team", {}) or {}
        return t.get("abbreviation") or ""

    home = next((c for c in competitors if c.get("homeAway") == "home"), None) or competitors[0]
    away = next((c for c in competitors if c.get("homeAway") == "away"), None) or competitors[1]

    home_name = team_display_name(home)
    away_name = team_display_name(away)
    home_abbr = team_abbr(home)
    away_abbr = team_abbr(away)

    home_total = _safe_int_from_any(home.get("score"))
    away_total = _safe_int_from_any(away.get("score"))

    home_ls = extract_linescores(home)
    away_ls = extract_linescores(away)

    # Asegurar mismo largo
    L = max(len(home_ls), len(away_ls))
    while len(home_ls) < L:
        home_ls.append(0)
    while len(away_ls) < L:
        away_ls.append(0)

    # Asegurar al menos 4 cuartos
    while len(home_ls) < 4:
        home_ls.append(0)
    while len(away_ls) < 4:
        away_ls.append(0)

    # OT count (periodos extra)
    ot_count = max(0, len(home_ls) - 4)

    # Validación de linescore
    sum_home = sum(home_ls)
    sum_away = sum(away_ls)
    valid_linescore = (sum_home == home_total) and (sum_away == away_total)

    # Link ESPN (si existe)
    game_link = ""
    for lk in header.get("links", []) or []:
        if isinstance(lk, dict) and lk.get("href"):
            game_link = lk["href"]
            break

    # Convertir a formato TEAM vs OPP centrado en el equipo solicitado
    tgt_norm = normalize(target_team_name)
    is_target_home = normalize(home_name) == tgt_norm or normalize(home_abbr) == tgt_norm
    is_target_away = normalize(away_name) == tgt_norm or normalize(away_abbr) == tgt_norm

    if not is_target_home and not is_target_away:
        # A veces target_team_name viene en displayName; si no, dejamos raw pero marcamos
        pass

    if is_target_home:
        team_loc = "HOME"
        team_name = home_name
        opp_name = away_name
        team_total = home_total
        opp_total = away_total
        team_q = home_ls
        opp_q = away_ls
    else:
        team_loc = "AWAY"
        team_name = away_name
        opp_name = home_name
        team_total = away_total
        opp_total = home_total
        team_q = away_ls
        opp_q = home_ls

    # ganador del partido (TEAM/OPP/TIE)
    if team_total > opp_total:
        game_winner = "TEAM"
    elif team_total < opp_total:
        game_winner = "OPP"
    else:
        game_winner = "TIE"

    rec: Dict[str, Any] = {
        "date": date_iso,
        "season": "",          # se llena afuera
        "season_type": "",     # PRE/REG/POST se llena afuera
        "team": team_name,
        "opponent": opp_name,
        "location": team_loc,  # HOME/AWAY
        "team_total": team_total,
        "opp_total": opp_total,
        "team_q1": team_q[0],
        "opp_q1": opp_q[0],
        "team_q2": team_q[1],
        "opp_q2": opp_q[1],
        "team_q3": team_q[2],
        "opp_q3": opp_q[2],
        "team_q4": team_q[3],
        "opp_q4": opp_q[3],
        "ot_count": ot_count,
        "valid_linescore": valid_linescore,
        "winner": game_winner,
        "espn_url": game_link,
    }

    # OT columns (si hay)
    for i in range(ot_count):
        idx = 4 + i
        rec[f"team_ot{i+1}"] = team_q[idx] if idx < len(team_q) else 0
        rec[f"opp_ot{i+1}"] = opp_q[idx] if idx < len(opp_q) else 0

    return rec


# -------------------------
# Dataset builder
# -------------------------
def build_dataset(
    team_query: str,
    seasons: List[int],
    include_preseason: bool,
    include_regular: bool,
    include_postseason: bool,
    max_games: int,
    sleep_s: float,
) -> List[Dict[str, Any]]:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    team = resolve_team(session, team_query)
    print(f"[OK] Equipo: {team.display_name} ({team.abbreviation}) id={team.id}")

    season_types: List[int] = []
    if include_preseason:
        season_types.append(1)
    if include_regular:
        season_types.append(2)
    if include_postseason:
        season_types.append(3)

    if not season_types:
        raise RuntimeError("Debes incluir al menos un tipo de temporada (preseason/regular/postseason).")

    # Recolectar eventos (deduplicar)
    events: List[Tuple[str, int, int, str]] = []  # (event_id, season, seasontype, date)
    for s in seasons:
        for st in season_types:
            evs = fetch_schedule_events(session, team.id, s, st)
            for ev in evs:
                if not is_completed_event(ev):
                    continue
                eid = get_event_id(ev)
                if not eid:
                    continue
                d = ev.get("date", "") or ""
                events.append((eid, s, st, d))

    if not events:
        raise RuntimeError("No se encontraron juegos finalizados. Prueba con otras seasons o agregando más años.")

    # Dedup por event_id
    seen = set()
    uniq: List[Tuple[str, int, int, str]] = []
    for eid, s, st, d in events:
        if eid in seen:
            continue
        seen.add(eid)
        uniq.append((eid, s, st, d))

    # Ordenar por fecha desc (newest first)
    def sk(x: Tuple[str, int, int, str]) -> datetime:
        try:
            return dtparser.isoparse(x[3])
        except Exception:
            return datetime.min

    uniq.sort(key=sk, reverse=True)

    rows: List[Dict[str, Any]] = []
    for i, (eid, s, st, _) in enumerate(uniq[:max_games]):
        try:
            summary = fetch_summary(session, eid)
            rec = parse_game_record(summary, team.display_name)
            rec["season"] = str(s)
            rec["season_type"] = SEASONTYPE_LABEL.get(st, str(st))
            rows.append(rec)
        except Exception as e:
            print(f"[WARN] No pude procesar event={eid}: {e}", file=sys.stderr)
        time.sleep(sleep_s)

    return rows


def write_csv(out_path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError("No hay filas para exportar.")

    # construir columnas base + OT dinámico
    base_cols = [
        "date", "season", "season_type",
        "team", "opponent", "location",
        "team_total", "opp_total",
        "team_q1", "opp_q1",
        "team_q2", "opp_q2",
        "team_q3", "opp_q3",
        "team_q4", "opp_q4",
        "ot_count",
        "winner",
        "valid_linescore",
        "espn_url",
    ]

    # detectar OT columns
    keys = set()
    for r in rows:
        keys |= set(r.keys())
    ot_cols = sorted(
        [k for k in keys if re.match(r"^(team|opp)_ot\d+$", k)],
        key=lambda x: (0 if x.startswith("team_") else 1, int(re.findall(r"\d+", x)[0])),
    )

    fieldnames = base_cols + ot_cols

    # por si aparece algo extra inesperado, añadir al final
    extras = sorted([k for k in keys if k not in fieldnames])
    fieldnames += extras

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    total = len(rows)
    valid = sum(1 for r in rows if str(r.get("valid_linescore")).lower() == "true" or r.get("valid_linescore") is True)
    print(f"[OK] CSV guardado: {out_path}")
    print(f"[INFO] Filas: {total} | valid_linescore=True: {valid} | inválidas: {total - valid}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ESPN NBA -> CSV con Q1-Q4 (+OT) para un equipo.")
    p.add_argument("--team", required=True, help='Equipo: "Orlando Magic" o "NYK" o "ORL".')
    p.add_argument("--seasons", nargs="+", type=int, required=True, help="Ej: 2024 2025")
    p.add_argument("--include-preseason", action="store_true", default=False, help="Incluye PRE (seasontype=1)")
    p.add_argument("--include-regular", action="store_true", default=True, help="Incluye REG (seasontype=2)")
    p.add_argument("--include-postseason", action="store_true", default=True, help="Incluye POST (seasontype=3)")
    p.add_argument("--max-games", type=int, default=140, help="Máximo de juegos a descargar.")
    p.add_argument("--sleep", type=float, default=0.20, help="Pausa entre requests (seg).")
    p.add_argument("--out", default="nba_team_quarters.csv", help="Salida CSV.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_dataset(
        team_query=args.team,
        seasons=args.seasons,
        include_preseason=args.include_preseason,
        include_regular=args.include_regular,
        include_postseason=args.include_postseason,
        max_games=args.max_games,
        sleep_s=args.sleep,
    )
    write_csv(args.out, rows)


if __name__ == "__main__":
    main()

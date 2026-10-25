"""Contrato ESPN WNBA estricto. No completa marcadores mediante suposiciones."""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

VERSION_CONTRATO = "espn_wnba_v1"
LIMITE = 500
BOGOTA = ZoneInfo("America/Bogota")
FASES = {1: "PRE", 2: "REG", 3: "POST"}
ESTADOS = {
    "STATUS_SCHEDULED": ("pre", False, "PROGRAMADO"),
    "STATUS_IN_PROGRESS": ("in", False, "EN_VIVO"),
    "STATUS_HALFTIME": ("in", False, "EN_VIVO"),
    "STATUS_END_PERIOD": ("in", False, "EN_VIVO"),
    "STATUS_FINAL": ("post", True, "FINALIZADO"),
    "STATUS_FINAL_OVERTIME": ("post", True, "FINALIZADO"),
    "STATUS_POSTPONED": ("pre", False, "POSPUESTO"),
    "STATUS_CANCELED": ("pre", False, "CANCELADO"),
    "STATUS_DELAYED": ("pre", False, "DEMORADO"),
    "STATUS_SUSPENDED": ("in", False, "SUSPENDIDO"),
}


class ContratoError(ValueError):
    def __init__(self, codigo: str, campo: str):
        self.codigo, self.campo = codigo, campo
        super().__init__(f"{codigo}: {campo}")


def exigir(condicion: bool, codigo: str, campo: str) -> None:
    if not condicion:
        raise ContratoError(codigo, campo)


def objeto(value: Any, campo: str) -> dict:
    exigir(isinstance(value, dict), "OBJETO_INVALIDO", campo)
    return value


def entero(value: Any, campo: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ContratoError("ENTERO_AUSENTE_O_INVALIDO", campo)
    if isinstance(value, int):
        n = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        n = int(value)
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        n = int(value)
    else:
        raise ContratoError("ENTERO_AUSENTE_O_INVALIDO", campo)
    exigir(n >= 0, "ENTERO_NEGATIVO", campo)
    return n


def identificador(value: Any, campo: str) -> str:
    exigir(isinstance(value, (str, int)) and not isinstance(value, bool), "ID_INVALIDO", campo)
    value = str(value)
    exigir(bool(re.fullmatch(r"[0-9]{1,20}", value)), "ID_INVALIDO", campo)
    return value


def instante(value: Any) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ContratoError("FECHA_INVALIDA", "date") from exc
    exigir(dt.tzinfo is not None, "FECHA_SIN_ZONA", "date")
    return dt.astimezone(timezone.utc)


def liga(value: Any) -> None:
    value = objeto(value, "league")
    exigir(value.get("slug") == "wnba" and str(value.get("id")) == "59", "OTRA_LIGA", "league")


def eventos_scoreboard(payload: dict) -> list[dict]:
    objeto(payload, "scoreboard")
    ligas = payload.get("leagues")
    exigir(isinstance(ligas, list) and len(ligas) == 1, "LIGA_AMBIGUA", "leagues")
    liga(ligas[0])
    eventos = payload.get("events")
    exigir(isinstance(eventos, list), "EVENTOS_AUSENTES", "events")
    exigir(len(eventos) < LIMITE, "POSIBLE_TRUNCAMIENTO", "events")
    # No inventar paginación cuando el proveedor anuncia más filas de las recibidas.
    for key in ("count", "totalCount"):
        if key in payload:
            exigir(entero(payload[key], key) == len(eventos), "POSIBLE_TRUNCAMIENTO", key)
    return eventos


def competicion(evento: dict) -> dict:
    comps = evento.get("competitions")
    exigir(isinstance(comps, list) and len(comps) == 1, "COMPETICION_AMBIGUA", "competitions")
    comp = objeto(comps[0], "competition")
    exigir(identificador(comp.get("id"), "competition.id") == identificador(evento.get("id"), "event.id"),
           "ID_DISCORDANTE", "competition.id")
    return comp


def lados(comp: dict) -> dict[str, dict]:
    competitors = comp.get("competitors")
    exigir(isinstance(competitors, list) and len(competitors) == 2, "LADOS_INCOMPLETOS", "competitors")
    for item in competitors:
        objeto(item, "competitor")
        exigir(isinstance(item.get("homeAway"), str), "LOCALIA_AMBIGUA", "homeAway")
    por_lado = {c.get("homeAway"): c for c in competitors}
    exigir(set(por_lado) == {"home", "away"}, "LOCALIA_AMBIGUA", "homeAway")
    ids = []
    for side, item in por_lado.items():
        team = objeto(item.get("team"), "team")
        tid = identificador(team.get("id"), "team.id")
        exigir(isinstance(team.get("displayName"), str) and bool(team["displayName"].strip()),
               "EQUIPO_SIN_NOMBRE", side)
        if "id" in item:
            exigir(str(item["id"]) == tid, "ID_DISCORDANTE", "competitor.id")
        for obj in (item, team):
            if "uid" in obj:
                exigir(obj["uid"] == f"s:40~l:59~t:{tid}", "OTRA_LIGA", "team.uid")
        ids.append(tid)
    exigir(len(set(ids)) == 2, "EQUIPOS_IGUALES", "team.id")
    return por_lado


def estado(comp: dict, evento: dict) -> tuple[str, dict]:
    status = objeto(comp.get("status", evento.get("status")), "status")
    tipo = objeto(status.get("type"), "status.type")
    exigir(isinstance(tipo.get("name"), str), "ESTADO_DESCONOCIDO", "status.type.name")
    esperado = ESTADOS.get(tipo.get("name"))
    exigir(esperado is not None, "ESTADO_DESCONOCIDO", "status.type.name")
    exigir(tipo.get("state") == esperado[0] and tipo.get("completed") is esperado[1],
           "ESTADO_CONTRADICTORIO", "status.type")
    return esperado[2], status


def periodos(item: dict) -> list[int]:
    lista = item.get("linescores")
    exigir(isinstance(lista, list) and len(lista) >= 4, "PERIODOS_INCOMPLETOS", "linescores")
    exigir(len(lista) <= 20, "PERIODOS_EXCESIVOS", "linescores")
    for row in lista:
        objeto(row, "linescore")
    con_numero = ["period" in row for row in lista]
    exigir(all(con_numero) or not any(con_numero), "PERIODOS_AMBIGUOS", "period")
    if all(con_numero):
        numeros = [entero(r["period"], "period") for r in lista]
        exigir(sorted(numeros) == list(range(1, len(lista) + 1)), "PERIODOS_NO_CONSECUTIVOS", "period")
        lista = sorted(lista, key=lambda r: entero(r["period"], "period"))
    values = []
    for row in lista:
        presentes = [entero(row[key], key) for key in ("value", "displayValue") if row.get(key) is not None]
        exigir(bool(presentes), "PERIODO_SIN_PUNTOS", "linescores")
        exigir(len(set(presentes)) == 1, "PUNTOS_DISCORDANTES", "linescores")
        values.append(presentes[0])
    return values


def validar_summary(evento: dict, summary: dict) -> tuple[dict, dict[str, dict]]:
    h = objeto(summary.get("header"), "header")
    liga(h.get("league"))
    exigir(identificador(h.get("id"), "header.id") == identificador(evento.get("id"), "event.id")
           and h.get("uid") == evento.get("uid"), "SUMMARY_OTRO_EVENTO", "header")
    source_season, target_season = objeto(evento.get("season"), "season"), objeto(h.get("season"), "header.season")
    exigir(target_season.get("year") == source_season.get("year")
           and target_season.get("type") == source_season.get("type"),
           "SUMMARY_OTRA_TEMPORADA", "season")
    original, enriquecido = competicion(evento), competicion(h)
    exigir(instante(original.get("date", evento.get("date"))) == instante(enriquecido.get("date")),
           "SUMMARY_OTRA_FECHA", "date")
    exigir(estado(original, evento)[0] == estado(enriquecido, h)[0], "SUMMARY_OTRO_ESTADO", "status")
    iniciales, finales = lados(original), lados(enriquecido)
    for side in iniciales:
        exigir(str(iniciales[side]["team"]["id"]) == str(finales[side]["team"]["id"]), "SUMMARY_OTROS_EQUIPOS", side)
        if iniciales[side].get("score") is not None:
            exigir(entero(iniciales[side]["score"], "score") == entero(finales[side].get("score"), "score"),
                   "SUMMARY_OTRO_MARCADOR", side)
        # Lo publicado en el scoreboard no puede ser sobreescrito por el summary.
        publicados = iniciales[side].get("linescores", [])
        exigir(isinstance(publicados, list), "PERIODOS_INVALIDOS", "linescores")
        reemplazo = periodos(finales[side])
        indices = set()
        for index, row in enumerate(publicados, 1):
            objeto(row, "linescore")
            number = entero(row.get("period", index), "period")
            exigir(1 <= number <= len(reemplazo) and number not in indices, "PERIODOS_AMBIGUOS", "period")
            indices.add(number)
            for key in ("value", "displayValue"):
                if row.get(key) is not None:
                    exigir(entero(row[key], key) == reemplazo[number - 1], "SUMMARY_OTROS_PERIODOS", side)
    return enriquecido, finales


STAT_KEYS = {
    "rebotes": "totalRebounds", "rebotes_ofensivos": "offensiveRebounds",
    "rebotes_defensivos": "defensiveRebounds", "asistencias": "assists",
    "robos": "steals", "tapones": "blocks", "perdidas_jugadoras": "turnovers",
    "perdidas_equipo": "teamTurnovers", "perdidas_totales": "totalTurnovers", "faltas": "fouls",
}
SHOOT_KEYS = {"campo": "fieldGoalsMade-fieldGoalsAttempted",
              "triples": "threePointFieldGoalsMade-threePointFieldGoalsAttempted",
              "libres": "freeThrowsMade-freeThrowsAttempted"}


def estadisticas(summary: dict | None, teams: dict[str, dict], totals: dict) -> dict:
    result = {}
    source = {} if summary is None else objeto(summary.get("boxscore", {}), "boxscore")
    items = source.get("teams", [])
    exigir(isinstance(items, list), "ESTADISTICAS_INVALIDAS", "boxscore.teams")
    by_id = {}
    for item in items:
        objeto(item, "boxscore.team")
        tid = identificador(objeto(item.get("team"), "team").get("id"), "team.id")
        exigir(tid not in by_id, "ESTADISTICAS_DUPLICADAS", tid)
        rows = item.get("statistics", [])
        exigir(isinstance(rows, list), "ESTADISTICAS_INVALIDAS", "statistics")
        values = {}
        for row in rows:
            objeto(row, "statistic")
            key = row.get("name")
            exigir(isinstance(key, str) and key not in values, "ESTADISTICAS_DUPLICADAS", "name")
            values[key] = row.get("displayValue")
        by_id[tid] = values
    expected = {str(t["team"]["id"]) for t in teams.values()}
    exigir(set(by_id).issubset(expected), "ESTADISTICAS_OTROS_EQUIPOS", "boxscore")
    for side, team in teams.items():
        values = by_id.get(str(team["team"]["id"]), {})
        stats = {dest: None if values.get(key) in (None, "", "--", "N/A") else entero(values[key], key)
                 for dest, key in STAT_KEYS.items()}
        for dest, key in SHOOT_KEYS.items():
            raw = values.get(key)
            made = attempted = None
            if raw not in (None, "", "--", "N/A"):
                exigir(isinstance(raw, str) and bool(re.fullmatch(r"\d+-\d+", raw)), "TIROS_INVALIDOS", key)
                made, attempted = (int(n) for n in raw.split("-"))
                exigir(made <= attempted, "TIROS_INCONSISTENTES", key)
            stats[f"{dest}_anotados"], stats[f"{dest}_intentados"] = made, attempted
        fg, th, ft = (stats[f"{k}_anotados"] for k in ("campo", "triples", "libres"))
        if fg is not None and th is not None:
            exigir(th <= fg, "TIROS_INCONSISTENTES", "triples/campo")
        if all(v is not None for v in (fg, th, ft)):
            exigir(2 * fg + th + ft == totals[side], "TIROS_NO_CONCILIAN_MARCADOR", side)
        reb = [stats[k] for k in ("rebotes", "rebotes_ofensivos", "rebotes_defensivos")]
        if all(v is not None for v in reb):
            exigir(reb[0] == reb[1] + reb[2], "REBOTES_INCONSISTENTES", side)
        result[side] = stats
    return result


def normalizar(evento: dict, summary: dict | None = None) -> dict:
    objeto(evento, "event")
    eid = identificador(evento.get("id"), "event.id")
    exigir(evento.get("uid") == f"s:40~l:59~e:{eid}", "OTRA_LIGA", "event.uid")
    comp = competicion(evento)
    dt = instante(evento.get("date"))
    if comp.get("date") is not None:
        exigir(instante(comp["date"]) == dt, "FECHA_DISCORDANTE", "competition.date")
    exigir(comp.get("timeValid") is not False and evento.get("dateValid") is not False,
           "HORA_NO_CONFIRMADA", "timeValid")
    season = objeto(evento.get("season"), "season")
    year = entero(season.get("year"), "season.year")
    exigir(year >= 2006, "FORMATO_TEMPORADA_NO_SOPORTADO", "season.year")
    exigir(year == dt.astimezone(ZoneInfo("America/New_York")).year, "TEMPORADA_FECHA_DISCORDANTE", "season.year")
    phase = entero(season.get("type"), "season.type")
    exigir(phase in FASES, "FASE_NO_SOPORTADA", "season.type")
    kind = objeto(comp.get("type"), "competition.type")
    exigir((str(kind.get("id")), kind.get("abbreviation")) in {("1", "STD"), ("39", "CC")},
           "TIPO_COMPETICION_NO_SOPORTADO", "competition.type")
    phase_name = "COPA" if kind["abbreviation"] == "CC" else FASES[phase]
    sides = lados(comp)
    originales = sides
    state, status = estado(comp, evento)
    if "status" in evento:
        exigir(estado({"status": evento["status"]}, evento)[0] == state, "ESTADO_CONTRADICTORIO", "event.status")
    if summary is not None:
        exigir(state == "FINALIZADO", "SUMMARY_NO_FINAL", "status")
        _, sides = validar_summary(evento, summary)
    neutral = comp.get("neutralSite")
    exigir(neutral is None or isinstance(neutral, bool), "NEUTRAL_INVALIDO", "neutralSite")
    result = {"contrato": VERSION_CONTRATO, "competicion": "wnba", "fuente": "ESPN",
              "source_game_id": eid, "temporada": year, "fase": phase_name,
              "tipo_competicion_fuente": kind["abbreviation"], "estado": state,
              "inicio_utc": dt.isoformat(), "inicio_colombia": dt.astimezone(BOGOTA).isoformat(),
              "sede_neutral": neutral, "duracion_regulacion_minutos": 40,
              "final_completo": state == "FINALIZADO", "numero_prorrogas": None,
              "ganador_id_fuente": None, "estadisticas": None,
              "url_fuente": f"https://www.espn.com/wnba/game/_/gameId/{eid}"}
    points, totals = {}, {}
    for side, label in (("home", "local"), ("away", "visitante")):
        team = sides[side]["team"]
        result[f"{label}_id_fuente"] = str(team["id"])
        result[f"{label}_nombre"] = team["displayName"]
        for field in ("q1", "q2", "q3", "q4", "regulacion", "ot", "total", "prorrogas"):
            result[f"{label}_{field}"] = None
        if state == "FINALIZADO":
            points[side] = periodos(sides[side])
            totals[side] = entero(sides[side].get("score"), "score")
            exigir(totals[side] > 0 and sum(points[side]) == totals[side], "PERIODOS_NO_CONCILIAN_TOTAL", side)
            for i in range(4):
                result[f"{label}_q{i + 1}"] = points[side][i]
            result.update({f"{label}_regulacion": sum(points[side][:4]), f"{label}_ot": sum(points[side][4:]),
                           f"{label}_total": totals[side], f"{label}_prorrogas": points[side][4:]})
    if state == "FINALIZADO":
        n = len(points["home"])
        exigir(n == len(points["away"]), "PERIODOS_DESIGUALES", "linescores")
        for st in (status, evento.get("status", {})):
            if "period" in st:
                exigir(entero(st["period"], "status.period") == n, "PERIODO_FINAL_DISCORDANTE", "status.period")
        for i in range(4, n):
            exigir(sum(points["home"][:i]) == sum(points["away"][:i]), "PRORROGA_SIN_EMPATE_PREVIO", f"period:{i+1}")
        exigir(totals["home"] != totals["away"], "FINAL_EMPATE", "score")
        for side in sides:
            win = totals[side] > totals["away" if side == "home" else "home"]
            for origen in (sides, originales):
                if "winner" in origen[side]:
                    exigir(origen[side]["winner"] is win, "GANADOR_DISCORDANTE", side)
        winner = "home" if totals["home"] > totals["away"] else "away"
        result["ganador_id_fuente"] = str(sides[winner]["team"]["id"])
        result["numero_prorrogas"] = n - 4
        result["estadisticas"] = estadisticas(summary, sides, totals)
    return result

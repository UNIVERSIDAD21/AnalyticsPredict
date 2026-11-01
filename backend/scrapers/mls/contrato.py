"""Contrato MLS: marcadores, métricas por equipo y penales separados."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LIMITE = 500
VERSION_CONTRATO = "espn_mls_v1"
LIGA_ID = "770"
LIGA_UID = "s:600~l:770"
FINALES = {"STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_AET", "STATUS_FINAL_PEN"}
ESTADOS = {
    "STATUS_SCHEDULED": ("PROGRAMADO", {"pre"}, False),
    "STATUS_IN_PROGRESS": ("EN_VIVO", {"in"}, False),
    "STATUS_HALFTIME": ("EN_VIVO", {"in"}, False),
    "STATUS_END_PERIOD": ("EN_VIVO", {"in"}, False),
    "STATUS_POSTPONED": ("POSPUESTO", {"pre", "post"}, False),
    "STATUS_CANCELED": ("CANCELADO", {"pre", "post"}, False),
    "STATUS_DELAYED": ("DEMORADO", {"pre", "in"}, False),
    "STATUS_SUSPENDED": ("SUSPENDIDO", {"in", "post"}, False),
    "STATUS_ABANDONED": ("ABANDONADO", {"post"}, False),
    **{k: ("FINALIZADO", {"post"}, True) for k in FINALES},
}
METRICAS = {
    "corners": "wonCorners",
    "tiros_al_arco": "shotsOnTarget",
    "tiros_totales": "totalShots",
    "amarillas": "yellowCards",
    "rojas": "redCards",
    "faltas": "foulsCommitted",
    "atajes": "saves",
}
REQUERIDOS = [
    f"{lado}_{campo}"
    for lado in ("local", "visitante")
    for campo in ("corners", "tiros_al_arco", "tiros_totales")
]
PERIODOS = [
    f"{lado}_goles_{p}" for lado in ("local", "visitante") for p in ("1t", "2t", "90", "et")
]


class ContratoError(ValueError):
    def __init__(self, codigo, campo):
        self.codigo, self.campo = codigo, campo
        super().__init__(f"{codigo}: {campo}")


def exigir(ok, codigo, campo):
    if not ok:
        raise ContratoError(codigo, campo)


def objeto(value, campo):
    exigir(isinstance(value, dict), "OBJETO_INVALIDO", campo)
    return value


def identificador(value, campo):
    exigir(isinstance(value, (str, int)) and not isinstance(value, bool), "ID_INVALIDO", campo)
    value = str(value)
    exigir(bool(re.fullmatch(r"[0-9]{1,20}", value)), "ID_INVALIDO", campo)
    return value


def entero(value, campo):
    exigir(not isinstance(value, bool), "ENTERO_INVALIDO", campo)
    if isinstance(value, int):
        n = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        n = int(value)
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        n = int(value)
    else:
        raise ContratoError("ENTERO_INVALIDO", campo)
    exigir(n >= 0, "ENTERO_NEGATIVO", campo)
    return n


def instante(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError, TypeError) as exc:
        raise ContratoError("FECHA_INVALIDA", "date") from exc
    exigir(dt.tzinfo is not None, "FECHA_SIN_ZONA", "date")
    return dt.astimezone(timezone.utc)


def liga(value):
    value = objeto(value, "league")
    exigir(value.get("slug") == "usa.1" and str(value.get("id")) == LIGA_ID, "OTRA_LIGA", "league")
    if "uid" in value:
        exigir(value["uid"] == LIGA_UID, "OTRA_LIGA", "league.uid")


def eventos_scoreboard(payload):
    payload = objeto(payload, "scoreboard")
    leagues = payload.get("leagues")
    exigir(isinstance(leagues, list) and len(leagues) == 1, "LIGA_AMBIGUA", "leagues")
    liga(leagues[0])
    events = payload.get("events")
    exigir(isinstance(events, list), "EVENTOS_AUSENTES", "events")
    exigir(len(events) < LIMITE, "POSIBLE_TRUNCAMIENTO", "events")
    for key in ("count", "totalCount"):
        if key in payload:
            exigir(entero(payload[key], key) == len(events), "POSIBLE_TRUNCAMIENTO", key)
    return events


def competicion(event):
    event = objeto(event, "event")
    eid = identificador(event.get("id"), "event.id")
    comps = event.get("competitions")
    exigir(isinstance(comps, list) and len(comps) == 1, "COMPETICION_AMBIGUA", "competitions")
    c = objeto(comps[0], "competition")
    exigir(identificador(c.get("id"), "competition.id") == eid, "ID_DISCORDANTE", "competition.id")
    return c


def lados(c):
    items = c.get("competitors")
    exigir(isinstance(items, list) and len(items) == 2, "LADOS_INCOMPLETOS", "competitors")
    result = {}
    for item in items:
        item = objeto(item, "competitor")
        side = item.get("homeAway")
        exigir(
            isinstance(side, str) and side in ("home", "away") and side not in result,
            "LOCALIA_AMBIGUA",
            "homeAway",
        )
        team = objeto(item.get("team"), "team")
        tid = identificador(team.get("id"), "team.id")
        exigir(
            isinstance(team.get("displayName"), str) and bool(team["displayName"].strip()),
            "EQUIPO_SIN_NOMBRE",
            "team",
        )
        if "id" in item:
            exigir(str(item["id"]) == tid, "ID_DISCORDANTE", "competitor.id")
        for obj in (item, team):
            if "uid" in obj:
                exigir(obj["uid"] == f"s:600~t:{tid}", "EQUIPO_OTRO_DEPORTE", "team.uid")
        result[side] = item
    exigir(
        str(result["home"]["team"]["id"]) != str(result["away"]["team"]["id"]),
        "EQUIPOS_IGUALES",
        "team.id",
    )
    return result


def estado(value):
    s = objeto(value, "status")
    t = objeto(s.get("type"), "status.type")
    name = t.get("name")
    exigir(isinstance(name, str) and name in ESTADOS, "ESTADO_DESCONOCIDO", "status.type.name")
    label, states, done = ESTADOS[name]
    exigir(
        isinstance(t.get("state"), str) and t["state"] in states and t.get("completed") is done,
        "ESTADO_CONTRADICTORIO",
        "status.type",
    )
    return label, name, done


def marcador(value):
    if isinstance(value, dict):
        values = [
            entero(value[k], "score") for k in ("value", "displayValue") if value.get(k) is not None
        ]
        exigir(bool(values) and len(set(values)) == 1, "MARCADOR_INVALIDO", "score")
        return values[0]
    return entero(value, "score")


def normalizar(event):
    c = competicion(event)
    eid = identificador(event["id"], "event.id")
    exigir(event.get("uid") == f"{LIGA_UID}~e:{eid}", "OTRA_LIGA", "event.uid")
    if "uid" in c:
        exigir(c["uid"] == f"{LIGA_UID}~e:{eid}~c:{eid}", "OTRA_LIGA", "competition.uid")
    dt = instante(event.get("date"))
    if "date" in c:
        exigir(instante(c["date"]) == dt, "FECHA_DISCORDANTE", "competition.date")
    exigir(
        event.get("dateValid") is not False and c.get("timeValid") is not False,
        "HORA_NO_CONFIRMADA",
        "date",
    )
    season = objeto(event.get("season"), "season")
    year = entero(season.get("year"), "season.year")
    exigir(1996 <= year and dt.year - 1 <= year <= dt.year + 1, "TEMPORADA_INVALIDA", "season.year")
    stype = identificador(season.get("type"), "season.type")
    slug = season.get("slug")
    exigir(isinstance(slug, str) and bool(slug), "FASE_AUSENTE", "season.slug")
    phase = (
        "REG"
        if slug == "regular-season"
        else (
            "POST"
            if "playoff" in slug or "cup" in slug
            else "PRE" if "preseason" in slug or "pre-season" in slug else "OTRA"
        )
    )
    teams = lados(c)
    status = c.get("status", event.get("status"))
    label, name, final = estado(status)
    if "status" in event:
        exigir(
            estado(event["status"]) == (label, name, final), "ESTADO_CONTRADICTORIO", "event.status"
        )
    result = {
        "contrato": VERSION_CONTRATO,
        "competicion": "mls",
        "codigo_liga": "usa.1",
        "fuente": "ESPN",
        "source_game_id": eid,
        "temporada": year,
        "fase": phase,
        "fase_fuente": slug,
        "season_type_fuente": stype,
        "inicio_utc": dt.isoformat(),
        "inicio_colombia": dt.astimezone(ZoneInfo("America/Bogota")).isoformat(),
        "estado": label,
        "estado_fuente": name,
        "final_completo": final,
        "sede_neutral": c.get("neutralSite"),
        "hubo_prorroga": (
            True
            if name == "STATUS_FINAL_AET"
            else False if name in ("STATUS_FINAL", "STATUS_FULL_TIME") else None
        ),
        "hubo_penales": name == "STATUS_FINAL_PEN" if final else None,
        "ganador_partido_id": None,
        "ganador_tanda_id": None,
        "detalle_estado": "PENDIENTE" if final else "NO_APLICA",
        "estadisticas_completas": False,
        "alcance_estadisticas": "PARTIDO_SIN_TANDA",
        "campos_faltantes": [],
        "incidencias": [],
        "url_fuente": f"https://www.espn.com/soccer/match/_/gameId/{eid}",
    }
    exigir(
        result["sede_neutral"] is None or isinstance(result["sede_neutral"], bool),
        "SEDE_INVALIDA",
        "neutralSite",
    )
    for side, label in [("home", "local"), ("away", "visitante")]:
        t = teams[side]
        result[f"{label}_id_fuente"] = str(t["team"]["id"])
        result[f"{label}_nombre"] = t["team"]["displayName"]
        result[f"{label}_goles"] = marcador(t.get("score")) if final else None
        result[f"{label}_penales"] = None
        for k in METRICAS:
            result[f"{label}_{k}"] = None
        for p in ("1t", "2t", "90", "et"):
            result[f"{label}_goles_{p}"] = None
        if final and name in ("STATUS_FULL_TIME", "STATUS_FINAL"):
            result[f"{label}_goles_90"] = result[f"{label}_goles"]
            result[f"{label}_goles_et"] = 0
    if final:
        a, b = result["local_goles"], result["visitante_goles"]
        if a != b:
            result["ganador_partido_id"] = result[
                "local_id_fuente" if a > b else "visitante_id_fuente"
            ]
        if name == "STATUS_FINAL_AET":
            exigir(a != b, "PRORROGA_EMPATE_FINAL", "score")
        if name != "STATUS_FINAL_PEN":
            for side, label in [("home", "local"), ("away", "visitante")]:
                if "winner" in teams[side]:
                    exigir(
                        teams[side]["winner"]
                        is (result[f"{label}_id_fuente"] == result["ganador_partido_id"]),
                        "GANADOR_DISCORDANTE",
                        side,
                    )
        result["campos_faltantes"] = list(REQUERIDOS)
    return result


def validar_summary(record, payload):
    h = objeto(payload.get("header"), "header")
    liga(h.get("league"))
    exigir(
        str(h.get("id")) == record["source_game_id"]
        and h.get("uid") == f"{LIGA_UID}~e:{record['source_game_id']}",
        "SUMMARY_OTRO_EVENTO",
        "header",
    )
    season = objeto(h.get("season"), "header.season")
    exigir(
        entero(season.get("year"), "season.year") == record["temporada"]
        and str(season.get("type")) == record["season_type_fuente"],
        "SUMMARY_OTRA_TEMPORADA",
        "season",
    )
    c = competicion(h)
    teams = lados(c)
    exigir(
        instante(c.get("date")).isoformat() == record["inicio_utc"], "SUMMARY_OTRA_FECHA", "date"
    )
    exigir(
        estado(c.get("status")) == ("FINALIZADO", record["estado_fuente"], True),
        "SUMMARY_OTRO_ESTADO",
        "status",
    )
    for side, label in [("home", "local"), ("away", "visitante")]:
        exigir(
            str(teams[side]["team"]["id"]) == record[f"{label}_id_fuente"],
            "SUMMARY_OTROS_EQUIPOS",
            side,
        )
        exigir(
            marcador(teams[side].get("score")) == record[f"{label}_goles"],
            "SUMMARY_OTRO_MARCADOR",
            side,
        )
    return c, teams


def prorroga_en_tanda(payload, numero_periodos, goles_extra):
    """No confundir ceros de relleno de ESPN con una prórroga disputada."""
    pruebas = set()
    if numero_periodos == 3:
        pruebas.add(False)
    if goles_extra > 0:
        pruebas.add(True)
    plays = []
    if isinstance(payload.get("keyEvents"), list):
        plays.extend(payload["keyEvents"])
    if isinstance(payload.get("commentary"), list):
        plays.extend(x.get("play") for x in payload["commentary"] if isinstance(x, dict))
    tipos_extra = {
        "start-extra-time",
        "start-1st-half-extra-time",
        "end-1st-half-extra-time",
        "start-2nd-half-extra-time",
        "end-extra-time",
    }
    for play in plays:
        if not isinstance(play, dict) or not isinstance(play.get("type"), dict):
            continue
        tipo = play["type"].get("type")
        if isinstance(tipo, str) and tipo in tipos_extra:
            pruebas.add(True)
        if tipo == "start-shootout" and isinstance(play.get("clock"), dict):
            clock = play["clock"].get("value")
            if not isinstance(clock, bool) and isinstance(clock, (int, float)):
                if clock == 5400:
                    pruebas.add(False)
                elif clock == 7200:
                    pruebas.add(True)
    exigir(len(pruebas) <= 1, "PRORROGA_CONTRADICTORIA", "keyEvents/linescores")
    return next(iter(pruebas)) if pruebas else None


def enriquecer(record, payload, evento=None):
    """Solo enriquecer una identidad validada; una métrica inválida se aparta."""
    from copy import deepcopy

    r = deepcopy(record)
    c, teams = validar_summary(r, payload)
    source = objeto(payload.get("boxscore", {}), "boxscore").get("teams", [])
    exigir(isinstance(source, list), "BOXScore_INVALIDO", "boxscore.teams")
    by_id = {}
    for item in source:
        item = objeto(item, "boxscore.team")
        tid = identificador(objeto(item.get("team"), "team").get("id"), "team.id")
        exigir(
            tid in (r["local_id_fuente"], r["visitante_id_fuente"]) and tid not in by_id,
            "BOXScore_OTROS_EQUIPOS",
            "team.id",
        )
        rows = item.get("statistics", [])
        exigir(isinstance(rows, list), "ESTADISTICAS_INVALIDAS", "statistics")
        values = {}
        for row in rows:
            row = objeto(row, "statistic")
            key = row.get("name")
            exigir(isinstance(key, str) and key not in values, "ESTADISTICAS_DUPLICADAS", "name")
            values[key] = row.get("displayValue")
        by_id[tid] = values

    def warning(code, field, raw=None):
        r["incidencias"].append({"codigo": code, "campo": field, "valor_fuente": raw})

    for side, label in [("home", "local"), ("away", "visitante")]:
        values = by_id.get(r[f"{label}_id_fuente"], {})
        for dest, key in METRICAS.items():
            raw = values.get(key)
            field = f"{label}_{dest}"
            if raw in (None, "", "--", "N/A"):
                continue
            try:
                r[field] = entero(raw, key)
            except ContratoError as exc:
                warning(exc.codigo, field, raw)
        sot, total = r[f"{label}_tiros_al_arco"], r[f"{label}_tiros_totales"]
        if sot is not None and total is not None and sot > total:
            warning(
                "TIROS_INCONSISTENTES",
                f"{label}_tiros_al_arco/tiros_totales",
                {"al_arco": sot, "totales": total},
            )
            r[f"{label}_tiros_al_arco"] = r[f"{label}_tiros_totales"] = None
    # Las mitades son un enriquecimiento independiente; nunca reconstruirlas por resta.
    try:
        regulation = objeto(
            objeto(payload.get("format", {}), "format").get("regulation", {}), "regulation"
        )
        exigir(
            regulation.get("periods") == 2 and regulation.get("slug") == "half",
            "FORMATO_PERIODOS_NO_ACREDITADO",
            "format",
        )
        values = {}
        lengths = set()
        for side, label in [("home", "local"), ("away", "visitante")]:
            lines = teams[side].get("linescores")
            exigir(isinstance(lines, list), "PERIODOS_AUSENTES", "linescores")
            n = len(lines)
            allowed = {3, 5} if r["hubo_penales"] else {4} if r["hubo_prorroga"] else {2}
            exigir(n in allowed, "PERIODOS_INVALIDOS", "linescores")
            lengths.add(n)
            nums = []
            for i, line in enumerate(lines, 1):
                line = objeto(line, "linescore")
                p = line.get("period", i)
                if isinstance(p, dict):
                    p = p.get("number")
                exigir(entero(p, "period") == i, "PERIODOS_DESORDENADOS", "period")
                nums.append(marcador({k: line[k] for k in ("value", "displayValue") if k in line}))
            played = nums[:-1] if r["hubo_penales"] else nums
            exigir(sum(played) == r[f"{label}_goles"], "PERIODOS_NO_CONCILIAN", "linescores")
            if evento is not None:
                published = lados(competicion(evento))[side].get("linescores", [])
                exigir(isinstance(published, list), "PERIODOS_INVALIDOS", "scoreboard.linescores")
                indices = set()
                for index, line in enumerate(published, 1):
                    line = objeto(line, "scoreboard.linescore")
                    number = line.get("period", index)
                    if isinstance(number, dict):
                        number = number.get("number")
                    number = entero(number, "period")
                    exigir(
                        1 <= number <= len(nums) and number not in indices,
                        "PERIODOS_AMBIGUOS",
                        "period",
                    )
                    indices.add(number)
                    if line.get("value") is not None or line.get("displayValue") is not None:
                        value = marcador(
                            {
                                k: line[k]
                                for k in ("value", "displayValue")
                                if line.get(k) is not None
                            }
                        )
                        exigir(value == nums[number - 1], "SUMMARY_OTROS_PERIODOS", side)
            values.update(
                {
                    f"{label}_goles_1t": nums[0],
                    f"{label}_goles_2t": nums[1],
                    f"{label}_goles_90": nums[0] + nums[1],
                    f"{label}_goles_et": sum(played[2:]),
                }
            )
            if r["hubo_penales"]:
                pen = entero(teams[side].get("shootoutScore"), "shootoutScore")
                exigir(pen == nums[-1], "PENALES_DISCORDANTES", "shootoutScore")
                values[f"{label}_penales"] = pen
        exigir(len(lengths) == 1, "PERIODOS_DESIGUALES", "linescores")
        n = next(iter(lengths))
        if n in (4, 5):
            exigir(
                values["local_goles_90"] == values["visitante_goles_90"],
                "PRORROGA_SIN_EMPATE",
                "linescores",
            )
        if r["hubo_penales"]:
            exigir(r["local_goles"] == r["visitante_goles"], "TANDA_SIN_EMPATE", "score")
            a, b = values["local_penales"], values["visitante_penales"]
            exigir(a != b, "TANDA_EMPATE", "shootoutScore")
            winner = "local" if a > b else "visitante"
            values["ganador_tanda_id"] = r[f"{winner}_id_fuente"]
            for side, label in [("home", "local"), ("away", "visitante")]:
                if "winner" in teams[side]:
                    exigir(
                        teams[side]["winner"] is (label == winner),
                        "GANADOR_TANDA_DISCORDANTE",
                        side,
                    )
        extra = (
            prorroga_en_tanda(payload, n, values["local_goles_et"] + values["visitante_goles_et"])
            if r["hubo_penales"]
            else n == 4
        )
        if extra is None:
            warning("PRORROGA_NO_ACREDITADA", "hubo_prorroga")
        r.update(values)
        r["hubo_prorroga"] = extra
    except ContratoError as exc:
        warning(exc.codigo, exc.campo)
    r["campos_faltantes"] = [k for k in REQUERIDOS if r[k] is None]
    r["estadisticas_completas"] = not r["campos_faltantes"]
    r["detalle_estado"] = "OK" if r["estadisticas_completas"] else "PARCIAL"
    return r

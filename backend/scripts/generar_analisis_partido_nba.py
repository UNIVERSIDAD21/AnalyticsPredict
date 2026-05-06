#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera análisis estadístico previo para un enfrentamiento NBA.

Usa el JSON canónico de forma reciente generado por
`backend/scripts/generar_reporte_forma_reciente_nba.py` y produce:
- JSON completo en reports/match_analysis_input/
- Markdown copiable en reports/match_analysis_reports/

No recomienda apuestas, no calcula stake y no usa lenguaje de certeza.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
RECENT_FORM_PATH = ROOT / "reports" / "team_recent_form" / "nba_team_recent_form.json"
DEFAULT_JSON_DIR = ROOT / "reports" / "match_analysis_input"
DEFAULT_MD_DIR = ROOT / "reports" / "match_analysis_reports"
WINDOWS = (5, 10, 20, 30)
FIELDS_BY_MARKET = {
    "Q1_TOTAL": ("puntos_q1", "recibidos_q1", "game_q1"),
    "FULL_GAME_TOTAL": ("puntos_total", "recibidos_total", "game_total"),
    "HOME_TEAM_TOTAL": ("puntos_total", "recibidos_total", "home_total"),
    "AWAY_TEAM_TOTAL": ("puntos_total", "recibidos_total", "away_total"),
}
QUARTER_FIELDS = ["q1", "q2", "q3", "q4"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().lower()
    return text


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", normalize(text)).strip("_")


def resolve_team(query: str, teams: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    q = normalize(query)
    matches = []
    for abbr, data in teams.items():
        candidates = {normalize(abbr), normalize(data.get("equipo", ""))}
        if q in candidates:
            return abbr, data
        if q and any(q in c or c in q for c in candidates):
            matches.append((abbr, data))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"Equipo no encontrado en reporte reciente: {query!r}")
    opts = ", ".join(f"{a} - {d['equipo']}" for a, d in matches[:10])
    raise SystemExit(f"Equipo ambiguo para {query!r}. Opciones: {opts}")


def pct(values: list[float], line: float, side: str = "over") -> float | None:
    if not values:
        return None
    if side == "under":
        hits = sum(1 for v in values if v < line)
    else:
        hits = sum(1 for v in values if v > line)
    return round(hits * 100 / len(values), 2)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"promedio": None, "mediana": None, "desviacion_estandar": None, "minimo": None, "maximo": None}
    vals = [float(v) for v in values]
    return {
        "promedio": round(sum(vals) / len(vals), 3),
        "mediana": round(float(statistics.median(vals)), 3),
        "desviacion_estandar": round(float(statistics.pstdev(vals)), 3) if len(vals) > 1 else 0.0,
        "minimo": round(min(vals), 3),
        "maximo": round(max(vals), 3),
    }


def avg2(a: float | int | None, b: float | int | None) -> float:
    if a is None or b is None:
        return math.nan
    return (float(a) + float(b)) / 2


def paired_values(home_rows: list[dict[str, Any]], away_rows: list[dict[str, Any]], market: str, n: int) -> list[float]:
    rows = list(zip(home_rows[:n], away_rows[:n]))
    out: list[float] = []
    for h, a in rows:
        if market == "Q1_TOTAL":
            out.append(avg2(h["puntos_q1"], a["recibidos_q1"]) + avg2(a["puntos_q1"], h["recibidos_q1"]))
        elif market == "FULL_GAME_TOTAL":
            out.append(avg2(h["puntos_total"], a["recibidos_total"]) + avg2(a["puntos_total"], h["recibidos_total"]))
        elif market == "HOME_TEAM_TOTAL":
            out.append(avg2(h["puntos_total"], a["recibidos_total"]))
        elif market == "AWAY_TEAM_TOTAL":
            out.append(avg2(a["puntos_total"], h["recibidos_total"]))
    return out


def combined_metric(home: dict[str, Any], away: dict[str, Any], h_split: str, a_split: str, n: int, field: str) -> dict[str, float | None]:
    h = home["splits"][h_split][str(n)]["metricas"]
    a = away["splits"][a_split][str(n)]["metricas"]
    home_attack = h[f"puntos_{field}"]["promedio"]
    away_def = a[f"recibidos_{field}"]["promedio"]
    away_attack = a[f"puntos_{field}"]["promedio"]
    home_def = h[f"recibidos_{field}"]["promedio"]
    return {
        "local_ataque_vs_defensa_visitante": round(avg2(home_attack, away_def), 3),
        "visitante_ataque_vs_defensa_local": round(avg2(away_attack, home_def), 3),
        "total_combinado": round(avg2(home_attack, away_def) + avg2(away_attack, home_def), 3),
    }


def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurada")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def is_valid_scored_row(row: dict[str, Any]) -> bool:
    return int(row.get("puntos_total") or 0) > 0 and int(row.get("recibidos_total") or 0) > 0


def build_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = [
        "puntos_q1", "puntos_q2", "puntos_q3", "puntos_q4", "puntos_total",
        "recibidos_q1", "recibidos_q2", "recibidos_q3", "recibidos_q4", "recibidos_total",
    ]
    out: dict[str, Any] = {}
    for n in WINDOWS:
        sample = rows[:n]
        out[str(n)] = {
            "partidos": len(sample),
            "fecha_mas_reciente": sample[0]["fecha_partido"] if sample else None,
            "overtime": sum(1 for r in sample if r.get("hubo_overtime")),
            "metricas": {m: summary([r[m] for r in sample]) for m in metrics},
        }
    return out


def fetch_team_rows_from_db(team_abbr: str, localia: str | None = None, limit: int = 30) -> tuple[list[dict[str, Any]], int]:
    import psycopg
    from psycopg.rows import dict_row

    where_localia = ""
    if localia == "local":
        where_localia = "WHERE localia = 'local'"
    elif localia == "visitante":
        where_localia = "WHERE localia = 'visitante'"
    sql = f"""
    WITH nba AS (
      SELECT id FROM competiciones_baloncesto WHERE lower(codigo)='nba' LIMIT 1
    ), equipo AS (
      SELECT id, abreviatura, nombre FROM equipos WHERE upper(abreviatura)=upper(%s) LIMIT 1
    ), apariciones AS (
      SELECT e.abreviatura,e.nombre equipo,p.id partido_id,p.fecha_partido,'local' localia,p.tipo_partido,
             p.local_q1 puntos_q1,p.local_q2 puntos_q2,p.local_q3 puntos_q3,p.local_q4 puntos_q4,p.local_total puntos_total,
             p.visitante_q1 recibidos_q1,p.visitante_q2 recibidos_q2,p.visitante_q3 recibidos_q3,p.visitante_q4 recibidos_q4,p.visitante_total recibidos_total,
             p.hubo_overtime,p.source,p.source_game_id
      FROM partidos_baloncesto p JOIN equipo e ON e.id=p.equipo_local_id JOIN nba ON nba.id=p.competicion_id
      UNION ALL
      SELECT e.abreviatura,e.nombre,p.id,p.fecha_partido,'visitante',p.tipo_partido,
             p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4,p.visitante_total,
             p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.local_total,
             p.hubo_overtime,p.source,p.source_game_id
      FROM partidos_baloncesto p JOIN equipo e ON e.id=p.equipo_visitante_id JOIN nba ON nba.id=p.competicion_id
    )
    SELECT * FROM apariciones
    {where_localia}
    ORDER BY fecha_partido DESC, partido_id DESC
    LIMIT %s
    """
    with psycopg.connect(db_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (team_abbr, max(limit * 3, 90)))
            raw = [dict(r) for r in cur.fetchall()]
    invalid = [r for r in raw if not is_valid_scored_row(r)]
    valid = [r for r in raw if is_valid_scored_row(r)][:limit]
    for r in valid:
        r["fecha_partido"] = str(r["fecha_partido"])
        r["partido_id"] = str(r["partido_id"])
    return valid, len(invalid)


def extract_rows(team: dict[str, Any], localia: str | None = None) -> list[dict[str, Any]]:
    rows = team.get("ultimos_30_partidos", [])
    if localia:
        return [r for r in rows if r.get("localia") == localia and is_valid_scored_row(r)]
    return [r for r in rows if is_valid_scored_row(r)]


def evaluate_signal(avg: float | None, line: float, percentages: dict[str, float | None], volatility: float | None, warnings: list[str]) -> str:
    valid = [v for v in percentages.values() if v is not None]
    if avg is None or len(valid) < 2 or any("muestra baja" in w for w in warnings):
        return "no evaluable por datos insuficientes"
    avg_gap = abs(avg - line)
    hit_consensus = sum(1 for v in valid if v >= 60 or v <= 40)
    direction_consistent = max(valid) - min(valid) <= 20
    high_vol = volatility is not None and volatility >= 14
    if high_vol or any("inconsistente" in w for w in warnings):
        return "señal inconsistente"
    if avg_gap >= 6 and hit_consensus >= 3 and direction_consistent:
        return "señal estadística fuerte"
    if avg_gap >= 3 and hit_consensus >= 2:
        return "señal estadística moderada"
    return "señal estadística débil"


def evaluate_market(market: dict[str, Any], home_rows: list[dict[str, Any]], away_rows: list[dict[str, Any]], home_local_rows: list[dict[str, Any]], away_visit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    name = str(market.get("market", "")).upper()
    line = market.get("line")
    result: dict[str, Any] = {"market": name, "input": market, "advertencias": []}
    if name not in FIELDS_BY_MARKET:
        result.update({"evaluable": False, "clasificacion": "no evaluable por datos insuficientes"})
        result["advertencias"].append("mercado no soportado por el script")
        return result
    if not isinstance(line, (int, float)):
        result.update({"evaluable": False, "clasificacion": "no evaluable por datos insuficientes"})
        result["advertencias"].append("línea ausente o no numérica")
        return result

    values_by_window = {str(n): paired_values(home_rows, away_rows, name, n) for n in WINDOWS}
    split_values = paired_values(home_local_rows, away_visit_rows, name, 30)
    s30 = summary(values_by_window["30"])
    avg = s30["promedio"]
    med = s30["mediana"]
    volatility = s30["desviacion_estandar"]
    over_pct = {str(n): pct(values_by_window[str(n)], float(line), "over") for n in WINDOWS}
    under_pct = {str(n): pct(values_by_window[str(n)], float(line), "under") for n in WINDOWS}
    recent_avg = summary(values_by_window["5"])["promedio"]
    if len(values_by_window["30"]) < 20:
        result["advertencias"].append("muestra baja: menos de 20 observaciones combinadas")
    if volatility is not None and volatility >= 14:
        result["advertencias"].append("desviación estándar alta: mercado volátil")
    if avg is not None and recent_avg is not None and abs(float(recent_avg) - float(avg)) >= 8:
        result["advertencias"].append("diferencia fuerte entre forma reciente (5) y muestra completa (30)")
    ot_count = sum(1 for r in home_rows[:30] if r.get("hubo_overtime")) + sum(1 for r in away_rows[:30] if r.get("hubo_overtime"))
    if ot_count:
        result["advertencias"].append(f"datos afectados por overtime en {ot_count} apariciones recientes")

    signal_pcts = over_pct if avg is not None and avg >= float(line) else under_pct
    result.update({
        "evaluable": True,
        "promedio_combinado": avg,
        "mediana_combinada": med,
        "diferencia_contra_linea": round(float(avg) - float(line), 3) if avg is not None else None,
        "volatilidad": volatility,
        "porcentaje_cumplimiento_over": over_pct,
        "porcentaje_cumplimiento_under": under_pct,
        "cumplimiento_split_local_visitante_over": pct(split_values, float(line), "over"),
        "cumplimiento_split_local_visitante_under": pct(split_values, float(line), "under"),
        "resumen_muestras": {str(n): summary(values_by_window[str(n)]) for n in WINDOWS},
    })
    result["clasificacion"] = evaluate_signal(avg if isinstance(avg, (int, float)) else None, float(line), signal_pcts, volatility if isinstance(volatility, (int, float)) else None, result["advertencias"])
    return result


def build_analysis(home_q: str, away_q: str, game_date: str, markets_path: Path | None) -> tuple[dict[str, Any], str]:
    teams = load_json(RECENT_FORM_PATH)
    home_abbr, home = resolve_team(home_q, teams)
    away_abbr, away = resolve_team(away_q, teams)
    if home_abbr == away_abbr:
        raise SystemExit("Equipo local y visitante no pueden ser el mismo")

    all_dates = [d.get("fecha_mas_reciente") for d in teams.values() if d.get("fecha_mas_reciente")]
    max_db_date = max(all_dates) if all_dates else None
    try:
        home_rows, home_invalid = fetch_team_rows_from_db(home_abbr, None)
        away_rows, away_invalid = fetch_team_rows_from_db(away_abbr, None)
        home_local_rows, home_local_invalid = fetch_team_rows_from_db(home_abbr, "local")
        away_visit_rows, away_visit_invalid = fetch_team_rows_from_db(away_abbr, "visitante")
        data_source = "bd_partidos_baloncesto"
    except Exception as exc:  # noqa: BLE001
        home_rows = extract_rows(home)
        away_rows = extract_rows(away)
        home_local_rows = extract_rows(home, "local")
        away_visit_rows = extract_rows(away, "visitante")
        home_invalid = away_invalid = home_local_invalid = away_visit_invalid = 0
        data_source = f"fallback_json_forma_reciente: {exc}"

    home_general_split = build_split(home_rows)
    away_general_split = build_split(away_rows)
    home_local_split = build_split(home_local_rows)
    away_visit_split = build_split(away_visit_rows)

    warnings = []
    for label, data, rows in (("local", home, home_rows), ("visitante", away, away_rows)):
        warnings.extend([f"{label} {data['equipo']}: {w}" for w in data.get("advertencias", [])])
        if len(rows) < 30:
            warnings.append(f"{label} {data['equipo']}: muestra general válida menor a 30")
    if len(home_local_rows) < 30:
        warnings.append(f"local {home['equipo']}: split local válido menor a 30")
    if len(away_visit_rows) < 30:
        warnings.append(f"visitante {away['equipo']}: split visitante válido menor a 30")
    invalid_total = home_invalid + away_invalid + home_local_invalid + away_visit_invalid
    if invalid_total:
        warnings.append(f"se excluyeron {invalid_total} apariciones con marcador 0 o incompleto antes de calcular muestras")
    if max_db_date and game_date > max_db_date:
        warnings.append(f"fecha del partido posterior a fecha máxima disponible ({max_db_date})")

    home_calc = {"splits": {"general": home_general_split, "local": home_local_split}}
    away_calc = {"splits": {"general": away_general_split, "visitante": away_visit_split}}
    combined = {
        "general": {str(n): {q: combined_metric(home_calc, away_calc, "general", "general", n, q) for q in ["q1", "q2", "q3", "q4", "total"]} for n in WINDOWS},
        "local_vs_visitante": {str(n): {q: combined_metric(home_calc, away_calc, "local", "visitante", n, q) for q in ["q1", "q2", "q3", "q4", "total"]} for n in WINDOWS},
    }

    markets = []
    if markets_path:
        raw = load_json(markets_path)
        markets = raw.get("markets", []) if isinstance(raw, dict) else []
    market_eval = [evaluate_market(m, home_rows, away_rows, home_local_rows, away_visit_rows) for m in markets]

    analysis = {
        "metadata": {
            "generado_en": datetime.now().isoformat(timespec="seconds"),
            "fuente_forma_reciente": display_path(RECENT_FORM_PATH),
            "fuente_muestras_calculadas": data_source,
            "markets_file": display_path(markets_path),
            "reglas_clasificacion": {
                "señal estadística fuerte": "brecha promedio-línea >= 6, al menos 3 ventanas con cumplimiento direccional >=60% o <=40%, y ventanas consistentes",
                "señal estadística moderada": "brecha promedio-línea >= 3 y al menos 2 ventanas con cumplimiento direccional",
                "señal estadística débil": "evaluable, pero sin suficiente brecha/consenso",
                "señal inconsistente": "volatilidad alta o advertencias de inconsistencia reciente vs completa",
                "no evaluable por datos insuficientes": "línea inválida, mercado no soportado o muestra insuficiente",
            },
        },
        "partido": {
            "fecha": game_date,
            "equipo_local": {"abreviatura": home_abbr, "nombre": home["equipo"]},
            "equipo_visitante": {"abreviatura": away_abbr, "nombre": away["equipo"]},
            "fecha_maxima_disponible_bd": max_db_date,
        },
        "muestras": {
            "local": {"general": len(home_rows), "local": len(home_local_rows), "excluidas_incompletas": home_invalid + home_local_invalid, "conteos_historicos": home.get("conteos", {})},
            "visitante": {"general": len(away_rows), "visitante": len(away_visit_rows), "excluidas_incompletas": away_invalid + away_visit_invalid, "conteos_historicos": away.get("conteos", {})},
        },
        "forma_local": {"general": home_general_split, "local": home_local_split, "ultimos_30": home_rows, "ultimos_30_local": home_local_rows},
        "forma_visitante": {"general": away_general_split, "visitante": away_visit_split, "ultimos_30": away_rows, "ultimos_30_visitante": away_visit_rows},
        "comparaciones": {
            "ataque_local_vs_defensa_visitante": {str(n): {q: combined[str("general")][str(n)][q]["local_ataque_vs_defensa_visitante"] for q in combined["general"][str(n)]} for n in WINDOWS},
            "ataque_visitante_vs_defensa_local": {str(n): {q: combined["general"][str(n)][q]["visitante_ataque_vs_defensa_local"] for q in combined["general"][str(n)]} for n in WINDOWS},
            "metricas_combinadas_esperadas": combined,
        },
        "evaluacion_mercados": market_eval,
        "advertencias": warnings,
    }
    file_slug = f"{slugify(home['equipo'])}_vs_{slugify(away['equipo'])}_{game_date}"
    return analysis, file_slug


def fmt(x: Any) -> str:
    if x is None:
        return "N/D"
    if isinstance(x, float):
        return f"{x:.2f}"
    return str(x)


def metric_line(label: str, split: dict[str, Any], n: int) -> str:
    m = split[str(n)]["metricas"]
    return (
        f"- Últimos {n}: PF total {fmt(m['puntos_total']['promedio'])} / PA total {fmt(m['recibidos_total']['promedio'])}; "
        f"Q1 PF {fmt(m['puntos_q1']['promedio'])}, Q2 {fmt(m['puntos_q2']['promedio'])}, Q3 {fmt(m['puntos_q3']['promedio'])}, Q4 {fmt(m['puntos_q4']['promedio'])}; "
        f"OT {split[str(n)]['overtime']}"
    )


def render_markdown(analysis: dict[str, Any]) -> str:
    p = analysis["partido"]
    home = p["equipo_local"]
    away = p["equipo_visitante"]
    lines = [
        f"# Análisis estadístico previo NBA: {home['nombre']} vs {away['nombre']}",
        "",
        "> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.",
        "",
        "## Metadata",
        f"- Partido: {home['nombre']} ({home['abreviatura']}) local vs {away['nombre']} ({away['abreviatura']}) visitante",
        f"- Fecha del partido: {p['fecha']}",
        f"- Fecha máxima disponible en BD: {p['fecha_maxima_disponible_bd']}",
        f"- Generado: {analysis['metadata']['generado_en']}",
        "",
        "## Reglas de clasificación de señales",
    ]
    for k, v in analysis["metadata"]["reglas_clasificacion"].items():
        lines.append(f"- **{k}:** {v}")
    lines += ["", "## Muestras usadas", f"- Local general/local: {analysis['muestras']['local']['general']} / {analysis['muestras']['local']['local']}", f"- Visitante general/visitante: {analysis['muestras']['visitante']['general']} / {analysis['muestras']['visitante']['visitante']}", ""]

    lines += [f"## Forma reciente - {home['nombre']} local", "", "### General"]
    for n in WINDOWS:
        lines.append(metric_line(home['nombre'], analysis['forma_local']['general'], n))
    lines += ["", "### Split local"]
    for n in WINDOWS:
        lines.append(metric_line(home['nombre'], analysis['forma_local']['local'], n))

    lines += ["", f"## Forma reciente - {away['nombre']} visitante", "", "### General"]
    for n in WINDOWS:
        lines.append(metric_line(away['nombre'], analysis['forma_visitante']['general'], n))
    lines += ["", "### Split visitante"]
    for n in WINDOWS:
        lines.append(metric_line(away['nombre'], analysis['forma_visitante']['visitante'], n))

    lines += ["", "## Métricas combinadas esperadas", "", "| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |", "|---:|---:|---:|---:|---:|---:|"]
    combined = analysis["comparaciones"]["metricas_combinadas_esperadas"]["local_vs_visitante"]
    for n in WINDOWS:
        row = combined[str(n)]
        lines.append(f"| {n} | {fmt(row['q1']['total_combinado'])} | {fmt(row['q2']['total_combinado'])} | {fmt(row['q3']['total_combinado'])} | {fmt(row['q4']['total_combinado'])} | {fmt(row['total']['total_combinado'])} |")

    lines += ["", "## Evaluación técnica de líneas"]
    if not analysis["evaluacion_mercados"]:
        lines.append("- No se pasó archivo de mercados; solo se generó análisis estadístico base.")
    for m in analysis["evaluacion_mercados"]:
        lines += ["", f"### {m['market']}", f"- Línea: {m['input'].get('line')}", f"- Clasificación técnica: **{m.get('clasificacion')}**"]
        if not m.get("evaluable"):
            lines.append(f"- No evaluable: {'; '.join(m.get('advertencias', []))}")
            continue
        lines += [
            f"- Promedio combinado: {fmt(m.get('promedio_combinado'))}",
            f"- Mediana combinada: {fmt(m.get('mediana_combinada'))}",
            f"- Diferencia contra línea: {fmt(m.get('diferencia_contra_linea'))}",
            f"- Volatilidad/desv. estándar: {fmt(m.get('volatilidad'))}",
            f"- Cumplimiento over 5/10/20/30: {m['porcentaje_cumplimiento_over']}",
            f"- Cumplimiento under 5/10/20/30: {m['porcentaje_cumplimiento_under']}",
            f"- Cumplimiento split local/visitante over: {fmt(m.get('cumplimiento_split_local_visitante_over'))}%",
            f"- Cumplimiento split local/visitante under: {fmt(m.get('cumplimiento_split_local_visitante_under'))}%",
        ]
        if m.get("advertencias"):
            lines.append("- Advertencias: " + "; ".join(m["advertencias"]))

    lines += ["", "## Advertencias generales"]
    if analysis["advertencias"]:
        lines.extend(f"- {w}" for w in analysis["advertencias"])
    else:
        lines.append("- Sin advertencias generales de cobertura en las muestras principales.")

    total30 = combined["30"]
    lines += [
        "",
        "## Resumen para análisis externo",
        f"Partido: {home['nombre']} local vs {away['nombre']} visitante, fecha {p['fecha']}. BD disponible hasta {p['fecha_maxima_disponible_bd']}.",
        f"Muestras recientes: {home['abreviatura']} general {analysis['muestras']['local']['general']} y local {analysis['muestras']['local']['local']}; {away['abreviatura']} general {analysis['muestras']['visitante']['general']} y visitante {analysis['muestras']['visitante']['visitante']}.",
        f"Combinado split local/visitante últimos 30: Q1 {fmt(total30['q1']['total_combinado'])}, Q2 {fmt(total30['q2']['total_combinado'])}, Q3 {fmt(total30['q3']['total_combinado'])}, Q4 {fmt(total30['q4']['total_combinado'])}, total partido {fmt(total30['total']['total_combinado'])}.",
    ]
    if analysis["evaluacion_mercados"]:
        compact = "; ".join(f"{m['market']} línea {m['input'].get('line')}: {m.get('clasificacion')}, diff {fmt(m.get('diferencia_contra_linea'))}, vol {fmt(m.get('volatilidad'))}" for m in analysis["evaluacion_mercados"])
        lines.append(f"Líneas evaluadas técnicamente: {compact}.")
    lines.append("Usar como evidencia estadística, no como recomendación de apuesta.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    global RECENT_FORM_PATH
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--home", required=True, help="Equipo local: nombre completo o abreviatura")
    parser.add_argument("--away", required=True, help="Equipo visitante: nombre completo o abreviatura")
    parser.add_argument("--date", required=True, help="Fecha del partido YYYY-MM-DD")
    parser.add_argument("--markets", help="JSON opcional con líneas de mercado")
    parser.add_argument("--recent-form", default=str(RECENT_FORM_PATH), help="JSON de forma reciente")
    args = parser.parse_args()

    RECENT_FORM_PATH = Path(args.recent_form)
    markets_path = Path(args.markets).resolve() if args.markets else None
    datetime.strptime(args.date, "%Y-%m-%d")
    if markets_path and not markets_path.exists():
        raise SystemExit(f"No existe archivo de mercados: {markets_path}")

    analysis, file_slug = build_analysis(args.home, args.away, args.date, markets_path)
    DEFAULT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_MD_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DEFAULT_JSON_DIR / f"{file_slug}.json"
    md_path = DEFAULT_MD_DIR / f"{file_slug}.md"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(analysis), encoding="utf-8")
    print(json.dumps({"json": str(json_path.relative_to(ROOT)), "markdown": str(md_path.relative_to(ROOT))}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

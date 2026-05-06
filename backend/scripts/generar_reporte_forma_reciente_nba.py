#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera reporte de calidad y forma reciente NBA desde BD actualizada."""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics as stats
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")


def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def numeric_summary(values: list[int | float]) -> dict[str, float | int | None]:
    if not values:
        return {"promedio": None, "mediana": None, "desviacion_estandar": None, "minimo": None, "maximo": None}
    vals = [float(v) for v in values]
    return {
        "promedio": round(sum(vals) / len(vals), 3),
        "mediana": round(float(stats.median(vals)), 3),
        "desviacion_estandar": round(float(stats.pstdev(vals)), 3) if len(vals) > 1 else 0.0,
        "minimo": int(min(vals)),
        "maximo": int(max(vals)),
    }


def split_summary(rows: list[dict[str, Any]], n: int) -> dict[str, Any]:
    subset = rows[:n]
    fields = [
        "puntos_q1", "puntos_q2", "puntos_q3", "puntos_q4", "puntos_total",
        "recibidos_q1", "recibidos_q2", "recibidos_q3", "recibidos_q4", "recibidos_total",
    ]
    return {
        "partidos": len(subset),
        "fecha_mas_reciente": str(subset[0]["fecha_partido"]) if subset else None,
        "overtime": sum(1 for r in subset if r["hubo_overtime"]),
        "metricas": {field: numeric_summary([r[field] for r in subset]) for field in fields},
    }


def build_reports(output_md: Path, output_json: Path) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(db_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("select id,nombre,codigo from competiciones_baloncesto where lower(codigo)='nba' limit 1")
            comp = cur.fetchone()
            if not comp:
                raise RuntimeError("No existe competición NBA")
            comp_id = comp["id"]

            cur.execute(
                """
                select t.nombre,t.anio_inicio,t.anio_fin,t.activa,count(p.id) partidos,min(p.fecha_partido) min_fecha,max(p.fecha_partido) max_fecha
                from temporadas_baloncesto t
                left join partidos_baloncesto p on p.temporada_id=t.id and p.competicion_id=t.competicion_id
                where t.competicion_id=%s
                group by t.id,t.nombre,t.anio_inicio,t.anio_fin,t.activa
                order by t.anio_fin desc
                """,
                (comp_id,),
            )
            temporadas = cur.fetchall()

            cur.execute(
                """
                select
                  count(*) total,
                  max(fecha_partido) ultima_fecha,
                  count(*) filter (where source is null or source_game_id is null) sin_source,
                  count(*) filter (where hubo_overtime) overtime,
                  count(*) filter (where local_total <> local_q1+local_q2+local_q3+local_q4+coalesce(local_ot,0)) bad_local,
                  count(*) filter (where visitante_total <> visitante_q1+visitante_q2+visitante_q3+visitante_q4+coalesce(visitante_ot,0)) bad_visitante,
                  count(*) filter (where hubo_overtime is distinct from (coalesce(local_ot,0)>0 or coalesce(visitante_ot,0)>0)) bad_ot_flag
                from partidos_baloncesto where competicion_id=%s
                """,
                (comp_id,),
            )
            calidad = cur.fetchone()

            cur.execute(
                """
                select source, source_game_id, count(*) c
                from partidos_baloncesto
                where competicion_id=%s and source is not null and source_game_id is not null
                group by 1,2 having count(*) > 1
                order by c desc limit 20
                """,
                (comp_id,),
            )
            duplicados = cur.fetchall()

            cur.execute(
                """
                WITH apariciones AS (
                  SELECT e.id equipo_id,e.abreviatura,e.nombre equipo,p.id partido_id,p.fecha_partido,'local' localia,p.tipo_partido,
                         p.local_q1 puntos_q1,p.local_q2 puntos_q2,p.local_q3 puntos_q3,p.local_q4 puntos_q4,p.local_total puntos_total,
                         p.visitante_q1 recibidos_q1,p.visitante_q2 recibidos_q2,p.visitante_q3 recibidos_q3,p.visitante_q4 recibidos_q4,p.visitante_total recibidos_total,
                         p.hubo_overtime,p.source,p.source_game_id
                  FROM partidos_baloncesto p JOIN equipos e ON e.id=p.equipo_local_id WHERE p.competicion_id=%s
                  UNION ALL
                  SELECT e.id,e.abreviatura,e.nombre,p.id,p.fecha_partido,'visitante',p.tipo_partido,
                         p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4,p.visitante_total,
                         p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.local_total,
                         p.hubo_overtime,p.source,p.source_game_id
                  FROM partidos_baloncesto p JOIN equipos e ON e.id=p.equipo_visitante_id WHERE p.competicion_id=%s
                )
                SELECT * FROM apariciones ORDER BY equipo, fecha_partido DESC, partido_id DESC
                """,
                (comp_id, comp_id),
            )
            rows = cur.fetchall()

    by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_team[str(row["abreviatura"] or row["equipo"])] .append(dict(row))

    team_json: dict[str, Any] = {}
    warnings: list[str] = []
    for abbr, team_rows in sorted(by_team.items()):
        name = team_rows[0]["equipo"]
        local = [r for r in team_rows if r["localia"] == "local"]
        away = [r for r in team_rows if r["localia"] == "visitante"]
        warn = []
        if len(team_rows) < 30:
            warn.append(f"solo {len(team_rows)} partidos generales")
        if len(local) < 30:
            warn.append(f"solo {len(local)} partidos local")
        if len(away) < 30:
            warn.append(f"solo {len(away)} partidos visitante")
        if warn:
            warnings.append(f"{abbr} {name}: " + "; ".join(warn))
        team_json[abbr] = {
            "equipo": name,
            "conteos": {"general": len(team_rows), "local": len(local), "visitante": len(away)},
            "fecha_mas_reciente": str(team_rows[0]["fecha_partido"]) if team_rows else None,
            "advertencias": warn,
            "splits": {
                "general": {str(n): split_summary(team_rows, n) for n in (5, 10, 20, 30)},
                "local": {str(n): split_summary(local, n) for n in (5, 10, 20, 30)},
                "visitante": {str(n): split_summary(away, n) for n in (5, 10, 20, 30)},
            },
            "ultimos_30_partidos": [
                {k: (str(v) if isinstance(v, (date, datetime)) else v) for k, v in r.items() if k not in {"equipo_id"}}
                for r in team_rows[:30]
            ],
        }

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(team_json, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines = [
        "# Reporte de calidad de datos NBA",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Estado general",
        f"- Total partidos NBA: {calidad['total']}",
        f"- Última fecha cargada: {calidad['ultima_fecha']}",
        f"- Partidos sin source/source_game_id: {calidad['sin_source']}",
        f"- Partidos con overtime: {calidad['overtime']}",
        f"- Inconsistencias total local: {calidad['bad_local']}",
        f"- Inconsistencias total visitante: {calidad['bad_visitante']}",
        f"- Inconsistencias flag overtime: {calidad['bad_ot_flag']}",
        f"- Duplicados por source/source_game_id: {len(duplicados)}",
        "",
        "## Partidos por temporada NBA",
        "",
        "| Temporada | Activa | Partidos | Primera fecha | Última fecha |",
        "|---|---:|---:|---|---|",
    ]
    for t in temporadas:
        lines.append(f"| {t['nombre']} | {t['activa']} | {t['partidos']} | {t['min_fecha']} | {t['max_fecha']} |")
    lines += ["", "## Cobertura reciente por equipo", "", "| Equipo | General | Local | Visitante | Fecha reciente | Advertencias |", "|---|---:|---:|---:|---|---|"]
    for abbr, data in sorted(team_json.items()):
        c = data["conteos"]
        lines.append(f"| {abbr} - {data['equipo']} | {c['general']} | {c['local']} | {c['visitante']} | {data['fecha_mas_reciente']} | {'; '.join(data['advertencias']) or 'OK'} |")
    if warnings:
        lines += ["", "## Advertencias", ""] + [f"- {w}" for w in warnings]
    lines += ["", "## Archivos", f"- JSON por equipo: `{output_json}`", "- SQL base: `backend/scripts/sql/ultimos_30_partidos_nba_por_equipo.sql`", ""]
    output_md.write_text("\n".join(lines), encoding="utf-8")
    return {"markdown": str(output_md), "json": str(output_json), "equipos": len(team_json), "advertencias": len(warnings)}


def main() -> int:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--output-md", default="reports/data_quality/nba_data_quality.md")
    parser.add_argument("--output-json", default="reports/team_recent_form/nba_team_recent_form.json")
    args = parser.parse_args()
    result = build_reports(Path(args.output_md), Path(args.output_json))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

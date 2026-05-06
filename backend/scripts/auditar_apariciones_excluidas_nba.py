#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audita apariciones NBA excluidas por marcador 0/incompleto/inconsistente."""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / "backend" / ".env")
OUT_JSON = ROOT / "reports" / "data_quality" / "nba_excluded_appearances_audit.json"
OUT_MD = ROOT / "reports" / "data_quality" / "nba_excluded_appearances_audit.md"


def db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurada")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


EXCLUSION_CATEGORY_MESSAGES = {
    "FUTURE_OR_NOT_PLAYED": "Partido futuro o aún no jugado",
    "INCOMPLETE_SCORE": "Marcador parcial/incompleto",
    "INVALID_ZERO_ZERO": "Marcador 0-0 no válido para muestra histórica",
    "MISSING_QUARTERS": "Faltan cuartos o todos los cuartos están en cero",
    "TOTAL_MISMATCH": "La suma de cuartos no coincide con el total",
    "UNKNOWN_EXCLUSION_REASON": "Razón de exclusión desconocida",
}


def category(fecha: date, local_total: int, visitante_total: int, qs: list[int]) -> str | None:
    if fecha > date.today():
        return "FUTURE_OR_NOT_PLAYED"
    if local_total == 0 and visitante_total == 0:
        return "INVALID_ZERO_ZERO"
    if local_total <= 0 or visitante_total <= 0:
        return "INCOMPLETE_SCORE"
    if sum(qs[:4]) == 0 or sum(qs[5:9]) == 0:
        return "MISSING_QUARTERS"
    if sum(qs[:5]) > local_total or sum(qs[5:]) > visitante_total:
        return "TOTAL_MISMATCH"
    return None


def build() -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    sql = """
    select p.id partido_id,p.fecha_partido,el.abreviatura local_abrev,el.nombre local,
           ev.abreviatura visitante_abrev,ev.nombre visitante,
           p.local_q1,p.local_q2,p.local_q3,p.local_q4,p.local_ot,p.local_total,
           p.visitante_q1,p.visitante_q2,p.visitante_q3,p.visitante_q4,p.visitante_ot,p.visitante_total,
           p.hubo_overtime,p.tipo_partido,p.source,p.source_game_id
    from partidos_baloncesto p
    join equipos el on el.id=p.equipo_local_id
    join equipos ev on ev.id=p.equipo_visitante_id
    join competiciones_baloncesto c on c.id=p.competicion_id
    where lower(c.codigo)='nba'
    order by p.fecha_partido desc, p.id
    """
    rows = []
    with psycopg.connect(db_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            for r in cur.fetchall():
                d = dict(r)
                qs = [int(d[k] or 0) for k in ("local_q1","local_q2","local_q3","local_q4","local_ot","visitante_q1","visitante_q2","visitante_q3","visitante_q4","visitante_ot")]
                cat = category(d["fecha_partido"], int(d["local_total"] or 0), int(d["visitante_total"] or 0), qs)
                if not cat:
                    continue
                rz = EXCLUSION_CATEGORY_MESSAGES.get(cat, EXCLUSION_CATEGORY_MESSAGES["UNKNOWN_EXCLUSION_REASON"])
                item = {
                    "equipo_local": d["local"],
                    "equipo_visitante": d["visitante"],
                    "partido_id": str(d["partido_id"]),
                    "fecha": str(d["fecha_partido"]),
                    "local": d["local"],
                    "visitante": d["visitante"],
                    "puntos_local": d["local_total"],
                    "puntos_visitante": d["visitante_total"],
                    "puntos_por_cuarto": {
                        "local_q1": d["local_q1"], "local_q2": d["local_q2"], "local_q3": d["local_q3"], "local_q4": d["local_q4"], "local_ot": d["local_ot"],
                        "visitante_q1": d["visitante_q1"], "visitante_q2": d["visitante_q2"], "visitante_q3": d["visitante_q3"], "visitante_q4": d["visitante_q4"], "visitante_ot": d["visitante_ot"],
                    },
                    "razon_exclusion": rz,
                    "categoria_exclusion": cat,
                    "source": d["source"],
                    "source_game_id": d["source_game_id"],
                    "tipo_partido": d["tipo_partido"],
                }
                rows.append(item)
    counts = Counter(x["razon_exclusion"] for x in rows)
    classes = Counter(x["categoria_exclusion"] for x in rows)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_excluded_games": len(rows),
        "reason_counts": dict(counts),
        "classification_counts": dict(classes),
        "rows": rows,
    }


def write_reports(data: dict[str, Any]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Auditoría de apariciones NBA excluidas",
        "",
        f"Generado: {data['generated_at']}",
        f"Total partidos excluibles detectados: {data['total_excluded_games']}",
        "",
        "## Conteo por razón",
    ]
    for k, v in sorted(data["reason_counts"].items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Conteo por clasificación"]
    for k, v in sorted(data["classification_counts"].items()):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Detalle", "", "| Fecha | Local | Visitante | Marcador | Razón | Clasificación | Source | Source Game ID |", "|---|---|---|---:|---|---|---|---|"]
    for r in data["rows"][:500]:
        lines.append(f"| {r['fecha']} | {r['local']} | {r['visitante']} | {r['puntos_local']}-{r['puntos_visitante']} | {r['razon_exclusion']} | {r['categoria_exclusion']} | {r.get('source') or 'N/D'} | {r.get('source_game_id') or 'N/D'} |")
    if len(data["rows"]) > 500:
        lines.append(f"\n> Detalle truncado en Markdown a 500 filas. JSON contiene {len(data['rows'])} filas.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = build()
    write_reports(data)
    print(json.dumps({"json": str(OUT_JSON.relative_to(ROOT)), "markdown": str(OUT_MD.relative_to(ROOT)), "total": data["total_excluded_games"], "reason_counts": data["reason_counts"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

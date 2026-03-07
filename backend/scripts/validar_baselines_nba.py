#!/usr/bin/env python3
"""
Ejecutor reproducible de validación cuantitativa de baselines NBA.

Uso:
  cd backend
  python scripts/validar_baselines_nba.py --inicio 2024-01-01 --fin 2026-12-31

Requisitos:
- Variable de entorno DATABASE_URL configurada.
- psycopg instalado.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "reports" / "auditoria_baselines"


@dataclass
class QueryResult:
    nombre: str
    sql: str
    filas: list[dict[str, Any]]


def _q_universo() -> str:
    return """
    WITH base AS (
      SELECT id, creado_en, fecha_partido, mercado, lado, cuota, stake, ganancia, confianza_sistema, resultado
      FROM apuestas
      WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN %(inicio)s::date AND %(fin)s::date
    )
    SELECT
      COUNT(*) AS n_total,
      COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA','PUSH')) AS n_resueltas,
      MIN(COALESCE(fecha_partido::date, creado_en::date)) AS fecha_min,
      MAX(COALESCE(fecha_partido::date, creado_en::date)) AS fecha_max
    FROM base;
    """


def _q_global() -> str:
    return """
    WITH base AS (
      SELECT *
      FROM apuestas
      WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN %(inicio)s::date AND %(fin)s::date
        AND resultado IN ('GANADA','PERDIDA','PUSH')
    )
    SELECT
      COUNT(*) AS n_resueltas,
      COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
      COUNT(*) FILTER (WHERE resultado = 'GANADA') AS n_ganadas,
      ROUND(
        100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
        / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
        4
      ) AS win_rate_pct,
      ROUND(
        100.0 * COALESCE(SUM(ganancia), 0)
        / NULLIF(COALESCE(SUM(stake), 0), 0),
        4
      ) AS roi_pct,
      ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
      ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
    FROM base;
    """


def _q_confidence() -> str:
    return """
    WITH base AS (
      SELECT *
      FROM apuestas
      WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN %(inicio)s::date AND %(fin)s::date
        AND resultado IN ('GANADA','PERDIDA','PUSH')
    )
    SELECT
      UPPER(COALESCE(confianza_sistema, 'SIN_DATO')) AS confianza,
      COUNT(*) AS n_resueltas,
      COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
      COUNT(*) FILTER (WHERE resultado = 'GANADA') AS n_ganadas,
      ROUND(
        100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
        / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
        4
      ) AS win_rate_pct,
      ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
      ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
      ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
    FROM base
    GROUP BY 1
    ORDER BY CASE UPPER(COALESCE(confianza_sistema, 'SIN_DATO'))
      WHEN 'ALTA' THEN 1
      WHEN 'MEDIA' THEN 2
      WHEN 'BAJA' THEN 3
      ELSE 9
    END;
    """


def _q_odds() -> str:
    return """
    WITH base AS (
      SELECT *
      FROM apuestas
      WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN %(inicio)s::date AND %(fin)s::date
        AND resultado IN ('GANADA','PERDIDA','PUSH')
        AND cuota IS NOT NULL
    )
    SELECT
      CASE WHEN cuota > 2.0 THEN 'ODDS_GT_2_0' ELSE 'ODDS_LE_2_0' END AS segmento_odds,
      COUNT(*) AS n_resueltas,
      COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
      ROUND(
        100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
        / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
        4
      ) AS win_rate_pct,
      ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
      ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
      ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
    FROM base
    GROUP BY 1
    ORDER BY 1;
    """


def _q_markets() -> str:
    return """
    WITH base AS (
      SELECT *
      FROM apuestas
      WHERE COALESCE(fecha_partido::date, creado_en::date) BETWEEN %(inicio)s::date AND %(fin)s::date
        AND resultado IN ('GANADA','PERDIDA','PUSH')
    )
    SELECT
      CASE
        WHEN UPPER(COALESCE(mercado, '')) IN ('Q1','Q2','Q3','Q4') THEN 'QUARTER_MARKETS'
        WHEN UPPER(COALESCE(mercado, '')) IN ('COMPLETO','FULL','FULL_GAME') THEN 'FULL_GAME_MARKETS'
        ELSE 'OTROS'
      END AS segmento_mercado,
      COUNT(*) AS n_resueltas,
      COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')) AS n_winloss,
      ROUND(
        100.0 * COUNT(*) FILTER (WHERE resultado = 'GANADA')
        / NULLIF(COUNT(*) FILTER (WHERE resultado IN ('GANADA','PERDIDA')), 0),
        4
      ) AS win_rate_pct,
      ROUND(100.0 * COALESCE(SUM(ganancia),0) / NULLIF(COALESCE(SUM(stake),0),0), 4) AS roi_pct,
      ROUND(COALESCE(SUM(stake),0), 2) AS stake_total,
      ROUND(COALESCE(SUM(ganancia),0), 2) AS ganancia_total
    FROM base
    GROUP BY 1
    ORDER BY 1;
    """


def run(inicio: str, fin: str) -> Path:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "backend" / ".env")

    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL no configurada en entorno/.env")

    queries = [
        ("universo", _q_universo()),
        ("global_winrate_roi", _q_global()),
        ("confidence_segmentado", _q_confidence()),
        ("odds_segmentado", _q_odds()),
        ("markets_segmentado", _q_markets()),
    ]

    resultados: list[QueryResult] = []
    with psycopg.connect(url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for nombre, sql in queries:
                cur.execute(sql, {"inicio": inicio, "fin": fin})
                filas = [dict(r) for r in cur.fetchall()]
                resultados.append(QueryResult(nombre=nombre, sql=sql.strip(), filas=filas))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"baseline_nba_{inicio}_{fin}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(
        json.dumps(
            [asdict(r) for r in resultados],
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inicio", required=True, help="YYYY-MM-DD")
    p.add_argument("--fin", required=True, help="YYYY-MM-DD")
    args = p.parse_args()

    out = run(args.inicio, args.fin)
    print(f"OK: resultados en {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Aplica vistas etapa 4 del bloque 06 y corre validaciones reproducibles."""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "backend" / "scripts" / "sql" / "analitica_bloque_06"
REPORT_DIR = ROOT / "reports" / "auditoria_baselines"


def run() -> Path:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "backend" / ".env")
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL no configurada")

    sql_files = [
        "01_base_unificada_v1.sql",
        "03_vw_perf_market_odds_confidence.sql",
        "04_vw_policy_odds_compliance.sql",
        "06_vw_calibration_scorecard.sql",
        "07_vw_stake_and_risk_consistency.sql",
    ]
    validation_file = SQL_DIR / "08_validaciones_vistas_calibration_risk.sql"
    validations = [q.strip() for q in validation_file.read_text(encoding="utf-8").split(";") if q.strip()]

    out: dict[str, object] = {
        "applied_sql": [str(SQL_DIR / f) for f in sql_files],
        "validation_file": str(validation_file),
        "results": {},
    }

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for sql_name in sql_files:
                cur.execute((SQL_DIR / sql_name).read_text(encoding="utf-8"))
            conn.commit()

            for idx, query in enumerate(validations, start=1):
                cur.execute(query)
                out["results"][f"q{idx}"] = [dict(r) for r in cur.fetchall()]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / "vistas_bloque_06_etapa4_validaciones_20260307T0220Z.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    print(f"OK: {run()}")

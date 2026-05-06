# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.generar_analisis_partido_nba import validate_markets

ROOT = Path(__file__).resolve().parents[2]


def _valid_market(**overrides):
    data = {
        "market": "FULL_GAME_TOTAL",
        "line": 218.5,
        "over_odds": 1.91,
        "under_odds": 1.91,
        "source": "ESPN/DraftKings close",
        "source_type": "REAL_MARKET",
        "source_url": None,
        "notes": None,
    }
    data.update(overrides)
    return data


def test_validate_markets_accepts_real_market():
    validate_markets([_valid_market()])


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("source_type", None, "source_type es obligatorio"),
        ("source_type", "BAD_TYPE", "source_type inválido"),
        ("market", "BAD_MARKET", "market no soportado"),
        ("line", "218.5", "line debe ser numérico"),
        ("over_odds", "1.91", "over_odds debe ser numérico"),
        ("under_odds", "1.91", "under_odds debe ser numérico"),
        ("source", "", "source es obligatorio"),
    ],
)
def test_validate_markets_rejects_invalid_fields(field, value, error):
    market = _valid_market(**{field: value})
    if value is None:
        market.pop(field, None)
    with pytest.raises(ValueError, match=error):
        validate_markets([market])


def test_validate_markets_requires_notes_for_non_real_line():
    market = _valid_market(
        market="Q1_TOTAL",
        source_type="TECHNICAL_ESTIMATE",
        source="manual/technical",
        notes=None,
        over_odds=None,
        under_odds=None,
    )
    with pytest.raises(ValueError, match="notes es obligatorio"):
        validate_markets([market])


def test_cli_still_generates_analysis_with_valid_markets(tmp_path):
    markets_path = tmp_path / "markets.json"
    markets_path.write_text(
        json.dumps({"markets": [_valid_market()]}),
        encoding="utf-8",
    )
    cmd = [
        sys.executable,
        str(ROOT / "backend" / "scripts" / "generar_analisis_partido_nba.py"),
        "--home",
        "SAS",
        "--away",
        "MIN",
        "--date",
        "2026-05-05",
        "--markets",
        str(markets_path),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["json"].endswith("san_antonio_spurs_vs_minnesota_timberwolves_2026-05-05.json")
    assert out["markdown"].endswith("san_antonio_spurs_vs_minnesota_timberwolves_2026-05-05.md")

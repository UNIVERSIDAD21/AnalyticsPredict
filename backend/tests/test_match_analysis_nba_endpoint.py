# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _payload(**market_overrides):
    market = {
        "market": "FULL_GAME_TOTAL",
        "line": 218.5,
        "over_odds": 1.91,
        "under_odds": 1.91,
        "source": "ESPN/DraftKings close",
        "source_type": "REAL_MARKET",
        "source_url": None,
        "notes": None,
    }
    market.update(market_overrides)
    return {
        "home": "San Antonio Spurs",
        "away": "Minnesota Timberwolves",
        "date": "2026-05-05",
        "markets": [market],
    }


def test_match_analysis_valid_request_returns_contract():
    resp = client.post("/api/nba/match-analysis", json=_payload())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    for key in (
        "metadata",
        "teams",
        "samples",
        "combined_metrics",
        "market_evaluations",
        "data_quality",
        "warnings",
        "external_summary",
        "policy",
    ):
        assert key in data
    assert data["policy"] == {
        "no_picks": True,
        "no_stake": True,
        "no_betting_recommendations": True,
    }
    assert isinstance(data["warnings"], list)
    for warning in data["warnings"]:
        assert {"code", "severity", "message", "scope"}.issubset(warning.keys())


def test_match_analysis_missing_source_type_returns_422():
    payload = _payload()
    payload["markets"][0].pop("source_type")
    resp = client.post("/api/nba/match-analysis", json=payload)
    assert resp.status_code == 422


def test_match_analysis_invalid_source_type_returns_422():
    resp = client.post("/api/nba/match-analysis", json=_payload(source_type="BAD_TYPE"))
    assert resp.status_code == 422


def test_match_analysis_invalid_market_returns_422():
    resp = client.post("/api/nba/match-analysis", json=_payload(market="BAD_MARKET"))
    assert resp.status_code == 422


def test_match_analysis_non_numeric_line_returns_422():
    resp = client.post("/api/nba/match-analysis", json=_payload(line="218.5"))
    assert resp.status_code == 422


def test_match_analysis_non_real_line_without_notes_returns_422():
    resp = client.post(
        "/api/nba/match-analysis",
        json=_payload(
            market="Q1_TOTAL",
            line=54.5,
            over_odds=None,
            under_odds=None,
            source="manual/technical",
            source_type="TECHNICAL_ESTIMATE",
            notes=None,
        ),
    )
    assert resp.status_code == 422


def test_match_analysis_technical_line_with_notes_has_structured_market_warning():
    resp = client.post(
        "/api/nba/match-analysis",
        json=_payload(
            market="Q1_TOTAL",
            line=54.5,
            over_odds=None,
            under_odds=None,
            source="manual/technical",
            source_type="TECHNICAL_ESTIMATE",
            notes="Línea técnica para validación; no mercado real.",
        ),
    )
    assert resp.status_code == 200, resp.text
    market_warnings = resp.json()["market_evaluations"][0]["advertencias"]
    assert any(w["code"] == "NON_REAL_MARKET_LINE" for w in market_warnings)
    for warning in market_warnings:
        assert {"code", "severity", "message", "scope"}.issubset(warning.keys())

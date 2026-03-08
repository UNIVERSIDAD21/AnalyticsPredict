# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from explicabilidad.contrato import (
    QualityCoherenceError,
    adaptar_legacy,
    construir_contrato,
)


def _pred_base(sport: str = "NBA"):
    return {
        "prediction_id": "58d648d6-b9b6-4d46-9c5b-c3427b5b4cc8",
        "sport": sport,
        "home_team": "Home",
        "away_team": "Away",
        "game_date": datetime.now(timezone.utc),
        "league": "NBA" if sport == "NBA" else "Premier League",
        "value": 110.0 if sport == "NBA" else 2.6,
        "unit": "points" if sport == "NBA" else "goals",
        "line": 108.5 if sport == "NBA" else 2.5,
        "recommendation": "over",
        "confidence_numeric": 84.0,
        "interval_lower": 106.0 if sport == "NBA" else 2.1,
        "interval_upper": 114.0 if sport == "NBA" else 3.0,
        "model_version": "test_model",
        "backend_version": "api-test",
    }


def _factors():
    return [
        {"factor_name": "pace_recent", "contribution": 22.5, "value": 1.1, "description": "Ritmo reciente"},
        {"factor_name": "off_rating", "contribution": 18.0, "value": 1.0, "description": "Ofensiva"},
    ]


def test_nivel_a_sin_warnings_contrato_limpio() -> None:
    pred = _pred_base("NBA")
    scorecard = {"score_final": 94.0, "nivel": "A"}
    contrato = construir_contrato(pred, scorecard, [], _factors())

    assert contrato.data_quality.level == "A"
    assert contrato.prediction.confidence.level == "high"
    assert contrato.explanation.warnings == []


def test_nivel_b_con_warning_drift_reduce_confidence() -> None:
    pred = _pred_base("FOOTBALL")
    scorecard = {"score_final": 78.0, "nivel": "B"}
    alertas = [{"alert_id": "DQ-HIGH-05", "severity": "ALTA", "title": "Drift naranja"}]

    contrato = construir_contrato(pred, scorecard, alertas, _factors())

    assert contrato.data_quality.level == "B"
    assert contrato.prediction.confidence.level == "medium"
    assert any(w.type == "drift" for w in contrato.explanation.warnings)


def test_nivel_c_disclaimer_fuerte_confianza_baja() -> None:
    pred = _pred_base("FOOTBALL")
    scorecard = {"score_final": 62.0, "nivel": "C"}

    contrato = construir_contrato(pred, scorecard, [], _factors())

    assert contrato.data_quality.level == "C"
    assert contrato.prediction.confidence.level == "low"
    assert any("ADVERTENCIA" in w.message for w in contrato.explanation.warnings)


def test_hardcheck_nivel_a_warning_critico_lanza_error() -> None:
    pred = _pred_base("NBA")
    scorecard = {"score_final": 95.0, "nivel": "A"}
    alertas = [{"alert_id": "DQ-CRIT-02", "severity": "CRITICA", "title": "Regla crítica"}]

    with pytest.raises(QualityCoherenceError):
        construir_contrato(pred, scorecard, alertas, _factors())


def test_adaptar_legacy_no_pierde_minimos() -> None:
    pred = _pred_base("NBA")
    scorecard = {"score_final": 90.0, "nivel": "A"}

    contrato = construir_contrato(pred, scorecard, [], _factors())
    legacy = adaptar_legacy(contrato)

    assert legacy["id"]
    assert legacy["confianza"] is not None
    assert legacy["calidad_nivel"] in {"A", "B", "C"}
    assert legacy["metadata"]["is_legacy_contract"] is True

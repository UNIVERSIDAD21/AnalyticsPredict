# -*- coding: utf-8 -*-
"""Tests de integración y coherencia del pipeline calidad -> explicabilidad.

Importante de gobierno:
- Si falla un hard-check de coherencia, se considera bug nuevo de bloque 08.
- Si falla por falta de datos reales de producción, documentar como deuda bloque 05.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import app
from calidad import alertas, scorecard
from explicabilidad.contrato import QualityCoherenceError, construir_contrato


class DummyConn:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _pred_base(sport: str = "NBA") -> dict:
    return {
        "prediction_id": "58d648d6-b9b6-4d46-9c5b-c3427b5b4cc8",
        "sport": sport,
        "home_team": "HOME",
        "away_team": "AWAY",
        "game_date": datetime.now(timezone.utc),
        "league": "NBA" if sport == "NBA" else "Premier League",
        "value": 110.0 if sport == "NBA" else 2.4,
        "unit": "points" if sport == "NBA" else "goals",
        "line": 108.5 if sport == "NBA" else 2.5,
        "recommendation": "over",
        "confidence_numeric": 88.0,
        "interval_lower": 106.0 if sport == "NBA" else 2.0,
        "interval_upper": 114.0 if sport == "NBA" else 2.9,
        "model_version": "test-model",
        "backend_version": "api-test",
    }


def _factors() -> list[dict]:
    return [
        {"factor_name": "factor_1", "contribution": 30.0, "value": 1.0, "description": "impacto 1"},
        {"factor_name": "factor_2", "contribution": 20.0, "value": 0.8, "description": "impacto 2"},
    ]


def test_e2e_pipeline_nba_ejecutar_reglas_score_alerta_contrato(monkeypatch: pytest.MonkeyPatch) -> None:
    """E2E con mocks: ejecutar_reglas -> calcular_scorecard -> generar_alertas -> construir_contrato."""
    conn = DummyConn()

    # ejecutar_reglas
    monkeypatch.setattr(scorecard, "_reglas_por_dominio", lambda _d: [])
    monkeypatch.setattr(scorecard, "_calcular_drift_signal_level", lambda *_: "none")
    res_reglas = scorecard.ejecutar_reglas(conn, "NBA", date(2026, 3, 8))
    assert res_reglas["domain"] == "NBA"

    # calcular_scorecard
    resultados = [
        {
            "rule_id": "NBA-COMP-01",
            "category": "Completitud",
            "severity": "Crítica",
            "failed_rows": 0,
            "total_rows": 100,
            "fail_rate": 0.0,
            "drift_signal_level": "none",
        },
        {
            "rule_id": "NBA-LOG-02",
            "category": "IntegridadLogica",
            "severity": "Alta",
            "failed_rows": 1,
            "total_rows": 100,
            "fail_rate": 0.01,
            "drift_signal_level": "none",
        },
    ]
    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: resultados)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)
    res_score = scorecard.calcular_scorecard(conn, "NBA", date(2026, 3, 8))
    assert res_score["nivel"] in {"A", "B", "C"}

    # generar_alertas
    monkeypatch.setattr(alertas, "_evaluar_alertas", lambda *_args, **_kwargs: [])
    res_alertas = alertas.generar_alertas(conn, res_score, "NBA", date(2026, 3, 8))
    assert res_alertas["domain"] == "NBA"

    # construir contrato
    contrato = construir_contrato(_pred_base("NBA"), res_score, [], _factors())
    assert contrato.sport == "NBA"


def test_coherencia_nivel_c_nunca_confianza_alta() -> None:
    score = {"score_final": 60.0, "nivel": "C"}
    contrato = construir_contrato(_pred_base("NBA"), score, [], _factors())
    assert contrato.prediction.confidence.level != "high", (
        "BUG B08: nivel C no puede publicar confianza alta"
    )


def test_hardcheck_a_warning_critico_siempre_error() -> None:
    score = {"score_final": 95.0, "nivel": "A"}
    alertas_criticas = [{"alert_id": "DQ-CRIT-02", "severity": "CRITICA", "title": "Regla crítica"}]

    with pytest.raises(QualityCoherenceError):
        construir_contrato(_pred_base("NBA"), score, alertas_criticas, _factors())


def test_deuda_visible_futbol_drift_incluye_warning_drift() -> None:
    score = {"score_final": 72.0, "nivel": "B"}
    alerts = [{"alert_id": "DQ-CRIT-03", "severity": "CRITICA", "title": "Drift rojo sostenido"}]

    contrato = construir_contrato(_pred_base("FOOTBALL"), score, alerts, _factors())

    assert any(w.type == "drift" for w in contrato.explanation.warnings), (
        "Si falla con datos reales, revisar deuda B05 (drift runtime) antes de culpar B08"
    )


def test_smoke_endpoint_alertas_http_200() -> None:
    client = TestClient(app)
    resp = client.get("/api/calidad/alertas")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("exito") is True
    assert "alertas" in data


def test_smoke_endpoint_explicacion_http_200_o_422_o_404_featureflag() -> None:
    client = TestClient(app)
    resp = client.get("/api/prediccion/no-existe/explicacion")
    # 404 es válido cuando FEATURE_CONTRATO_EXPLICACION_V1=false (rollout gradual B08).
    assert resp.status_code in {200, 422, 404}


def test_coherencia_scorecard_critica_activa_no_nivel_a(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    resultados = [
        {
            "rule_id": "NBA-COMP-01",
            "category": "Completitud",
            "severity": "Crítica",
            "failed_rows": 1,
            "total_rows": 1000,
            "fail_rate": 0.001,
            "drift_signal_level": "none",
        }
    ]
    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: resultados)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)

    out = scorecard.calcular_scorecard(conn, "NBA", date(2026, 3, 8))
    assert out["nivel"] != "A", "BUG B08: crítica activa no puede dejar nivel A"


def test_alerta_critica_por_regla_critica_activa(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    monkeypatch.setattr(alertas, "_query_value", lambda *_args, **_kwargs: 0.0)
    monkeypatch.setattr(alertas, "_obtener_criticas_activas", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(alertas, "_drift_consecutivo_rojo", lambda *_args, **_kwargs: 0)

    candidates = alertas._evaluar_alertas(  # pylint: disable=protected-access
        conn,
        {"nivel": "B", "score_final": 80.0, "criticas_activas": 1, "drift_signal_level": "none"},
        "NBA",
        date(2026, 3, 8),
    )
    assert any(c.alert_id == "DQ-CRIT-02" for c in candidates)

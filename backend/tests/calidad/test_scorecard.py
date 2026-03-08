# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date

import pytest

from calidad import scorecard


class DummyConn:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _result(
    rule_id: str,
    category: str,
    severity: str,
    failed_rows: int,
    total_rows: int,
    fail_rate: float,
    drift_signal_level: str = "none",
):
    return {
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "failed_rows": failed_rows,
        "total_rows": total_rows,
        "fail_rate": fail_rate,
        "drift_signal_level": drift_signal_level,
    }


def test_formula_con_datos_sinteticos(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()

    data = [
        _result("NBA-COMP-01", "Completitud", "Crítica", 0, 100, 0.00),
        _result("NBA-LOG-02", "IntegridadLogica", "Alta", 1, 100, 0.01),
        _result("NBA-TMP-01", "IntegridadTemporal", "Media", 2, 100, 0.02),
        _result("NBA-RNG-01", "RangosOutliers", "Alta", 1, 100, 0.01),
        _result("NBA-FRSH-01", "Freshness", "Alta", 0, 100, 0.00),
        _result("NBA-COV-01", "Coverage", "Media", 3, 100, 0.03),
    ]

    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: data)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)

    result = scorecard.calcular_scorecard(conn, "NBA", date(2026, 3, 8))

    assert 0 <= result["score_final"] <= 100
    assert result["nivel"] in {"A", "B", "C"}
    assert isinstance(result["componentes"], dict)
    assert conn.commits == 1


def test_override_critico_maximo_b(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()

    data = [
        _result("NBA-COMP-01", "Completitud", "Crítica", 1, 1000, 0.001),
        _result("NBA-LOG-02", "IntegridadLogica", "Alta", 0, 1000, 0.0),
        _result("NBA-TMP-01", "IntegridadTemporal", "Media", 0, 1000, 0.0),
        _result("NBA-RNG-01", "RangosOutliers", "Alta", 0, 1000, 0.0),
        _result("NBA-FRSH-01", "Freshness", "Alta", 0, 1000, 0.0),
        _result("NBA-COV-01", "Coverage", "Media", 0, 1000, 0.0),
    ]

    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: data)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)

    result = scorecard.calcular_scorecard(conn, "NBA", date(2026, 3, 8))

    assert result["criticas_activas"] >= 1
    assert result["nivel"] != "A"


def test_penalizacion_drift_rojo_futbol(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()

    data = [
        _result("FUT-LOG-02", "IntegridadLogica", "Alta", 1, 1000, 0.001, "red"),
        _result("FUT-TMP-01", "IntegridadTemporal", "Media", 0, 1000, 0.0, "red"),
        _result("FUT-RNG-01", "RangosOutliers", "Alta", 0, 1000, 0.0, "red"),
        _result("FUT-FRSH-01", "Freshness", "Alta", 0, 1000, 0.0, "red"),
        _result("FUT-COV-01", "Coverage", "Media", 0, 1000, 0.0, "red"),
        _result("FUT-COMP-01", "Completitud", "Crítica", 0, 1000, 0.0, "red"),
    ]

    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: data)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)

    result = scorecard.calcular_scorecard(conn, "FUTBOL", date(2026, 3, 8))

    assert result["drift_penalty"] == 15.0
    assert result["nivel"] in {"B", "C"}


def test_caso_base_limpio_nivel_a(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()

    data = [
        _result("NBA-COMP-01", "Completitud", "Crítica", 0, 1000, 0.0),
        _result("NBA-LOG-02", "IntegridadLogica", "Alta", 0, 1000, 0.0),
        _result("NBA-TMP-01", "IntegridadTemporal", "Media", 0, 1000, 0.0),
        _result("NBA-RNG-01", "RangosOutliers", "Alta", 0, 1000, 0.0),
        _result("NBA-FRSH-01", "Freshness", "Alta", 0, 1000, 0.0),
        _result("NBA-COV-01", "Coverage", "Media", 0, 1000, 0.0),
    ]

    monkeypatch.setattr(scorecard, "_leer_resultados_periodo", lambda *_: data)
    monkeypatch.setattr(scorecard, "_persistir_scorecard", lambda *_: None)

    result = scorecard.calcular_scorecard(conn, "NBA", date(2026, 3, 8))

    assert result["nivel"] == "A"
    assert result["score_final"] == 100.0

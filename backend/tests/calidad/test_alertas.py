# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date

import pytest

from calidad.alertas import AlertCandidate, generar_alertas, _evaluar_alertas


class DummyConn:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_genera_critica_por_nivel_c(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    inserted = []

    def _fake_eval(*_args, **_kwargs):
        return [
            AlertCandidate(
                alert_id="DQ-CRIT-01",
                severity="CRITICA",
                component="Scorecard",
                title="Nivel C en NBA",
                condition_text="Scorecard NBA en nivel C",
                incident_key="nba_nivel_c",
                root_cause="scorecard",
            )
        ]

    monkeypatch.setattr("calidad.alertas._evaluar_alertas", _fake_eval)
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("calidad.alertas._upsert_alert", lambda _c, _d, _p, cand, emitted, _r: inserted.append((cand.alert_id, emitted)))

    result = generar_alertas(conn, {"nivel": "C", "score_final": 60}, "NBA", date(2026, 3, 8))

    assert result["emitidas"] == 1
    assert inserted[0][0] == "DQ-CRIT-01"


def test_anti_ruido_no_duplica_misma_alerta_mismo_periodo(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    storage = {}

    candidate = AlertCandidate(
        alert_id="DQ-MED-01",
        severity="MEDIA",
        component="Coverage",
        title="Cobertura baja NBA",
        condition_text="Cobertura baja",
        incident_key="nba_coverage_low",
        root_cause="coverage",
    )

    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [candidate])
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)

    def _fake_upsert(_conn, domain, periodo, cand, emitted, reincidente):
        key = (periodo, domain, cand.alert_id, cand.incident_key)
        storage[key] = {"emitted": emitted, "reincidente": reincidente}

    monkeypatch.setattr("calidad.alertas._upsert_alert", _fake_upsert)

    payload = {"nivel": "B", "score_final": 78}
    generar_alertas(conn, payload, "NBA", date(2026, 3, 8))
    generar_alertas(conn, payload, "NBA", date(2026, 3, 8))

    assert len(storage) == 1


def test_alerta_drift_critica_3_dias_consecutivos(monkeypatch: pytest.MonkeyPatch) -> None:
    class ConnNoop:
        pass

    conn = ConnNoop()

    monkeypatch.setattr("calidad.alertas._obtener_criticas_activas", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr("calidad.alertas._drift_consecutivo_rojo", lambda *_args, **_kwargs: 3)
    monkeypatch.setattr("calidad.alertas._query_value", lambda *_args, **_kwargs: 0.0)

    candidates = _evaluar_alertas(
        conn,
        {"nivel": "B", "score_final": 75, "drift_signal_level": "red", "criticas_activas": 0},
        "FUTBOL",
        date(2026, 3, 8),
    )

    ids = {c.alert_id for c in candidates}
    assert "DQ-CRIT-03" in ids


def test_hard_check_nivel_a_warning_critico(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [])

    with pytest.raises(ValueError):
        generar_alertas(
            conn,
            {"nivel": "A", "score_final": 95, "warning_critico_activo": True},
            "NBA",
            date(2026, 3, 8),
        )


def test_drift_yellow_con_cooldown_no_reemite(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    c = AlertCandidate(
        alert_id="DQ-MED-05",
        severity="MEDIA",
        component="Drift",
        title="Drift amarillo fútbol",
        condition_text="Drift amarillo detectado",
        incident_key="fut_drift_yellow",
        root_cause="drift_runtime",
    )
    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [c])
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("calidad.alertas._get_cooldown_activo", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("calidad.alertas._es_reincidente_14d", lambda *_args, **_kwargs: True)

    emitted = []
    monkeypatch.setattr("calidad.alertas._upsert_alert", lambda _c, _d, _p, _cand, emit, _r: emitted.append(emit))

    out = generar_alertas(conn, {"nivel": "B", "score_final": 77}, "FUTBOL", date(2026, 3, 8))
    assert out["emitidas"] == 0
    assert emitted == [False]


def test_drift_orange_cooldown_1_no_reemite_mismo_periodo(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    c = AlertCandidate(
        alert_id="DQ-HIGH-05",
        severity="ALTA",
        component="Drift",
        title="Drift naranja fútbol",
        condition_text="Drift naranja activo",
        incident_key="fut_drift_orange",
        root_cause="drift_runtime",
    )
    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [c])
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)

    seq = {"n": 0}
    def _cooldown(*_args, **_kwargs):
        seq["n"] += 1
        return seq["n"] > 1

    monkeypatch.setattr("calidad.alertas._get_cooldown_activo", _cooldown)
    monkeypatch.setattr("calidad.alertas._es_reincidente_14d", lambda *_args, **_kwargs: False)

    emitted = []
    monkeypatch.setattr("calidad.alertas._upsert_alert", lambda _c, _d, _p, _cand, emit, _r: emitted.append(emit))

    payload = {"nivel": "B", "score_final": 80}
    generar_alertas(conn, payload, "FUTBOL", date(2026, 3, 8), cooldown_config={"DQ-HIGH-05": 1})
    generar_alertas(conn, payload, "FUTBOL", date(2026, 3, 8), cooldown_config={"DQ-HIGH-05": 1})
    assert emitted == [True, False]


def test_dq_crit_03_ignora_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    c = AlertCandidate(
        alert_id="DQ-CRIT-03",
        severity="CRITICA",
        component="Drift",
        title="Drift rojo sostenido",
        condition_text="3+ días rojo",
        incident_key="fut_drift_red_3d",
        root_cause="drift_runtime",
    )
    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [c])
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("calidad.alertas._get_cooldown_activo", lambda *_args, **_kwargs: False)
    monkeypatch.setattr("calidad.alertas._es_reincidente_14d", lambda *_args, **_kwargs: True)

    emitted = []
    monkeypatch.setattr("calidad.alertas._upsert_alert", lambda _c, _d, _p, _cand, emit, _r: emitted.append(emit))

    out = generar_alertas(conn, {"nivel": "C", "score_final": 60}, "FUTBOL", date(2026, 3, 8), cooldown_config={"DQ-CRIT-03": 99})
    assert out["emitidas"] == 1
    assert emitted == [True]


def test_reincidencia_marca_true(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = DummyConn()
    c = AlertCandidate(
        alert_id="DQ-MED-05",
        severity="MEDIA",
        component="Drift",
        title="Drift amarillo fútbol",
        condition_text="Drift amarillo detectado",
        incident_key="fut_drift_yellow",
        root_cause="drift_runtime",
    )
    monkeypatch.setattr("calidad.alertas._evaluar_alertas", lambda *_args, **_kwargs: [c])
    monkeypatch.setattr("calidad.alertas._debounce_ok", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("calidad.alertas._get_cooldown_activo", lambda *_args, **_kwargs: False)
    monkeypatch.setattr("calidad.alertas._es_reincidente_14d", lambda *_args, **_kwargs: True)

    rec = []
    monkeypatch.setattr("calidad.alertas._upsert_alert", lambda _c, _d, _p, _cand, _emit, reinc: rec.append(reinc))

    generar_alertas(conn, {"nivel": "B", "score_final": 78}, "FUTBOL", date(2026, 3, 8))
    assert rec == [True]

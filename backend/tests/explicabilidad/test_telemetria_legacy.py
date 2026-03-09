# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


class _DummyCursor:
    def __init__(self):
        self.calls = []
        self._fetchone = None
        self._fetchall = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "FROM analytics.contrato_uso_log" in sql:
            self._fetchall = []

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


class _DummyConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self, **_kwargs):
        return self._cursor

    def commit(self):
        return None

    def rollback(self):
        return None


class _DummyPool:
    def __init__(self, cursor):
        self._cursor = cursor

    def connection(self):
        return _DummyConn(self._cursor)


def _patch_basics(monkeypatch, rutas_explicabilidad):
    pred = {
        "prediction_id": "58d648d6-b9b6-4d46-9c5b-c3427b5b4cc8",
        "sport": "NBA",
        "home_team": "A",
        "away_team": "B",
        "game_date": "2026-03-09T00:00:00Z",
        "league": "NBA",
        "line": 108.5,
        "value": 110.0,
        "recommendation": "over",
        "confidence_numeric": 80.0,
        "interval_lower": 106.0,
        "interval_upper": 114.0,
        "unit": "points",
        "model_version": "m",
        "backend_version": "b",
    }
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_args, **_kwargs: pred)
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_args, **_kwargs: {"score_final": 90.0, "nivel": "A"})
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])


def test_header_deprecation_aparece_en_legacy(monkeypatch):
    from api import rutas_explicabilidad

    cursor = _DummyCursor()
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _DummyPool(cursor))
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _name: True)
    _patch_basics(monkeypatch, rutas_explicabilidad)

    client = TestClient(app)
    resp = client.get("/api/prediccion/abc/explicacion?version=legacy")

    assert resp.status_code == 200
    assert resp.headers.get("Deprecation") == "true"
    assert resp.headers.get("Sunset")
    assert "successor-version" in (resp.headers.get("Link") or "")


def test_header_deprecation_no_aparece_en_v1(monkeypatch):
    from api import rutas_explicabilidad

    cursor = _DummyCursor()
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _DummyPool(cursor))
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _name: True)
    _patch_basics(monkeypatch, rutas_explicabilidad)

    client = TestClient(app)
    resp = client.get("/api/prediccion/abc/explicacion?version=v1")

    assert resp.status_code == 200
    assert resp.headers.get("Deprecation") is None


def test_contador_uso_se_registra(monkeypatch):
    from api import rutas_explicabilidad

    cursor = _DummyCursor()
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _DummyPool(cursor))
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _name: True)
    _patch_basics(monkeypatch, rutas_explicabilidad)

    client = TestClient(app)
    resp = client.get("/api/prediccion/abc/explicacion?version=legacy")
    assert resp.status_code == 200

    inserts = [c for c in cursor.calls if "INSERT INTO analytics.contrato_uso_log" in c[0]]
    assert len(inserts) >= 1

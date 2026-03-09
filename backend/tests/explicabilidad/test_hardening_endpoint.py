# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
import pytest
from psycopg import OperationalError

from app import app


def _pred(**overrides):
    base = {
        "prediction_id": "abc",
        "sport": "NBA",
        "home_team": "A",
        "away_team": "B",
        "game_date": datetime.now(timezone.utc),
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
        "calibration_source": "p_calibrada",
        "market_valid": True,
    }
    base.update(overrides)
    return base


class _PoolFail:
    def connection(self):
        raise OperationalError("db down")


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self, **kwargs):
        return self

    def execute(self, *args, **kwargs):
        return None

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def commit(self):
        return None


class _Pool:
    def connection(self):
        return _Conn()


def test_prediction_id_no_existe_404(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: None)
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)

    c = TestClient(app)
    r = c.get("/api/prediccion/nope/explicacion")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PREDICTION_NOT_FOUND"


def test_feature_off_v1_404(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: False)

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "FEATURE_DISABLED"


def test_scorecard_ausente_200_unknown(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: _pred())
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_: None)
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 200
    body = r.json()
    assert body["data_quality"]["level"] == "UNKNOWN"
    assert any(w["type"] == "no_scorecard" for w in body["explanation"]["warnings"])


def test_p_calibrada_null_usa_p_raw_y_debt_flag(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: _pred(calibration_source="p_raw", confidence_numeric=45.0))
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_: {"score_final": 88, "nivel": "A"})
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 200
    debt = r.json()["metadata"]["debt_flags"]
    assert "calibracion_ausente" in debt


def test_mercado_desconocido_200_explanation_vacia(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: _pred(market_valid=False))
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_: {"score_final": 80, "nivel": "B"})
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 200
    assert r.json()["explanation"]["top_factors"] == []
    assert "mercado_desconocido" in r.json()["metadata"]["debt_flags"]


def test_quality_coherence_error_422(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: _pred())
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_: {"score_final": 95, "nivel": "A"})
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [{"alert_id": "DQ-CRIT-02", "severity": "CRITICA", "title": "Regla crítica"}])

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "QUALITY_COHERENCE_ERROR"


def test_db_no_disponible_503(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _PoolFail())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: True)

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=v1")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_legacy_con_flag_off_retorna_200(monkeypatch):
    from api import rutas_explicabilidad
    monkeypatch.setattr(rutas_explicabilidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_explicabilidad, "flag_activo", lambda _n: False)
    monkeypatch.setattr(rutas_explicabilidad, "_fetch_prediccion", lambda *_: _pred())
    monkeypatch.setattr(rutas_explicabilidad, "obtener_scorecard_actual", lambda *_: {"score_final": 80, "nivel": "B"})
    monkeypatch.setattr(rutas_explicabilidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])

    c = TestClient(app)
    r = c.get("/api/prediccion/x/explicacion?version=legacy")
    assert r.status_code == 200
    assert r.json()["exito"] is True

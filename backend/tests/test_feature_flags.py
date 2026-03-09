# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
import pytest

from app import app
from calidad import scorecard


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, row):
        self._row = row

    def cursor(self):
        return _FakeCursor(self._row)


def test_flag_false_scorecard_retorna_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scorecard, "flag_activo", lambda _name: False)
    conn = _FakeConn(None)

    out = scorecard.obtener_scorecard_actual(conn, "NBA")
    assert out is None


def test_flag_true_scorecard_retorna_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scorecard, "flag_activo", lambda _name: True)

    row = (
        date(2026, 3, 8),
        91.3,
        "A",
        0,
        0.0,
        0.0,
        {"Completitud": 0.0},
        {"override_c_automatico": False},
    )
    conn = _FakeConn(row)

    out = scorecard.obtener_scorecard_actual(conn, "NBA")
    assert out is not None
    assert out["nivel"] == "A"


def test_estado_sistema_endpoint_flags_correctos(monkeypatch: pytest.MonkeyPatch) -> None:
    from api import rutas_calidad

    monkeypatch.setattr(
        rutas_calidad,
        "estado_flags",
        lambda: {
            "FEATURE_CALIDAD_SCORECARD": True,
            "FEATURE_ALERTAS_CALIDAD": True,
            "FEATURE_CONTRATO_EXPLICACION_V1": False,
            "FEATURE_EXPLICABILIDAD_UI": False,
        },
    )
    monkeypatch.setattr(rutas_calidad, "obtener_scorecard_actual", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(rutas_calidad, "obtener_alertas_activas", lambda *_args, **_kwargs: [])

    class _Pool:
        class _Conn:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self, **_kwargs):
                return self

        def connection(self):
            return self._Conn()

    monkeypatch.setattr(rutas_calidad, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_calidad, "flag_activo", lambda *_args, **_kwargs: False)

    client = TestClient(app)
    resp = client.get("/api/calidad/estado-sistema")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "feature_flags" in data
    assert data["deuda_residual_b05"].get("drift_futbol_parcial_alto") == "ACTIVO"

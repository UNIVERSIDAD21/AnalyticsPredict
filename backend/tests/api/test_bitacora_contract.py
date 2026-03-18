from pathlib import Path

from fastapi import Response

from api import rutas_bitacora


def test_respuesta_contrato_bitacora_v2_y_legacy(tmp_path, monkeypatch):
    usage_path = tmp_path / "bitacora_usage.json"
    monkeypatch.setattr(rutas_bitacora, "BITACORA_USAGE_PATH", usage_path)

    payload_legacy = {
        "exito": True,
        "total": 1,
        "pagina": 1,
        "total_paginas": 1,
        "apuestas": [],
    }

    response_v2 = Response()
    body_v2 = rutas_bitacora._respuesta_contrato(payload_legacy, "v2", response_v2, "")
    assert body_v2["ok"] is True
    assert body_v2["data"]["total"] == 1
    assert body_v2["meta"]["contract_version"] == "v2"

    response_legacy = Response()
    body_legacy = rutas_bitacora._respuesta_contrato(payload_legacy, "legacy", response_legacy, "resumen")
    assert body_legacy["exito"] is True
    assert response_legacy.headers["Deprecation"] == "true"
    assert "version=v2" in response_legacy.headers["Link"]

    raw = usage_path.read_text(encoding="utf-8")
    assert '"v2": 1' in raw
    assert '"legacy": 1' in raw


def test_leer_uso_contrato_bitacora_vacio(tmp_path, monkeypatch):
    usage_path = tmp_path / "missing_usage.json"
    monkeypatch.setattr(rutas_bitacora, "BITACORA_USAGE_PATH", usage_path)

    data = rutas_bitacora._leer_uso_contrato()
    assert data == {"by_date": {}}

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

    response_stats = Response()
    rutas_bitacora._respuesta_contrato(payload_legacy, "legacy", response_stats, "estadisticas")
    assert "/api/bitacora/estadisticas?version=v2" in response_stats.headers["Link"]

    response_metrics = Response()
    rutas_bitacora._respuesta_contrato(payload_legacy, "legacy", response_metrics, "metricas")
    assert "/api/bitacora/metricas?version=v2" in response_metrics.headers["Link"]

    response_detalle = Response()
    rutas_bitacora._respuesta_contrato(
        payload_legacy,
        "legacy",
        response_detalle,
        "00000000-0000-0000-0000-000000000000",
    )
    assert "/api/bitacora/00000000-0000-0000-0000-000000000000?version=v2" in response_detalle.headers["Link"]

    response_resultado = Response()
    rutas_bitacora._respuesta_contrato(
        payload_legacy,
        "legacy",
        response_resultado,
        "00000000-0000-0000-0000-000000000000/resultado",
    )
    assert "/api/bitacora/00000000-0000-0000-0000-000000000000/resultado?version=v2" in response_resultado.headers["Link"]

    import json

    raw = usage_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    today_row = next(iter(data["by_date"].values()))
    assert today_row["v2"] >= 1
    assert today_row["legacy"] >= 1


def test_leer_uso_contrato_bitacora_vacio(tmp_path, monkeypatch):
    usage_path = tmp_path / "missing_usage.json"
    monkeypatch.setattr(rutas_bitacora, "BITACORA_USAGE_PATH", usage_path)

    data = rutas_bitacora._leer_uso_contrato()
    assert data == {"by_date": {}}

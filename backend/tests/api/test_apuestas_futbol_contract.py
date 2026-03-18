from fastapi import Response

from api import rutas_apuestas_futbol


def test_respuesta_contrato_apuestas_futbol_v2_y_legacy(tmp_path, monkeypatch):
    usage_path = tmp_path / "apuestas_futbol_usage.json"
    monkeypatch.setattr(rutas_apuestas_futbol, "APUESTAS_FUTBOL_USAGE_PATH", usage_path)

    payload_legacy = {
        "exito": True,
        "resueltas": 2,
        "ganadas": 1,
        "perdidas": 1,
        "push": 0,
        "errores": 0,
        "ganancia_neta": 1.5,
    }

    response_v2 = Response()
    body_v2 = rutas_apuestas_futbol._respuesta_contrato(payload_legacy, "v2", response_v2, "resolver")
    assert body_v2["ok"] is True
    assert body_v2["data"]["resueltas"] == 2
    assert body_v2["meta"]["contract_version"] == "v2"

    response_legacy = Response()
    body_legacy = rutas_apuestas_futbol._respuesta_contrato(
        payload_legacy,
        "legacy",
        response_legacy,
        "resolver",
    )
    assert body_legacy["exito"] is True
    assert response_legacy.headers["Deprecation"] == "true"
    assert "/api/futbol/apuestas/resolver?version=v2" in response_legacy.headers["Link"]

    data = rutas_apuestas_futbol._leer_uso_contrato()
    assert len(data["by_date"]) == 1
    today_row = next(iter(data["by_date"].values()))
    assert today_row["v2"] >= 1
    assert today_row["legacy"] >= 1

from pathlib import Path
import asyncio

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

    response_unificada = Response()
    rutas_bitacora._respuesta_contrato(payload_legacy, "legacy", response_unificada, "unificada")
    assert "/api/bitacora/unificada?version=v2" in response_unificada.headers["Link"]

    response_analizadas = Response()
    rutas_bitacora._respuesta_contrato(payload_legacy, "legacy", response_analizadas, "apuestas-analizadas")
    assert "/api/bitacora/apuestas-analizadas?version=v2" in response_analizadas.headers["Link"]

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

    assert not usage_path.exists(), "GET no debe persistir telemetría al serializar contrato"
    assert rutas_bitacora._leer_uso_contrato() == {"by_date": {}}


def test_leer_uso_contrato_bitacora_vacio(tmp_path, monkeypatch):
    usage_path = tmp_path / "missing_usage.json"
    monkeypatch.setattr(rutas_bitacora, "BITACORA_USAGE_PATH", usage_path)

    data = rutas_bitacora._leer_uso_contrato()
    assert data == {"by_date": {}}


def test_analizadas_total_no_es_tamano_de_pagina(tmp_path, monkeypatch):
    from servicios import apuestas_analizadas

    class Cursor:
        def __init__(self):
            self.consulta = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def execute(self, consulta, *_args):
            self.consulta = consulta

        def fetchone(self):
            return {"total": 16}

        def fetchall(self):
            return [{"id": 1, "estado": "FINALIZADA"}]

    class Conexion:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def cursor(self, **_kwargs):
            return Cursor()

    class Pool:
        def connection(self):
            return Conexion()

    def escritura_inesperada(*_args, **_kwargs):
        raise AssertionError("GET /apuestas-analizadas no debe escribir en la base")

    monkeypatch.setattr(apuestas_analizadas, "resolver_apuestas_analizadas", escritura_inesperada)
    monkeypatch.setattr(apuestas_analizadas, "asegurar_tabla_apuestas_analizadas", escritura_inesperada)
    monkeypatch.setattr(rutas_bitacora, "obtener_pool", Pool)
    monkeypatch.setattr(rutas_bitacora, "BITACORA_USAGE_PATH", tmp_path / "usage.json")

    payload = asyncio.run(rutas_bitacora.listar_apuestas_analizadas(Response(), version="v2", limite=1, offset=0))
    assert payload["data"]["total"] == 16
    assert payload["data"]["items"] == [{"id": 1, "estado": "FINALIZADA"}]

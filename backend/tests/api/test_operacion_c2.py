# -*- coding: utf-8 -*-
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rutas_auth import router as router_auth
from api.rutas_operacion_c2 import router as router_operacion_c2
from api.rutas_pagos import router as router_pagos


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["AUTH_DB_PATH"] = str(tmp_path / "auth-test.db")
    os.environ["PAGOS_DB_PATH"] = str(tmp_path / "pagos-test.db")

    app = FastAPI()
    app.include_router(router_auth)
    app.include_router(router_pagos)
    app.include_router(router_operacion_c2)
    return TestClient(app)


def test_health_critical_responde_y_enumera_componentes(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    r = client.get("/api/operacion/c2/health-critical")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    data = body["data"]
    assert "overall" in data
    assert "components" in data
    assert "pagos_store" in data["components"]
    assert "auth_store" in data["components"]

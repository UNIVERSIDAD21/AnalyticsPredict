# -*- coding: utf-8 -*-

import os
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencias import UsuarioActual, obtener_usuario_actual
from api.rutas_notificaciones import router as notificaciones_router


class _DummySMTP:
    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def starttls(self):
        return None

    def login(self, *_args):
        return None

    def send_message(self, *_args):
        return None


def _crear_cliente(tmp_path: Path) -> TestClient:
    os.environ["NOTIFICACIONES_DB_PATH"] = str(tmp_path / "notificaciones-test.db")

    app = FastAPI()
    app.include_router(notificaciones_router)
    app.dependency_overrides[obtener_usuario_actual] = lambda: UsuarioActual(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="tester@example.com",
    )
    return TestClient(app)


def test_preferencias_default_y_actualizacion(tmp_path: Path):
    client = _crear_cliente(tmp_path)

    r = client.get("/api/notificaciones/preferencias")
    assert r.status_code == 200
    assert r.json()["data"]["preferencias"]["email_habilitado"] is True

    r2 = client.put(
        "/api/notificaciones/preferencias",
        json={
            "email_habilitado": True,
            "alertas_partidos": False,
            "alertas_suscripcion": True,
            "resumen_semanal": True,
        },
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["preferencias"]["alertas_partidos"] is False


def test_encolar_y_procesar_registra_historial(monkeypatch, tmp_path: Path):
    client = _crear_cliente(tmp_path)

    os.environ["AUTH_SMTP_HOST"] = "smtp.local"
    monkeypatch.setattr("api.rutas_notificaciones.smtplib.SMTP", _DummySMTP)

    q = client.post("/api/notificaciones/encolar-prueba", json={"tipo": "alertas_partidos"})
    assert q.status_code == 200
    assert q.json()["data"]["encolado"] is True

    p = client.post("/api/notificaciones/procesar-cola")
    assert p.status_code == 200
    assert p.json()["data"]["enviados"] >= 1

    h = client.get("/api/notificaciones/historial")
    assert h.status_code == 200
    assert h.json()["data"]["total"] >= 1


def test_scheduler_encola_por_tipo(monkeypatch, tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.put(
        "/api/notificaciones/preferencias",
        json={
            "email_habilitado": True,
            "alertas_partidos": True,
            "alertas_suscripcion": False,
            "resumen_semanal": True,
        },
    )

    q = client.post("/api/notificaciones/scheduler/encolar?tipo=todos")
    assert q.status_code == 200
    data = q.json()["data"]
    assert data["total"] == 2
    assert len(data["omitidas"]) == 1

    os.environ["AUTH_SMTP_HOST"] = "smtp.local"
    monkeypatch.setattr("api.rutas_notificaciones.smtplib.SMTP", _DummySMTP)

    p = client.post("/api/notificaciones/procesar-cola")
    assert p.status_code == 200
    assert p.json()["data"]["enviados"] >= 1


def test_enviar_prueba_respeta_preferencias(monkeypatch, tmp_path: Path):
    client = _crear_cliente(tmp_path)

    client.put(
        "/api/notificaciones/preferencias",
        json={
            "email_habilitado": False,
            "alertas_partidos": True,
            "alertas_suscripcion": True,
            "resumen_semanal": False,
        },
    )

    os.environ["AUTH_SMTP_HOST"] = "smtp.local"
    monkeypatch.setattr("api.rutas_notificaciones.smtplib.SMTP", _DummySMTP)

    r = client.post("/api/notificaciones/enviar-prueba", json={"tipo": "alertas_partidos"})
    assert r.status_code == 200
    assert r.json()["data"]["estado"] == "omitido"


def test_metricas_entrega_y_max_intentos_por_tipo(monkeypatch, tmp_path: Path):
    client = _crear_cliente(tmp_path)
    os.environ["AUTH_SMTP_HOST"] = "smtp.local"
    monkeypatch.setattr("api.rutas_notificaciones.smtplib.SMTP", _DummySMTP)

    client.put(
        "/api/notificaciones/preferencias",
        json={
            "email_habilitado": True,
            "alertas_partidos": True,
            "alertas_suscripcion": True,
            "resumen_semanal": True,
        },
    )

    q = client.post("/api/notificaciones/scheduler/encolar?tipo=resumen_semanal")
    assert q.status_code == 200
    job = q.json()["data"]["encoladas"][0]
    assert int(job["max_intentos"]) == 2

    p = client.post("/api/notificaciones/procesar-cola")
    assert p.status_code == 200

    m = client.get("/api/notificaciones/metricas-entrega?horas=24")
    assert m.status_code == 200
    data = m.json()["data"]
    assert "totales" in data
    assert "tasa_entrega_pct" in data
    assert "por_tipo" in data

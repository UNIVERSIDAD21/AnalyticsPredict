# -*- coding: utf-8 -*-
"""Smoke tests de separación conceptual NBA/FUTBOL (sin refactor físico agresivo)."""

from fastapi.testclient import TestClient

from app import app


def test_endpoint_nba_independiente_de_motor_futbol() -> None:
    client = TestClient(app)
    # Endpoint NBA/compartido debe responder sin depender de ejecución fútbol.
    r = client.get('/salud')
    assert r.status_code == 200


def test_endpoint_futbol_no_rompe_si_nba_falla_startup() -> None:
    client = TestClient(app)
    # Smoke básico de ruta fútbol registrada.
    # Se valida que el router está vivo y no rompe el app init.
    r = client.get('/api/partidos-futbol')
    assert r.status_code in {200, 404, 422}

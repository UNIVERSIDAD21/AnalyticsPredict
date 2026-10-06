"""Tests de integración livianos para endpoints profesionales de métricas.

Nota: usan la app real con TestClient. No fuerzan datos mínimos de negocio,
solo validan contrato y disponibilidad de campos clave.
"""

from fastapi.testclient import TestClient
import os
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict

from app import app
from db import obtener_pool


client = TestClient(app)


def test_tablero_salud_contrato_basico():
    resp = client.get("/api/metricas/tablero-salud")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "score_global" in data
    assert "deportes" in data
    assert "alertas" in data


def test_calidad_mercados_contrato_basico():
    resp = client.get("/api/metricas/calidad-mercados?min_muestras=10&limite=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "ranking" in data
    assert "recomendaciones" in data


def test_recomendaciones_accion_contrato_basico():
    resp = client.get("/api/metricas/recomendaciones-accion?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert data["semaforo_global"] in {"verde", "amarillo", "rojo"}
    assert isinstance(data["acciones"], list)


def test_drift_mercados_contrato_basico():
    resp = client.get("/api/metricas/drift-mercados?min_muestras=10&limite=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "items" in data
    assert "resumen" in data


def test_politica_mercados_contrato_basico():
    resp = client.get("/api/metricas/politica-mercados?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "mercados" in data
    assert "resumen" in data


def test_alertas_ingestion_contrato_basico():
    resp = client.get("/api/metricas/alertas-ingestion?max_horas_sin_actualizar=24")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "alertas" in data
    assert "resumen" in data


def test_sugerencias_umbrales_contrato_basico():
    resp = client.get("/api/metricas/sugerencias-umbrales?min_muestras=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exito"] is True
    assert "sugerencias" in data
    assert len(data["sugerencias"]) >= 1


def test_tablero_no_atribuye_calibracion_sin_id_en_postgres_efimero():
    """La misma fila debe usar raw sin UUID y calibrada con UUID verificado."""
    cfg = conninfo_to_dict(os.environ.get("DATABASE_URL") or "")
    if not str(cfg.get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo se ejecuta en la base sintética del runner global")

    nba_id, fut_id, calibrador_id = uuid4(), uuid4(), uuid4()
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO predicciones_registradas (id, mercado, p_raw, p_calibrada, outcome_binario, resuelto) "
                "VALUES (%s, 'Q1', 0.2, 0.9, false, true)", (nba_id,),
            )
            conn.execute(
                "INSERT INTO predicciones_futbol (id, mercado, prob_over, prob_over_calibrada, outcome_binario, resuelto) "
                "VALUES (%s, 'GOLES_FT', 0.3, 0.8, true, true)", (fut_id,),
            )

        def brier_por_deporte():
            response = client.get("/api/metricas/tablero-salud")
            assert response.status_code == 200
            return {d["deporte"]: d["brier"] for d in response.json()["deportes"]}

        raw = brier_por_deporte()
        assert raw["baloncesto"] == pytest.approx(0.04)
        assert raw["futbol"] == pytest.approx(0.49)

        with pool.connection() as conn:
            conn.execute("UPDATE predicciones_registradas SET calibrador_id = %s WHERE id = %s", (calibrador_id, nba_id))
            conn.execute("UPDATE predicciones_futbol SET calibrador_id = %s WHERE id = %s", (calibrador_id, fut_id))
        calibrada = brier_por_deporte()
        assert calibrada["baloncesto"] == pytest.approx(0.81)
        assert calibrada["futbol"] == pytest.approx(0.04)
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE id = %s", (nba_id,))
            conn.execute("DELETE FROM predicciones_futbol WHERE id = %s", (fut_id,))

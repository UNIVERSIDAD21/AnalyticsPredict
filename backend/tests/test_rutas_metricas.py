# -*- coding: utf-8 -*-
"""
Tests para endpoints de métricas de calibración (T22, T23).
"""

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.rutas_metricas import router as router_metricas


def _crear_cliente():
    app = FastAPI()
    app.include_router(router_metricas)
    return TestClient(app)


def test_origen_obligatorio_metricas():
    client = _crear_cliente()
    response = client.get("/api/metricas/calibracion")
    assert response.status_code == 422


def test_metricas_respuesta_basica():
    client = _crear_cliente()
    resultado = {
        "n_predicciones": 45,
        "brier_score": 0.21,
        "brier_score_raw": 0.23,
        "brier_score_calibrado": 0.21,
        "log_loss": 0.49,
        "ece": 0.04,
        "mce": 0.08,
        "sharpness": 0.11,
        "base_rate": 0.52,
        "distribucion": {"mae_media": 1.2, "rmse_media": 1.6, "sesgo_media": -0.2},
        "alertas": [],
    }
    periodo = date(2024, 1, 1), date(2024, 1, 31)
    with patch("api.rutas_metricas._resolver_periodo") as resolver:
        resolver.return_value = SimpleNamespace(
            inicio=periodo[0],
            fin=periodo[1],
            texto_inicio=periodo[0].isoformat(),
            texto_fin=periodo[1].isoformat(),
        )
        with patch("api.rutas_metricas._buscar_metricas_precalculadas", return_value=None):
            with patch("api.rutas_metricas.calcular_metricas_calibracion", return_value=resultado):
                with patch("api.rutas_metricas._contar_excluidos_push", return_value=5):
                    with patch("api.rutas_metricas.listar_alertas_calibracion", return_value=[]):
                        with patch(
                            "api.rutas_metricas.obtener_calibrador_activo",
                            return_value=SimpleNamespace(metodo="platt", id="1234"),
                        ):
                            response = client.get(
                                "/api/metricas/calibracion?origen=API_USUARIO&mercado=Q1"
                            )

    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["origen"] == "API_USUARIO"
    metrica = data["metricas_por_mercado"][0]
    assert metrica["n_excluidos_push"] == 5
    assert metrica["suficiente_data"] is False
    assert metrica["calibrador_activo"] == "platt"
    assert metrica["mejora_vs_raw"] == pytest.approx(0.02)


def test_curva_bins_y_excluidos():
    client = _crear_cliente()
    periodo = date(2024, 2, 1), date(2024, 2, 28)
    predicciones = [
        {"p_efectiva": 0.1, "outcome_binario": True},
        {"p_efectiva": 0.2, "outcome_binario": False},
        {"p_efectiva": 0.8, "outcome_binario": True},
    ]
    with patch("api.rutas_metricas._resolver_periodo") as resolver:
        resolver.return_value = SimpleNamespace(
            inicio=periodo[0],
            fin=periodo[1],
            texto_inicio=periodo[0].isoformat(),
            texto_fin=periodo[1].isoformat(),
        )
        with patch("api.rutas_metricas._obtener_predicciones_para_curva", return_value=predicciones):
            with patch("api.rutas_metricas._contar_excluidos_push", return_value=1):
                response = client.get("/api/metricas/calibracion/Q1/curva?origen=API_USUARIO")

    assert response.status_code == 200
    data = response.json()
    assert data["n_excluidos_push"] == 1
    assert sum(bin_info["n"] for bin_info in data["bins"]) == data["n_predicciones_total"]

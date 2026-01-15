# -*- coding: utf-8 -*-
"""
Tests para reporte de backtest (T25).
"""

import sys
import csv
import io
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.rutas_backtest import router as router_backtest


def _crear_cliente():
    app = FastAPI()
    app.include_router(router_backtest)
    return TestClient(app)


def _backtest_base():
    return {
        "id": "backtest-123",
        "estado": "COMPLETADO",
        "configuracion": {"mercados": ["Q1"], "origen": "BACKTEST_SINTETICO"},
        "fecha_inicio_eval": "2024-01-01",
        "fecha_fin_eval": "2024-01-31",
        "mercados": ["Q1"],
        "total_predicciones_generadas": 10,
    }


class TestReporteJSON:
    def test_estructura_completa(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_metricas_backtest", return_value=[]):
                with patch("api.rutas_backtest._obtener_curvas_backtest", return_value={}):
                    with patch("api.rutas_backtest._obtener_alertas_backtest", return_value=[]):
                        with patch("api.rutas_backtest._obtener_trazabilidad_backtest", return_value={}):
                            with patch("api.rutas_backtest._calcular_resumen_global", return_value={}):
                                response = client.get(
                                    "/api/backtest/backtest-123/reporte?formato=json"
                                )

        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "configuracion" in data
        assert "trazabilidad" in data
        assert "resumen_global" in data
        assert "metricas_por_mercado" in data
        assert "curvas_calibracion" in data
        assert "alertas" in data
        assert "recomendaciones" in data
        assert "firma_digital" in data

    def test_firma_digital_presente(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_metricas_backtest", return_value=[]):
                with patch("api.rutas_backtest._obtener_curvas_backtest", return_value={}):
                    with patch("api.rutas_backtest._obtener_alertas_backtest", return_value=[]):
                        with patch("api.rutas_backtest._obtener_trazabilidad_backtest", return_value={}):
                            with patch("api.rutas_backtest._calcular_resumen_global", return_value={}):
                                response = client.get(
                                    "/api/backtest/backtest-123/reporte"
                                )

        data = response.json()
        firma = data["firma_digital"]
        assert firma["hash_reporte"].startswith("sha256:")
        assert "timestamp" in firma


class TestReporteCSV:
    def test_formato_csv_valido(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_predicciones_backtest", return_value=[
                {
                    "id": "uuid1",
                    "fecha_partido": "2024-01-15",
                    "mercado": "Q1",
                    "equipo_local": "Lakers",
                    "equipo_visitante": "Heat",
                    "lado": "OVER",
                    "linea": 52.5,
                    "linea_es_sintetica": True,
                    "p_raw": 0.62,
                    "p_calibrada": 0.6,
                    "media_predicha": 54.2,
                    "desviacion_predicha": 6.1,
                    "valor_real": 56,
                    "outcome_binario": True,
                    "modelo_version_id": 15,
                    "cutoff_entrenamiento": "2024-01-14",
                }
            ]):
                response = client.get(
                    "/api/backtest/backtest-123/reporte?formato=csv"
                )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        content = response.content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) > 1

    def test_headers_csv_completos(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_predicciones_backtest", return_value=[]):
                response = client.get(
                    "/api/backtest/backtest-123/reporte?formato=csv"
                )

        content = response.content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))
        headers = next(reader)
        for campo in ["prediccion_id", "fecha_partido", "mercado", "lado", "linea"]:
            assert campo in headers

    def test_descarga_filename_correcto(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_predicciones_backtest", return_value=[]):
                response = client.get(
                    "/api/backtest/backtest-123/reporte?formato=csv"
                )

        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert "backtest-123" in content_disposition
        assert ".csv" in content_disposition

    def test_encoding_excel_compatible(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=_backtest_base()):
            with patch("api.rutas_backtest._obtener_predicciones_backtest", return_value=[]):
                response = client.get(
                    "/api/backtest/backtest-123/reporte?formato=csv"
                )

        content_bytes = response.content
        assert content_bytes[:3] == b"\xef\xbb\xbf"


class TestBacktestNoExiste:
    def test_404_si_no_existe(self):
        client = _crear_cliente()
        with patch("api.rutas_backtest._obtener_backtest", return_value=None):
            response = client.get("/api/backtest/backtest-inexistente/reporte")

        assert response.status_code == 404

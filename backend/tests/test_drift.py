# -*- coding: utf-8 -*-
"""
Tests para detección de drift (T24).
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.monitoreo.configuracion_drift import ConfiguracionDrift
from backtesting.monitoreo.drift import detectar_drift, _evaluar_metrica


def _metricas_base(n_predicciones: int = 150) -> dict:
    return {
        "n_predicciones": n_predicciones,
        "ece": 0.02,
        "brier_score": 0.2,
        "brier_score_raw": 0.2,
        "brier_score_calibrado": 0.19,
        "sesgo_media": 0.1,
        "periodo_inicio": date(2024, 1, 1),
        "periodo_fin": date(2024, 1, 31),
        "modelo_version_id": 1,
    }


class TestDeteccionDrift:
    def test_datos_insuficientes_genera_alerta_info(self):
        """Con <100 predicciones, genera alerta INFO de datos insuficientes."""
        metricas = _metricas_base(n_predicciones=80)
        with patch(
            "backtesting.monitoreo.drift._obtener_metricas_periodo",
            return_value=metricas,
        ):
            with patch("backtesting.monitoreo.drift._persistir_alerta"):
                resultado = detectar_drift("Q1", "API_USUARIO")

        assert resultado.evaluacion_exitosa
        assert len(resultado.alertas) == 1
        assert resultado.alertas[0].tipo == "DATOS_INSUFICIENTES"
        assert resultado.alertas[0].severidad == "INFO"

    def test_ece_alto_genera_alerta_critical(self):
        """ECE > 0.05 genera alerta CRITICAL."""
        metricas = _metricas_base()
        metricas["ece"] = 0.08
        baseline = _metricas_base()
        with patch(
            "backtesting.monitoreo.drift._obtener_metricas_periodo",
            side_effect=[metricas, baseline],
        ):
            with patch("backtesting.monitoreo.drift._obtener_tendencia", return_value=None):
                with patch("backtesting.monitoreo.drift._persistir_alerta"):
                    resultado = detectar_drift("Q1", "API_USUARIO")

        alertas_critical = [a for a in resultado.alertas if a.severidad == "CRITICAL"]
        assert alertas_critical
        assert any("ECE" in a.tipo for a in alertas_critical)

    def test_cambio_relativo_vs_baseline(self):
        """Aumento >50% vs baseline genera alerta."""
        metricas = _metricas_base()
        metricas["ece"] = 0.05
        baseline = _metricas_base()
        baseline["ece"] = 0.02
        with patch(
            "backtesting.monitoreo.drift._obtener_metricas_periodo",
            side_effect=[metricas, baseline],
        ):
            with patch("backtesting.monitoreo.drift._obtener_tendencia", return_value=None):
                with patch("backtesting.monitoreo.drift._persistir_alerta"):
                    resultado = detectar_drift("Q1", "API_USUARIO")

        alertas_relativas = [a for a in resultado.alertas if "RELATIVO" in a.tipo]
        assert alertas_relativas
        assert alertas_relativas[0].cambio_porcentual is not None

    def test_tendencia_negativa_detectada(self):
        """3 periodos empeorando genera alerta."""
        config = ConfiguracionDrift(evaluar_tendencia=True, ventanas_tendencia=3)
        metricas = _metricas_base()
        baseline = _metricas_base()
        tendencia = [
            {"ece": 0.02, "brier_score": 0.18},
            {"ece": 0.03, "brier_score": 0.19},
            {"ece": 0.04, "brier_score": 0.21},
        ]
        with patch(
            "backtesting.monitoreo.drift._obtener_metricas_periodo",
            side_effect=[metricas, baseline],
        ):
            with patch("backtesting.monitoreo.drift._obtener_tendencia", return_value=tendencia):
                with patch("backtesting.monitoreo.drift._persistir_alerta"):
                    resultado = detectar_drift("Q1", "API_USUARIO", config)

        alertas_tendencia = [a for a in resultado.alertas if a.tipo == "TENDENCIA_NEGATIVA"]
        assert alertas_tendencia

    def test_calibrador_que_empeora(self):
        """Brier calibrado > raw genera alerta."""
        metricas = _metricas_base()
        metricas["brier_score_raw"] = 0.2
        metricas["brier_score_calibrado"] = 0.24
        baseline = _metricas_base()
        with patch(
            "backtesting.monitoreo.drift._obtener_metricas_periodo",
            side_effect=[metricas, baseline],
        ):
            with patch("backtesting.monitoreo.drift._obtener_tendencia", return_value=None):
                with patch("backtesting.monitoreo.drift._persistir_alerta"):
                    resultado = detectar_drift("Q1", "API_USUARIO")

        alertas_calibrador = [a for a in resultado.alertas if a.tipo == "CALIBRADOR_EMPEORA"]
        assert alertas_calibrador
        assert "desactivar" in alertas_calibrador[0].recomendacion.lower()


class TestEvaluarMetrica:
    def test_umbral_absoluto_critical(self):
        """Valor > umbral_critical genera alerta CRITICAL."""
        config = ConfiguracionDrift()
        alertas = _evaluar_metrica(
            "Q1",
            "API_USUARIO",
            "ece",
            0.08,
            None,
            config,
            periodo_inicio=date(2024, 1, 1),
            periodo_fin=date(2024, 1, 31),
            modelo_version_id=1,
        )

        assert len(alertas) == 1
        assert alertas[0].severidad == "CRITICAL"

    def test_umbral_absoluto_warning(self):
        """Valor > umbral_warning pero < critical genera WARNING."""
        config = ConfiguracionDrift()
        alertas = _evaluar_metrica(
            "Q1",
            "API_USUARIO",
            "ece",
            0.04,
            None,
            config,
            periodo_inicio=date(2024, 1, 1),
            periodo_fin=date(2024, 1, 31),
            modelo_version_id=1,
        )

        assert len(alertas) == 1
        assert alertas[0].severidad == "WARNING"

    def test_valor_normal_sin_alerta(self):
        """Valor normal no genera alertas."""
        config = ConfiguracionDrift()
        alertas = _evaluar_metrica(
            "Q1",
            "API_USUARIO",
            "ece",
            0.02,
            0.02,
            config,
            periodo_inicio=date(2024, 1, 1),
            periodo_fin=date(2024, 1, 31),
            modelo_version_id=1,
        )

        assert len(alertas) == 0

    def test_sesgo_usa_valor_absoluto(self):
        """Sesgo negativo también genera alerta si |sesgo| > umbral."""
        config = ConfiguracionDrift()
        alertas = _evaluar_metrica(
            "Q1",
            "API_USUARIO",
            "sesgo",
            -4.0,
            None,
            config,
            usar_valor_absoluto=True,
            periodo_inicio=date(2024, 1, 1),
            periodo_fin=date(2024, 1, 31),
            modelo_version_id=1,
        )

        assert alertas
        assert alertas[0].severidad == "CRITICAL"

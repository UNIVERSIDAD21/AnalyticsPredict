# -*- coding: utf-8 -*-
"""
Tests de flujo completo para calibración (T21).

Verifica el pipeline: Motor → Calibrador Activo → EV/edge → API → Registro.
"""

import sys
from datetime import date
from pathlib import Path
from uuid import UUID

import numpy as np
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionAnalisis
from api.rutas_analisis import ejecutar_analisis
from motor.nba_predictor_cuartos import analizar_partido
from motor.tipos import ModeloRidge, Ubicacion
from motor.utilidades import normalizar_nombre


def _crear_modelo_simple() -> ModeloRidge:
    entidad_a_indice = {
        normalizar_nombre("Lakers"): 0,
        normalizar_nombre("Heat"): 1,
    }
    pesos_equipo = np.zeros((6, 4))
    pesos_equipo[0, :] = 25.0
    pesos_equipo[-1, :] = 1.0

    pesos_rival = np.zeros((6, 4))
    pesos_rival[0, :] = 24.0

    desviacion_equipo = np.array([5.0, 5.0, 5.0, 5.0])
    desviacion_rival = np.array([5.0, 5.0, 5.0, 5.0])

    modelo = ModeloRidge(
        alfa=1.0,
        entidad_a_indice=entidad_a_indice,
        pesos_equipo=pesos_equipo,
        pesos_rival=pesos_rival,
        desviacion_equipo=desviacion_equipo,
        desviacion_rival=desviacion_rival,
    )
    setattr(modelo, "version", 1)
    return modelo


class DummyCalibrador:
    def __init__(self, mercado: str):
        self.metodo = "platt"
        self.mercado = mercado
        self.id = UUID("11111111-1111-1111-1111-111111111111")

    def calibrar(self, _p: float) -> float:
        return 0.75


def test_flujo_sin_calibrador_activo_usa_p_raw_para_ev(monkeypatch):
    modelo = _crear_modelo_simple()
    monkeypatch.setattr(
        "motor.nba_predictor_cuartos.obtener_calibrador_activo",
        lambda **kwargs: None,
    )

    resultado = analizar_partido(
        modelo=modelo,
        equipo="Lakers",
        rival="Heat",
        ubicacion=Ubicacion.LOCAL,
        mercado="Q1",
        linea=50.5,
        cuota_over=2.0,
        cuota_under=None,
        lado="OVER",
        modo_devig="estricto",
        fecha_partido=date(2024, 1, 15),
        origen_prediccion="API_USUARIO",
        incluir_contexto=False,
    )

    candidato = resultado.candidatos[0]
    assert candidato.p_calibrada is None
    assert candidato.calibrador_usado is None
    assert candidato.ev == pytest.approx((candidato.p_raw * candidato.cuota) - 1.0)


def test_flujo_con_calibrador_activo_usa_p_calibrada_para_ev(monkeypatch):
    modelo = _crear_modelo_simple()
    calibrador = DummyCalibrador("Q1")
    monkeypatch.setattr(
        "motor.nba_predictor_cuartos.obtener_calibrador_activo",
        lambda **kwargs: calibrador,
    )

    resultado = analizar_partido(
        modelo=modelo,
        equipo="Lakers",
        rival="Heat",
        ubicacion=Ubicacion.LOCAL,
        mercado="Q1",
        linea=50.5,
        cuota_over=2.0,
        cuota_under=None,
        lado="OVER",
        modo_devig="estricto",
        fecha_partido=date(2024, 1, 15),
        origen_prediccion="API_USUARIO",
        incluir_contexto=False,
    )

    candidato = resultado.candidatos[0]
    assert candidato.p_calibrada == pytest.approx(0.75)
    assert candidato.p_raw != candidato.p_calibrada
    assert candidato.calibrador_usado == "platt"
    assert candidato.calibrador_id == calibrador.id
    assert candidato.ev == pytest.approx((0.75 * candidato.cuota) - 1.0)


def test_api_expone_p_raw_y_p_calibrada_y_registra_calibrador(monkeypatch):
    modelo = _crear_modelo_simple()
    calibrador = DummyCalibrador("Q1")
    llamadas_registro = []

    monkeypatch.setattr("api.rutas_analisis.obtener_modelo", lambda: modelo)
    monkeypatch.setattr("api.rutas_analisis.validar_equipos", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "motor.nba_predictor_cuartos.obtener_calibrador_activo",
        lambda **kwargs: calibrador,
    )

    def fake_registrar_prediccion(**kwargs):
        llamadas_registro.append(kwargs)
        return None

    monkeypatch.setattr("api.rutas_analisis.registrar_prediccion", fake_registrar_prediccion)

    peticion = PeticionAnalisis(
        partido_id=UUID("22222222-2222-2222-2222-222222222222"),
        temporada_id=UUID("33333333-3333-3333-3333-333333333333"),
        equipo_local_id=UUID("44444444-4444-4444-4444-444444444444"),
        equipo_visitante_id=UUID("55555555-5555-5555-5555-555555555555"),
        fecha_partido=date(2024, 1, 15),
        tipo_partido="REG",
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        cuota_over=2.0,
        cuota_under=None,
        lado="OVER",
        modo_devig="estricto",
    )

    respuesta = ejecutar_analisis(peticion)

    candidato = respuesta.datos["candidatos"][0]
    assert candidato["p_raw"] is not None
    assert candidato["p_calibrada"] == pytest.approx(0.75)
    assert candidato["calibrador_usado"] == "platt"

    assert len(llamadas_registro) == 1
    assert llamadas_registro[0]["calibrador_id"] == calibrador.id

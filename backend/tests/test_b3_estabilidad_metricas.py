# -*- coding: utf-8 -*-

from api.rutas_metricas_futbol import _clasificar_estabilidad_b3


def test_clasificar_estabilidad_detecta_critico_y_gate_false():
    actual = [
        {
            "competicion_id": "c1",
            "competicion_codigo": "LALIGA",
            "competicion_nombre": "La Liga",
            "n": 120,
            "brier": 0.29,
        }
    ]
    previo = [
        {
            "competicion_id": "c1",
            "competicion_codigo": "LALIGA",
            "competicion_nombre": "La Liga",
            "n": 120,
            "brier": 0.24,
        }
    ]

    r = _clasificar_estabilidad_b3(actual, previo)
    assert r["gate_aprobado"] is False
    assert r["ligas_criticas"] == 1
    assert r["ligas"][0]["estado"] == "critico"


def test_clasificar_estabilidad_estable_y_gate_true():
    actual = [
        {
            "competicion_id": "c1",
            "competicion_codigo": "SERIE_A",
            "competicion_nombre": "Serie A",
            "n": 90,
            "brier": 0.205,
        }
    ]
    previo = [
        {
            "competicion_id": "c1",
            "competicion_codigo": "SERIE_A",
            "competicion_nombre": "Serie A",
            "n": 95,
            "brier": 0.210,
        }
    ]

    r = _clasificar_estabilidad_b3(actual, previo)
    assert r["gate_aprobado"] is True
    assert r["ligas_criticas"] == 0
    assert r["ligas"][0]["estado"] == "estable"

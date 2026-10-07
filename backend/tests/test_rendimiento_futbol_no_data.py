"""Contrato de rendimiento: ausencia de importe o muestra no es ROI cero."""

import asyncio

from api import rutas_metricas_futbol


class _Cursor:
    def execute(self, query, _params=None):
        self.query = query

    def fetchall(self):
        return [
            {"mercado": "GOLES_FT", "n_apuestas": 2, "ganadas": 1,
             "perdidas": 1, "stake_total": 20, "ganancia_neta": 2,
             "n_ganancias": 2},
            {"mercado": "CORNERS_FT", "n_apuestas": 1, "ganadas": 0,
             "perdidas": 0, "stake_total": 10, "ganancia_neta": None,
             "n_ganancias": 0},
        ]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Conn:
    def cursor(self, **_kwargs):
        return _Cursor()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Pool:
    def connection(self):
        return _Conn()


def test_roi_futbol_porcentaje_y_ausencia_de_ganancia(monkeypatch):
    monkeypatch.setattr(rutas_metricas_futbol, "obtener_pool", lambda: _Pool())
    monkeypatch.setattr(rutas_metricas_futbol, "_tabla_existe", lambda *_: True)
    monkeypatch.setattr(rutas_metricas_futbol, "_resolver_columna_estado_apuestas", lambda *_: "estado")
    monkeypatch.setattr(rutas_metricas_futbol, "_resolver_columna_ganancia_apuestas", lambda *_: "ganancia")

    respuesta = asyncio.run(rutas_metricas_futbol.obtener_metricas_rendimiento(
        mercado=None, periodo="todo"))
    medidas = {m.mercado: m for m in respuesta.metricas}
    assert medidas["GOLES_FT"].roi == 10.0  # API en porcentaje
    assert medidas["GOLES_FT"].win_rate == 0.5
    assert medidas["CORNERS_FT"].roi is None
    assert medidas["CORNERS_FT"].ganancia_neta is None
    assert medidas["CORNERS_FT"].win_rate is None

"""Contratos matemáticos/lectura, sin app, BD deportiva ni entrenamiento."""
from datetime import datetime, timezone
import math

import pytest

from motor_futbol.prediccion.distribuciones_contextuales import (
    _calcular_probabilidad_over, _calcular_1x2_dixon_coles,
)
from servicios.lecturas_analisis_futbol import (
    _obtener_partidos_equipo, _obtener_partidos_h2h, _obtener_partidos_liga,
)


def test_probabilidades_conocidas_y_fallback_no_cambian_estimador():
    assert _calcular_probabilidad_over(2, 1, 0, 'poisson') == pytest.approx(1 - math.exp(-2))
    assert _calcular_probabilidad_over(2, 1, 0, 'nbinom') == _calcular_probabilidad_over(2, 1, 0, 'poisson')
    assert _calcular_probabilidad_over(10, 2, 10, 'normal') == .5
    assert _calcular_probabilidad_over(10, 0, 10, 'normal') == .5  # fallback legacy sigma=1
    assert _calcular_probabilidad_over(10, 2, 12, 'normal') == pytest.approx(.15865525393145707)
    assert _calcular_probabilidad_over(10, 2, 12, 'desconocida') == _calcular_probabilidad_over(10, 2, 12, 'normal')
    l,e,v,_ = _calcular_1x2_dixon_coles(1.5, 1.5)
    assert l == pytest.approx(v) and l + e + v == pytest.approx(1)


class Cursor:
    def __init__(self):
        self.filas = [{'id': 'sintetico', 'local_goles_1t': None, 'visitante_goles_1t': 0}]
        self.llamadas = []

    def execute(self, sql, params):
        self.llamadas.append((sql, params))

    def fetchall(self):
        return self.filas


@pytest.mark.parametrize('funcion,args', [
    (_obtener_partidos_equipo, ['eq']), (_obtener_partidos_h2h, ['eq', 'rival']),
    (_obtener_partidos_liga, ['liga']),
])
def test_lectura_parametrizada_preserva_corte_exclusivo_temporadas_y_null(funcion, args):
    cursor = Cursor()
    corte = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token = "temporada'; no-es-sql"
    r = funcion(cursor, *args, corte, 30, temporada_ids=[token], fecha_minima=corte)
    assert r is cursor.filas and r[0]['local_goles_1t'] is None and r[0]['visitante_goles_1t'] == 0
    assert len(cursor.llamadas) == 1
    sql, params = cursor.llamadas[0]
    assert sql.strip().startswith('SELECT') and 'pf.fecha_partido < %s' in sql
    assert token not in sql and [token] in params and corte in params
    assert 'pf.fecha_partido >= %s' not in sql  # Temporadas explícitas prevalecen sobre fallback.
    assert 'ORDER BY pf.fecha_partido DESC,pf.id DESC LIMIT %s' in sql and params[-1] == 30


def test_compatibilidad_de_importacion_http_sin_copias_matematicas():
    from api import rutas_analisis_futbol as r
    assert r._calcular_probabilidad_over is _calcular_probabilidad_over
    assert r._calcular_1x2_dixon_coles is _calcular_1x2_dixon_coles
    assert r._obtener_partidos_equipo is _obtener_partidos_equipo

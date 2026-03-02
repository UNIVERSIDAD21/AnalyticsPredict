from api.rutas_analisis_futbol import _calcular_1x2_poisson


def test_poisson_1x2_suma_uno_aproximadamente():
    pl, pe, pv, marcador = _calcular_1x2_poisson(1.6, 1.1)
    total = pl + pe + pv
    assert 0.999 <= total <= 1.001
    assert isinstance(marcador, str) and '-' in marcador


def test_poisson_1x2_favorece_local_cuando_xg_local_mayor():
    pl, pe, pv, _ = _calcular_1x2_poisson(2.2, 0.8)
    assert pl > pv

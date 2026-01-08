import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.calculadora_probabilidad import calcular_devig
from motor.tipos import AnalisisMercado, TipoRecomendacion


def test_analisis_mercado_exacto_usa_probabilidad_fair():
    datos = calcular_devig(1.9, 1.9)
    analisis = AnalisisMercado.calcular(0.56, 1.9, datos, umbral_edge_valor=0.05)

    assert analisis.datos_devig.metodo == "exacto"
    assert analisis.probabilidad_implicita_fair == pytest.approx(datos.p_mkt_fair)
    assert analisis.edge_raw == pytest.approx(0.56 - datos.p_mkt_raw)
    assert analisis.edge_real == pytest.approx(0.56 - datos.p_mkt_fair)


def test_analisis_mercado_no_aplicado_conserva_raw():
    datos = calcular_devig(2.0, modo_estimado=False)
    analisis = AnalisisMercado.calcular(0.55, 2.0, datos, umbral_edge_valor=0.05)

    assert analisis.datos_devig.metodo == "no_aplicado"
    assert analisis.probabilidad_implicita_fair == pytest.approx(analisis.probabilidad_implicita_raw)
    assert analisis.edge_real == pytest.approx(analisis.edge_raw)


def test_analisis_mercado_estimado_usa_overround_por_defecto():
    datos = calcular_devig(2.0, modo_estimado=True)
    analisis = AnalisisMercado.calcular(0.55, 2.0, datos, umbral_edge_valor=0.05)

    assert analisis.datos_devig.metodo == "estimado"
    assert analisis.probabilidad_implicita_fair == pytest.approx(datos.p_mkt_fair)


def test_recomendacion_ev_negativo_es_evitar():
    datos = calcular_devig(1.5, modo_estimado=False)
    analisis = AnalisisMercado.calcular(0.4, 1.5, datos, umbral_edge_valor=0.05)

    assert analisis.valor_esperado < 0
    assert analisis.recomendacion == TipoRecomendacion.EVITAR


def test_recomendacion_ev_positivo_edge_real_negativo_es_evitar():
    datos = calcular_devig(2.5, 2.5)
    analisis = AnalisisMercado.calcular(0.45, 2.5, datos, umbral_edge_valor=0.05)

    assert analisis.valor_esperado > 0
    assert analisis.edge_real <= 0
    assert analisis.recomendacion == TipoRecomendacion.EVITAR


def test_recomendacion_valor_supera_umbral():
    datos = calcular_devig(2.0, 2.0)
    analisis = AnalisisMercado.calcular(0.6, 2.0, datos, umbral_edge_valor=0.05)

    assert analisis.valor_esperado > 0
    assert analisis.edge_real > 0.05
    assert analisis.recomendacion == TipoRecomendacion.VALOR

# -*- coding: utf-8 -*-

from servicios.b3_estabilizacion_futbol import (
    ajustar_probabilidad_por_muestras,
    combinar_valor_cross_liga,
    nivel_confianza_b3,
    peso_contexto_por_competicion,
)


def test_peso_contexto_por_competicion_known_and_default():
    assert peso_contexto_por_competicion("PREMIER_LEAGUE") > peso_contexto_por_competicion("LIGA_X")
    assert peso_contexto_por_competicion(None) == 0.70


def test_combinar_valor_cross_liga_aumenta_peso_liga_con_baja_muestra():
    con_muestra = combinar_valor_cross_liga(
        valor_ctx=8.0,
        n_ctx=30,
        valor_global=9.0,
        n_global=120,
        valor_liga=10.0,
        codigo_competicion="LALIGA",
    )
    sin_muestra = combinar_valor_cross_liga(
        valor_ctx=8.0,
        n_ctx=2,
        valor_global=9.0,
        n_global=120,
        valor_liga=10.0,
        codigo_competicion="LALIGA",
    )
    assert sin_muestra > con_muestra


def test_ajustar_probabilidad_por_muestras_contrae_edge():
    p_alta_muestra = ajustar_probabilidad_por_muestras(0.72, n_total=100, n_relevante=30)
    p_baja_muestra = ajustar_probabilidad_por_muestras(0.72, n_total=20, n_relevante=4)

    assert p_alta_muestra > p_baja_muestra
    assert p_baja_muestra > 0.5


def test_nivel_confianza_b3():
    assert nivel_confianza_b3(0.8, n_total=90, n_relevante=26) == "ALTA"
    assert nivel_confianza_b3(0.62, n_total=50, n_relevante=15) == "MEDIA"
    assert nivel_confianza_b3(0.6, n_total=10, n_relevante=3) == "BAJA"

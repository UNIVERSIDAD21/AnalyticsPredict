import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.ajustes.aplicador_ajustes import aplicar_ajustes
from motor.ajustes.motor_ajustes import aplicar_ajustes_contextuales
from motor.ajustes.reglas_ajuste import calcular_ajustes
from motor.ajustes.tipos_ajustes import AjusteIndividual, ResultadoAjustes
from motor.ajustes.validador_ajustes import aplicar_caps
from motor.contexto.tipos_contexto import (
    ContextoCompleto,
    ContextoDescanso,
    ContextoForma,
    ContextoH2H,
)
from motor.generador_razones import generar_razones_basicas
from motor.tipos import NivelConfianza
from motor.calculadora_probabilidad import calcular_probabilidad_over


def _contexto_base(**overrides):
    forma = ContextoForma(
        ultimos_n=10,
        victorias=5,
        derrotas=5,
        racha="W1",
        ppg=110.0,
        opp_ppg=108.0,
        net_rating=2.0,
        ppg_temporada=110.0,
        diferencia_vs_temporada=0.0,
        tendencia="ESTABLE",
    )
    descanso = ContextoDescanso(
        dias_descanso=1,
        es_back_to_back=False,
        ultimo_partido=None,
        distancia_viaje_km=None,
    )
    base = ContextoCompleto(
        h2h=None,
        forma_equipo=forma,
        forma_rival=forma,
        descanso_equipo=descanso,
        descanso_rival=descanso,
        stats_temporada_equipo={},
        stats_temporada_rival={},
    )
    for clave, valor in overrides.items():
        setattr(base, clave, valor)
    return base


def test_back_to_back_aplica_ajuste():
    contexto = _contexto_base(
        descanso_equipo=ContextoDescanso(
            dias_descanso=0,
            es_back_to_back=True,
            ultimo_partido=None,
            distancia_viaje_km=None,
        )
    )
    resultado = aplicar_caps(calcular_ajustes(contexto, media_base=220.0))
    ajuste_b2b = next(
        ajuste for ajuste in resultado.ajustes if ajuste.factor == "back_to_back"
    )
    assert ajuste_b2b.valor == pytest.approx(-4.0)


def test_h2h_aplica_ajuste_con_muestra():
    contexto = _contexto_base(
        h2h=ContextoH2H(
            total_partidos=5,
            victorias_equipo=2,
            victorias_rival=3,
            promedio_total=230.0,
            promedio_equipo=115.0,
            promedio_rival=115.0,
            tendencia_over=0.6,
            ultimo_enfrentamiento=None,
            partidos=[],
        )
    )
    resultado = aplicar_caps(calcular_ajustes(contexto, media_base=220.0))
    ajuste_h2h = next(
        ajuste for ajuste in resultado.ajustes if ajuste.factor == "h2h_tendencia"
    )
    assert ajuste_h2h.valor == pytest.approx(3.0)


def test_h2h_no_aplica_con_muestra_insuficiente():
    contexto = _contexto_base(
        h2h=ContextoH2H(
            total_partidos=2,
            victorias_equipo=1,
            victorias_rival=1,
            promedio_total=230.0,
            promedio_equipo=115.0,
            promedio_rival=115.0,
            tendencia_over=0.5,
            ultimo_enfrentamiento=None,
            partidos=[],
        )
    )
    resultado = aplicar_caps(calcular_ajustes(contexto, media_base=220.0))
    assert all(ajuste.factor != "h2h_tendencia" for ajuste in resultado.ajustes)


def test_ajuste_total_no_excede_cap():
    resultado = ResultadoAjustes(
        ajustes=[
            AjusteIndividual(
                factor="forma",
                valor=5.0,
                direccion="sube",
                confianza_ajuste=0.8,
                descripcion="",
                datos_soporte={},
            ),
            AjusteIndividual(
                factor="forma",
                valor=5.0,
                direccion="sube",
                confianza_ajuste=0.8,
                descripcion="",
                datos_soporte={},
            ),
            AjusteIndividual(
                factor="forma",
                valor=5.0,
                direccion="sube",
                confianza_ajuste=0.8,
                descripcion="",
                datos_soporte={},
            ),
        ],
        ajuste_total=15.0,
        ajuste_total_capped=15.0,
        fue_capped=False,
        advertencias=[],
        confianza_delta=0.0,
    )
    resultado = aplicar_caps(resultado)
    assert abs(resultado.ajuste_total_capped) <= 8.0
    assert resultado.fue_capped is True


def test_probabilidades_recalculadas():
    ajustes = ResultadoAjustes(
        ajustes=[
            AjusteIndividual(
                factor="forma",
                valor=4.0,
                direccion="sube",
                confianza_ajuste=0.7,
                descripcion="",
                datos_soporte={},
            )
        ],
        ajuste_total=4.0,
        ajuste_total_capped=4.0,
        fue_capped=False,
        advertencias=[],
        confianza_delta=0.0,
    )
    media_base = 220.0
    desviacion = 20.0
    linea = 222.5
    prob_base = calcular_probabilidad_over(media_base, desviacion, linea)
    media_ajustada, prob_over, prob_under = aplicar_ajustes(
        media_base=media_base,
        desviacion_base=desviacion,
        linea=linea,
        ajustes=ajustes,
        mercado="COMPLETO",
    )
    assert media_ajustada == pytest.approx(224.0)
    assert prob_over != pytest.approx(prob_base)
    assert prob_under == pytest.approx(1.0 - prob_over)


def test_razones_indican_partido_y_cuarto():
    razones_completo = generar_razones_basicas(
        nombre_equipo="LAL",
        nombre_rival="BOS",
        media_equipo=110.0,
        media_rival=108.0,
        media_total=218.0,
        mercado="COMPLETO",
    )
    assert "partido" in razones_completo[1].descripcion

    razones_cuarto = generar_razones_basicas(
        nombre_equipo="LAL",
        nombre_rival="BOS",
        media_equipo=28.0,
        media_rival=27.0,
        media_total=55.0,
        mercado="Q1",
    )
    assert "cuarto" in razones_cuarto[1].descripcion


def test_confianza_baja_con_b2b_y_h2h_contradiccion():
    contexto = _contexto_base(
        h2h=ContextoH2H(
            total_partidos=5,
            victorias_equipo=2,
            victorias_rival=3,
            promedio_total=240.0,
            promedio_equipo=120.0,
            promedio_rival=120.0,
            tendencia_over=0.8,
            ultimo_enfrentamiento=None,
            partidos=[],
        ),
        descanso_equipo=ContextoDescanso(
            dias_descanso=0,
            es_back_to_back=True,
            ultimo_partido=None,
            distancia_viaje_km=None,
        ),
    )
    prediccion = aplicar_ajustes_contextuales(
        contexto=contexto,
        media_base=220.0,
        desviacion_base=20.0,
        probabilidad_over_base=0.48,
        probabilidad_under_base=0.52,
        linea=222.5,
        mercado="COMPLETO",
        confianza_base=NivelConfianza.MEDIA,
    )
    assert prediccion.confianza_ajustada == "BAJA"

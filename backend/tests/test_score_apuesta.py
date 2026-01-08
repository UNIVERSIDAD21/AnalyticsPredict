import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.tipos import DatosDeVig, ScoreApuesta


def _datos_devig(metodo: str) -> DatosDeVig:
    if metodo == "no_aplicado":
        return DatosDeVig(
            metodo="no_aplicado",
            overround=None,
            p_mkt_raw=0.5,
            p_mkt_fair=0.5,
            advertencias=[],
        )
    return DatosDeVig(
        metodo=metodo,
        overround=1.05,
        p_mkt_raw=0.5,
        p_mkt_fair=0.48,
        advertencias=[],
    )


def test_gate_ev_invalido_bloquea():
    score = ScoreApuesta.calcular(
        ev=0.0,
        edge_real=0.1,
        riesgo=5.0,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.1,
    )

    assert score.gates_pasados is False
    assert score.score_total == pytest.approx(-1000.0)


def test_gate_edge_real_invalido_bloquea():
    score = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.0,
        riesgo=5.0,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.1,
    )

    assert score.gates_pasados is False
    assert score.score_total == pytest.approx(-1000.0)


def test_gate_kelly_invalido_bloquea():
    score = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=5.0,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.0,
    )

    assert score.gates_pasados is False
    assert score.score_total == pytest.approx(-1000.0)


def test_penalizacion_riesgo_aplica_solo_si_es_alto():
    score_bajo = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=5.5,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.1,
    )
    score_alto = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=7.0,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.1,
    )

    assert score_bajo.componentes["riesgo"] == pytest.approx(0.0)
    assert score_alto.componentes["riesgo"] < 0
    assert "Riesgo alto" in score_alto.penalizaciones_aplicadas


def test_penalizacion_devig_segun_metodo():
    score_exacto = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=5.0,
        datos_devig=_datos_devig("exacto"),
        kelly_full=0.1,
    )
    score_estimado = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=5.0,
        datos_devig=_datos_devig("estimado"),
        kelly_full=0.1,
    )
    score_no_aplicado = ScoreApuesta.calcular(
        ev=0.1,
        edge_real=0.1,
        riesgo=5.0,
        datos_devig=_datos_devig("no_aplicado"),
        kelly_full=0.1,
    )

    assert score_exacto.componentes["devig"] == pytest.approx(0.0)
    assert score_estimado.componentes["devig"] < score_exacto.componentes["devig"]
    assert score_no_aplicado.componentes["devig"] < score_estimado.componentes["devig"]
    assert "De-vig estimado" in score_estimado.penalizaciones_aplicadas
    assert "Sin de-vig" in score_no_aplicado.penalizaciones_aplicadas


def test_componentes_y_explicacion_auditables():
    score = ScoreApuesta.calcular(
        ev=0.12,
        edge_real=0.08,
        riesgo=6.2,
        datos_devig=_datos_devig("estimado"),
        kelly_full=0.1,
    )

    assert set(score.componentes.keys()) >= {"ev", "edge_real", "riesgo", "devig"}
    assert "EV=" in score.explicacion
    assert "Edge=" in score.explicacion
    assert score.penalizaciones_aplicadas

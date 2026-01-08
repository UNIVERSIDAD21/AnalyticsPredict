import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.nba_predictor_cuartos import candidatos_para_cuarto
from motor.tipos import ScoreApuesta


def test_candidatos_con_dos_cuotas_generan_score_completo():
    candidatos = candidatos_para_cuarto(
        cuarto="Q1",
        linea=50.0,
        media_equipo=28.0,
        desviacion_equipo=3.0,
        media_rival=25.0,
        desviacion_rival=3.0,
        cuota_over=2.0,
        cuota_under=1.8,
        modo_devig="estricto",
        config_sizing=None,
    )

    assert len(candidatos) == 2
    for candidato in candidatos:
        assert candidato.datos_devig is not None
        assert candidato.datos_devig.metodo == "exacto"
        assert candidato.edge_real is not None
        assert candidato.ev is not None
        assert candidato.score is not None
        assert candidato.sizing is None


def test_candidatos_con_una_cuota_stricto_penaliza_sin_devig():
    candidatos = candidatos_para_cuarto(
        cuarto="Q1",
        linea=50.0,
        media_equipo=28.0,
        desviacion_equipo=3.0,
        media_rival=25.0,
        desviacion_rival=3.0,
        cuota_over=2.0,
        cuota_under=None,
        modo_devig="estricto",
        config_sizing=None,
    )

    assert len(candidatos) == 1
    candidato = candidatos[0]
    assert candidato.datos_devig is not None
    assert candidato.datos_devig.metodo == "no_aplicado"
    assert candidato.score is not None
    assert ScoreApuesta.CODIGO_SIN_DEVIG in candidato.score.penalizaciones_aplicadas


def test_candidatos_con_una_cuota_estimado_penaliza_devig():
    candidatos = candidatos_para_cuarto(
        cuarto="Q1",
        linea=50.0,
        media_equipo=28.0,
        desviacion_equipo=3.0,
        media_rival=25.0,
        desviacion_rival=3.0,
        cuota_over=None,
        cuota_under=1.8,
        modo_devig="estimado",
        config_sizing=None,
    )

    assert len(candidatos) == 1
    candidato = candidatos[0]
    assert candidato.datos_devig is not None
    assert candidato.datos_devig.metodo == "estimado"
    assert candidato.score is not None
    assert ScoreApuesta.CODIGO_DEVIG_ESTIMADO in candidato.score.penalizaciones_aplicadas

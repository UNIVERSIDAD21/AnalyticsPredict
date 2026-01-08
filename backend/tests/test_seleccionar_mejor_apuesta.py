import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.nba_predictor_cuartos import seleccionar_mejor_apuesta
from motor.tipos import CandidatoApuesta, LadoApuesta, ScoreApuesta, TipoMercado


def _candidato(score_total: float, gates: bool, ev: float = 0.1, edge: float = 0.1) -> CandidatoApuesta:
    score = ScoreApuesta(
        score_total=score_total,
        componentes={},
        gates_pasados=gates,
        explicacion="score test",
    )
    return CandidatoApuesta(
        cuarto="Q1",
        mercado=TipoMercado.TOTAL,
        lado=LadoApuesta.OVER,
        linea=50.0,
        probabilidad=0.55,
        media=52.0,
        desviacion=6.0,
        distancia_z=0.3,
        score=score,
        ev=ev,
        edge_real=edge,
    )


def test_seleccionar_mejor_apuesta_lista_vacia():
    assert seleccionar_mejor_apuesta([]) is None


def test_seleccionar_mejor_apuesta_sin_gates():
    candidatos = [_candidato(score_total=5.0, gates=False)]
    assert seleccionar_mejor_apuesta(candidatos) is None


def test_seleccionar_mejor_apuesta_por_score_total():
    candidato_bajo = _candidato(score_total=5.0, gates=True)
    candidato_alto = _candidato(score_total=7.0, gates=True)
    assert seleccionar_mejor_apuesta([candidato_bajo, candidato_alto]) == candidato_alto


def test_seleccionar_mejor_apuesta_empate_resuelve_por_ev():
    candidato_menor_ev = _candidato(score_total=7.0, gates=True, ev=0.05)
    candidato_mayor_ev = _candidato(score_total=7.0, gates=True, ev=0.15)
    assert seleccionar_mejor_apuesta([candidato_menor_ev, candidato_mayor_ev]) == candidato_mayor_ev

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.calculadora_probabilidad import calcular_kelly
from motor.tipos import ConfiguracionSizing, DatosDeVig, PerfilRiesgo


def _config_base(
    perfil: PerfilRiesgo = PerfilRiesgo.CONSERVADOR,
    bankroll: float | None = 1000.0,
    cap_por_apuesta: float = 0.5,
    cap_diario: float = 1.0,
    stake_minimo: float = 5.0,
) -> ConfiguracionSizing:
    return ConfiguracionSizing(
        cap_por_apuesta=cap_por_apuesta,
        cap_diario=cap_diario,
        stake_minimo=stake_minimo,
        fraccion_kelly_conservador=0.125,
        fraccion_kelly_medio=0.25,
        fraccion_kelly_agresivo=0.5,
        perfil_riesgo=perfil,
        bankroll=bankroll,
    )


def _datos_devig(metodo: str) -> DatosDeVig:
    return DatosDeVig(
        metodo=metodo,
        overround=1.05,
        p_mkt_raw=0.5,
        p_mkt_fair=0.5,
        advertencias=[],
    )


def test_kelly_negativo_no_apostar():
    config = _config_base()
    resultado = calcular_kelly(0.4, 2.0, config, _datos_devig("exacto"))

    assert resultado.kelly_full == pytest.approx(-0.2)
    assert resultado.kelly_fraccional == 0.0
    assert resultado.stake_porcentaje == 0.0
    assert resultado.penalizaciones["kelly_negativo"] == 1.0


def test_penaliza_devig_estimado():
    config = _config_base()
    resultado = calcular_kelly(0.6, 2.0, config, _datos_devig("estimado"))

    assert resultado.kelly_fraccional == pytest.approx(0.0125)
    assert resultado.penalizaciones["devig_estimado"] == 0.5


def test_penaliza_devig_no_aplicado():
    config = _config_base()
    resultado = calcular_kelly(0.6, 2.0, config, _datos_devig("no_aplicado"))

    assert resultado.kelly_fraccional == pytest.approx(0.0075)
    assert resultado.penalizaciones["devig_no_aplicado"] == 0.3


def test_penaliza_riesgo_alto():
    config = _config_base(perfil=PerfilRiesgo.MEDIO)
    resultado = calcular_kelly(0.6, 2.0, config, _datos_devig("exacto"), riesgo_alto=True)

    assert resultado.kelly_fraccional == pytest.approx(0.035)
    assert resultado.penalizaciones["riesgo_alto"] == 0.7


def test_aplica_cap_por_apuesta():
    config = _config_base(perfil=PerfilRiesgo.AGRESIVO, cap_por_apuesta=0.01)
    resultado = calcular_kelly(0.8, 2.0, config, _datos_devig("exacto"))

    assert resultado.kelly_fraccional == pytest.approx(0.01)
    assert resultado.aplicaron_caps is True


def test_calcula_porcentaje_y_stake_minimo():
    config = _config_base(bankroll=100.0, stake_minimo=5.0)
    resultado = calcular_kelly(0.6, 2.0, config, _datos_devig("exacto"))

    assert resultado.stake_porcentaje == pytest.approx(2.5)
    assert resultado.stake == pytest.approx(2.5)
    assert "Stake por debajo del mínimo configurado." in resultado.advertencias

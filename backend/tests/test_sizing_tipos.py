import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.tipos import (
    ConfiguracionSizing,
    PerfilRiesgo,
    ResultadoSizing,
    DEFAULT_CAP_POR_APUESTA,
)


def test_perfil_riesgo_valores_exactos():
    valores = {perfil.value for perfil in PerfilRiesgo}
    assert valores == {"CONSERVADOR", "MEDIO", "AGRESIVO"}


def test_configuracion_sizing_desde_dict_con_faltantes():
    config_usuario = {
        "cap_diario": 0.15,
        "stake_minimo": 10.0,
        "fraccion_kelly_conservador": 0.1,
        "fraccion_kelly_medio": 0.2,
        "fraccion_kelly_agresivo": 0.4,
    }

    config = ConfiguracionSizing.construir_desde_fuentes(
        config_sizing_usuario=config_usuario,
        bankroll_override=None,
        perfil_override=None,
        bankroll_usuario=1500.0,
        perfil_default="MEDIO",
    )

    assert config.cap_por_apuesta == pytest.approx(DEFAULT_CAP_POR_APUESTA)
    assert any("cap_por_apuesta" in aviso for aviso in config.advertencias)
    assert config.perfil_riesgo == PerfilRiesgo.MEDIO
    assert config.bankroll == pytest.approx(1500.0)


def test_resultado_sizing_serializa_para_bd():
    resultado = ResultadoSizing(
        kelly_full=0.08,
        kelly_fraccional=0.02,
        fraccion_aplicada=0.25,
        stake_recomendado=12.5,
        stake_porcentaje=0.01,
        bankroll_momento=1250.0,
        perfil_riesgo_usado=PerfilRiesgo.CONSERVADOR,
        advertencias=["sin bankroll"],
        penalizaciones={"cap_por_apuesta": 0.02},
        aplicaron_caps=True,
    )

    serializado = resultado.como_diccionario()

    assert isinstance(serializado["sizing_advertencias"], list)
    assert isinstance(serializado["sizing_penalizaciones"], dict)
    assert serializado["perfil_riesgo_usado"] == "CONSERVADOR"

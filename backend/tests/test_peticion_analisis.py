import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionAnalisis
from api.rutas_analisis import _construir_configuracion_sizing
from motor.tipos import PerfilRiesgo


def _peticion_base(**kwargs):
    data = {
        "equipo_local": "Lakers",
        "equipo_visitante": "Heat",
        "mercado": "Q1",
        "linea": 200.0,
    }
    data.update(kwargs)
    return PeticionAnalisis(**data)


def test_valida_perfil_riesgo_case_insensitive():
    peticion = _peticion_base(perfil_riesgo="medio")
    assert peticion.perfil_riesgo == "MEDIO"


def test_valida_modo_devig_case_insensitive():
    peticion = _peticion_base(modo_devig="ESTIMADO")
    assert peticion.modo_devig == "estimado"


def test_invalida_perfil_riesgo():
    with pytest.raises(ValueError):
        _peticion_base(perfil_riesgo="ULTRA")


def test_precedencia_request_sobre_usuario():
    peticion = _peticion_base(bankroll=1200.0, perfil_riesgo="AGRESIVO")
    datos_usuario = {
        "bankroll_actual": 800.0,
        "perfil_riesgo_default": "CONSERVADOR",
        "config_sizing": {},
    }

    config = _construir_configuracion_sizing(peticion, datos_usuario)

    assert config.bankroll == pytest.approx(1200.0)
    assert config.perfil_riesgo == PerfilRiesgo.AGRESIVO


def test_precedencia_usuario_si_request_no_envia():
    peticion = _peticion_base()
    datos_usuario = {
        "bankroll_actual": 800.0,
        "perfil_riesgo_default": "MEDIO",
        "config_sizing": {},
    }

    config = _construir_configuracion_sizing(peticion, datos_usuario)

    assert config.bankroll == pytest.approx(800.0)
    assert config.perfil_riesgo == PerfilRiesgo.MEDIO

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.modelos_peticion import PeticionAnalisis
from api.rutas_analisis import _validar_peticion_analisis
from api.excepciones import ErrorValidacion


def test_validar_peticion_requiere_lado_con_cuotas():
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        cuota=1.9,
    )

    with pytest.raises(ErrorValidacion):
        _validar_peticion_analisis(peticion)


def test_validar_peticion_advierte_devig_estricto_con_una_cuota():
    peticion = PeticionAnalisis(
        equipo_local="Lakers",
        equipo_visitante="Heat",
        mercado="Q1",
        linea=50.5,
        cuota_over=1.9,
        lado="OVER",
        modo_devig="estricto",
    )

    advertencias = _validar_peticion_analisis(peticion)

    assert any("no se aplicará de-vig exacto" in mensaje for mensaje in advertencias)

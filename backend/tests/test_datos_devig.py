import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.tipos import DatosDeVig


def test_datos_devig_exacto_requiere_overround():
    with pytest.raises(ValueError):
        DatosDeVig(
            metodo="exacto",
            overround=None,
            p_mkt_raw=0.52,
            p_mkt_fair=0.50,
        )


def test_datos_devig_no_aplicado_mantiene_probabilidad():
    with pytest.raises(ValueError):
        DatosDeVig(
            metodo="no_aplicado",
            overround=None,
            p_mkt_raw=0.52,
            p_mkt_fair=0.50,
        )

    datos = DatosDeVig(
        metodo="no_aplicado",
        overround=None,
        p_mkt_raw=0.52,
        p_mkt_fair=0.52,
    )

    assert datos.p_mkt_fair == datos.p_mkt_raw
    assert datos.vig_porcentaje is None


def test_datos_devig_estimado_valido():
    datos = DatosDeVig(
        metodo="estimado",
        overround=1.04,
        p_mkt_raw=0.52,
        p_mkt_fair=0.50,
        advertencias=["Overround estimado"],
    )

    assert datos.vig_porcentaje == pytest.approx(4.0)

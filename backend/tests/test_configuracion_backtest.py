import sys
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.configuracion import ConfiguracionBacktest, ModoCutoff, ModoVentana


def test_configuracion_invalida_falla():
    with pytest.raises(ValidationError) as excinfo:
        ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            modo_cutoff=ModoCutoff.POR_BLOQUE,
        )

    assert "tamano_bloque" in str(excinfo.value)


def test_configuracion_valida_defaults_y_serializacion():
    config = ConfiguracionBacktest(fecha_inicio=date(2024, 1, 1))

    assert config.modo_ventana == ModoVentana.TODAS_TEMPORADAS
    assert config.excluir_pretemporada is True
    assert config.mercados
    assert config.min_partidos_entrenamiento > 0

    serial_1 = config.to_json_dict()
    serial_2 = config.to_json_dict()

    assert serial_1 == serial_2
    assert config.to_json_string() == config.to_json_string()


def test_configuracion_offset_sintetico_requiere_cero():
    with pytest.raises(ValidationError) as excinfo:
        ConfiguracionBacktest(
            fecha_inicio=date(2024, 1, 1),
            usar_lineas_sinteticas=True,
            offsets_linea=[1.5],
        )

    assert "offsets_linea" in str(excinfo.value)

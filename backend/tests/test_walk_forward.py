import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.configuracion import ConfiguracionBacktest, ModoCutoff
from backtesting.walk_forward import iterar_walk_forward


def _partido(
    fecha: date,
    temporada: int = 2023,
    equipo_local: int = 1,
    equipo_visitante: int = 2,
    tipo_partido: str = "REG",
):
    return {
        "fecha_partido": fecha,
        "temporada_id": temporada,
        "equipo_local_id": equipo_local,
        "equipo_visitante_id": equipo_visitante,
        "tipo_partido": tipo_partido,
    }


def test_walk_forward_diario_sin_leakage():
    partidos = [
        _partido(date(2023, 1, 1), tipo_partido="PRE"),
        _partido(date(2023, 1, 1), equipo_local=3, equipo_visitante=4),
        _partido(date(2023, 1, 2), equipo_local=5, equipo_visitante=6),
        _partido(date(2023, 1, 3), equipo_local=7, equipo_visitante=8),
    ]
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 4),
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    iteraciones = list(iterar_walk_forward(partidos, config))

    assert len(iteraciones) == 2
    for iteracion in iteraciones:
        assert all(
            partido["fecha_partido"] < iteracion.cutoff_date
            for partido in iteracion.partidos_entrenamiento
        )
        assert iteracion.metadata["partidos_excluidos_pretemporada"] >= 0


def test_walk_forward_semanal():
    partidos = [
        _partido(date(2023, 1, 1)),
        _partido(date(2023, 1, 5)),
        _partido(date(2023, 1, 9)),
        _partido(date(2023, 1, 15)),
        _partido(date(2023, 1, 20)),
    ]
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 22),
        modo_cutoff=ModoCutoff.SEMANAL,
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    iteraciones = list(iterar_walk_forward(partidos, config))

    assert len(iteraciones) == 2
    assert iteraciones[1].metadata["n_prediccion"] == 2


def test_walk_forward_por_bloque():
    partidos = [
        _partido(date(2023, 1, 1), equipo_local=1, equipo_visitante=2),
        _partido(date(2023, 1, 2), equipo_local=3, equipo_visitante=4),
        _partido(date(2023, 1, 3), equipo_local=5, equipo_visitante=6),
        _partido(date(2023, 1, 4), equipo_local=7, equipo_visitante=8),
        _partido(date(2023, 1, 5), equipo_local=9, equipo_visitante=10),
    ]
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 6),
        modo_cutoff=ModoCutoff.POR_BLOQUE,
        tamano_bloque=2,
        min_partidos_entrenamiento=1,
        min_temporadas_historia=1,
    )

    iteraciones = list(iterar_walk_forward(partidos, config))

    assert len(iteraciones) == 2
    assert iteraciones[0].metadata["n_prediccion"] == 2
    assert iteraciones[1].metadata["n_prediccion"] == 1


def test_skip_por_falta_entrenamiento(caplog):
    partidos = [_partido(date(2023, 1, 1)), _partido(date(2023, 1, 2))]
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 3),
        min_partidos_entrenamiento=5,
        min_temporadas_historia=1,
    )

    with caplog.at_level("WARNING"):
        iteraciones = list(iterar_walk_forward(partidos, config))

    assert not iteraciones
    assert "entrenamiento insuficiente" in caplog.text


def test_skip_por_falta_temporadas(caplog):
    partidos = [_partido(date(2023, 1, 1), temporada=2023)]
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 2),
        min_partidos_entrenamiento=1,
        min_temporadas_historia=2,
    )

    with caplog.at_level("WARNING"):
        iteraciones = list(iterar_walk_forward(partidos, config))

    assert not iteraciones
    assert "historia insuficiente" in caplog.text

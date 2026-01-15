from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backtesting.configuracion import ConfiguracionBacktest
from motor_autoentrenamiento.entrenador_bd import EntrenadorBD


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows
        self._result = []
        self.description = []
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params
        columnas = [
            "id",
            "fecha_partido",
            "tipo_partido",
            "temporada_id",
            "equipo_local_id",
            "equipo_visitante_id",
            "equipo_local",
            "equipo_visitante",
            "local_q1",
            "local_q2",
            "local_q3",
            "local_q4",
            "visitante_q1",
            "visitante_q2",
            "visitante_q3",
            "visitante_q4",
        ]
        self.description = [(col,) for col in columnas]
        cutoff = next((p for p in params if isinstance(p, date)), None)
        filas = self._rows
        if cutoff:
            filas = [fila for fila in filas if fila[1] < cutoff]
        self._result = filas

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0] if self._result else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, rows):
        self._rows = rows
        self.cursor_obj = FakeCursor(rows)

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, rows):
        self._rows = rows
        self.connection_obj = FakeConnection(rows)

    def connection(self):
        return self.connection_obj


def _filas_base():
    return [
        (
            1,
            date(2023, 1, 1),
            "REG",
            "2023",
            10,
            20,
            "Team A",
            "Team B",
            25,
            22,
            24,
            23,
            20,
            21,
            22,
            19,
        ),
        (
            2,
            date(2023, 1, 2),
            "REG",
            "2023",
            30,
            40,
            "Team C",
            "Team D",
            26,
            24,
            25,
            22,
            23,
            20,
            21,
            18,
        ),
    ]


def test_cutoff_filtra_partidos():
    pool = FakePool(_filas_base())
    entrenador = EntrenadorBD(pool)
    partidos = entrenador._obtener_partidos(cutoff_fecha=date(2023, 1, 2))

    assert partidos
    assert all(p["fecha_partido"] < date(2023, 1, 2) for p in partidos)
    assert "p.fecha_partido < %s" in pool.connection_obj.cursor_obj.query


def test_hash_cambia_con_cutoffs_distintos():
    pool = FakePool(_filas_base())
    entrenador = EntrenadorBD(pool)
    partidos_primero = entrenador._obtener_partidos(cutoff_fecha=date(2023, 1, 2))
    partidos_segundo = entrenador._obtener_partidos(cutoff_fecha=date(2023, 1, 3))

    hash_primero = entrenador._calcular_hash_datos(partidos_primero)
    hash_segundo = entrenador._calcular_hash_datos(partidos_segundo)

    assert hash_primero != hash_segundo


def test_skip_si_partidos_insuficientes(caplog):
    pool = FakePool(_filas_base())
    entrenador = EntrenadorBD(pool)
    config = ConfiguracionBacktest(
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 3),
        min_partidos_entrenamiento=3,
        min_temporadas_historia=1,
    )

    with caplog.at_level("WARNING"):
        resultado = entrenador.entrenar_para_backtest(date(2023, 1, 3), config)

    assert resultado["estado"] == "skip"
    assert "Skip entrenamiento" in caplog.text

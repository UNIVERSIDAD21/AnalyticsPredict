"""Calibración solo con predicciones resueltas y prospectivas."""

from datetime import datetime, timezone
from math import log
import os
from uuid import uuid4

import numpy as np
import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from motor_futbol.tipos import TipoMercadoFutbol
from scripts.calibrar_futbol import ParTemporal, obtener_datos_calibracion, dividir_train_validation
from scripts.re_scorecard_corners_b17 import _current
from scripts.rescate_corners_prioritarios_b16 import _metricas
from scripts import expansion_corners_b20a, auditoria_goles_b20b


def test_holdout_temporal_no_comparte_dia_de_partido():
    def par(dia, hora, resolucion):
        return ParTemporal(
            datetime(2024, 1, dia, hora, tzinfo=timezone.utc),
            datetime(2023, 12, 31, 10, tzinfo=timezone.utc)
            if dia == 1 else datetime(2024, 1, dia, 10, tzinfo=timezone.utc),
            datetime(2024, 1, dia, resolucion, tzinfo=timezone.utc),
        )
    fechas = [par(1, 12, 16), par(1, 20, 22), par(2, 12, 16), par(3, 12, 16)]
    train_p, train_y, val_p, val_y, cutoff = dividir_train_validation(
        np.array([0.2, 0.3, 0.6, 0.7]), np.array([0, 1, 0, 1]), fechas, 0.25
    )
    assert cutoff.isoformat() == "2024-01-01"
    assert train_p.tolist() == [0.2, 0.3]
    assert train_y.tolist() == [0, 1]
    assert val_p.tolist() == [0.6, 0.7]
    assert val_y.tolist() == [0, 1]


def test_holdout_rechaza_validacion_sin_fecha_posterior():
    fecha = ParTemporal(
        datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
        datetime(2023, 12, 31, tzinfo=timezone.utc),
        datetime(2024, 1, 1, 20, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="fecha posterior"):
        dividir_train_validation(
            np.array([0.2, 0.8]), np.array([0, 1]), [fecha, fecha], 0.5
        )


def test_holdout_rechaza_resultados_no_disponibles_al_predecir_validacion():
    pares = [
        ParTemporal(
            datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
            datetime(2023, 12, 31, tzinfo=timezone.utc),
            datetime(2024, 1, 4, tzinfo=timezone.utc),
        ),
        ParTemporal(
            datetime(2024, 1, 3, 12, tzinfo=timezone.utc),
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 1, 3, 20, tzinfo=timezone.utc),
        ),
    ]
    with pytest.raises(ValueError, match="no disponibles"):
        dividir_train_validation(
            np.array([0.2, 0.8]), np.array([0, 1]), pares, 0.5
        )


def test_fallo_sql_cancela_calibracion_sin_generar_sinteticos():
    class PoolRoto:
        def connection(self):
            raise OSError("sin conexion")

    with pytest.raises(RuntimeError, match="calibración cancelada"):
        obtener_datos_calibracion(PoolRoto(), TipoMercadoFutbol.GOLES_FT)


@pytest.mark.integracion
def test_sql_real_excluye_backfill_y_origenes_no_operativos():
    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    partido_id = uuid4()
    ids = [uuid4() for _ in range(5)]
    with ConnectionPool(url, min_size=1, max_size=2, open=True) as pool:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO partidos_futbol (id, fecha_partido, estado) "
                "VALUES (%s, '2024-01-10T20:00:00Z', 'FINALIZADO')",
                (partido_id,),
            )
            conn.execute(
                "INSERT INTO predicciones_futbol "
                "(id, partido_id, mercado, origen, prob_over, outcome_binario, resuelto, "
                "timestamp_generacion, timestamp_resolucion) VALUES "
                "(%s, %s, 'GOLES_FT', 'API_USUARIO', 0.2, false, true, "
                " '2024-01-09T12:00:00Z', '2024-01-11T12:00:00Z'), "
                "(%s, %s, 'GOLES_FT', 'API_USUARIO', 0.9, true, true, "
                " '2024-01-11T12:00:00Z', '2024-01-12T12:00:00Z'), "
                "(%s, %s, 'GOLES_FT', 'BACKTEST_SINTETICO', 0.7, true, true, "
                " '2024-01-09T12:00:00Z', '2024-01-11T12:00:00Z'), "
                "(%s, %s, 'GOLES_FT', 'BACKTEST_BATCH', 0.7, true, true, "
                " '2024-01-09T12:00:00Z', '2024-01-11T12:00:00Z'), "
                "(%s, %s, 'GOLES_FT', NULL, 0.7, true, true, "
                " '2024-01-09T12:00:00Z', '2024-01-11T12:00:00Z')",
                tuple(item for item in ids for item in (item, partido_id)),
            )
        try:
            raw, outcomes, fechas = obtener_datos_calibracion(
                pool, TipoMercadoFutbol.GOLES_FT
            )
            assert raw.tolist() == [0.2]
            assert outcomes.tolist() == [0]
            assert fechas[0].fecha_partido.date().isoformat() == "2024-01-10"
            assert fechas[0].generacion < fechas[0].fecha_partido
            assert fechas[0].resolucion >= fechas[0].fecha_partido
        finally:
            with pool.connection() as conn:
                conn.execute("DELETE FROM predicciones_futbol WHERE id = ANY(%s)", (ids,))
                conn.execute("DELETE FROM partidos_futbol WHERE id = %s", (partido_id,))


@pytest.mark.integracion
def test_scorecards_corners_usan_raw_si_falta_id_del_calibrador():
    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    ids = [uuid4(), uuid4()]
    with ConnectionPool(url, min_size=1, max_size=2, open=True) as pool:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO predicciones_futbol "
                "(id, mercado, linea, prob_over, prob_over_calibrada, "
                "prob_under_calibrada, calibrador_id, outcome_binario, resuelto) "
                "VALUES (%s, 'CORNERS_1T', 4.5, 0.2, 0.9, 0.1, NULL, false, true), "
                "(%s, 'CORNERS_1T', 5.5, 0.4, 0.7, 0.3, %s, true, true)",
                (ids[0], ids[1], uuid4()),
            )
        try:
            with pool.connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    b16 = _metricas(cur, ["CORNERS_1T"])["CORNERS_1T"]
                    b17 = _current(cur, "CORNERS_1T")
            assert b16["fallback_rows"] == 1
            assert b16["brier"] == pytest.approx(0.065)
            assert b17["fallback_rate"] == pytest.approx(0.5)
            assert b17["brier"] == pytest.approx(0.065)
            assert b17["log_loss"] == pytest.approx((-log(0.8) - log(0.7)) / 2)
        finally:
            with pool.connection() as conn:
                conn.execute("DELETE FROM predicciones_futbol WHERE id = ANY(%s)", (ids,))


@pytest.mark.integracion
def test_reportes_b20_no_atribuyen_calibracion_sin_id(tmp_path, monkeypatch):
    """Ejecuta ambos reportes contra SQL real y comprueba fallback/metricas."""
    import json

    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    partido_id = uuid4()
    ids = [uuid4() for _ in range(4)]
    with ConnectionPool(url, min_size=1, max_size=2, open=True) as pool:
        with pool.connection() as conn:
            conn.execute(
                "INSERT INTO partidos_futbol (id, fecha_partido, estado) "
                "VALUES (%s, '2024-01-10T20:00:00Z', 'FINALIZADO')",
                (partido_id,),
            )
            for mercado, a, b in (("CORNERS_FT", ids[0], ids[1]),
                                  ("GOLES_FT", ids[2], ids[3])):
                conn.execute(
                    "INSERT INTO predicciones_futbol "
                    "(id, partido_id, mercado, linea, prob_over, prob_over_calibrada, "
                    "prob_under_calibrada, calibrador_id, outcome_binario, resuelto) "
                    "VALUES (%s, %s, %s, 4.5, 0.2, 0.9, 0.1, NULL, false, true), "
                    "(%s, %s, %s, 5.5, 0.4, 0.7, 0.3, %s, true, true)",
                    (a, partido_id, mercado, b, partido_id, mercado, uuid4()),
                )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(expansion_corners_b20a, "obtener_pool", lambda: pool)
        monkeypatch.setattr(auditoria_goles_b20b, "obtener_pool", lambda: pool)
        expansion_corners_b20a.main()
        auditoria_goles_b20b.main()
        corners = json.loads((tmp_path / "docs/reportes/BLOQUE_20A_EXPANSION_CORNERS_FAMILIA.json").read_text())
        goles = json.loads((tmp_path / "docs/reportes/BLOQUE_20B_AUDITORIA_GOLES_FAMILIA.json").read_text())
        row_corners = next(x for x in corners["auditoria"] if x["mercado"] == "CORNERS_FT")
        row_goles = next(x for x in goles["auditoria_goles"] if x["mercado"] == "GOLES_FT")
        assert row_corners["fallback_rate"] == 0.5
        assert row_goles["fallback_rate"] == 0.5
        assert row_goles["brier"] == pytest.approx(0.065)
        assert row_goles["log_loss"] == pytest.approx((-log(0.8) - log(0.7)) / 2)

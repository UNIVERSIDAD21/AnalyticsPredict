"""Compatibilidad de la vista legacy NBA y procedencia tras migración H9."""

import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integracion
def test_migracion_vista_preserva_contrato_y_corrige_probabilidad():
    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    legacy_sql = (Path(__file__).with_name("vista_calibracion_legacy.sql")).read_text()
    migracion_sql = (ROOT / "migrations/2026-10-06_h9_vista_calibracion_procedencia.sql").read_text()
    cuerpo = "\n".join(
        line for line in migracion_sql.splitlines()
        if line.strip() not in {"BEGIN;", "COMMIT;"}
    )
    local_id, visitante_id, partido_id, pred_sin_id, pred_con_id = (uuid4() for _ in range(5))
    with psycopg.connect(url) as conn:
        try:
            conn.execute("DROP VIEW vista_predicciones_para_calibracion")
            conn.execute(
                "ALTER TABLE predicciones_registradas "
                "ADD COLUMN equipo_local_nombre text, ADD COLUMN equipo_visitante_nombre text, "
                "ADD COLUMN intervalo_inferior numeric, ADD COLUMN intervalo_superior numeric, "
                "ADD COLUMN nivel_intervalo integer"
            )
            conn.execute("ALTER TABLE equipos ADD COLUMN abreviatura text")
            conn.execute("CREATE TABLE temporadas_baloncesto (id uuid PRIMARY KEY, nombre text)")
            conn.execute("INSERT INTO equipos (id, nombre, abreviatura) VALUES "
                         "(%s, 'Local', 'LOC'), (%s, 'Visitante', 'VIS')",
                         (local_id, visitante_id))
            conn.execute(
                "INSERT INTO predicciones_registradas "
                "(id, partido_id, equipo_local_id, equipo_visitante_id, mercado, lado, "
                "linea, p_raw, p_calibrada, calibrador_id, resuelto, outcome_binario) "
                "VALUES (%s, %s, %s, %s, 'Q1', 'OVER', 50.5, 0.2, 0.9, NULL, true, false), "
                "(%s, %s, %s, %s, 'Q1', 'OVER', 51.5, 0.4, 0.7, %s, true, true)",
                (pred_sin_id, partido_id, local_id, visitante_id,
                 pred_con_id, partido_id, local_id, visitante_id, uuid4()),
            )
            conn.execute(legacy_sql)
            columnas_antes = conn.execute(
                "SELECT attname, atttypid FROM pg_attribute "
                "WHERE attrelid = 'vista_predicciones_para_calibracion'::regclass "
                "AND attnum > 0 AND NOT attisdropped ORDER BY attnum"
            ).fetchall()
            assert len(columnas_antes) == 42
            assert conn.execute(
                "SELECT p_efectiva FROM vista_predicciones_para_calibracion WHERE id = %s",
                (pred_sin_id,),
            ).fetchone()[0] == Decimal("0.9")
            conn.execute(cuerpo)
            columnas_despues = conn.execute(
                "SELECT attname, atttypid FROM pg_attribute "
                "WHERE attrelid = 'vista_predicciones_para_calibracion'::regclass "
                "AND attnum > 0 AND NOT attisdropped ORDER BY attnum"
            ).fetchall()
            assert columnas_despues == columnas_antes
            filas = conn.execute(
                "SELECT id, p_efectiva, bin_p_efectiva "
                "FROM vista_predicciones_para_calibracion ORDER BY p_raw"
            ).fetchall()
            assert filas == [
                (pred_sin_id, Decimal("0.2"), Decimal("0.2")),
                (pred_con_id, Decimal("0.7"), Decimal("0.7")),
            ]
        finally:
            conn.rollback()

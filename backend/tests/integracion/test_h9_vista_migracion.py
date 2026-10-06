"""Contrato real de ambas vistas H9 y casos de procedencia en PostgreSQL desechable."""

import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg.errors import ForeignKeyViolation


ROOT = Path(__file__).resolve().parents[2]
MIGRACION = ROOT / "migrations/2026-10-06_h9_vista_calibracion_procedencia.sql"
MIGRACION_RESUMEN = ROOT / "migrations/2026-10-06_resumen_calibracion_sin_outcome_cero_cero.sql"
ROLLBACK_RESUMEN = ROOT / "migrations/2026-10-06_resumen_calibracion_sin_outcome_cero_cero_rollback.sql"


def _columnas(conn, vista: str):
    return conn.execute(
        "SELECT attname, atttypid, atttypmod FROM pg_attribute "
        "WHERE attrelid = %s::regclass AND attnum > 0 AND NOT attisdropped ORDER BY attnum",
        (vista,),
    ).fetchall()


@pytest.mark.integracion
def test_migracion_vistas_preserva_contratos_y_descarta_calibracion_sin_procedencia():
    url = os.environ.get("DATABASE_URL") or ""
    dbname = conninfo_to_dict(url).get("dbname", "") if url else ""
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable del runner")

    legacy_sql = Path(__file__).with_name("vista_calibracion_legacy.sql").read_text()
    resumen_legacy_sql = Path(__file__).with_name("vista_resumen_calibracion_legacy.sql").read_text()
    migracion_sql = MIGRACION.read_text()
    cuerpo = "\n".join(
        line for line in migracion_sql.splitlines()
        if line.strip() not in {"BEGIN;", "COMMIT;"}
    )
    local_id, visitante_id, partido_id, partido_cero_cero, cal_q1, cal_q2 = (uuid4() for _ in range(6))
    casos = [
        # origen, mercado, raw, calibrada, ID, efectiva, ID visible, calibrada visible
        ("CAL_OK", "Q1", "0.4", "0.7", cal_q1, "0.7", True, "0.7"),
        ("SIN_ID", "Q1", "0.2", "0.9", None, "0.2", False, None),
        ("CAL_NULL", "Q1", "0.4", None, cal_q1, "0.4", False, None),
        ("RAW_NULL_CAL_OK", "Q1", None, "0.6", cal_q1, "0.6", True, "0.6"),
        ("SIN_PARES", "Q1", None, "0.8", None, None, False, None),
        ("RAW_INVALIDA", "Q1", "1.2", None, None, None, False, None),
        ("CAL_INVALIDA", "Q1", "0.3", "1.2", cal_q1, "0.3", False, None),
        ("MERCADO_DISTINTO", "Q1", "0.25", "0.95", cal_q2, "0.25", False, None),
        ("LEGACY", "Q1", "0.8", "0.95", None, "0.8", False, None),
        ("CERO_CERO", "Q1", "0.5", None, None, "0.5", False, None),
    ]

    with psycopg.connect(url) as conn:
        try:
            conn.execute("DROP VIEW vista_predicciones_para_calibracion")
            conn.execute(
                "ALTER TABLE predicciones_registradas "
                "ALTER COLUMN p_raw TYPE numeric(5,4), "
                "ALTER COLUMN p_calibrada TYPE numeric(5,4), "
                "ALTER COLUMN calibrador_metodo TYPE character varying(20)"
            )
            conn.execute(
                "ALTER TABLE predicciones_registradas "
                "ADD COLUMN equipo_local_nombre text, ADD COLUMN equipo_visitante_nombre text, "
                "ADD COLUMN intervalo_inferior numeric, ADD COLUMN intervalo_superior numeric, "
                "ADD COLUMN nivel_intervalo integer"
            )
            conn.execute("ALTER TABLE equipos ADD COLUMN abreviatura text")
            conn.execute("CREATE TABLE temporadas_baloncesto (id uuid PRIMARY KEY, nombre text)")
            conn.execute("CREATE TABLE calibradores (id uuid PRIMARY KEY, mercado text NOT NULL, activo boolean NOT NULL)")
            conn.execute(
                "ALTER TABLE predicciones_registradas ADD CONSTRAINT pred_calibrador_fkey "
                "FOREIGN KEY (calibrador_id) REFERENCES calibradores(id) ON DELETE SET NULL"
            )
            conn.execute(
                "INSERT INTO calibradores (id, mercado, activo) VALUES (%s, 'Q1', false), (%s, 'Q2', true)",
                (cal_q1, cal_q2),
            )
            conn.execute(
                "INSERT INTO equipos (id, nombre, abreviatura) VALUES "
                "(%s, 'Local', 'LOC'), (%s, 'Visitante', 'VIS')",
                (local_id, visitante_id),
            )
            conn.execute(
                "INSERT INTO partidos_baloncesto (id, local_total, visitante_total) "
                "VALUES (%s, 101, 99), (%s, 0, 0)",
                (partido_id, partido_cero_cero),
            )
            for idx, caso in enumerate(casos):
                origen, mercado, raw, calibrada, calibrador_id, *_ = caso
                conn.execute(
                    "INSERT INTO predicciones_registradas "
                    "(id, partido_id, equipo_local_id, equipo_visitante_id, mercado, origen, lado, "
                    "linea, p_raw, p_calibrada, calibrador_id, resuelto, outcome_binario) "
                    "VALUES (%s, %s, %s, %s, %s, %s, 'OVER', %s, %s, %s, %s, true, false)",
                    (uuid4(), partido_cero_cero if origen == "CERO_CERO" else partido_id,
                     local_id, visitante_id, mercado, origen,
                     idx + Decimal("0.5"), raw, calibrada, calibrador_id),
                )
            with pytest.raises(ForeignKeyViolation):
                with conn.transaction():
                    conn.execute(
                        "INSERT INTO predicciones_registradas "
                        "(id, partido_id, equipo_local_id, equipo_visitante_id, mercado, origen, lado, "
                        "linea, p_raw, p_calibrada, calibrador_id, resuelto, outcome_binario) "
                        "VALUES (%s, %s, %s, %s, 'Q1', 'ID_INEXISTENTE', 'OVER', 99.5, 0.2, 0.9, %s, true, false)",
                        (uuid4(), partido_id, local_id, visitante_id, uuid4()),
                    )

            conn.execute(legacy_sql)
            conn.execute(resumen_legacy_sql)
            columnas_antes = {
                vista: _columnas(conn, vista)
                for vista in ("public.vista_predicciones_para_calibracion", "public.vista_resumen_calibracion")
            }
            assert len(columnas_antes["public.vista_predicciones_para_calibracion"]) == 42
            assert conn.execute(
                "SELECT p_efectiva FROM vista_predicciones_para_calibracion WHERE origen='SIN_ID'"
            ).fetchone()[0] == Decimal("0.9")
            assert conn.execute(
                "SELECT promedio_p_efectiva FROM vista_resumen_calibracion WHERE origen='SIN_ID'"
            ).fetchone()[0] == Decimal("0.9000")

            conn.execute(cuerpo)
            assert {
                vista: _columnas(conn, vista) for vista in columnas_antes
            } == columnas_antes
            filas = conn.execute(
                "SELECT origen, p_efectiva, calibrador_id, p_calibrada, "
                "bin_p_raw, bin_p_efectiva FROM vista_predicciones_para_calibracion"
            ).fetchall()
            por_origen = {fila[0]: fila[1:] for fila in filas}
            assert len(por_origen) == len(casos)
            for origen, _, _, _, calibrador_id, efectiva, id_visible, cal_visible in casos:
                p_efectiva, id_observado, p_calibrada, _, bin_efectiva = por_origen[origen]
                assert p_efectiva == (Decimal(efectiva) if efectiva is not None else None)
                assert id_observado == (calibrador_id if id_visible else None)
                assert p_calibrada == (Decimal(cal_visible) if cal_visible is not None else None)
                assert bin_efectiva == (
                    Decimal(efectiva) // Decimal("0.1") / 10 if efectiva is not None else None
                )
            assert por_origen["RAW_INVALIDA"][3] is None  # bin raw inválida = N/D
            resumen = {
                origen: (n, promedio)
                for origen, n, promedio in conn.execute(
                    "SELECT origen, n_predicciones, promedio_p_efectiva FROM vista_resumen_calibracion"
                ).fetchall()
            }
            promedios = {origen: promedio for origen, (_, promedio) in resumen.items()}
            assert promedios["SIN_ID"] == Decimal("0.2000")
            assert resumen["SIN_PARES"][0] == 0
            assert promedios["SIN_PARES"] is None
            assert resumen["RAW_INVALIDA"] == (0, None)
            assert resumen["RAW_NULL_CAL_OK"] == (0, None)  # sin par comparable raw/cal
            assert promedios["CAL_OK"] == Decimal("0.7000")

            # La corrección E afecta solo al resumen; la vista base conserva
            # la fila 0–0 para permitir auditoría y contabilidad de exclusiones.
            resumen_antes = _columnas(conn, "public.vista_resumen_calibracion")
            cuerpo_resumen = "\n".join(
                line for line in MIGRACION_RESUMEN.read_text().splitlines()
                if line.strip() not in {"BEGIN;", "COMMIT;"}
            )
            conn.execute(cuerpo_resumen)
            assert _columnas(conn, "public.vista_resumen_calibracion") == resumen_antes
            assert conn.execute(
                "SELECT count(*) FROM vista_predicciones_para_calibracion "
                "WHERE origen = 'CERO_CERO'"
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT n_predicciones, promedio_p_raw, brier_score_raw, fecha_min "
                "FROM vista_resumen_calibracion WHERE origen = 'CERO_CERO'"
            ).fetchone() == (0, None, None, None)
            assert conn.execute(
                "SELECT n_predicciones, promedio_p_raw FROM vista_resumen_calibracion "
                "WHERE origen = 'CAL_OK'"
            ).fetchone() == (1, Decimal("0.4000"))
            conn.execute(cuerpo_resumen)  # idempotencia
            assert _columnas(conn, "public.vista_resumen_calibracion") == resumen_antes
            cuerpo_rollback = "\n".join(
                line for line in ROLLBACK_RESUMEN.read_text().splitlines()
                if line.strip() not in {"BEGIN;", "COMMIT;"}
            )
            conn.execute(cuerpo_rollback)
            assert _columnas(conn, "public.vista_resumen_calibracion") == resumen_antes
            assert conn.execute(
                "SELECT n_predicciones FROM vista_resumen_calibracion "
                "WHERE origen = 'CERO_CERO'"
            ).fetchone()[0] == 1

            # Rollback ensayado sin DROP/CASCADE ni alteración de predicciones.
            conn.execute(legacy_sql.replace("CREATE VIEW", "CREATE OR REPLACE VIEW", 1))
            conn.execute(resumen_legacy_sql.replace("CREATE VIEW", "CREATE OR REPLACE VIEW", 1))
            assert {
                vista: _columnas(conn, vista) for vista in columnas_antes
            } == columnas_antes
            assert conn.execute(
                "SELECT promedio_p_efectiva FROM vista_resumen_calibracion WHERE origen='SIN_ID'"
            ).fetchone()[0] == Decimal("0.9000")
        finally:
            conn.rollback()

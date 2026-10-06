import os
import math
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict

from db import obtener_pool
from servicios.apuestas_analizadas import obtener_auditoria_decisiones_futbol


def test_consulta_auditoria_ejecuta_sql_real():
    dbname = conninfo_to_dict(os.environ.get("DATABASE_URL") or "").get("dbname", "")
    if not dbname.startswith("ap_suite_test_"):
        pytest.skip("DDL de auditoría solo permitido en la base efímera sintética")
    pool = obtener_pool()
    # Asegurar vista canónica para el entorno de prueba real
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for ddl in [
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_p_raw NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_p_calibrada NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_edge_real NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_score NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_sizing NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_valor_esperado NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_calibrador_id TEXT",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_modelo_version_id TEXT",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_fuente TEXT",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_metodo TEXT",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_overround NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_devig_p_mkt_fair NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota_over NUMERIC",
                "ALTER TABLE apuestas_analizadas ADD COLUMN IF NOT EXISTS decision_cuota_under NUMERIC",
            ]:
                cur.execute(ddl)
            cur.execute(
                """
                CREATE OR REPLACE VIEW vw_auditoria_decisiones_futbol AS
                SELECT
                  a.id,
                  a.partido_id,
                  pf.fecha_partido,
                  a.mercado,
                  a.lado,
                  a.linea,
                  a.probabilidad_sistema,
                  a.confianza,
                  a.estado,
                  a.resultado_outcome,
                  a.decision_p_raw,
                  a.decision_p_calibrada,
                  a.decision_edge_real,
                  a.decision_score,
                  a.decision_sizing,
                  a.decision_valor_esperado,
                  a.decision_calibrador_id,
                  a.decision_modelo_version_id,
                  a.decision_fuente,
                  a.decision_devig_metodo,
                  a.decision_devig_overround,
                  a.decision_devig_p_mkt_fair,
                  a.decision_cuota,
                  a.decision_cuota_over,
                  a.decision_cuota_under,
                  a.creado_en,
                  a.actualizado_en
                FROM apuestas_analizadas a
                LEFT JOIN partidos_futbol pf ON pf.id = a.partido_id
                WHERE a.deporte = 'futbol';
                """
            )

    resp = obtener_auditoria_decisiones_futbol(limite=5, pool=pool)
    assert "total" in resp
    assert "items" in resp
    assert "totales" in resp

    with pool.connection() as conn:
        fila_id = conn.execute(
            "INSERT INTO apuestas_analizadas "
            "(deporte, partido_id, mercado, probabilidad_sistema, decision_p_calibrada, resultado_outcome) "
            "VALUES ('futbol', %s, 'GOLES_FT', 0.2, 0.9, 'PERDIDA') RETURNING id",
            (uuid4(),),
        ).fetchone()[0]
    try:
        sin_id = obtener_auditoria_decisiones_futbol(limite=5, pool=pool)["promedios"]
        assert sin_id["brier_score"] == pytest.approx(0.04)
        assert sin_id["log_loss"] == pytest.approx(-math.log(0.8))

        with pool.connection() as conn:
            conn.execute(
                "UPDATE apuestas_analizadas SET decision_calibrador_id = %s WHERE id = %s",
                (str(uuid4()), fila_id),
            )
        con_id = obtener_auditoria_decisiones_futbol(limite=5, pool=pool)["promedios"]
        assert con_id["brier_score"] == pytest.approx(0.81)
        assert con_id["log_loss"] == pytest.approx(-math.log(0.1))
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM apuestas_analizadas WHERE id = %s", (fila_id,))

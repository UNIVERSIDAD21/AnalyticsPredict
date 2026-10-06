"""El historial conserva registros dudosos sin contarlos como aciertos."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict

from app import app
from db import obtener_pool


def test_historial_separa_resultado_nba_cero_cero_en_postgres_sintetico():
    url = os.environ.get("DATABASE_URL") or ""
    if not str(conninfo_to_dict(url).get("dbname", "")).startswith("ap_suite_test_"):
        pytest.skip("Solo en PostgreSQL sintético desechable")

    local, visitante = uuid4(), uuid4()
    valido, dudoso = uuid4(), uuid4()
    pred_valida, pred_dudosa = uuid4(), uuid4()
    pool = obtener_pool()
    try:
        with pool.connection() as conn:
            conn.execute("INSERT INTO equipos(id, nombre) VALUES (%s, 'Local test'), (%s, 'Visitante test')",
                         (local, visitante))
            conn.execute(
                """INSERT INTO partidos_baloncesto
                   (id, equipo_local_id, equipo_visitante_id, fecha_partido,
                    local_total, visitante_total)
                   VALUES (%s, %s, %s, '2026-01-10', 100, 99),
                          (%s, %s, %s, '2026-01-11', 0, 0)""",
                (valido, local, visitante, dudoso, local, visitante),
            )
            conn.execute(
                """INSERT INTO predicciones_registradas
                   (id, partido_id, mercado, lado, linea, origen, p_raw,
                    outcome_binario, resuelto, valor_real, timestamp_generacion)
                   VALUES (%s, %s, 'COMPLETO', 'OVER', 180, 'API_USUARIO',
                           0.8, true, true, 199, now()),
                          (%s, %s, 'COMPLETO', 'OVER', 180, 'API_USUARIO',
                           0.8, true, true, 0, now())""",
                (pred_valida, valido, pred_dudosa, dudoso),
            )

        cliente = TestClient(app)
        base = "/api/predicciones/historial?desde=2026-01-10&hasta=2026-01-11"
        respuesta = cliente.get(base)
        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert datos["resumen"]["ganadas"] == 1
        assert datos["resumen"]["no_evaluables"] == 1
        assert datos["resumen"]["win_rate"] == 1.0
        por_id = {fila["id"]: fila for fila in datos["predicciones"]}
        assert por_id[str(pred_dudosa)]["estado"] == "NO_EVALUABLE"
        assert por_id[str(pred_dudosa)]["valor_real"] is None
        assert cliente.get(base + "&estado=GANADA").json()["total"] == 1
        assert cliente.get(base + "&estado=NO_EVALUABLE").json()["total"] == 1
    finally:
        with pool.connection() as conn:
            conn.execute("DELETE FROM predicciones_registradas WHERE id IN (%s, %s)",
                         (pred_valida, pred_dudosa))
            conn.execute("DELETE FROM partidos_baloncesto WHERE id IN (%s, %s)",
                         (valido, dudoso))
            conn.execute("DELETE FROM equipos WHERE id IN (%s, %s)", (local, visitante))

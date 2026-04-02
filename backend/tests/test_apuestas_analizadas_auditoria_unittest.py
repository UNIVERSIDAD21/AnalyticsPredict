import unittest
from datetime import datetime, timezone

from servicios.apuestas_analizadas import (
    _armar_where_auditoria_futbol,
    obtener_auditoria_decisiones_futbol,
)


class _FakeCursor:
    def __init__(self, filas, resumen, cortes):
        self.filas = filas
        self.resumen = resumen
        self.cortes = cortes
        self._select_step = 0

    def execute(self, _sql, _params=None):
        sql_u = str(_sql).strip().upper()
        if sql_u.startswith("SELECT"):
            self._select_step += 1

    def fetchall(self):
        if self._select_step == 1:
            return self.filas
        if self._select_step == 3:
            return self.cortes
        return []

    def fetchone(self):
        if self._select_step == 2:
            return self.resumen
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self, row_factory=None):
        _ = row_factory
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, cursor):
        self._conn = _FakeConn(cursor)

    def connection(self):
        return self._conn


class TestAuditoriaApuestasAnalizadas(unittest.TestCase):
    def test_where_base(self):
        where, params = _armar_where_auditoria_futbol()
        self.assertEqual(where, "deporte = 'futbol'")
        self.assertEqual(params, [])

    def test_where_con_todos_los_filtros(self):
        where, params = _armar_where_auditoria_futbol(
            mercado="GOLES_FT",
            fuente="ENSEMBLE",
            devig_metodo="exacto",
            fecha_desde=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fecha_hasta=datetime(2026, 1, 31, tzinfo=timezone.utc),
            partido_id="abc",
            modelo_version_id="m1",
            calibrador_id="c1",
            estado="FINALIZADA",
            resultado_outcome="GANADA",
        )
        for clause in [
            "mercado = %s",
            "decision_fuente = %s",
            "decision_devig_metodo = %s",
            "actualizado_en >= %s",
            "actualizado_en <= %s",
            "partido_id = %s",
            "decision_modelo_version_id = %s",
            "decision_calibrador_id = %s",
            "estado = %s",
            "resultado_outcome = %s",
        ]:
            self.assertIn(clause, where)
        self.assertEqual(len(params), 10)

    def test_contrato_respuesta_dataset_vacio(self):
        cursor = _FakeCursor(
            filas=[],
            resumen={
                "total": 0,
                "total_ml": 0,
                "total_heuristico": 0,
                "total_ensemble": 0,
                "edge_promedio": None,
                "score_promedio": None,
                "sizing_promedio": None,
                "ev_promedio": None,
            },
            cortes=[],
        )
        resp = obtener_auditoria_decisiones_futbol(pool=_FakePool(cursor))
        self.assertEqual(resp["total"], 0)
        self.assertIn("items", resp)
        self.assertIn("totales", resp)
        self.assertIn("promedios", resp)
        self.assertIn("cortes", resp)
        self.assertIn("filtros_aplicados", resp)
        self.assertIn("paginacion", resp)
        self.assertEqual(resp["items"], [])

    def test_contrato_respuesta_mapping_y_agregados(self):
        fila = {
            "id": 1,
            "partido_id": "p1",
            "mercado": "GOLES_FT",
            "lado": "OVER",
            "linea": 2.5,
            "probabilidad_sistema": 0.61,
            "confianza": "ALTA",
            "estado": "PENDIENTE",
            "resultado_outcome": None,
            "decision_p_raw": 0.6,
            "decision_p_calibrada": 0.61,
            "decision_edge_real": 0.04,
            "decision_score": 72.0,
            "decision_sizing": 0.02,
            "decision_valor_esperado": 0.05,
            "decision_calibrador_id": "cal1",
            "decision_modelo_version_id": "mod1",
            "decision_fuente": "ENSEMBLE",
            "decision_devig_metodo": "exacto",
            "decision_devig_overround": 1.05,
            "decision_devig_p_mkt_fair": 0.57,
            "creado_en": datetime.now(timezone.utc),
            "actualizado_en": datetime.now(timezone.utc),
        }
        cursor = _FakeCursor(
            filas=[fila],
            resumen={
                "total": 1,
                "total_ml": 0,
                "total_heuristico": 0,
                "total_ensemble": 1,
                "edge_promedio": 0.04,
                "score_promedio": 72.0,
                "sizing_promedio": 0.02,
                "ev_promedio": 0.05,
            },
            cortes=[
                {
                    "mercado": "GOLES_FT",
                    "fuente": "ENSEMBLE",
                    "devig_metodo": "exacto",
                    "total": 1,
                    "edge_promedio": 0.04,
                    "score_promedio": 72.0,
                    "sizing_promedio": 0.02,
                    "ev_promedio": 0.05,
                }
            ],
        )
        resp = obtener_auditoria_decisiones_futbol(pool=_FakePool(cursor))
        self.assertEqual(resp["total"], 1)
        self.assertEqual(resp["totales"]["ensemble"], 1)
        self.assertEqual(resp["items"][0]["decision_devig_metodo"], "exacto")
        self.assertEqual(resp["cortes"][0]["mercado"], "GOLES_FT")


if __name__ == "__main__":
    unittest.main()

import unittest

from servicios.apuestas_analizadas import _armar_where_auditoria_futbol


class TestAuditoriaApuestasAnalizadas(unittest.TestCase):
    def test_where_base(self):
        where, params = _armar_where_auditoria_futbol()
        self.assertEqual(where, "deporte = 'futbol'")
        self.assertEqual(params, [])

    def test_where_con_filtros(self):
        where, params = _armar_where_auditoria_futbol(
            mercado="GOLES_FT",
            fuente="ENSEMBLE",
            devig_metodo="exacto",
        )
        self.assertIn("mercado = %s", where)
        self.assertIn("decision_fuente = %s", where)
        self.assertIn("decision_devig_metodo = %s", where)
        self.assertEqual(params, ["GOLES_FT", "ENSEMBLE", "exacto"])


if __name__ == "__main__":
    unittest.main()

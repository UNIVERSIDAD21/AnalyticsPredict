import unittest

from api.schemas_futbol import RecomendacionApuesta
from api.rutas_analisis_futbol import (
    _arbitrar_recomendaciones,
    _calcular_metricas_mercado,
    _clave_recomendacion,
)


class TestP51P61(unittest.TestCase):
    def test_clave_recomendacion_normaliza(self):
        k1 = _clave_recomendacion("goles_ft", "over", 2.5)
        k2 = _clave_recomendacion("GOLES_FT", "OVER", 2.50)
        self.assertEqual(k1, k2)

    def test_devig_exacto_y_ev(self):
        m = _calcular_metricas_mercado(
            lado="OVER",
            prob_raw=0.56,
            prob_cal=0.58,
            cuota_over=1.90,
            cuota_under=1.90,
            std=1.2,
            mercado_estado="verde",
        )
        self.assertEqual(m["devig_metodo"], "exacto")
        self.assertIsNotNone(m["devig_p_mkt_fair"])
        self.assertIsNotNone(m["valor_esperado"])
        self.assertGreaterEqual(m["sizing"], 0.0)

    def test_devig_estimado_con_una_cuota(self):
        m = _calcular_metricas_mercado(
            lado="UNDER",
            prob_raw=0.54,
            prob_cal=0.57,
            cuota_over=None,
            cuota_under=1.95,
            std=2.5,
            mercado_estado="amarillo",
        )
        self.assertEqual(m["devig_metodo"], "estimado")
        self.assertTrue(any("Falta cuota opuesta" in w for w in m["advertencias"]))

    def test_arbitraje_dedupe_por_llave(self):
        r_ml = RecomendacionApuesta(
            mercado="GOLES_FT",
            lado="OVER",
            linea=2.5,
            probabilidad=0.61,
            confianza="ALTA",
            p_raw=0.60,
            p_calibrada=0.61,
            score=71.0,
            sizing=0.02,
            fuente="ML",
        )
        r_h = RecomendacionApuesta(
            mercado="GOLES_FT",
            lado="OVER",
            linea=2.5,
            probabilidad=0.59,
            confianza="MEDIA",
            p_raw=0.58,
            p_calibrada=0.59,
            score=62.0,
            sizing=0.015,
            fuente="HEURISTICO",
        )
        out = _arbitrar_recomendaciones(
            [r_ml],
            [r_h],
            estado_mercados={"GOLES_FT": "verde"},
            partidos_relevantes=80,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].fuente, "ENSEMBLE")
        self.assertIsNotNone(out[0].metadata_ensemble)
        self.assertIn("motivo_arbitraje", out[0].metadata_ensemble)


if __name__ == "__main__":
    unittest.main()

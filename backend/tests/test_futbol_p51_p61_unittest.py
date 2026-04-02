import unittest

from api.schemas_futbol import RecomendacionApuesta
from api.rutas_analisis_futbol import (
    _arbitrar_recomendaciones,
    _calcular_metricas_mercado,
    _clave_recomendacion,
)


class TestP52P62(unittest.TestCase):
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

    def test_single_side_no_se_vende_como_devig(self):
        m = _calcular_metricas_mercado(
            lado="UNDER",
            prob_raw=0.54,
            prob_cal=0.57,
            cuota_over=None,
            cuota_under=1.95,
            std=2.5,
            mercado_estado="amarillo",
        )
        self.assertEqual(m["devig_metodo"], "implied_raw_single_side")
        self.assertTrue(any("sin de-vig real" in w for w in m["advertencias"]))

    def test_sin_cuotas_fallback_conservador(self):
        m = _calcular_metricas_mercado(
            lado="OVER",
            prob_raw=0.53,
            prob_cal=0.55,
            cuota_over=None,
            cuota_under=None,
            std=3.0,
            mercado_estado="verde",
        )
        self.assertEqual(m["devig_metodo"], "fallback_conservador_no_odds")
        self.assertIsNone(m["valor_esperado"])

    def test_arbitraje_seleccion_dura_por_score(self):
        r_ml = RecomendacionApuesta(
            mercado="GOLES_FT",
            lado="OVER",
            linea=2.5,
            probabilidad=0.62,
            confianza="ALTA",
            p_raw=0.61,
            p_calibrada=0.62,
            score=86.0,
            sizing=0.03,
            fuente="ML",
            devig_metodo="implied_raw_single_side",
        )
        r_h = RecomendacionApuesta(
            mercado="GOLES_FT",
            lado="OVER",
            linea=2.5,
            probabilidad=0.57,
            confianza="MEDIA",
            p_raw=0.56,
            p_calibrada=0.57,
            score=60.0,
            sizing=0.01,
            fuente="HEURISTICO",
            devig_metodo="implied_raw_single_side",
        )
        out = _arbitrar_recomendaciones(
            [r_ml],
            [r_h],
            estado_mercados={"GOLES_FT": "verde"},
            partidos_relevantes=70,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].fuente, "ML")
        self.assertEqual(out[0].metadata_ensemble.get("decision"), "seleccion_dura")

    def test_arbitraje_blend_cuando_no_hay_evidencia_fuerte(self):
        r_ml = RecomendacionApuesta(
            mercado="CORNERS_FT",
            lado="UNDER",
            linea=10.5,
            probabilidad=0.58,
            confianza="MEDIA",
            p_raw=0.57,
            p_calibrada=0.58,
            score=67.0,
            sizing=0.015,
            fuente="ML",
            devig_metodo="implied_raw_single_side",
        )
        r_h = RecomendacionApuesta(
            mercado="CORNERS_FT",
            lado="UNDER",
            linea=10.5,
            probabilidad=0.56,
            confianza="MEDIA",
            p_raw=0.55,
            p_calibrada=0.56,
            score=63.0,
            sizing=0.012,
            fuente="HEURISTICO",
            devig_metodo="implied_raw_single_side",
        )
        out = _arbitrar_recomendaciones(
            [r_ml],
            [r_h],
            estado_mercados={"CORNERS_FT": "amarillo"},
            partidos_relevantes=40,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].fuente, "ENSEMBLE")
        self.assertEqual(out[0].metadata_ensemble.get("decision"), "blend")


if __name__ == "__main__":
    unittest.main()

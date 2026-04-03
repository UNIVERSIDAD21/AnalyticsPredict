import unittest

from api.config_estadistica_futbol import (
    distribucion_para_mercado,
    winsorizar_valores,
    estimar_ratio_tiempo_disparos,
)
from api.rutas_analisis_futbol import _resumen_valores


class TestModeloEstadisticoFutbol(unittest.TestCase):
    def test_distribuciones_por_mercado(self):
        self.assertEqual(distribucion_para_mercado("GOLES_FT"), "poisson")
        self.assertEqual(distribucion_para_mercado("CORNERS_LOCAL_1T"), "nbinom")
        self.assertEqual(distribucion_para_mercado("DISPAROS_ARCO_2T"), "nbinom")

    def test_winsorizacion_reduce_outlier_extremo(self):
        valores = [2.0] * 30 + [25.0]
        wins, low, high, applied = winsorizar_valores(valores)
        self.assertTrue(applied)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        self.assertLess(max(wins), 25.0)

    def test_resumen_valores_reporta_winsorizacion(self):
        valores = [1.0] * 40 + [20.0]
        resumen = _resumen_valores(valores, incluir_std=True)
        self.assertIn("winsorizacion_aplicada", resumen)
        self.assertTrue(resumen["winsorizacion_aplicada"])
        self.assertLess(resumen["promedio"], 2.5)

    def test_ratio_disparos_se_basa_en_senales_de_mercado(self):
        # Corners sugiere 1T bajo (0.30), goles sugiere 1T alto (0.70): debe mezclar
        split = estimar_ratio_tiempo_disparos(
            corners_1t_total=3.0,
            corners_2t_total=7.0,
            goles_1t_total=7.0,
            goles_2t_total=3.0,
        )
        self.assertGreater(split["ratio_1t"], 0.30)
        self.assertLess(split["ratio_1t"], 0.70)
        self.assertAlmostEqual(split["ratio_1t"] + split["ratio_2t"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()

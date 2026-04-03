import unittest

from api.schemas_futbol import (
    AnalisisRequest,
    PrediccionMercado,
    ProbabilidadLinea,
    RecomendacionApuesta,
)
from api.rutas_analisis_futbol import (
    _resolver_objetivo_canonico,
    _evaluar_muestra_contextual_objetivo,
    _aplicar_degradacion_recomendaciones_por_muestra,
)


class TestGatingContextoFutbol(unittest.TestCase):
    def _request_objetivo(self):
        return AnalisisRequest(
            partido_id="3d1b88a2-b858-4529-95e1-a92e2719d47f",
            mercado_objetivo="CORNERS_LOCAL_1T",
            lado_objetivo="OVER",
            linea_objetivo=5.5,
        )

    def _mercado_objetivo(self):
        return PrediccionMercado(
            mercado="CORNERS_LOCAL_1T",
            media=2.6,
            std=1.4,
            lineas={
                "5.5": ProbabilidadLinea(
                    over_raw=0.12,
                    over_calibrada=0.11,
                    under_raw=0.88,
                    under_calibrada=0.89,
                )
            },
        )

    def test_objetivo_estado_mercados_vacio_degrada_datos_insuficientes(self):
        req = self._request_objetivo()
        objetivo = _resolver_objetivo_canonico(
            request=req,
            mercados={"CORNERS_LOCAL_1T": self._mercado_objetivo()},
            recomendaciones=[],
            estado_mercados={},
            evaluacion_muestra={"muestra_suficiente": True, "bloques_insuficientes": []},
        )

        self.assertEqual(objetivo.estado, "datos_insuficientes")
        self.assertIn("estado_mercados_vacio", objetivo.disponibilidad_datos.degradacion_controlada)

    def test_objetivo_mercado_fuera_estado_mercados_degrada(self):
        req = self._request_objetivo()
        objetivo = _resolver_objetivo_canonico(
            request=req,
            mercados={"CORNERS_LOCAL_1T": self._mercado_objetivo()},
            recomendaciones=[],
            estado_mercados={"GOLES_FT": "verde"},
            evaluacion_muestra={"muestra_suficiente": True, "bloques_insuficientes": []},
        )

        self.assertEqual(objetivo.estado, "datos_insuficientes")
        self.assertIn("mercado_objetivo_fuera_estado_mercados", objetivo.disponibilidad_datos.degradacion_controlada)

    def test_evaluacion_muestra_insuficiente_por_bloque(self):
        req = self._request_objetivo()
        evaluacion = _evaluar_muestra_contextual_objetivo(
            req,
            partidos_h2h=2,
            partidos_local_home=10,
            partidos_visitante_away=8,
        )

        self.assertFalse(evaluacion["muestra_suficiente"])
        self.assertIn("h2h", evaluacion["bloques_insuficientes"])
        self.assertIn("local_home", evaluacion["bloques_insuficientes"])
        self.assertIn("visitante_away", evaluacion["bloques_insuficientes"])

    def test_degradacion_recomendacion_por_muestra_baja_confianza(self):
        rec = RecomendacionApuesta(
            mercado="CORNERS_LOCAL_1T",
            lado="OVER",
            linea=5.5,
            probabilidad=0.57,
            confianza="ALTA",
            valor_esperado=0.02,
        )
        evaluacion = {
            "muestra_suficiente": False,
            "bloques_insuficientes": ["h2h", "local_home"],
        }

        out = _aplicar_degradacion_recomendaciones_por_muestra([rec], evaluacion)
        self.assertEqual(out[0].confianza, "MEDIA")
        self.assertTrue(any("muestra_insuficiente_contexto" in w for w in (out[0].advertencias or [])))

    def test_objetivo_muestra_insuficiente_marca_estado(self):
        req = self._request_objetivo()
        objetivo = _resolver_objetivo_canonico(
            request=req,
            mercados={"CORNERS_LOCAL_1T": self._mercado_objetivo()},
            recomendaciones=[],
            estado_mercados={"CORNERS_LOCAL_1T": "verde"},
            evaluacion_muestra={"muestra_suficiente": False, "bloques_insuficientes": ["h2h"]},
        )

        self.assertEqual(objetivo.estado, "datos_insuficientes")
        self.assertIn("muestra_insuficiente", objetivo.disponibilidad_datos.degradacion_controlada)


if __name__ == "__main__":
    unittest.main()

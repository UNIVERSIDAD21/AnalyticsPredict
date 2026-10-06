import unittest

from fastapi import FastAPI

from api.rutas_bitacora import (
    AuditoriaDecisionFutbolResponse,
    router,
)


class TestBitacoraAuditoriaFutbolSmoke(unittest.TestCase):
    def test_ruta_auditoria_futbol_registrada(self):
        app = FastAPI()
        app.include_router(router)
        rutas = app.openapi()["paths"]
        self.assertIn("get", rutas["/api/bitacora/apuestas-analizadas/auditoria-futbol"])
        self.assertIn("get", rutas["/api/bitacora/apuestas-analizadas/auditoria-futbol/legacy"])
        self.assertIn("post", rutas["/api/bitacora/apuestas-analizadas/auditoria-futbol/backfill"])

    def test_ruta_auditoria_futbol_tiene_response_model(self):
        ruta = next(r for r in router.routes if r.path == "/api/bitacora/apuestas-analizadas/auditoria-futbol")
        self.assertEqual(ruta.response_model, AuditoriaDecisionFutbolResponse)


if __name__ == "__main__":
    unittest.main()

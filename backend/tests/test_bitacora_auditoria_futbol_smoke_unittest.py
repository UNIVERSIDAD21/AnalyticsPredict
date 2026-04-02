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
        rutas = {(r.path, tuple(sorted(getattr(r, 'methods', [])))) for r in app.routes}
        self.assertIn(("/api/bitacora/apuestas-analizadas/auditoria-futbol", ("GET",)), rutas)
        self.assertIn(("/api/bitacora/apuestas-analizadas/auditoria-futbol/legacy", ("GET",)), rutas)
        self.assertIn(("/api/bitacora/apuestas-analizadas/auditoria-futbol/backfill", ("POST",)), rutas)

    def test_ruta_auditoria_futbol_tiene_response_model(self):
        app = FastAPI()
        app.include_router(router)
        ruta = next(r for r in app.routes if r.path == "/api/bitacora/apuestas-analizadas/auditoria-futbol")
        self.assertEqual(ruta.response_model, AuditoriaDecisionFutbolResponse)


if __name__ == "__main__":
    unittest.main()

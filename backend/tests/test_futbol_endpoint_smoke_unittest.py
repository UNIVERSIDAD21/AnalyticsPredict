import unittest

from fastapi import FastAPI

from api.rutas_analisis_futbol import router


class TestFutbolEndpointSmoke(unittest.TestCase):
    def test_router_registra_endpoint_analizar(self):
        app = FastAPI()
        app.include_router(router)
        rutas = {(r.path, tuple(sorted(getattr(r, 'methods', [])))) for r in app.routes}
        self.assertIn(("/api/futbol/analizar", ("POST",)), rutas)


if __name__ == "__main__":
    unittest.main()

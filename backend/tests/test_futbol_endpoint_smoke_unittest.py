import unittest

from fastapi import FastAPI

from api.rutas_analisis_futbol import router


class TestFutbolEndpointSmoke(unittest.TestCase):
    def test_router_registra_endpoint_analizar(self):
        app = FastAPI()
        app.include_router(router)
        self.assertIn("post", app.openapi()["paths"]["/api/futbol/analizar"])


if __name__ == "__main__":
    unittest.main()

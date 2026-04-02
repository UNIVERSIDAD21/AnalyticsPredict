import unittest

from fastapi import FastAPI

from api.rutas_bitacora import router


class TestBitacoraAuditoriaFutbolSmoke(unittest.TestCase):
    def test_ruta_auditoria_futbol_registrada(self):
        app = FastAPI()
        app.include_router(router)
        rutas = {(r.path, tuple(sorted(getattr(r, 'methods', [])))) for r in app.routes}
        self.assertIn(("/api/bitacora/apuestas-analizadas/auditoria-futbol", ("GET",)), rutas)


if __name__ == "__main__":
    unittest.main()

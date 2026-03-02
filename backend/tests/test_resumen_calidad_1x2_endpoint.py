import asyncio

from api import rutas_metricas_futbol


class _Cursor:
    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return (50, 40, 21, 14, 5)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Conn:
    def cursor(self):
        return _Cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Pool:
    def connection(self):
        return _Conn()


def test_endpoint_resumen_calidad_1x2(monkeypatch):
    monkeypatch.setattr(rutas_metricas_futbol, 'obtener_pool', lambda: _Pool())
    data = asyncio.run(rutas_metricas_futbol.resumen_calidad_1x2())
    assert data['exito'] is True
    assert data['resumen']['total'] == 50
    assert data['resumen']['ganadas'] == 21

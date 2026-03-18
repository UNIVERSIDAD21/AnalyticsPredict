from fastapi import Response

from api import rutas_bitacora


def test_listar_apuestas_analizadas_basico():
    data = __import__("asyncio").run(
        rutas_bitacora.listar_apuestas_analizadas(response=Response(), limite=5, offset=0)
    )
    assert data["ok"] is True
    assert "items" in data["data"]
    assert "total" in data["data"]

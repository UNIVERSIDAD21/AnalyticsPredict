from api import rutas_bitacora


def test_listar_apuestas_analizadas_basico():
    data = __import__("asyncio").run(rutas_bitacora.listar_apuestas_analizadas(limite=5, offset=0))
    assert data["exito"] is True
    assert "items" in data
    assert "total" in data

"""El estado no inventa ceros al fallar BD ni escribe al consultar."""
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from api import rutas_operacion as rutas


def test_error_almacen_no_se_convierte_en_cero(monkeypatch):
    def fallar():
        raise RuntimeError('detalle privado que no debe salir')
    monkeypatch.setattr(rutas, 'obtener_pool', fallar)
    with pytest.raises(HTTPException) as exc:
        rutas.estado_operacion()
    assert exc.value.status_code == 503
    assert 'privado' not in str(exc.value.detail)


def test_consulta_read_only_y_ausencia_de_artefacto(monkeypatch):
    comandos = []
    class Conn:
        def execute(self, consulta): comandos.append(consulta)
    class Pool:
        @contextmanager
        def connection(self): yield Conn()
    monkeypatch.setattr(rutas, 'obtener_pool', Pool)
    monkeypatch.setattr(rutas, 'leer_estado', lambda conn: {'prospectiva': {'congeladas': None}, 'predictor_ml_futbol': {}})
    monkeypatch.setattr(rutas, 'cargar_artefacto', lambda: None)
    respuesta = rutas.estado_operacion()
    assert comandos[0] == 'SET TRANSACTION READ ONLY'
    assert respuesta['modelo_nba']['estado'] == 'NO_DISPONIBLE'
    assert respuesta['prospectiva']['congeladas'] is None
    assert respuesta['certificacion'] == 'NO_CERTIFICADO'

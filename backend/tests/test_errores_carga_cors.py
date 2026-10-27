"""Los fallos de datos deben poder leerse desde la UI sin convertirse en CORS."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app import app, manejador_http
from lecturas_http import solo_lectura_http


PRIVADO = 'postgresql://usuario:SECRETO_FICTICIO@example.invalid/bd'
MENSAJE_BD = (
    'No se pudo conectar con la base de datos. '
    'Intenta de nuevo cuando se restablezca el servicio.'
)


def crear_cliente(fallo):
    # Reutiliza el orden REAL de middlewares, sin arrancar modelos ni abrir BD.
    prueba = FastAPI(middleware=app.user_middleware)
    prueba.add_exception_handler(StarletteHTTPException, manejador_http)

    @prueba.api_route('/datos', methods=['GET', 'HEAD', 'POST'])
    def datos():
        assert solo_lectura_http.get() is True
        if fallo == 'pool':
            raise PoolTimeout(PRIVADO)
        if fallo == 'conexion':
            raise OperationalError('Your account or project has exceeded the quota. ' + PRIVADO)
        if fallo == 'capturado':
            try:
                raise PoolTimeout(PRIVADO)
            except PoolTimeout as exc:
                raise HTTPException(500, detail=PRIVADO) from exc
        if fallo == 'respuesta':
            return JSONResponse({'detalle': PRIVADO}, status_code=500)
        raise RuntimeError(PRIVADO)

    @prueba.get('/recuperado')
    def recuperado():
        return {'exito': True, 'solo_lectura': solo_lectura_http.get()}

    return TestClient(prueba, raise_server_exceptions=False)


@pytest.mark.parametrize('origen', ['http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:15176'])
@pytest.mark.parametrize('fallo,estado,es_bd', [
    ('pool', 503, True), ('conexion', 503, True), ('capturado', 503, True),
    ('respuesta', 500, False), ('inesperado', 500, False),
])
def test_errores_visibles_con_cors_sin_exponer_driver(origen, fallo, estado, es_bd):
    with crear_cliente(fallo) as cliente:
        respuesta = cliente.get('/datos', headers={'Origin': origen})
        assert respuesta.status_code == estado
        assert respuesta.headers['access-control-allow-origin'] == origen
        assert respuesta.headers['access-control-allow-credentials'] == 'true'
        assert 'x-trace-id' in respuesta.headers['access-control-expose-headers'].lower()
        error = respuesta.json()['error']
        assert error['trace_id'] == respuesta.headers['x-trace-id']
        assert PRIVADO not in respuesta.text
        assert 'exceeded the quota' not in respuesta.text
        if es_bd:
            assert error['code'] == 'BASE_DATOS_NO_DISPONIBLE'
            assert error['message'] == MENSAJE_BD
        else:
            assert error['code'] == 'LECTURA_NO_DISPONIBLE'
        # No se cachea el fallo ni se contamina la siguiente lectura.
        recuperada = cliente.get('/recuperado', headers={'Origin': origen})
        assert recuperada.json() == {'exito': True, 'solo_lectura': True}
        assert recuperada.headers['access-control-allow-origin'] == origen
    assert solo_lectura_http.get() is False


def test_preflight_y_head_conservan_cors_y_origen_ajeno_no_es_permitido():
    with crear_cliente('pool') as cliente:
        origen = 'http://127.0.0.1:5173'
        preflight = cliente.options('/datos', headers={
            'Origin': origen, 'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type',
        })
        assert preflight.status_code == 200
        assert preflight.headers['access-control-allow-origin'] == origen
        head = cliente.head('/datos', headers={'Origin': origen})
        assert head.status_code == 503
        assert head.content == b''
        assert head.headers['access-control-allow-origin'] == origen
        ajena = cliente.get('/datos', headers={'Origin': 'https://ajeno.invalid'})
        assert 'access-control-allow-origin' not in ajena.headers

"""El API público no conserva identidad, autenticación ni cobros."""
from app import app


def test_openapi_single_user_sin_rutas_comerciales_ni_identidad():
    spec = app.openapi()
    paths = spec['paths']
    for prefijo in ('/api/auth', '/api/pagos', '/api/premium', '/api/access',
                    '/api/onboarding', '/api/notificaciones', '/api/chat'):
        assert not any(path.startswith(prefijo) for path in paths)
    assert not spec.get('components', {}).get('securitySchemes')
    for operaciones in paths.values():
        for metodo, definicion in operaciones.items():
            if metodo not in {'get', 'post', 'put', 'patch', 'delete'}:
                continue
            parametros = {item['name'].lower() for item in definicion.get('parameters', [])}
            assert not parametros.intersection({'authorization', 'x-usuario-id', 'usuario_id'})

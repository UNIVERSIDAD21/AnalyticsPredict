from fastapi.testclient import TestClient

from app import app, observabilidad_http


client = TestClient(app)


def test_observabilidad_http_entrega_esquema_minimo():
    client.get('/salud')
    resp = client.get('/api/interno/observabilidad-http')
    assert resp.status_code == 200

    data = resp.json()
    assert data['exito'] is True
    assert 'http' in data
    assert 'uptime' in data
    assert 'alertas' in data


def test_observabilidad_http_dispara_alerta_por_error_rate_en_prueba_controlada():
    # Inyecta una muestra 5xx para validar alerta controlada sin depender de rutas inestables.
    observabilidad_http.registrar(latencia_ms=12.0, status_code=500)

    resp = client.get('/api/interno/observabilidad-http?umbral_error_rate=0.0')
    assert resp.status_code == 200

    data = resp.json()
    assert data['http']['requests_total'] >= 1
    assert any('ERROR_RATE_ALTO' in alerta for alerta in data['alertas'])

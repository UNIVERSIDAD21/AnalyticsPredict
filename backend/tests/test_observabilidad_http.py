from observabilidad_http import ObservabilidadHTTP


def test_resumen_basico_sin_alertas():
    obs = ObservabilidadHTTP(max_muestras=10)
    obs.registrar(100, 200)
    obs.registrar(200, 201)
    obs.registrar(300, 404)

    resumen = obs.resumen(umbral_p95_ms=1000, umbral_error_rate=0.5)

    assert resumen["exito"] is True
    assert resumen["http"]["requests_total"] == 3
    assert resumen["http"]["errors_5xx"] == 0
    assert resumen["http"]["error_rate"] == 0.0
    assert resumen["http"]["latency_p95_ms"] is not None
    assert resumen["alertas"] == []


def test_resumen_detecta_alertas_por_p95_y_error_rate():
    obs = ObservabilidadHTTP(max_muestras=10)
    obs.registrar(100, 200)
    obs.registrar(1200, 503)
    obs.registrar(1500, 500)

    resumen = obs.resumen(umbral_p95_ms=900, umbral_error_rate=0.3)

    assert resumen["http"]["requests_total"] == 3
    assert resumen["http"]["errors_5xx"] == 2
    assert resumen["http"]["error_rate"] > 0.3
    assert resumen["http"]["latency_p95_ms"] is not None
    assert any("LATENCIA_P95_ALTA" in a for a in resumen["alertas"])
    assert any("ERROR_RATE_ALTO" in a for a in resumen["alertas"])

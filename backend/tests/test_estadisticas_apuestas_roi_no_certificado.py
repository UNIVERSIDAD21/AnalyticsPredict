"""El GET de estadísticas conserva importes registrados sin publicar ROI bruto."""

from motor.resolucion_apuestas import obtener_estadisticas_apuestas


class _Cursor:
    def execute(self, query):
        assert "FROM apuestas" in query

    def fetchone(self):
        return (182, 0, 143, 38, 0, 1, 40, 999, 1000)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Connection:
    def cursor(self):
        return _Cursor()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Pool:
    def connection(self):
        return _Connection()


def test_estadisticas_no_publica_roi_aritmetico_sin_certificacion():
    resumen = obtener_estadisticas_apuestas(pool=_Pool())
    assert resumen["total"] == 182
    assert resumen["sin_partido_id"] == 40
    assert resumen["ganancia_total"] == 999.0  # Importe registrado, no certificado.
    assert resumen["roi"] is None

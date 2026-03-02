from api import rutas_metricas_futbol


class _FakeCursor:
    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        # total, finalizadas, ganadas, perdidas, push
        return (120, 100, 58, 32, 10)


def test_resumen_calidad_1x2_calcula_hit_rate():
    cursor = _FakeCursor()
    resumen = rutas_metricas_futbol._resumen_calidad_1x2_futbol(cursor)
    assert resumen['total'] == 120
    assert resumen['finalizadas'] == 100
    assert resumen['ganadas'] == 58
    assert resumen['perdidas'] == 32
    assert resumen['push'] == 10
    assert abs(resumen['hit_rate_sin_push'] - 64.44) < 0.1

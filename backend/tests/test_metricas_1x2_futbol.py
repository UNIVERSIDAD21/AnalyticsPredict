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

import math
import pytest


@pytest.mark.parametrize(
    ('ganadas', 'perdidas', 'push', 'esperado'),
    [(0, 0, 0, None), (0, 1, 2, 0.0), (1, 1, 1, 50.0), (14, 11, 3, 56.0), (1, 0, 0, 100.0)],
)
def test_hit_rate_en_porcentaje_y_sin_muestra_nulo(ganadas, perdidas, push, esperado):
    class Cursor:
        def execute(self, *_args):
            pass

        def fetchone(self):
            return (ganadas + perdidas + push, ganadas + perdidas + push,
                    ganadas, perdidas, push)

    resumen = rutas_metricas_futbol._resumen_calidad_1x2_futbol(Cursor())
    assert resumen['hit_rate_sin_push'] == esperado


def test_metricas_probabilisticas_reales_y_sin_muestra():
    calcular = rutas_metricas_futbol._metricas_probabilidades_binarias
    neutro = calcular([0.5, 0.5], [0, 1])
    assert neutro['n'] == 2
    assert neutro['brier'] == pytest.approx(0.25)
    assert neutro['ece'] == pytest.approx(0.0)
    assert neutro['log_loss'] == pytest.approx(math.log(2))
    perfecto = calcular([0.0, 1.0], [0, 1])
    assert perfecto['brier'] == pytest.approx(0.0)
    assert perfecto['ece'] == pytest.approx(0.0)
    assert perfecto['log_loss'] < 1e-9
    assert calcular([], []) == {'n': 0, 'brier': None, 'ece': None, 'log_loss': None}
    assert calcular([float('nan'), 2.0, 0.5], [1, 0, 1])['n'] == 1
    with pytest.raises(ValueError):
        calcular([0.5], [])

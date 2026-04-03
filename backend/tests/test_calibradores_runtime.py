import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from motor.calibradores import _aplicar_platt


def test_aplicar_platt_no_overflow_con_parametros_extremos():
    # Caso que antes podía disparar OverflowError: math range error
    # z = a*logit(p)+b muy negativo -> exp(positivo enorme)
    p_calibrada = _aplicar_platt(
        0.999999,
        {
            "a": 1000.0,
            "b": -1_000_000.0,
        },
    )

    assert 0.0 <= p_calibrada <= 1.0

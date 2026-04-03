from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.expansion_corners_b20a import puntuar_rescatabilidad, nivel_rescatabilidad


def test_score_rescatabilidad_alta_con_senal_rescatable():
    m = {
        "emitidos": 30,
        "lineas_cubiertas": 4,
        "fallback_rate": 0.0,
        "pendientes_finalizado_con_datos": 3,
        "partidos_finalizados_30d": 5,
        "resueltos_binarios": 8,
    }
    s = puntuar_rescatabilidad(m)
    assert s >= 6
    assert nivel_rescatabilidad(s) == "ALTA"


def test_score_baja_si_no_hay_masa_y_cero_resueltos():
    m = {
        "emitidos": 8,
        "lineas_cubiertas": 1,
        "fallback_rate": 0.3,
        "pendientes_finalizado_con_datos": 0,
        "partidos_finalizados_30d": 0,
        "resueltos_binarios": 0,
    }
    s = puntuar_rescatabilidad(m)
    assert s < 3
    assert nivel_rescatabilidad(s) == "BAJA"

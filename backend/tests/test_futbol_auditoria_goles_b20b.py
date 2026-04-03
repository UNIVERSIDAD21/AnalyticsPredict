from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.auditoria_goles_b20b import _score_rescatabilidad, _nivel


def test_ranking_goles_baja_sin_finalizados_ventana():
    m = {
        "emitidos": 28,
        "lineas_cubiertas": 4,
        "fallback_rate": 0.0,
        "partidos_finalizados_30d": 0,
        "resueltos_binarios": 4,
        "pendientes_finalizado_con_datos": 0,
    }
    s = _score_rescatabilidad(m)
    assert s <= 2
    assert _nivel(s) == "BAJA"


def test_ranking_goles_sube_con_senal_real_rescatable():
    m = {
        "emitidos": 40,
        "lineas_cubiertas": 4,
        "fallback_rate": 0.01,
        "partidos_finalizados_30d": 10,
        "resueltos_binarios": 16,
        "pendientes_finalizado_con_datos": 2,
    }
    s = _score_rescatabilidad(m)
    assert s >= 6
    assert _nivel(s) == "ALTA"

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor.resolucion_predicciones_futbol import _valor_real_futbol, ResumenResolucionFutbol
from motor_futbol.constantes import LINEAS_CORNERS


def test_lineas_focalizadas_corners_1t_y_local_1t():
    assert 5.0 in LINEAS_CORNERS["CORNERS_1T"]
    assert 5.0 in LINEAS_CORNERS["CORNERS_LOCAL_1T"]


def test_resumen_resolucion_incluye_anuladas():
    r = ResumenResolucionFutbol(anuladas=3)
    d = r.to_dict()
    assert d["anuladas"] == 3


def test_valor_real_corners_1t_y_local_1t_correcto():
    fila = {
        "local_corners_1t": 4,
        "visitante_corners_1t": 2,
        "local_corners_total": 8,
        "visitante_corners_total": 5,
    }
    assert _valor_real_futbol("CORNERS_1T", fila) == 6.0
    assert _valor_real_futbol("CORNERS_LOCAL_1T", fila) == 4.0

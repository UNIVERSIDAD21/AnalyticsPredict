from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.rutas_metricas_futbol import _days_by_window


def test_days_by_window_mapea_valores_esperados():
    assert _days_by_window('semanal') == 7
    assert _days_by_window('quincenal') == 15
    assert _days_by_window('mensual') == 30
    assert _days_by_window('desconocido') == 30

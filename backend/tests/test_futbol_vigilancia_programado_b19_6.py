from pathlib import Path
import sys
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_futbol.freshness_programado import clasificar_programado_por_sla

POLITICA = {
    "sla_horas": {
        "normal_hasta": 6,
        "alerta_desde": 6,
        "vencido_desde": 24,
    }
}


def test_sla_sano_sin_falso_positivo():
    now = datetime(2026, 4, 3, 21, 0, tzinfo=timezone.utc)
    fecha = now - timedelta(hours=2)
    assert clasificar_programado_por_sla(fecha, POLITICA, now) == "SANO"


def test_sla_amarillo_en_rango_intermedio():
    now = datetime(2026, 4, 3, 21, 0, tzinfo=timezone.utc)
    fecha = now - timedelta(hours=10)
    assert clasificar_programado_por_sla(fecha, POLITICA, now) == "AMARILLO"


def test_sla_vencido_detecta_atraso_claro():
    now = datetime(2026, 4, 3, 21, 0, tzinfo=timezone.utc)
    fecha = now - timedelta(hours=30)
    assert clasificar_programado_por_sla(fecha, POLITICA, now) == "VENCIDO"

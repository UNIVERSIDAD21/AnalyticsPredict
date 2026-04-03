from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_futbol.automation_diaria import generar_alertas


def test_alerta_primer_vencido():
    prev = {
        "mercados": [
            {"mercado": "CORNERS_1T", "programado_vencido": 0, "masa_actual": 4, "readiness_status": "NO_LISTO", "gate_reevaluacion_seria": False},
            {"mercado": "CORNERS_LOCAL_1T", "programado_vencido": 0, "masa_actual": 4, "readiness_status": "NO_LISTO", "gate_reevaluacion_seria": False},
        ],
        "gate_b20": False,
    }
    curr = {
        "mercados": [
            {"mercado": "CORNERS_1T", "programado_vencido": 1, "programado_amarillo": 2, "masa_actual": 4, "readiness_status": "NO_LISTO", "gate_reevaluacion_seria": False},
            {"mercado": "CORNERS_LOCAL_1T", "programado_vencido": 0, "programado_amarillo": 2, "masa_actual": 4, "readiness_status": "NO_LISTO", "gate_reevaluacion_seria": False},
        ],
        "gate_b20": False,
    }
    alerts = generar_alertas(prev, curr)
    tipos = {a["tipo"] for a in alerts}
    assert "primer_vencido" in tipos


def test_no_disparo_falso_b20():
    prev = {"mercados": [], "gate_b20": False}
    curr = {"mercados": [], "gate_b20": False}
    alerts = generar_alertas(prev, curr)
    tipos = {a["tipo"] for a in alerts}
    assert "gate_b20_habilitado" not in tipos


def test_alerta_cambio_readiness_y_masa():
    prev = {
        "mercados": [
            {"mercado": "CORNERS_1T", "programado_amarillo": 0, "masa_actual": 4, "readiness_status": "NO_LISTO", "gate_reevaluacion_seria": False},
        ],
        "gate_b20": False,
    }
    curr = {
        "mercados": [
            {"mercado": "CORNERS_1T", "programado_amarillo": 1, "masa_actual": 6, "readiness_status": "LISTO_REEVALUACION", "gate_reevaluacion_seria": True},
        ],
        "gate_b20": False,
    }
    alerts = generar_alertas(prev, curr)
    tipos = {a["tipo"] for a in alerts}
    assert "sube_masa" in tipos
    assert "cambio_readiness" in tipos
    assert "gate_reevaluacion_habilitado" in tipos

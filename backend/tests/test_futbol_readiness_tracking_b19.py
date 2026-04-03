from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_futbol.readiness_tracking import (
    calcular_delta_readiness,
    proyectar_horizonte_semanas,
    evaluar_disparo_b20,
)


def test_calculo_gap_delta_correcto():
    assert calcular_delta_readiness(26, 20) == 6
    assert calcular_delta_readiness(26, 26) == 0


def test_horizonte_semanas_none_sin_ritmo():
    assert proyectar_horizonte_semanas(26, 0) is None
    assert proyectar_horizonte_semanas(26, -1) is None


def test_horizonte_semanas_con_ritmo():
    assert proyectar_horizonte_semanas(26, 4) == 7


def test_disparo_b20_desactivado_si_un_mercado_no_listo():
    r = evaluar_disparo_b20(
        {
            "CORNERS_1T": {"gate_reevaluacion_seria_habilitado": True},
            "CORNERS_LOCAL_1T": {"gate_reevaluacion_seria_habilitado": False},
        }
    )
    assert r["habilitado"] is False
    assert r["motivo"] == "mercados_no_listos"
    assert "CORNERS_LOCAL_1T" in r["mercados_pendientes"]


def test_disparo_b20_activado_si_todos_listos():
    r = evaluar_disparo_b20(
        {
            "CORNERS_1T": {"gate_reevaluacion_seria_habilitado": True},
            "CORNERS_LOCAL_1T": {"gate_reevaluacion_seria_habilitado": True},
        }
    )
    assert r["habilitado"] is True
    assert r["motivo"] == "habilitado"
    assert r["mercados_pendientes"] == []

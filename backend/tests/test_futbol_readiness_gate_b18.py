from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from motor_futbol.readiness_gate import cargar_politica_readiness, evaluar_readiness_corners


def test_readiness_no_listo_con_masa_binaria_ridicula():
    politica = cargar_politica_readiness()
    r = evaluar_readiness_corners(
        {
            "emitidos": 28,
            "resueltos_binarios": 4,
            "pendientes": 16,
            "lineas_cubiertas": 4,
        },
        politica,
        ventanas_estables=0,
    )

    assert r["status"] == "NO_LISTO"
    assert r["gates"]["reevaluacion"] is False
    assert r["gaps"]["resueltas_para_reevaluacion"] == 26
    assert "masa_binaria_insuficiente_para_reevaluacion" in r["faltantes"]


def test_readiness_habilita_reevaluacion_pero_no_salida_de_bloqueado():
    politica = cargar_politica_readiness()
    r = evaluar_readiness_corners(
        {
            "emitidos": 40,
            "resueltos_binarios": 30,
            "pendientes": 10,
            "lineas_cubiertas": 3,
        },
        politica,
        ventanas_estables=1,
    )

    assert r["gates"]["reevaluacion"] is True
    assert r["gates"]["salir_bloqueado"] is False
    assert r["status"] == "LISTO_REEVALUACION"


def test_readiness_no_salta_silenciosamente_hacia_validacion():
    politica = cargar_politica_readiness()
    r = evaluar_readiness_corners(
        {
            "emitidos": 120,
            "resueltos_binarios": 120,
            "pendientes": 0,
            "lineas_cubiertas": 4,
        },
        politica,
        ventanas_estables=2,
    )

    assert r["gates"]["salir_bloqueado"] is True
    assert r["gates"]["candidatura_validacion"] is False
    assert r["status"] == "LISTO_SALIR_BLOQUEADO"

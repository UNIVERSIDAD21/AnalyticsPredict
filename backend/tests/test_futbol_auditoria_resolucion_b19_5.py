from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.auditoria_resolucion_corners_b19_5 import clasificar_cuello


def test_detecta_pipeline_roto_si_hay_resolubles_pendientes():
    s = {
        "pendientes_finalizado_con_datos": 3,
        "partidos_finalizados": 3,
        "pendientes_programado": 0,
        "finalizados_con_datos": 3,
        "outcomes_nuevos": 0,
    }
    assert clasificar_cuello(s) == "pipeline_roto_resolubles_sin_convertir"


def test_detecta_calendario_real_si_no_hay_finalizados():
    s = {
        "pendientes_finalizado_con_datos": 0,
        "partidos_finalizados": 0,
        "pendientes_programado": 12,
        "finalizados_con_datos": 0,
        "outcomes_nuevos": 0,
    }
    assert clasificar_cuello(s) == "calendario_real_sin_partidos_finalizados"

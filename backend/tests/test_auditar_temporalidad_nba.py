"""La clasificación temporal evita aprobar por fechas sin horas ni outcomes."""

from datetime import date, datetime, timezone

from scripts.auditar_temporalidad_nba import clasificar_traza


def _traza(**cambios):
    fila = {
        "timestamp_generacion": datetime(2026, 1, 10, 18, tzinfo=timezone.utc),
        "cutoff_entrenamiento": date(2026, 1, 9),
        "fecha_entrenamiento": datetime(2026, 1, 10, 8, tzinfo=timezone.utc),
        "fecha_partido": date(2026, 1, 10),
        "timestamp_resolucion": datetime(2026, 1, 11, 3, tzinfo=timezone.utc),
    }
    fila.update(cambios)
    return fila


def test_cutoff_futuro_invalida_aun_si_hay_outcome():
    estado, motivo = clasificar_traza(_traza(cutoff_entrenamiento=date(2026, 1, 11)))
    assert estado == "TEMPORALMENTE_INVALIDA"
    assert motivo == "CUTOFF_POSTERIOR_A_GENERACION_UTC"


def test_mismo_dia_y_fecha_evento_sin_hora_no_son_validos():
    assert clasificar_traza(_traza(cutoff_entrenamiento=date(2026, 1, 10)))[0] == "AMBIGUA"
    assert clasificar_traza(_traza())[0] == "AMBIGUA"
    assert clasificar_traza(_traza(fecha_partido=date(2026, 1, 9)))[0] == "AMBIGUA"


def test_sin_resolucion_o_zona_no_se_inventa_outcome():
    assert clasificar_traza(_traza(timestamp_resolucion=None))[0] == "NO_DETERMINABLE"
    assert clasificar_traza(_traza(timestamp_generacion=datetime(2026, 1, 10, 18)))[0] == "NO_DETERMINABLE"


def test_valida_solo_con_orden_estricto_y_evidencia_precisa():
    fila = _traza(
        fit_end_preciso=datetime(2026, 1, 10, 12, tzinfo=timezone.utc),
        inicio_evento_preciso=datetime(2026, 1, 10, 21, tzinfo=timezone.utc),
        outcome_time_independiente=datetime(2026, 1, 11, 4, tzinfo=timezone.utc),
    )
    assert clasificar_traza(fila)[0] == "TEMPORALMENTE_VALIDA"
    fila["outcome_time_independiente"] = datetime(2026, 1, 10, 17, tzinfo=timezone.utc)
    assert clasificar_traza(fila)[0] == "TEMPORALMENTE_INVALIDA"
    fila["outcome_time_independiente"] = datetime(2026, 1, 11, 4)
    assert clasificar_traza(fila)[0] == "NO_DETERMINABLE"

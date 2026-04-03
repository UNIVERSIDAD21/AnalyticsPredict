from motor_futbol.madurez_beta import clasificar_madurez_mercado, mapear_status_promocion, aplicar_autodemotion


def test_no_apto_si_estado_rojo_o_volumen_critico():
    nivel, razones = clasificar_madurez_mercado(
        {
            "n_resueltas": 40,
            "lineas_cubiertas": 3,
            "brier": 0.20,
            "log_loss": 0.60,
            "ece": 0.04,
            "resolved_rate": 0.9,
            "fallback_rate": 0.1,
            "window_drift_brier": 0.01,
        },
        "rojo",
    )
    assert nivel == "NO_APTO"
    assert "estado_mercado_no_estable" in razones


def test_promocionable_si_cumple_todos_umbral():
    nivel, _ = clasificar_madurez_mercado(
        {
            "n_resueltas": 320,
            "lineas_cubiertas": 6,
            "brier": 0.19,
            "log_loss": 0.56,
            "ece": 0.04,
            "resolved_rate": 0.92,
            "fallback_rate": 0.08,
            "window_drift_brier": 0.01,
        },
        "verde",
    )
    assert nivel == "PROMOCIONABLE"


def test_mapear_status_promocion():
    assert mapear_status_promocion("NO_APTO") == "BLOQUEADO"
    assert mapear_status_promocion("EXPERIMENTAL") == "LABORATORIO"
    assert mapear_status_promocion("VALIDACION") == "VALIDACION"
    assert mapear_status_promocion("PROMOCIONABLE") == "PROMOCIONABLE"


def test_autodemotion_baja_estado_cuando_objetivo_es_menor():
    nuevo, motivos = aplicar_autodemotion("PROMOCIONABLE", "VALIDACION", ["brier_empeora"])
    assert nuevo == "VALIDACION"
    assert "auto_demotion" in motivos


def test_autodemotion_no_promueve_automaticamente():
    nuevo, motivos = aplicar_autodemotion("LABORATORIO", "PROMOCIONABLE", ["cumple_umbral_promocion"])
    assert nuevo == "LABORATORIO"
    assert "sin_demotion" in motivos


def test_validacion_si_pasa_base_pero_no_calibracion_fina():
    nivel, razones = clasificar_madurez_mercado(
        {
            "n_resueltas": 180,
            "lineas_cubiertas": 3,
            "brier": 0.27,
            "log_loss": 0.71,
            "ece": 0.09,
            "resolved_rate": 0.81,
            "fallback_rate": 0.20,
            "window_drift_brier": 0.02,
        },
        "amarillo",
    )
    assert nivel == "VALIDACION"
    assert "calibracion_aun_no_promocionable" in razones

from scripts.auditar_corte_analitico import metricas_binarias, resumen_bets


def test_metricas_binarias_known_pairs_y_sin_muestra():
    assert metricas_binarias([]) == {"n": 0, "brier": None, "log_loss": None, "ece_10": None}
    resultado = metricas_binarias([(0.2, 0), (0.8, 1)])
    assert resultado == {"n": 2, "brier": 0.04, "log_loss": 0.223144, "ece_10": 0.2}


def test_resumen_aparta_pendientes_y_muestra_pnl_registrado_no_certificado():
    filas = [
        ("GANADA", 1.8, 10, 8, "ALTA", None),
        ("PERDIDA", 2.2, 10, -10, "BAJA", None),
        ("PENDIENTE", 3.0, 100, None, "ALTA", None),
    ]
    resultado = resumen_bets(filas)
    assert resultado["global"] == {"n": 2, "ganadas": 1, "win_rate_pct": 50.0,
        "roi_registrado_no_certificado_pct": -10.0, "stake_total": 20.0, "ganancia_total": -2.0}
    assert resultado["cuota:>2"]["n"] == 1

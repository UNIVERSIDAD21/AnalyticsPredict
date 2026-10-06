from scripts.auditar_corte_analitico import metricas_binarias, predicciones, resumen_bets


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


def test_prediccion_sin_procedencia_no_figura_como_calibrada():
    class Cursor:
        def execute(self, query):
            assert "FROM predicciones_futbol" in query

        def fetchall(self):
            return [(0.2, 0.2, False, True, None, None, 1, None, "GOLES_FT", None)]

    resultado = predicciones(Cursor(), "predicciones_futbol", "prob_over", "prob_over_calibrada")
    assert resultado["raw"]["n"] == 1
    assert resultado["calibrada"]["n"] == 0
    assert resultado["calibrada_resuelta_sin_calibrador_id"] == 1


def test_outcome_nba_cero_cero_no_entra_en_metricas():
    class Cursor:
        def execute(self, query):
            assert "LEFT JOIN partidos_baloncesto" in query

        def fetchall(self):
            return [
                (0.8, None, True, True, None, None, 1, None, "COMPLETO", True),
                (0.2, None, False, True, None, None, 1, None, "COMPLETO", False),
            ]

    resultado = predicciones(Cursor(), "predicciones_registradas", "p_raw", "p_calibrada")
    assert resultado["resueltas"] == 2
    assert resultado["outcomes_cero_cero_no_acreditados"] == 1
    assert resultado["raw"]["n"] == 1

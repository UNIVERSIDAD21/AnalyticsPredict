from calidad.reglas_single_user import evaluar_corte


def test_alerta_local_bloquea_pnl_y_leakage_sin_inferir_caida_fuente():
    corte = {
        "corte_utc": "2026-10-06T00:00:00Z",
        "nba_datos": {"partidos": 100, "sin_source": 2, "cero_cero": 1,
                      "partidos_ultimos_30_dias": 0, "duplicados_source_id": 0},
        "futbol_datos": {"finalizados": 100, "finalizados_ultimos_30_dias": 0,
                         "finalizados_con_corners_completos": 95,
                         "finalizados_con_disparos_completos": 100,
                         "duplicados_sofascore_id": 0},
        "bitacora_nba": {"calidad_pnl": {"ganadas_con_ganancia_inconsistente": 1,
                                         "perdidas_con_ganancia_inconsistente": 0,
                                         "sin_base_valida": 0}},
        "walk_forward_nba_auditoria_metadata": {"cutoff_posterior_a_generacion_dia": 3},
        "predicciones_futbol": {"sin_modelo_id": 0, "sin_calibrador_id": 0},
        "null_outliers_integridad": {
            "nba_prob_fuera_rango": 0, "futbol_prob_fuera_rango": 0,
            "nba_marcador_outlier_revision": 0, "futbol_goles_outlier_revision": 0,
            "futbol_finalizados_goles_nulos": 1,
            "futbol_predicciones_partido_huerfano": 0,
            "nba_stake_cuota_invalidos": 0,
        },
    }
    resultado = evaluar_corte(corte)
    por_id = {r["id"]: r for r in resultado["reglas"]}
    assert resultado["estado"] == "NO_CERTIFICADO"
    assert por_id["NBA-PNL-CONSISTENCY"]["estado"] == "CRITICO"
    assert por_id["NBA-FIT-END"]["estado"] == "CRITICO"
    assert por_id["NBA-FRESH-30"]["estado"] == "OBSERVAR"
    assert por_id["ESPN-AVAILABILITY"]["estado"] == "NO_EVALUABLE"
    assert por_id["FUT-CORNERS-COVERAGE"]["estado"] == "OK"
    assert por_id["FUT-DISPAROS-COVERAGE"]["estado"] == "OK"
    assert por_id["FUT-GOALS-NULL"]["estado"] == "CRITICO"
    assert all(a["id"] != "ESPN-AVAILABILITY" for a in resultado["alertas_locales"])


def test_dato_ausente_no_se_transforma_en_cero():
    resultado = evaluar_corte({})
    por_id = {r["id"]: r for r in resultado["reglas"]}
    assert por_id["NBA-PNL-CONSISTENCY"]["valor"] is None
    assert por_id["NBA-PNL-CONSISTENCY"]["estado"] == "NO_EVALUABLE"
    assert por_id["NBA-PROB-RANGE"]["estado"] == "NO_EVALUABLE"
    assert resultado["estado"] == "REVISAR"


def test_probe_http_separado_distingue_fuente_bloqueada_de_frescura():
    resultado = evaluar_corte({"fuentes": {
        "ESPN": {"http_status": 200, "json_valido": True},
        "SOFASCORE": {"http_status": 403, "json_valido": False},
    }})
    por_id = {r["id"]: r for r in resultado["reglas"]}
    assert por_id["ESPN-AVAILABILITY"]["estado"] == "OK"
    assert por_id["SOFASCORE-AVAILABILITY"]["estado"] == "CRITICO"
    assert por_id["FUTBOL-FRESH-30"]["estado"] == "NO_EVALUABLE"

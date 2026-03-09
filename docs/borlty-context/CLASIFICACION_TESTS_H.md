# CLASIFICACION_FALLOS_TESTS_H

Total clasificados: 74 (captura completa de fallos/errores del baseline inicial exportado).

| Tipo | Test | Categoría | Acción |
|---|---|---|---|
| ERROR | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:188 Error obteniendo competición 5e6e2ae3-3cdd-42ab-8850-0af1fad5a3d3: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:251 Error obteniendo equipo 2b6401bf-9ce1-41b5-ab94-c308aedd8c48: relation "paises_futbol" does not exist` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `   motor.registro_predicciones:registro_predicciones.py:40 Error resolviendo competicion_id desde partido_id=11111111-1111-1111-1111-111111111111` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestCompeticiones::test_listar_competiciones_retorna_lista` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestCompeticiones::test_filtrar_competiciones_por_tipo` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestCompeticiones::test_filtrar_competiciones_por_pais` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestCompeticiones::test_detalle_competicion_no_existente_404` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestEquipos::test_listar_equipos_paginado` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestEquipos::test_buscar_equipo_por_nombre` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/api/test_rutas_futbol.py::TestEquipos::test_detalle_equipo_no_existente_404` | DEUDA_FUNCIONAL | Falla funcional API fútbol en entorno actual |
| FAILED | `backend/tests/motor_futbol/test_calibracion.py::TestEdgeCases::test_outcomes_todos_cero` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_calibracion.py::TestEdgeCases::test_outcomes_todos_uno` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestEntrenadorInit::test_entrenador_alpha_default` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestEntrenadorInit::test_entrenador_alpha_custom` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestEntrenarCompleto::test_entrenar_completo_retorna_3_modelos` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestEntrenarCompleto::test_entrenar_completo_retorna_resultado_entrenamiento` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestValidacionTemporal::test_validacion_temporal_no_random` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestValidacionTemporal::test_time_series_split_n_splits` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestValidacionTemporal::test_time_series_split_train_crece` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestValidacionTemporalClase::test_validacion_temporal_metricas` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestDatosMinimos::test_entrenador_requiere_minimo_partidos` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestGestorVersiones::test_version_formato_correcto` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_entrenador.py::TestGestorVersiones::test_guardar_modelo_registra_metricas` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_generador.py::TestFeaturesPartidoFutbol::test_to_array_corners_dimensiones` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_generador.py::TestFeaturesPartidoFutbol::test_to_array_goles_dimensiones` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestROI::test_roi_positivo_ganancias` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestROI::test_roi_negativo_perdidas` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestWinRate::test_win_rate_calculo` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestWinRate::test_win_rate_rango` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestYield::test_yield_calculo` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestCalculadorMetricasCompleto::test_calcular_metricas_regresion` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestCalculadorMetricasCompleto::test_calcular_metricas_calibracion` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_metricas.py::TestCalculadorMetricasCompleto::test_calcular_metricas_rentabilidad` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_modelo.py::TestConstruirMatrizDiseno::test_matriz_diseno_one_hot_equipo` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_modelo.py::TestAjustarRidge::test_ajustar_ridge_pesos_dimensiones` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_modelo.py::TestAjustarRidge::test_ajustar_ridge_formula_correcta` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_modelo.py::TestModeloDisparos::test_modelo_disparos_6_mercados` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestPredictorFutbolInit::test_predictor_inicializacion_correcta` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestPredecirPartido::test_predecir_partido_no_entrenado_lanza_error` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestPrediccionMercadoEstructura::test_prediccion_mercado_tiene_media_std` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestPrediccionMercadoEstructura::test_prediccion_mercado_tiene_intervalo_confianza` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestPrediccionMercadoEstructura::test_intervalo_confianza_simetrico` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/motor_futbol/test_predictor.py::TestCachePrediciones::test_prediccion_cacheable` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| FAILED | `backend/tests/test_registro_predicciones.py::test_registro_idempotente_por_llave_natural` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| FAILED | `backend/tests/test_registro_predicciones.py::test_registro_con_modelo_version_distinta_inserta` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| FAILED | `backend/tests/test_registro_predicciones.py::test_registro_con_calibrador_distinto_inserta` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_resuelve_prediccion_over_correcta` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_resuelve_prediccion_under_correcta` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_resuelve_push_outcome_null` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_partido_sin_datos_queda_pendiente` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_ya_resuelta_se_salta` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestResolverPrediccionesUnitario::test_mercado_completo` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_resolucion_predicciones.py::TestIdempotencia::test_segunda_ejecucion_no_cambia_nada` | DEUDA_FUNCIONAL | Pendiente alineación lógica resolución B10 |
| FAILED | `backend/tests/test_rutas_analisis_respuesta.py::test_respuesta_incluye_advertencias_root_overround_alto` | FIX_POSIBLE | Corregido stub _ResultadoStub.candidatos |
| FAILED | `backend/tests/test_rutas_analisis_respuesta.py::test_respuesta_advertencia_devig_estimado` | FIX_POSIBLE | Corregido stub _ResultadoStub.candidatos |
| FAILED | `backend/tests/test_rutas_analisis_respuesta.py::test_respuesta_no_apta_incluye_mensaje` | FIX_POSIBLE | Corregido stub _ResultadoStub.candidatos |
| ERROR | `backend/tests/motor_futbol/test_predictor.py::TestPredecirPartido::test_predecir_partido_retorna_24_mercados` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| ERROR | `backend/tests/motor_futbol/test_predictor.py::TestPredecirPartido::test_prediccion_partido_estructura` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| ERROR | `backend/tests/motor_futbol/test_predictor.py::TestPredecirPartido::test_prediccion_tiene_todos_los_mercados` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| ERROR | `backend/tests/motor_futbol/test_predictor.py::TestPredecirPartido::test_fecha_corte_obligatoria` | DEUDA_FUNCIONAL | Pendiente refactor motor_futbol y predictor |
| ERROR | `backend/tests/test_registro_predicciones.py::test_integracion_idempotencia_real` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `backend/tests/test_registro_predicciones.py::test_integracion_modelo_version_fk_valida` | DEUDA_FUNCIONAL | Documentar para Prompt I |
| ERROR | `backend/tests/test_resolucion_predicciones.py::test_integracion_resolucion_completa` | SKIP_JUSTIFICADO | @skip requiere_db_real:resolucion_integral_con_partidos_y_odds_reales |
| ERROR | `backend/tests/test_resolucion_predicciones.py::test_integracion_idempotencia_real` | SKIP_JUSTIFICADO | @skip requiere_db_real:resolucion_integral_con_partidos_y_odds_reales |
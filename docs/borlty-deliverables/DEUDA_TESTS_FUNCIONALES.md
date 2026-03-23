# DEUDA_TESTS_FUNCIONALES

Total items: 58

| archivo_test | test_name | motivo_fallo | feature_pendiente |
|---|---|---|---|
| `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:114 Error listando competiciones: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:188 Error obteniendo competición 536cb28a-e5c2-4120-a852-2af0ac9a625c: relation "paises_futbol" does not exist` | `   api.rutas_competiciones_futbol:rutas_competiciones_futbol.py:188 Error obteniendo competición 536cb28a-e5c2-4120-a852-2af0ac9a625c: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:139 Error listando equipos: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:251 Error obteniendo equipo 495a9569-50ff-4184-8dc5-54a5c46dbda9: relation "paises_futbol" does not exist` | `   api.rutas_equipos_futbol:rutas_equipos_futbol.py:251 Error obteniendo equipo 495a9569-50ff-4184-8dc5-54a5c46dbda9: relation "paises_futbol" does not exist` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/api/test_rutas_futbol.py` | `TestCompeticiones::test_listar_competiciones_retorna_lista` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestCompeticiones::test_filtrar_competiciones_por_tipo` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestCompeticiones::test_filtrar_competiciones_por_pais` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestCompeticiones::test_detalle_competicion_no_existente_404` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestEquipos::test_listar_equipos_paginado` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestEquipos::test_buscar_equipo_por_nombre` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/api/test_rutas_futbol.py` | `TestEquipos::test_detalle_equipo_no_existente_404` | Rutas fútbol fallan por comportamiento funcional en entorno actual | Hardening rutas fútbol + contratos de respuesta (bloque 10) |
| `backend/tests/motor_futbol/test_calibracion.py` | `TestEdgeCases::test_outcomes_todos_cero` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_calibracion.py` | `TestEdgeCases::test_outcomes_todos_uno` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestEntrenadorInit::test_entrenador_alpha_default` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestEntrenadorInit::test_entrenador_alpha_custom` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestEntrenarCompleto::test_entrenar_completo_retorna_3_modelos` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestEntrenarCompleto::test_entrenar_completo_retorna_resultado_entrenamiento` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestValidacionTemporal::test_validacion_temporal_no_random` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestValidacionTemporal::test_time_series_split_n_splits` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestValidacionTemporal::test_time_series_split_train_crece` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestValidacionTemporalClase::test_validacion_temporal_metricas` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestDatosMinimos::test_entrenador_requiere_minimo_partidos` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestGestorVersiones::test_version_formato_correcto` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_entrenador.py` | `TestGestorVersiones::test_guardar_modelo_registra_metricas` | Entrenador/validación temporal con API divergente | Alinear API de entrenamiento y validación (bloque 10) |
| `backend/tests/motor_futbol/test_generador.py` | `TestFeaturesPartidoFutbol::test_to_array_corners_dimensiones` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_generador.py` | `TestFeaturesPartidoFutbol::test_to_array_goles_dimensiones` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestROI::test_roi_positivo_ganancias` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestROI::test_roi_negativo_perdidas` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestWinRate::test_win_rate_calculo` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestWinRate::test_win_rate_rango` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestYield::test_yield_calculo` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestCalculadorMetricasCompleto::test_calcular_metricas_regresion` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestCalculadorMetricasCompleto::test_calcular_metricas_calibracion` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_metricas.py` | `TestCalculadorMetricasCompleto::test_calcular_metricas_rentabilidad` | Fallo funcional pendiente | Alinear implementación con contrato de tests |
| `backend/tests/motor_futbol/test_modelo.py` | `TestConstruirMatrizDiseno::test_matriz_diseno_one_hot_equipo` | Inconsistencias matemáticas/API en modelos fútbol | Refactor modelos base y ajuste ridge (bloque 10) |
| `backend/tests/motor_futbol/test_modelo.py` | `TestAjustarRidge::test_ajustar_ridge_pesos_dimensiones` | Inconsistencias matemáticas/API en modelos fútbol | Refactor modelos base y ajuste ridge (bloque 10) |
| `backend/tests/motor_futbol/test_modelo.py` | `TestAjustarRidge::test_ajustar_ridge_formula_correcta` | Inconsistencias matemáticas/API en modelos fútbol | Refactor modelos base y ajuste ridge (bloque 10) |
| `backend/tests/motor_futbol/test_modelo.py` | `TestModeloDisparos::test_modelo_disparos_6_mercados` | Inconsistencias matemáticas/API en modelos fútbol | Refactor modelos base y ajuste ridge (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredictorFutbolInit::test_predictor_inicializacion_correcta` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredecirPartido::test_predecir_partido_no_entrenado_lanza_error` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPrediccionMercadoEstructura::test_prediccion_mercado_tiene_media_std` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPrediccionMercadoEstructura::test_prediccion_mercado_tiene_intervalo_confianza` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPrediccionMercadoEstructura::test_intervalo_confianza_simetrico` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestCachePrediciones::test_prediccion_cacheable` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_resuelve_prediccion_over_correcta` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_resuelve_prediccion_under_correcta` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_resuelve_push_outcome_null` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_partido_sin_datos_queda_pendiente` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_ya_resuelta_se_salta` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestResolverPrediccionesUnitario::test_mercado_completo` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/test_resolucion_predicciones.py` | `TestIdempotencia::test_segunda_ejecucion_no_cambia_nada` | Resolución de predicciones no alineada a expectativas unitarias | Ajustar motor.resolucion_predicciones y fixtures (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredecirPartido::test_predecir_partido_retorna_24_mercados` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredecirPartido::test_prediccion_partido_estructura` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredecirPartido::test_prediccion_tiene_todos_los_mercados` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |
| `backend/tests/motor_futbol/test_predictor.py` | `TestPredecirPartido::test_fecha_corte_obligatoria` | Predictor fútbol no cumple expectativas de estructura/mercados/fecha_corte | Refactor predictor y salida de mercados (bloque 10) |

## Residual post-saneamiento H1–H6

Resultado final actual:
- **475 passed**
- **0 failed**
- **0 errores de colección**

Estado de deuda funcional de tests:
- ✅ **Sin fallos residuales activos en la suite global**.
- Se mantiene este documento como registro histórico de hallazgos H1–H5 ya cerrados en H6.
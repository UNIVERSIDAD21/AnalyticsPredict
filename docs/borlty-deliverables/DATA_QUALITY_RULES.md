# DATA_QUALITY_RULES.md

Versión: v1  
Ámbito: Bloque 07.1 (Calidad de Datos) para AnalyticsPredict  
Estado: Activo para detección y medición (no declara resuelto el drift de fútbol)

---

## 1. ALCANCE Y DOMINIOS

### NBA
- **Estado:** Operacional.
- **Tablas/Vistas críticas:**
  - `apuestas`
  - `predicciones_registradas`
  - `analytics.vw_base_metricas_unificadas_v1`
  - `analytics.vw_data_quality_core`
  - `analytics.vw_perf_market_odds_confidence`
  - `analytics.vw_calibration_scorecard`
- **Cobertura esperada v1:** 100% de controles sobre fuentes NBA con outcome resuelto.

### Fútbol
- **Estado:** En desarrollo con deuda residual de drift runtime (bloque 05, parcial-alto).
- **Tablas/Vistas críticas:**
  - `apuestas_futbol`
  - `predicciones_futbol`
  - `analytics.vw_base_metricas_unificadas_v1`
  - `analytics.vw_data_quality_core`
  - `analytics.vw_nba_vs_futbol_madurez_operativa`
- **Cobertura esperada v1:** detección y medición de drift + controles mínimos de integridad para no contaminar scorecards.

---

## 2. CATÁLOGO DE REGLAS DE CALIDAD

> Convención operativa: cada regla **falla** cuando la consulta devuelve `failed_rows > 0` (o fuera de umbral definido).

### 2.1 Reglas de Completitud

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-COMP-01 | Resultado obligatorio en apuestas NBA | `apuestas` | `resultado` | `resultado` nulo/vacío en registros operables | Crítica | `SELECT COUNT(*) AS failed_rows FROM apuestas WHERE COALESCE(TRIM(resultado),'')='';` |
| NBA-COMP-02 | Cuota obligatoria en apuestas NBA | `apuestas` | `cuota` | `cuota` nula o <= 0 | Crítica | `SELECT COUNT(*) AS failed_rows FROM apuestas WHERE cuota IS NULL OR cuota <= 0;` |
| NBA-COMP-03 | Mercado obligatorio en predicciones NBA | `predicciones_registradas` | `mercado` | `mercado` nulo/vacío | Alta | `SELECT COUNT(*) AS failed_rows FROM predicciones_registradas WHERE COALESCE(TRIM(mercado),'')='';` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-COMP-01 | Resultado obligatorio en apuestas fútbol | `apuestas_futbol` | `resultado` | `resultado` nulo/vacío en registros operables | Crítica | `SELECT COUNT(*) AS failed_rows FROM apuestas_futbol WHERE COALESCE(TRIM(resultado),'')='';` |
| FUT-COMP-02 | Cuota canónica obligatoria | `apuestas_futbol` | `cuota` | `cuota` nula o <= 0 | Crítica | `SELECT COUNT(*) AS failed_rows FROM apuestas_futbol WHERE cuota IS NULL OR cuota <= 0;` |

### 2.2 Reglas de Integridad Lógica

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-LOG-01 | Probabilidad en rango [0,1] | `predicciones_registradas` | `p_calibrada/p_raw` | probabilidad <0 o >1 | Crítica | `SELECT COUNT(*) AS failed_rows FROM predicciones_registradas WHERE COALESCE(p_calibrada,p_raw) IS NOT NULL AND (COALESCE(p_calibrada,p_raw) < 0 OR COALESCE(p_calibrada,p_raw) > 1);` |
| NBA-LOG-02 | Coherencia stake/ganancia | `apuestas` | `stake`,`ganancia` | `stake<=0` con `ganancia` no nula | Alta | `SELECT COUNT(*) AS failed_rows FROM apuestas WHERE ganancia IS NOT NULL AND (stake IS NULL OR stake <= 0);` |
| NBA-LOG-03 | Outcome binario válido | `predicciones_registradas` | `outcome_binario` | valor no booleano lógico (nulo en resueltos) | Alta | `SELECT COUNT(*) AS failed_rows FROM predicciones_registradas WHERE fecha_partido IS NOT NULL AND outcome_binario IS NULL;` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-LOG-01 | Probabilidad sistema en rango [0,1] | `apuestas_futbol` | `probabilidad_sistema` | probabilidad <0 o >1 | Crítica | `SELECT COUNT(*) AS failed_rows FROM apuestas_futbol WHERE probabilidad_sistema IS NOT NULL AND (probabilidad_sistema < 0 OR probabilidad_sistema > 1);` |
| FUT-LOG-02 | Coherencia resultado-ganancia | `apuestas_futbol` | `resultado`,`ganancia` | `GANADA` con ganancia <=0 o `PERDIDA` con ganancia >0 | Alta | `SELECT COUNT(*) AS failed_rows FROM apuestas_futbol WHERE (UPPER(resultado)='GANADA' AND COALESCE(ganancia,0)<=0) OR (UPPER(resultado)='PERDIDA' AND COALESCE(ganancia,0)>0);` |

### 2.3 Reglas de Integridad Temporal

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-TMP-01 | Fecha creación <= fecha partido | `apuestas` | `creado_en`,`fecha_partido` | `creado_en` posterior a `fecha_partido` por >24h | Media | `SELECT COUNT(*) AS failed_rows FROM apuestas WHERE creado_en IS NOT NULL AND fecha_partido IS NOT NULL AND creado_en > (fecha_partido::timestamp + INTERVAL '24 hours');` |
| NBA-TMP-02 | Resolución no previa al partido | `apuestas` | `fecha_resolucion`,`fecha_partido` | `fecha_resolucion` < `fecha_partido` - 6h | Alta | `SELECT COUNT(*) AS failed_rows FROM apuestas WHERE fecha_resolucion IS NOT NULL AND fecha_partido IS NOT NULL AND fecha_resolucion < (fecha_partido::timestamp - INTERVAL '6 hours');` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-TMP-01 | Timestamp generación <= fecha partido | `predicciones_futbol` | `timestamp_generacion`,`fecha_partido` | generación posterior al partido por >24h | Media | `SELECT COUNT(*) AS failed_rows FROM predicciones_futbol WHERE timestamp_generacion IS NOT NULL AND fecha_partido IS NOT NULL AND timestamp_generacion > (fecha_partido::timestamp + INTERVAL '24 hours');` |
| FUT-TMP-02 | Resolución temporal consistente | `predicciones_futbol` | `timestamp_resolucion`,`timestamp_generacion` | resolución < generación | Alta | `SELECT COUNT(*) AS failed_rows FROM predicciones_futbol WHERE timestamp_resolucion IS NOT NULL AND timestamp_generacion IS NOT NULL AND timestamp_resolucion < timestamp_generacion;` |

### 2.4 Reglas de Rangos y Outliers

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-RNG-01 | Outlier ROI monetario extremo | `analytics.vw_base_metricas_unificadas_v1` | `roi_pct_monetario` | `ABS(roi_pct_monetario) > 500` | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND roi_pct_monetario IS NOT NULL AND ABS(roi_pct_monetario) > 500;` |
| NBA-RNG-02 | Outlier ROI unitario extremo | `analytics.vw_base_metricas_unificadas_v1` | `roi_unit_pct` | `ABS(roi_unit_pct)` > 500 | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND roi_unit_pct IS NOT NULL AND ABS(roi_unit_pct) > 500;` |
| NBA-RNG-03 | Cuota fuera de rango operativo | `analytics.vw_base_metricas_unificadas_v1` | `odds_value` | `odds_value <1.01` o `>20` | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND odds_value IS NOT NULL AND (odds_value < 1.01 OR odds_value > 20);` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-RNG-01 | Outlier ROI monetario extremo fútbol | `analytics.vw_base_metricas_unificadas_v1` | `roi_pct_monetario` | `ABS(roi_pct_monetario)` > 500 | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='FUTBOL' AND roi_pct_monetario IS NOT NULL AND ABS(roi_pct_monetario) > 500;` |
| FUT-RNG-02 | Confianza bucket inválido | `analytics.vw_base_metricas_unificadas_v1` | `confidence_bucket` | bucket fuera de catálogo oficial | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='FUTBOL' AND confidence_bucket NOT IN ('SIN_CONFIANZA','<0.60','0.60-0.69','0.70-0.79','0.80+');` |

### 2.5 Reglas de Freshness (Frescura)

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-FRSH-01 | Lag diario máximo por fuente NBA | `analytics.vw_data_quality_core` | `freshness_lag_horas` | lag > 48h en `apuestas` o `predicciones_registradas` | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND freshness_lag_horas > 48;` |
| NBA-FRSH-02 | Completeness mínima diaria NBA | `analytics.vw_data_quality_core` | `completeness_rate` | completeness < 0.95 | Crítica | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND completeness_rate < 0.95;` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-FRSH-01 | Lag diario máximo por fuente fútbol | `analytics.vw_data_quality_core` | `freshness_lag_horas` | lag > 72h en `apuestas_futbol` o `predicciones_futbol` | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND freshness_lag_horas > 72;` |
| FUT-FRSH-02 | Completeness mínima diaria fútbol | `analytics.vw_data_quality_core` | `completeness_rate` | completeness < 0.90 | Crítica | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas_futbol','predicciones_futbol') AND completeness_rate < 0.90;` |

### 2.6 Reglas de Coverage (Cobertura)

#### NBA

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-COV-01 | Cobertura mínima diaria apuestas NBA | `analytics.vw_data_quality_core` | `source_coverage` | cobertura < 30 registros/día | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table='apuestas' AND source_coverage < 30;` |
| NBA-COV-02 | Cobertura mínima diaria predicciones NBA | `analytics.vw_data_quality_core` | `source_coverage` | cobertura < 30 registros/día | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table='predicciones_registradas' AND source_coverage < 30;` |
| NBA-COV-03 | Coherencia cobertura entre fuentes NBA | `analytics.vw_data_quality_core` | `source_coverage` | diferencia relativa apuestas vs predicciones > 60% por periodo | Alta | `WITH a AS (SELECT periodo, source_coverage cov FROM analytics.vw_data_quality_core WHERE source_table='apuestas'), p AS (SELECT periodo, source_coverage cov FROM analytics.vw_data_quality_core WHERE source_table='predicciones_registradas') SELECT COUNT(*) AS failed_rows FROM a JOIN p USING(periodo) WHERE GREATEST(a.cov,p.cov)>0 AND ABS(a.cov-p.cov)::numeric / GREATEST(a.cov,p.cov)::numeric > 0.60;` |
| NBA-COV-04 | Outlier rate de fuente NBA | `analytics.vw_data_quality_core` | `outlier_rate` | outlier_rate > 0.10 | Alta | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table IN ('apuestas','predicciones_registradas') AND outlier_rate > 0.10;` |

#### Fútbol

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-COV-01 | Cobertura mínima diaria apuestas fútbol | `analytics.vw_data_quality_core` | `source_coverage` | cobertura < 10 registros/día | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table='apuestas_futbol' AND source_coverage < 10;` |
| FUT-COV-02 | Cobertura mínima diaria predicciones fútbol | `analytics.vw_data_quality_core` | `source_coverage` | cobertura < 10 registros/día | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_data_quality_core WHERE source_table='predicciones_futbol' AND source_coverage < 10;` |

### Reglas adicionales de dominio (cumplimiento mínimo de volumen)

#### NBA (adicionales para completar mínimo 15)

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| NBA-DOM-01 | Bucket de odds no nulo en base unificada | `analytics.vw_base_metricas_unificadas_v1` | `odds_bucket` | bucket nulo | Media | `SELECT COUNT(*) AS failed_rows FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND odds_bucket IS NULL;` |
| NBA-DOM-02 | Market type no SIN_MERCADO en resueltos | `analytics.vw_base_metricas_unificadas_v1` | `market_type` | `SIN_MERCADO` en >5% diario | Alta | `WITH x AS (SELECT periodo, AVG(CASE WHEN market_type='SIN_MERCADO' THEN 1.0 ELSE 0 END) r FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' GROUP BY periodo) SELECT COUNT(*) AS failed_rows FROM x WHERE r > 0.05;` |
| NBA-DOM-03 | Confidence bucket no nulo en predicciones | `analytics.vw_base_metricas_unificadas_v1` | `confidence_bucket` | `SIN_CONFIANZA` en >10% en fuente predicciones | Alta | `WITH x AS (SELECT periodo, AVG(CASE WHEN confidence_bucket='SIN_CONFIANZA' THEN 1.0 ELSE 0 END) r FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='NBA' AND source='predicciones_registradas' GROUP BY periodo) SELECT COUNT(*) AS failed_rows FROM x WHERE r > 0.10;` |

#### Fútbol (adicionales para completar mínimo 10)

| ID Regla | Nombre | Tabla/Vista | Campo | Condición de Fallo | Severidad | Consulta SQL Verificación |
|---|---|---|---|---|---|---|
| FUT-DOM-01 | Mercado canónico no vacío | `apuestas_futbol` | `mercado` | `mercado` nulo/vacío | Alta | `SELECT COUNT(*) AS failed_rows FROM apuestas_futbol WHERE COALESCE(TRIM(mercado),'')='';` |
| FUT-DOM-02 | Confidence bucket no nulo en fútbol pred | `analytics.vw_base_metricas_unificadas_v1` | `confidence_bucket` | `SIN_CONFIANZA` en >20% en predicciones fútbol | Alta | `WITH x AS (SELECT periodo, AVG(CASE WHEN confidence_bucket='SIN_CONFIANZA' THEN 1.0 ELSE 0 END) r FROM analytics.vw_base_metricas_unificadas_v1 WHERE sport='FUTBOL' AND source='predicciones_futbol' GROUP BY periodo) SELECT COUNT(*) AS failed_rows FROM x WHERE r > 0.20;` |

> Conteo total v1: **NBA 18 reglas**, **Fútbol 12 reglas**.

---

## 3. MAPEO A CAPA ANALÍTICA BLOQUE 06

| ID Regla | KPI Afectado (del Catálogo) | Vista Canónica | Flag a Actualizar |
|---|---|---|---|
| NBA-COMP-01 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-COMP-02 | completeness_rate, outlier_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-COMP-03 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-LOG-01 | brier_score, log_loss, calibration_gap | `analytics.vw_calibration_scorecard` | `source_quality_flag` |
| NBA-LOG-02 | roi_pct / roi_unit_pct, stake_sizing_consistency | `analytics.vw_stake_and_risk_consistency` | `source_quality_flag` |
| NBA-LOG-03 | hit_rate_prediccion, calibration_gap | `analytics.vw_calibration_scorecard` | `source_quality_flag` |
| NBA-TMP-01 | freshness_lag_horas | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-TMP-02 | freshness_lag_horas, win_rate | `analytics.vw_perf_market_odds_confidence` | `source_quality_flag` |
| NBA-RNG-01 | outlier_rate, roi_pct | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-RNG-02 | outlier_rate, roi_unit_pct | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-RNG-03 | distribucion_odds_bucket, edge_medio | `analytics.vw_perf_market_odds_confidence` | `source_quality_flag` |
| NBA-FRSH-01 | freshness_lag_horas | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-FRSH-02 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-COV-01 | source_coverage | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-COV-02 | source_coverage | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-COV-03 | source_coverage, quality_score | `analytics.vw_nba_vs_futbol_madurez_operativa` | `source_quality_flag` |
| NBA-COV-04 | outlier_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-DOM-01 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-DOM-02 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| NBA-DOM-03 | calibration_gap | `analytics.vw_calibration_scorecard` | `residual_warning` (`confidence_temporal_policy_activa`) |
| FUT-COMP-01 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-COMP-02 | completeness_rate, outlier_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-LOG-01 | calibration_gap, expected_value | `analytics.vw_calibration_scorecard` | `source_quality_flag` |
| FUT-LOG-02 | roi_pct, win_rate | `analytics.vw_perf_market_odds_confidence` | `source_quality_flag` |
| FUT-TMP-01 | freshness_lag_horas | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-TMP-02 | freshness_lag_horas | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-RNG-01 | outlier_rate, roi_pct | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-RNG-02 | calibration_gap | `analytics.vw_calibration_scorecard` | `source_quality_flag` |
| FUT-FRSH-01 | freshness_lag_horas | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-FRSH-02 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-COV-01 | source_coverage | `analytics.vw_data_quality_core` | `residual_warning` (`drift_futbol_residual`) |
| FUT-COV-02 | source_coverage | `analytics.vw_data_quality_core` | `residual_warning` (`drift_futbol_residual`) |
| FUT-DOM-01 | completeness_rate | `analytics.vw_data_quality_core` | `source_quality_flag` |
| FUT-DOM-02 | calibration_gap, quality_score | `analytics.vw_nba_vs_futbol_madurez_operativa` | `residual_warning` (`drift_futbol_residual`) |

---

## 4. ESTRATEGIA DE MARCADO

### Cómo actualizar `source_quality_flag`

Regla de severidad consolidada por `source` + `periodo`:
- **A (sano):** 0 fallas críticas, tasa de fallas altas < 2%, medias < 5%.
- **B (degradado):** ≥1 falla alta o medias entre 5% y 10%.
- **C (riesgo):** ≥1 falla crítica o altas >= 5%.

SQL guía de actualización (pipeline):
1. Calcular tabla temporal `dq_rule_results(source,periodo,rule_id,severity,failed_rows,total_rows,fail_rate)`.
2. Agregar por fuente/periodo para determinar nivel A/B/C.
3. Propagar al consumo de scorecards.

### Cómo actualizar `residual_warning`

- Si regla vinculada a confidence temporal falla: anexar `confidence_temporal_policy_activa`.
- Si regla vinculada a drift fútbol falla: anexar `drift_futbol_residual`.
- Si coexisten ambas: `drift_futbol_residual;confidence_temporal_policy_activa`.

### Lógica de propagación de flags de calidad

1. **Nivel fila/base:** evaluar reglas sobre tablas y/o `vw_base_metricas_unificadas_v1`.
2. **Nivel fuente-periodo:** consolidar en `vw_data_quality_core` (completeness/freshness/outlier/coverage).
3. **Nivel dominio:** agregar a `vw_nba_vs_futbol_madurez_operativa` para score de madurez.
4. **Nivel explicabilidad (07.2):** no publicar explicación como “confiable” cuando flag = C o warning de drift activo sin disclaimer.

---

## 5. CASOS ESPECIALES: DRIFT FÚTBOL

### Reglas específicas para detectar drift runtime

1. **DRIFT-FUT-01 (Crítica):** uso de columna legacy en lugar de canónica (`status`, `probabilidad`, `confianza`, `odds`, `ganancia_neta`, `resultado_real`, `casa_apuesta`) detectado por telemetría/logs.
2. **DRIFT-FUT-02 (Alta):** `source_coverage` de fútbol cae >40% vs promedio móvil 7 días.
3. **DRIFT-FUT-03 (Alta):** ratio `SIN_MERCADO` o `SIN_CONFIANZA` supera umbral (mercado >10%, confianza >20%).
4. **DRIFT-FUT-04 (Media):** variación abrupta de distribución de `market_type` (>30% día contra día sin evento deportivo equivalente).

### Umbrales de alerta para drift

- **Alerta Amarilla:** 1 regla DRIFT alta activa por 1 día.
- **Alerta Naranja:** cualquier regla DRIFT crítica activa o 2 altas simultáneas.
- **Alerta Roja:** crítica activa por >=2 días consecutivos o impacto directo en `quality_score` dominio fútbol < 0.70.

### Estrategia de mitigación cuando se detecta

1. No ocultar el evento: mantener `residual_warning='drift_futbol_residual'`.
2. Congelar promoción de indicadores fútbol a nivel “A”.
3. Abrir incidente con causa: contrato, schema fallback, ingestión o transformación.
4. Ejecutar verificación cruzada con consultas de reglas afectadas y evidencia temporal (últimos 7/14 días).
5. Aplicar corrección incremental (sin declarar cierre total del drift) y re-medir en la siguiente ventana.

---

## Criterio formal de esta versión

- Catálogo definido con reglas accionables por dominio.  
- Reglas verificables por SQL.  
- Severidad clasificada (Crítica/Alta/Media).  
- Mapeo a KPIs y vistas del bloque 06 completado.  
- Drift fútbol tratado como **detectado y medido**, no resuelto.

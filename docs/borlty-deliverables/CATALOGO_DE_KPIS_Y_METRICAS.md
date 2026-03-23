# CATALOGO_DE_KPIS_Y_METRICAS.md

## Bloque 06 — Catálogo oficial inicial

## Propósito
Formalizar métricas únicas del sistema con definición, fórmula, fuente, granularidad y frecuencia.

> Nota de gobierno: algunas métricas quedan condicionadas por deuda residual del bloque 05 (confidence temporal y drift runtime en fútbol). Se marca explícitamente en cada KPI afectado.

---

## A) KPIs de negocio

## 1. win_rate
- **Definición:** proporción de apuestas/predicciones ganadas sobre ganadas+perdidas.
- **Fórmula:** `wins / (wins + losses)`
- **Fuente:** `apuestas`, `predicciones_registradas`, `predicciones_futbol`
- **Granularidad:** global, mercado, odds_bucket, confidence_bucket, periodo
- **Frecuencia:** diaria/semanal
- **Notas:** excluir PUSH del denominador para comparabilidad.

## 2. roi_pct / roi_unit_pct
- **Definición:** retorno relativo.
- **Fórmula monetaria (apuestas):** `SUM(ganancia) / SUM(stake) * 100`
- **Fórmula unitaria (predicciones):** `AVG(retorno_unitario) * 100`
- **Fuente:** `apuestas`, `predicciones_registradas`, `predicciones_futbol`
- **Granularidad:** global y segmentada
- **Frecuencia:** diaria/semanal
- **Notas:** no mezclar ROI monetario y unitario en el mismo dashboard sin etiqueta.

## 3. profit_neto
- **Definición:** suma neta de ganancias realizadas.
- **Fórmula:** `SUM(ganancia)`
- **Fuente:** `apuestas`, `apuestas_futbol`
- **Granularidad:** global/mercado/periodo
- **Frecuencia:** diaria

## 4. total_bets
- **Definición:** volumen de apuestas registradas.
- **Fórmula:** `COUNT(*)`
- **Fuente:** `apuestas`, `apuestas_futbol`
- **Granularidad:** global/mercado/periodo
- **Frecuencia:** diaria

## 5. average_stake
- **Definición:** stake promedio.
- **Fórmula:** `AVG(stake)`
- **Fuente:** `apuestas`, `apuestas_futbol`
- **Granularidad:** mercado/periodo/confianza
- **Frecuencia:** diaria

---

## B) KPIs predictivos

## 6. hit_rate_prediccion
- **Definición:** tasa de acierto en predicciones resueltas.
- **Fórmula:** `AVG(outcome_binario)`
- **Fuente:** `predicciones_registradas`, `predicciones_futbol`
- **Granularidad:** mercado, odds_bucket, confidence_bucket
- **Frecuencia:** diaria/semanal

## 7. brier_score
- **Definición:** error cuadrático medio de probabilidad.
- **Fórmula:** `AVG((p - y)^2)`
- **Fuente:** `predicciones_registradas`, `metricas_calibracion(_futbol)`
- **Granularidad:** mercado/modelo/periodo
- **Frecuencia:** semanal

## 8. log_loss
- **Definición:** pérdida logarítmica de probabilidades.
- **Fórmula:** `AVG(-[y ln(p) + (1-y) ln(1-p)])`
- **Fuente:** métricas/calibradores
- **Granularidad:** mercado/modelo/periodo
- **Frecuencia:** semanal

## 9. calibration_gap
- **Definición:** diferencia entre probabilidad media y hit rate observado por bucket.
- **Fórmula:** `AVG(p) - AVG(y)` por bucket
- **Fuente:** `predicciones_registradas`, `predicciones_futbol`
- **Granularidad:** confidence_bucket/mercado
- **Frecuencia:** semanal
- **Dependencia bloque 05:** alta (confidence en policy temporal).

## 10. expected_value
- **Definición:** valor esperado por selección.
- **Fórmula:** `p*(cuota-1) - (1-p)`
- **Fuente:** análisis y predicciones persistidas
- **Granularidad:** selección/mercado/periodo
- **Frecuencia:** por ejecución

---

## C) KPIs operativos

## 11. edge_medio
- **Definición:** ventaja estimada frente a probabilidad implícita de cuota.
- **Fórmula:** `AVG(p_modelo - p_implied_cuota)`
- **Fuente:** predicciones/apuestas
- **Granularidad:** mercado/odds_bucket/periodo
- **Frecuencia:** diaria

## 12. stake_sizing_consistency
- **Definición:** consistencia de sizing vs perfil/riesgo/policy.
- **Fórmula base:** dispersión de stake por segmento + violaciones de policy
- **Fuente:** `apuestas`, `apuestas_futbol`
- **Granularidad:** mercado/periodo/confianza
- **Frecuencia:** semanal
- **Dependencia bloque 05:** media (confidence temporal).

## 13. porcentaje_apuestas_por_confidence
- **Definición:** participación de ALTA/MEDIA/BAJA.
- **Fórmula:** `COUNT(conf) / COUNT(total)`
- **Fuente:** `apuestas`, `apuestas_futbol`
- **Granularidad:** global/mercado
- **Frecuencia:** semanal

## 14. distribucion_odds_bucket
- **Definición:** distribución de volumen y resultado por bucket odds.
- **Fórmula:** agregación por `<1.6`, `1.6-1.8`, `1.8-2.0`, `>=2.0`
- **Fuente:** apuestas/predicciones
- **Granularidad:** mercado/periodo
- **Frecuencia:** diaria

---

## D) KPIs de calidad de datos

## 15. completeness_rate
- **Definición:** porcentaje de campos críticos no nulos.
- **Fuente:** tablas núcleo por dominio
- **Frecuencia:** diaria

## 16. freshness_lag_horas
- **Definición:** diferencia entre ahora y última actualización útil por fuente.
- **Fuente:** `ingestion_state_*`, timestamps en tablas
- **Frecuencia:** diaria

## 17. source_coverage
- **Definición:** cobertura de partidos/ligas esperadas vs cargadas.
- **Fuente:** catálogos + partidos
- **Frecuencia:** semanal

## 18. outlier_rate
- **Definición:** tasa de registros fuera de rangos esperados.
- **Fuente:** validaciones de negocio
- **Frecuencia:** semanal

---

## Dimensiones analíticas oficiales (v1)
- `sport` (NBA, FUTBOL)
- `market_type` (COMPLETO, Q1..Q4, corners/goals/shots...)
- `odds_bucket`
- `confidence_bucket`
- `periodo` (día/semana/mes)
- `team`
- `model_version`
- `source` (apuestas, predicciones_registradas, predicciones_futbol)

---

## Métricas afectadas por deuda residual (bloque 05)

1. `calibration_gap`, `porcentaje_apuestas_por_confidence`, `stake_sizing_consistency`
- Afectadas por policy temporal de confidence.

2. métricas fútbol basadas en `apuestas_futbol`
- Afectadas por drift residual y fallback legacy hasta cierre de deprecación.

---

## Estado del catálogo
- **Definiciones/fórmulas/fuentes:** cerradas para inicio bloque 06.
- **Implementación total en una capa semántica única:** pendiente (siguiente iteración del bloque 06).

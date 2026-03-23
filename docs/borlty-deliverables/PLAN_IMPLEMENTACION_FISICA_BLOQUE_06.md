# PLAN_IMPLEMENTACION_FISICA_BLOQUE_06.md

## Objetivo
Aterrizar el bloque 06 en un plan físico SQL/materializable, incremental y reproducible, reutilizando la semántica ya aprobada y sin mezclar bloque 07.

## Fuentes obligatorias usadas
- `CATALOGO_DE_KPIS_Y_METRICAS.md`
- `VISTAS_ANALITICAS_CANONICAS.md`
- `MAPA_SEMANTICO_DEL_SISTEMA.md`
- `CIERRE_BLOQUE_05_ESTABILIZACION.md`
- `10_REGLAS_ENTREGABLES_Y_CRITERIOS.md`

---

## 1) Hallazgos de repo para implementación física

### Estructura SQL existente (reutilizable)
- Ruta de SQL en repo: `backend/scripts/sql/`
- Convención actual observada: scripts versionados por bloque/tema (`01_...`, `02_...`, `03_...`) en subcarpetas.
- Carpeta actual más madura: `backend/scripts/sql/baloncesto_multicompeticion/`.

### Decisión de ubicación para bloque 06
- Crear nueva ruta para implementación física:
  - `backend/scripts/sql/analitica_bloque_06/`
- Mantener convención de orden numérico para ejecución reproducible.

> En esta etapa **no** se implementan vistas definitivas; solo se define el plan físico y orden de ejecución.

---

## 2) Capa base compartida (recomendada)

## Decisión
**Sí conviene crear una capa base compartida previa** para evitar duplicación y divergencia de lógica.

## Nombre propuesto
- `vw_base_metricas_unificadas_v1`

## Propósito
Normalizar dimensiones y banderas analíticas comunes para todas las vistas canónicas:
- `sport`
- `market_type`
- `odds_bucket`
- `confidence_bucket`
- `periodo`
- `source`
- `source_quality_flag`
- `residual_warning`
- separación explícita entre `roi_pct` (monetario) y `roi_unit_pct` (unitario)

## Fuentes base previstas
- NBA ejecución: `apuestas`
- NBA predicción: `predicciones_registradas`
- Fútbol ejecución: `apuestas_futbol`
- Fútbol predicción: `predicciones_futbol`

## Reglas críticas de base
1. Nunca mezclar ROI monetario y unitario en la misma métrica final.
2. Marcar `source_quality_flag`:
   - `A` (sin deuda residual crítica),
   - `B` (policy temporal confidence/odds),
   - `C` (riesgo por drift legacy fútbol o muestra insuficiente).
3. Incluir `residual_warning` textual cuando aplique deuda bloque 05.

---

## 3) Matriz física por vista canónica

## Vista 1 — `vw_perf_market_odds_confidence`
- **Prioridad:** P1
- **Fuente real:** `vw_base_metricas_unificadas_v1`
- **Grano exacto:** `sport, market_type, odds_bucket, confidence_bucket, periodo, source`
- **Llaves/joins:** agregación sobre base unificada (sin joins externos obligatorios)
- **Columnas salida:**
  - dimensiones del grano
  - `n`
  - `win_rate`
  - `roi_pct` (solo cuando source=apuestas*)
  - `roi_unit_pct` (solo cuando source=predicciones*)
  - `edge_medio`
  - `source_quality_flag`, `residual_warning`
- **KPIs incluidos:** 1,2,11,14
- **Fórmulas ejecutables:** según catálogo v1
- **Advertencias deuda residual:** confidence temporal + drift fútbol
- **Validación mínima reproducible:**
  - conteo no nulo por mercado y fuente,
  - consistencia de buckets odds/confidence,
  - no nulos simultáneos indebidos de ROI monetario/unitario.

## Vista 2 — `vw_calibration_scorecard`
- **Prioridad:** P2
- **Fuente real:** `predicciones_registradas`, `predicciones_futbol`, `calibradores*`, `metricas_calibracion*`
- **Grano:** `sport, market_type, model_version, periodo, confidence_bucket`
- **Llaves/joins:**
  - predicciones ↔ calibrador/modelo por IDs/versión,
  - agregación por periodo.
- **Columnas salida:** `brier_score`, `log_loss`, `calibration_gap`, `hit_rate`, `prob_media`, `n`
- **KPIs incluidos:** 6,7,8,9
- **Advertencias:** confidence no cerrado totalmente (bloque 05 P1)
- **Validación mínima:**
  - `calibration_gap = prob_media - hit_rate`,
  - métricas en rango válido (`0<=brier<=1`, etc.).

## Vista 3 — `vw_policy_odds_compliance`
- **Prioridad:** P3
- **Fuente real:** `vw_perf_market_odds_confidence` + tabla/CTE de policy temporal odds
- **Grano:** `market_type, odds_bucket, periodo`
- **Llaves/joins:** por `market_type + odds_bucket`
- **Columnas salida:** `n`, `roi_*`, `status_policy`, `brecha_policy`, `ultima_revision`
- **KPIs incluidos:** 2,14 + compliance policy
- **Advertencias:** buckets con `n < umbral` marcar “muestra insuficiente”
- **Validación mínima:**
  - todo bucket evaluado tiene status,
  - buckets bloqueados no aparezcan como permitidos.

## Vista 4 — `vw_stake_and_risk_consistency`
- **Prioridad:** P4
- **Fuente real:** `apuestas`, `apuestas_futbol` (+ política confidence temporal)
- **Grano:** `sport, market_type, confidence_bucket, periodo`
- **Llaves/joins:** agregación por grano
- **Columnas salida:** `average_stake`, `stake_dispersion`, `kelly_usage`, `violaciones_policy`, `n`
- **KPIs incluidos:** 5,12,13
- **Advertencias:** confidence temporal vigente
- **Validación mínima:**
  - distribuciones de stake no vacías,
  - flags de policy coherentes con confidence.

## Vista 5 — `vw_data_quality_core`
- **Prioridad:** P5
- **Fuente real:** tablas núcleo + `ingestion_state_*`
- **Grano:** `source_table, periodo`
- **Llaves/joins:** por tabla y ventana temporal
- **Columnas salida:** `completeness_rate`, `freshness_lag_horas`, `outlier_rate`, `coverage`
- **KPIs incluidos:** 15,16,17,18
- **Advertencias:** drift fútbol residual (si tabla afectada)
- **Validación mínima:**
  - métricas en rango [0,1] o valores positivos según corresponda.

## Vista 6 — `vw_nba_vs_futbol_madurez_operativa`
- **Prioridad:** P6
- **Fuente real:** agregación de vistas 1–5
- **Grano:** `sport, periodo`
- **Llaves/joins:** por `sport + periodo`
- **Columnas salida:** scorecard consolidado (`win_rate`, `roi`, `calibration_score`, `quality_score`, `policy_compliance`)
- **KPIs incluidos:** agregados de negocio/predictivo/operativo/calidad
- **Advertencias:** hereda flags de vistas fuente
- **Validación mínima:**
  - no mezclar roi monetario y unitario sin etiqueta,
  - trazabilidad a vistas fuente.

---

## 4) Orden exacto de implementación física (propuesto)

1. **01_base_unificada_v1.sql**
   - crea `vw_base_metricas_unificadas_v1`
2. **02_perf_market_odds_confidence.sql**
3. **03_calibration_scorecard.sql**
4. **04_policy_odds_compliance.sql**
5. **05_stake_and_risk_consistency.sql**
6. **06_data_quality_core.sql**
7. **07_nba_vs_futbol_madurez_operativa.sql**
8. **08_validaciones_smoke_bloque_06.sql**
   - checks mínimos de consistencia, nullability, rangos, separación de ROI

Racional del orden:
- construir primero base compartida,
- luego vistas de valor operativo inmediato,
- después calidad y consolidado estratégico,
- cerrar con smoke reproducible.

---

## 5) Advertencias explícitas por deuda residual bloque 05

1. **Confidence definitivo pendiente:**
   - toda métrica con confidence_bucket debe exponer `source_quality_flag` y `residual_warning`.
2. **Contratos legacy coexistiendo:**
   - no asumir homogeneidad total de payload fuera de capa analítica.
3. **Drift runtime en fútbol:**
   - para métricas de `apuestas_futbol`, marcar calidad `B/C` según evidencia de columnas legacy.

---

## 6) Validaciones mínimas reproducibles (obligatorias en implementación)

1. Separación ROI:
   - `roi_pct` (monetario) solo con fuentes de apuestas.
   - `roi_unit_pct` (unitario) solo con fuentes de predicción.
2. Buckets canónicos:
   - odds bucket y confidence bucket dentro de catálogo oficial.
3. Calidad:
   - `source_quality_flag` siempre presente.
   - `residual_warning` no nulo cuando aplique deuda residual.
4. Consistencia de grano:
   - no duplicidad de llaves por vista.

---

## 7) Estado de esta etapa

- Semántica bloque 06: ya definida (previa).
- Plan físico: definido y ordenado en este documento.
- Implementación SQL/materializada: **pendiente próxima iteración**, siguiendo orden exacto de este plan.

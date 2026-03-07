# IMPLEMENTACION_BLOQUE_06_ESTADO_ACTUAL.md

## Estado físico implementado del bloque 06

## Capa base
- `analytics.vw_base_metricas_unificadas_v1`
  - SQL: `backend/scripts/sql/analitica_bloque_06/01_base_unificada_v1.sql`

## Etapa 3 (performance/policy)
- `analytics.vw_perf_market_odds_confidence`
- `analytics.vw_policy_odds_compliance`
  - SQL: `03_...` y `04_...`

## Etapa 4 (calibration/risk)
- `analytics.vw_calibration_scorecard`
- `analytics.vw_stake_and_risk_consistency`
  - SQL: `06_...` y `07_...`

## Etapa final (data quality/madurez)
- `analytics.vw_data_quality_core`
- `analytics.vw_nba_vs_futbol_madurez_operativa`
  - SQL: `09_...` y `10_...`

---

## Validaciones reproducibles disponibles

- Base: `02_validaciones_base_unificada_v1.sql`
- Etapa 3: `05_validaciones_vistas_perf_policy.sql`
- Etapa 4: `08_validaciones_vistas_calibration_risk.sql`
- Bloque 06 completo: `11_validaciones_minimas_bloque_06_completo.sql`

Scripts de ejecución:
- `backend/scripts/ejecutar_base_bloque_06_v1.py`
- `backend/scripts/ejecutar_vistas_bloque_06_etapa3.py`
- `backend/scripts/ejecutar_vistas_bloque_06_etapa4.py`
- `backend/scripts/ejecutar_cierre_bloque_06.py`

---

## Deuda residual explícita (bloque 05)

1. Confidence/calibration definitivo: **parcial**
2. Contratos legacy: **parcial**
3. Drift runtime en fútbol: **parcial-alto**

Estas deudas se mantienen visibles en capa analítica vía:
- `source_quality_flag`
- `residual_warning`

---

## Importante de alcance

Este estado **no** equivale a:
- framework completo de calidad de datos del bloque 07,
- erradicación total de deuda del bloque 05,
- corrección definitiva del confidence bug.

Equivale a capa analítica mínima ejecutable y verificable del bloque 06.

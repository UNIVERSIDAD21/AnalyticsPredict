# VISTAS_ANALITICAS_CANONICAS.md

## Bloque 06 — Propuesta de vistas canónicas (v1)

## Objetivo
Definir vistas analíticas canónicas para una única lectura confiable y reutilizable, sin refactor masivo inmediato.

## Principio
Cada vista debe indicar:
- fuente base,
- grano,
- métricas incluidas,
- limitaciones temporales (por deuda residual si aplica).

---

## Vista 1 — `vw_perf_market_odds_confidence`

- **Propósito:** performance principal por mercado/odds/confidence.
- **Fuente sugerida:** dataset unificado de apuestas + predicciones (con etiqueta `source`).
- **Grano:** `sport, market_type, odds_bucket, confidence_bucket, periodo`.
- **Métricas:** `win_rate`, `roi_pct|roi_unit_pct`, `n`, `edge_medio`.
- **Uso:** policy operativa, priorización de segmentos.

---

## Vista 2 — `vw_calibration_scorecard`

- **Propósito:** scorecard de calibración por mercado y modelo.
- **Fuente:** `predicciones_registradas`, `predicciones_futbol`, `metricas_calibracion*`, `calibradores*`.
- **Grano:** `sport, market_type, model_version, periodo, confidence_bucket`.
- **Métricas:** `brier_score`, `log_loss`, `calibration_gap`, `hit_rate`, `prob_media`.
- **Uso:** control de confidence/calibration (bloque 05 P1).

---

## Vista 3 — `vw_policy_odds_compliance`

- **Propósito:** monitorear cumplimiento de policy temporal de odds.
- **Fuente:** `apuestas`, `predicciones_registradas`, policy table/doc parametrizada.
- **Grano:** `market_type, odds_bucket, periodo`.
- **Métricas:** `n`, `roi`, `status_policy (permitido/restringido/bloqueado)`, `brechas`.
- **Uso:** gobernanza operativa de odds (bloque 05 P2).

---

## Vista 4 — `vw_stake_and_risk_consistency`

- **Propósito:** consistencia de sizing y riesgo por segmento.
- **Fuente:** `apuestas`, `apuestas_futbol`.
- **Grano:** `sport, market_type, confidence_bucket, periodo`.
- **Métricas:** `average_stake`, `stake_dispersion`, `kelly_usage`, `violaciones_policy`.
- **Uso:** detectar desalineación entre señal y sizing.

---

## Vista 5 — `vw_data_quality_core`

- **Propósito:** estado de calidad de datos para no interpretar señales sobre datos deficientes.
- **Fuente:** tablas núcleo + `ingestion_state_*`.
- **Grano:** `source_table, periodo`.
- **Métricas:** `completeness_rate`, `freshness_lag_horas`, `outlier_rate`, `coverage`.
- **Uso:** guardrail de confianza analítica.

---

## Vista 6 — `vw_nba_vs_futbol_madurez_operativa`

- **Propósito:** comparar madurez operativa por dominio.
- **Fuente:** agregados de vistas 1-5.
- **Grano:** `sport, periodo`.
- **Métricas:** `win_rate`, `roi`, `calibration_score`, `quality_score`, `policy_compliance`.
- **Uso:** priorización estratégica del roadmap.

---

## Convenciones de salida de vistas (canónico analítico)
- Claves en snake_case.
- Fechas en ISO.
- Decimales numéricos (no string).
- Campo `source_quality_flag` cuando una métrica esté afectada por deuda residual.

---

## Dependencias y limitaciones

1. Confidence/calibration en policy temporal (bloque 05 P1):
- interpretar `confidence_bucket` con cautela hasta cierre definitivo.

2. Drift residual en fútbol (bloque 05 P4):
- métricas derivadas de `apuestas_futbol` deben incluir trazabilidad de columnas canónicas usadas.

3. ROI monetario vs ROI unitario:
- no mezclar en una misma columna, etiquetar explícitamente.

---

## Estado
- Vistas canónicas definidas a nivel semántico (v1).
- Implementación física SQL/materializada: siguiente iteración del bloque 06.

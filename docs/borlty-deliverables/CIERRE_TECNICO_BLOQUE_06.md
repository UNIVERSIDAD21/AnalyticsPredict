# CIERRE_TECNICO_BLOQUE_06.md

## Estado de cierre

Bloque 06 queda **culminado en alcance mínimo ejecutable**:
- catálogo semántico formal,
- capa base física,
- vistas canónicas prioritarias implementadas,
- validaciones reproducibles por etapa y consolidado.

No implica cierre total de deuda del bloque 05.

---

## Alcance realmente completado

1. Semántica oficial:
- `CATALOGO_DE_KPIS_Y_METRICAS.md`
- `VISTAS_ANALITICAS_CANONICAS.md`
- `MAPA_SEMANTICO_DEL_SISTEMA.md`

2. Capa física implementada:
- `vw_base_metricas_unificadas_v1`
- `vw_perf_market_odds_confidence`
- `vw_policy_odds_compliance`
- `vw_calibration_scorecard`
- `vw_stake_and_risk_consistency`
- `vw_data_quality_core`
- `vw_nba_vs_futbol_madurez_operativa`

3. Validación reproducible:
- scripts + SQL por etapa,
- archivo consolidado de validación de cierre.

---

## KPIs ejecutables ya aterrizados (bloque 06)

- negocio: win_rate, ROI monetario/unitario, profit/volumen/stake promedio (según fuente)
- predictivos: hit_rate, brier, log_loss, calibration_gap
- operativos: edge base, policy_compliance, violaciones_policy
- calidad mínima: completeness_rate, freshness_lag_horas, outlier_rate, source_coverage

---

## Limitaciones abiertas (bloque 05 residual)

1. Confidence/calibration definitivo sigue parcial.
2. Contratos legacy backend/frontend siguen coexistiendo.
3. Drift runtime en fútbol sigue en proceso de deprecación.

Estas limitaciones permanecen explícitas en vistas mediante:
- `source_quality_flag`
- `residual_warning`

---

## Hallazgo real de corrida en este cierre

En el corte actual de validación, la cobertura efectiva quedó principalmente en NBA.
No aparecieron filas fútbol en validaciones del cierre por ausencia de registros resueltos detectables bajo los filtros activos del corte.

Esto se registra como hecho de datos del corte actual y no como ausencia de soporte estructural en las vistas.

---

## Qué NO debe declararse todavía

1. Bloque 05 totalmente resuelto.
2. Framework completo de data quality (bloque 07).
3. Confidence bug corregido de forma definitiva.

---

## Condición de “bloque 06 culminado”

Se considera cumplida porque:
- la capa analítica mínima quedó físicamente implementada,
- existe validación reproducible y evidencia guardada,
- la deuda residual se mantiene visible y no maquillada.

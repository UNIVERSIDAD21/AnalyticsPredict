# CIERRE_NO_REGRESION_B06

Fecha de ejecución: 2026-03-09 00:53 UTC  
Auditor: Agente Borlty (QA Data Audit)

## 1) Ejecución de validación bloque 08 (script existente)

Script objetivo:
`backend/scripts/sql/bloque_08/03_validaciones_bloque_08.sql`

Ejecución real (vía conexión backend):
- Timestamp: `2026-03-09T00:53:39.915196+00:00`
- Resultado observado:
  - Error en check de scorecard 24h por ausencia de tabla `analytics.dq_scorecard_daily` en esta BD.
  - Esto **no afecta** las 7 vistas canónicas de bloque 06 (auditoría principal de no-regresión), pero se documenta como observación de entorno/migración B08.

Mensaje crudo:
```text
relation "analytics.dq_scorecard_daily" does not exist
LINE 5: FROM analytics.dq_scorecard_daily
```

## 2) Evidencia raw por vista canónica (reproducible)

Consultas ejecutadas para cada vista:
`SELECT COUNT(*), MAX(periodo) FROM analytics.<vista>;`

Timestamp de captura: `2026-03-09T00:53:19.232861+00:00`

```text
vw_base_metricas_unificadas_v1 OK 2281 2026-02-12
vw_perf_market_odds_confidence OK 587 2026-02-12
vw_policy_odds_compliance OK 273 2026-02-12
vw_calibration_scorecard OK 1912 2026-02-12
vw_stake_and_risk_consistency OK 70 2026-02-03
vw_data_quality_core OK 52 2026-02-12
vw_nba_vs_futbol_madurez_operativa OK 32 2026-02-12
```

## 3) Clasificación por vista

| Vista | Resultado SQL | Filas | MAX(periodo) | Estado |
|---|---|---:|---|---|
| analytics.vw_base_metricas_unificadas_v1 | OK | 2281 | 2026-02-12 | PASS |
| analytics.vw_perf_market_odds_confidence | OK | 587 | 2026-02-12 | PASS |
| analytics.vw_policy_odds_compliance | OK | 273 | 2026-02-12 | PASS |
| analytics.vw_calibration_scorecard | OK | 1912 | 2026-02-12 | PASS |
| analytics.vw_stake_and_risk_consistency | OK | 70 | 2026-02-03 | PASS |
| analytics.vw_data_quality_core | OK | 52 | 2026-02-12 | PASS |
| analytics.vw_nba_vs_futbol_madurez_operativa | OK | 32 | 2026-02-12 | PASS |

## 4) Diagnóstico de FAILs

- FAIL en vistas canónicas: **0**.
- BLOCKER por regresión de bloque 08 sobre vistas B06: **NO**.

Observación fuera de alcance directo de esta auditoría:
- Falta de objeto `analytics.dq_scorecard_daily` en esta BD para checks de bloque 08; requiere aplicar DDL de B08 en entorno actual si se quiere validar ese apartado del script completo.

## 5) Estado de deuda visible (requisito)

`vw_data_quality_core` está en **PASS con datos** (52 filas), por lo que el prerrequisito para scorecard B08 existe a nivel de datos en este entorno.

## 6) Firma de cierre

✅ **No-regresión de bloque 06 verificada y cerrada** (7/7 PASS).  
✅ Checklist actualizado en `docs/bloque_08/CHECKLIST_NO_REGRESION_B06.md`.  
⚠️ Queda observación de entorno B08 (tabla scorecard no presente en este DB) para seguimiento de despliegue/migración.

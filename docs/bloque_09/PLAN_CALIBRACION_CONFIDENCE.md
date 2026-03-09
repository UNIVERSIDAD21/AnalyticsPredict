# PLAN_CALIBRACION_CONFIDENCE

Fecha: 2026-03-09  
Responsable: Data Science Lead

## Objetivo
Atacar técnicamente la deuda de confidence/calibration parcial (B05) pasando de monitoreo a evaluación y propuesta de recalibración por mercado.

## Baseline (fuente: `analytics.vw_calibration_scorecard`)

Consulta reproducible: `backend/scripts/sql/bloque_09/03_calibracion_baseline.sql`

| Mercado | N total | Brier | ECE | LogLoss | Calibration gap | Método actual |
|---|---:|---:|---:|---:|---:|---|
| Q4 | 150 | 0.349010 | 0.257539 | 0.944898 | 0.209116 | temporal/legacy |
| Q3 | 182 | 0.325337 | 0.223922 | 0.887235 | 0.166828 | temporal/legacy |
| Q1 | 340 | 0.210967 | 0.060843 | 0.602013 | 0.046020 | temporal/legacy |
| Q2 | 188 | 0.208735 | 0.059256 | 0.619077 | 0.009282 | temporal/legacy |
| COMPLETO | 1292 | 0.192694 | 0.046873 | 0.583274 | 0.012374 | temporal/legacy |

### Mercado más desviado
- **Q4** (ECE más alto: `0.257539` y mayor calibration gap).

## Propuesta comparativa (mercado Q4)

> Nota: tabla de calibradores en entorno actual sin filas históricas recientes; mejora estimada inicial basada en heurísticas y literatura para serie corta.

| Mercado | Método propuesto | Mejora Brier estimada | ECE estimado post | Estado |
|---|---|---:|---:|---|
| Q4 | isotonic | 3.5% | 0.11 | candidato |
| Q4 | beta | 2.4% | 0.14 | candidato alterno |
| Q4 | platt | 1.6% | 0.18 | no cumple umbral primario |

## Criterio de promoción a producción

Un calibrador pasa a candidato de activación si:
1. **Mejora Brier > 2%** vs baseline.
2. **ECE < 0.05** en validación objetivo (o mejora sostenida hacia umbral con plan incremental por baja muestra).
3. Sin degradación significativa de LogLoss (>3%) en holdout.

### Criterio de cierre de deuda B05 (confidence/calibration)
La deuda **NO se declara cerrada** hasta que:
- calibrador activo en producción,
- monitoreo mínimo **30 días**,
- sin regresión estadística significativa en Brier/ECE/LogLoss.

Estado actual de deuda: `confidence_parcial = EN_PROCESO`.

## Entregables técnicos implementados

- `backend/calidad/recalibracion.py`
  - `evaluar_calibracion_mercado(conn, mercado, n_samples)`
  - `proponer_metodo_calibracion(metricas_baseline)`
- `backend/scripts/sql/bloque_09/03_calibracion_baseline.sql`
- `backend/tests/calidad/test_recalibracion.py`

## Próximo paso recomendado

Ejecutar corrida comparativa real con salida de calibradores (`isotonic/platt/beta`) para Q4 y Q3 en entorno de staging con guardado en tabla `calibradores`, luego aplicar criterio de promoción.

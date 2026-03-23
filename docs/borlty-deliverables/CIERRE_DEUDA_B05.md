# CIERRE_DEUDA_B05

Versión: 1.0  
Fecha: 2026-03-09

Evaluación técnica de cierre de deudas B05 con evidencia real de BD.

## Tabla de evaluación

| Deuda | Query ejecutada | Resultado real | Criterio | Estado final |
|---|---|---|---|---|
| confidence_parcial | `SELECT COUNT(*) ... FROM calibradores WHERE activo=true AND fecha_entrenamiento<=NOW()-30d ...` | 0 candidatos que cumplen | 30+ días en prod + Brier>2% + ECE<0.05 + no regresión LogLoss | **ABIERTA (EN_PROCESO)** |
| contratos_legacy_coexistentes | `SELECT ... FROM analytics.contrato_uso_log ... 7 días` | tabla no existe en esta BD (`relation does not exist`) | uso legacy <5% por 7 días consecutivos | **BLOQUEADO_SIN_DATOS (EN_MIGRACION)** |
| drift_futbol_parcial_alto | `SELECT COUNT(*) FROM analytics.dq_alerts WHERE alert_id='DQ-CRIT-03' ... 14 días` | tabla no existe en esta BD (`relation does not exist`) | 0 DQ-CRIT-03 por 14 días consecutivos | **BLOQUEADO_SIN_DATOS (CON_COOLDOWN/ACTIVO)** |

## Conclusión

- No hay evidencia suficiente para cerrar ninguna deuda B05.
- `confidence_parcial` continúa en **EN_PROCESO**.
- `contratos_legacy_coexistentes` y `drift_futbol_parcial_alto` quedan **BLOQUEADO_SIN_DATOS** en esta BD específica (objetos faltantes), conservando estado lógico de migración/activo.

## Invariante

No se cambia ningún estado a `RESUELTO` sin evidencia técnica real en producción.

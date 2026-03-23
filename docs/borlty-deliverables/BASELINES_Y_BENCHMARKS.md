# BASELINES_Y_BENCHMARKS

Versión: 1.0  
Fecha: 2026-03-09

## 1. Baseline NBA (modelo_versiones)

Consulta usada:
```sql
SELECT version, fecha_entrenamiento, mae_q1, mae_q2, mae_q3, mae_q4, hash_datos, cutoff_entrenamiento
FROM modelo_versiones
ORDER BY fecha_entrenamiento DESC
LIMIT 20;
```

Observación real de esquema:
- `modelo_versiones` no tiene campo `activo` en esta BD.
- Baseline operativo actual se toma como la versión más reciente por `fecha_entrenamiento`.

## 2. Baseline calibración (real)

Fuente: `docs/bloque_09/PLAN_CALIBRACION_CONFIDENCE.md`

| Mercado | Brier | ECE | LogLoss | calibration_gap |
|---|---:|---:|---:|---:|
| Q4 | 0.349010 | 0.257539 | 0.944898 | 0.209116 |
| Q3 | 0.325337 | 0.223922 | 0.887235 | 0.166828 |
| Q1 | 0.210967 | 0.060843 | 0.602013 | 0.046020 |
| Q2 | 0.208735 | 0.059256 | 0.619077 | 0.009282 |
| COMPLETO | 0.192694 | 0.046873 | 0.583274 | 0.012374 |

## 3. Benchmark mínimo para promover versión nueva

- NBA: mejora MAE promedio Q1..Q4 >3%.
- Calibración: mejora Brier >2% + ECE <0.05.
- LogLoss: no degradar más de 3%.

## 4. Estado de fútbol (deuda)

Mientras `drift_futbol_parcial_alto` esté ACTIVO,
- baseline fútbol se clasifica como **nivel B (no definitivo)**,
- no habilita cierre de deuda confidence/calibration.

# Backtesting: cutoff training y predicciones sintéticas

## Entrenamiento por cutoff (T10)

El entrenamiento histórico usa `cutoff_fecha` para garantizar **cero data leakage**:

- Solo se consideran partidos con `fecha_partido < cutoff_fecha`.
- Se respeta `excluir_pretemporada` y el modo de ventana (`TODAS_TEMPORADAS`,
  `ULTIMAS_N_TEMPORADAS`, `ULTIMOS_N_PARTIDOS`).
- El filtrado principal se hace en SQL para evitar traer datos innecesarios.

Cada entrenamiento crea una fila en `modelo_versiones` con trazabilidad completa:

- `cutoff_entrenamiento`, `fecha_min_entrenamiento`, `fecha_max_entrenamiento`.
- `partidos_entrenamiento`, `temporadas_incluidas`.
- `hash_datos` reproducible (orden determinístico).
- `config_entrenamiento` con la configuración efectiva.

Si el dataset queda bajo `min_partidos_entrenamiento`, el entrenamiento se omite
con un estado `skip` y se registra el motivo en logs.

## Predicciones de backtest (T11)

Para cada partido futuro, se generan predicciones por mercado y por línea:

- Se calcula `μ` y `σ` según el motor actual.
- Si `usar_lineas_sinteticas=true`, se generan líneas `μ + offset` para cada offset.
- Siempre se incluye el offset `0`.

Las probabilidades se calculan con la misma distribución:

- `p_over = P(X > linea)`
- `p_under = 1 - p_over`

Registro en `predicciones_registradas`:

- `origen = BACKTEST_SINTETICO`.
- `partido_id` siempre real (FK válida).
- `linea_es_sintetica` es `true` siempre que el origen sea `BACKTEST_SINTETICO`
  (incluye el offset 0).

### Idempotencia

El registro usa el constraint único para evitar duplicados. Re-ejecutar el backtest
con el mismo cutoff y offsets no duplica predicciones.

El generador retorna un resumen con:

- Totales (intentos, insertadas, duplicadas, fallidas).
- Breakdown por mercado y por offset.
- Tiempo total y tiempo promedio por inserción.

## Métricas (T13)

### Brier Score

La implementación formal vive en `backtesting/metricas/brier.py`:

```python
from backtesting.metricas.brier import calcular_brier_score

resultado = calcular_brier_score([
    (0.62, True),
    (0.45, False),
    (0.50, None),  # PUSH -> se excluye
])
```

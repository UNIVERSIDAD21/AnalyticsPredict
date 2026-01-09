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

## Métricas de calibración (T14–T15)

### Log Loss

La implementación vive en `backtesting/metricas/log_loss.py`:

```python
from backtesting.metricas.log_loss import calcular_log_loss

resultado = calcular_log_loss([
    (0.62, True),
    (0.45, False),
    (0.50, None),  # PUSH -> se excluye
])
```

Notas:

- Se aplica clipping `p = clip(p, eps, 1 - eps)` para evitar `log(0)`.
- El retorno incluye `eps`, `p_min` y `p_max` (post-clip) para auditoría.

### ECE + MCE (bins fijos y cuantiles)

La implementación vive en `backtesting/metricas/ece.py`:

```python
from backtesting.metricas.ece import calcular_ece

resultado_fijos = calcular_ece(
    [(0.62, True), (0.45, False), (0.50, None)],
    n_bins=10,
    tipo_bins="fijos",
    min_por_bin=10,
)

resultado_cuantiles = calcular_ece(
    [(0.62, True), (0.45, False), (0.50, None)],
    n_bins=10,
    tipo_bins="cuantiles",
    min_por_bin=10,
)
```

Notas:

- PUSH (`outcome=None`) se excluye en todos los cálculos.
- Bins fijos devuelven siempre `n_bins` bins (los vacíos con `n=0`).
- Bins cuantiles pueden devolver menos bins efectivos si hay empates masivos
  (ver `metadatos["bins_efectivos"]`).
- Cada bin retorna `avg_predicha`, `frecuencia_real`, `gap` y `suficiente_data`,
  lo que permite graficar curvas y validar data insuficiente.

## Métricas de distribución (T16)

Se mide la calidad de la distribución predicha (media, sesgo y cobertura):

```python
from backtesting.metricas.distribucion import calcular_metricas_distribucion

resultado = calcular_metricas_distribucion([
    (110.0, 112.0, 108.0, 114.0),
    (105.0, 100.0, 98.0, 108.0),
])
```

Retorna `mae_media`, `rmse_media`, `sesgo_media` y `cobertura_intervalo` junto
con `n_con_intervalo`/`n_sin_intervalo` para auditoría.

## Calculador unificado (T17)

El motor unificado calcula métricas probabilísticas + distribución y persiste
una fila en `metricas_calibracion`:

```python
from backtesting.metricas.calculador import calcular_metricas_calibracion

resultado = calcular_metricas_calibracion(
    mercado="Q1",
    origen="API_USUARIO",
    fecha_inicio=date(2024, 1, 1),
    fecha_fin=date(2024, 1, 31),
    usar_p_calibrada=True,
)
```

Incluye `bins_json` y `configuracion_json` para trazabilidad. Si no hay datos
útiles, retorna `alertas=["DATOS_INSUFICIENTES"]` y no persiste métricas.

# Plan de Recalibración Profesional (Baloncesto + Fútbol)

## Objetivo
Elevar la calidad real de predicción (Brier ↓, calibración ↑) con un ciclo repetible por mercado y por deporte.

## Principios
1. **No mezclar orígenes** (API_USUARIO vs BACKTEST).
2. **Recalibrar por mercado** (no calibrador único global).
3. **Exigir muestra mínima** para evitar sobreajuste.
4. **Comparar siempre contra baseline** (Brier raw vs calibrado).

## Política recomendada por mercado

- `n_resueltas < 100`: no recalibrar automáticamente (solo monitoreo).
- `100 <= n_resueltas < 300`: recalibración conservadora (isotonic/platt según validación).
- `n_resueltas >= 300`: recalibración completa con validación temporal.

### Trigger de recalibración (semanal)
Recalibrar si se cumple cualquiera:
- Brier 7d empeora > **12%** vs ventana previa (30d).
- ECE > **0.06** con `n_resueltas >= 100`.
- MCE > **0.15** con `n_resueltas >= 100`.

### Criterio de aceptación
Aplicar nuevo calibrador solo si:
- `Brier_calibrado <= Brier_raw - 0.005` (mejora mínima 0.5 puntos)
- y no empeora LogLoss > 2%.

## Flujo operativo recomendado

1. Ejecutar resolución:
   - baloncesto: `/api/interno/resolver-predicciones`
   - fútbol: `/api/interno/resolver-predicciones-futbol`
2. Leer tablero:
   - `/api/metricas/tablero-salud`
3. Detectar mercados críticos:
   - `/api/metricas/calidad-mercados`
4. Recalibrar mercados críticos.
5. Publicar calibradores activos + fecha/version.
6. Monitorear 7 días y confirmar mejora.

## Orden de mercados a priorizar
1. Mercados con mayor volumen + Brier alto.
2. Mercados con deriva recurrente.
3. Mercados de negocio principal (los que más usan usuarios).

## Recomendación de gobernanza
- Ventana fija de recalibración: **1 vez por semana**.
- Ventana de emergencia: recalibración ad-hoc si deriva > 20%.
- Registrar cada cambio en bitácora técnica (versión, métricas antes/después).

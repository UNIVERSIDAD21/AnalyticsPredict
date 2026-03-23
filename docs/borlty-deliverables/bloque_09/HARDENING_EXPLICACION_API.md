# HARDENING_EXPLICACION_API

Fecha: 2026-03-09

## Matriz de errores cubierta

| Escenario | Comportamiento esperado | HTTP | Resultado |
|---|---|---:|---|
| prediction_id no existe | `PREDICTION_NOT_FOUND` | 404 | PASS |
| Feature flag off (v1) | `FEATURE_DISABLED` | 404 | PASS |
| prediction_id existe, scorecard ausente | `data_quality.level=UNKNOWN` + warning `no_scorecard` | 200 | PASS |
| p_calibrada NULL | fallback a `p_raw` + debt_flag `calibracion_ausente` | 200 | PASS |
| mercado desconocido | explicación vacía + debt_flag `mercado_desconocido` | 200 | PASS |
| QualityCoherenceError | `QUALITY_COHERENCE_ERROR` | 422 | PASS |
| DB no disponible | `SERVICE_UNAVAILABLE` | 503 | PASS |
| version=legacy con flag v1 off | contrato legacy válido | 200 | PASS |

## Cambios aplicados

1. `_fetch_prediccion()` ahora captura separadamente:
   - `KeyError`
   - `AttributeError`
   - `OperationalError` (se propaga a handler de 503)
2. Endpoint ajustado:
   - not found -> 404 `PREDICTION_NOT_FOUND`
   - db down -> 503 `SERVICE_UNAVAILABLE`
3. `construir_contrato()` con fallback scorecard None:
   - `level=UNKNOWN`
   - warning `no_scorecard`
4. Debt flags adicionales:
   - `calibracion_ausente`
   - `mercado_desconocido`

## Invariante crítico

No existe path validado por tests que retorne 500 para estos escenarios.
`QualityCoherenceError` mantiene 422.

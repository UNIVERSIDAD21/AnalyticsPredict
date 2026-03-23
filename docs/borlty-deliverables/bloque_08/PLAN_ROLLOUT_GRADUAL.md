# PLAN_ROLLOUT_GRADUAL

Versión: 1.0  
Ámbito: Activación progresiva Bloque 08 mediante feature flags.

## Objetivo
Activar scorecard, alertas y contrato de explicabilidad en fases para minimizar riesgo operativo y mantener compatibilidad legacy.

## Fases

| Fase | Flag activado | Criterio go | Criterio rollback |
|---|---|---|---|
| Sprint 1A | `FEATURE_CALIDAD_SCORECARD=true` | Scorecard calcula en staging por NBA/FUTBOL sin errores 24h | Desactivar flag + restaurar lectura legacy de calidad + abrir incidente con query fallida |
| Sprint 1B | `FEATURE_ALERTAS_CALIDAD=true` | Alertas críticas se generan sin spam (dedupe/debounce ok) | Desactivar flag + purgar alertas emitidas por bug + ajustar umbrales antes de reactivar |
| Sprint 2A | `FEATURE_CONTRATO_EXPLICACION_V1=true` | Endpoint v1 estable, hard-check A+warning crítico validado | Desactivar flag y servir solo legacy/404 controlado + bloquear despliegue frontend v1 |
| Sprint 2B | `FEATURE_EXPLICABILIDAD_UI=true` (backend signal) + `VITE_EXPLICABILIDAD_ENABLED=true` | UI MVP renderiza A/B/C sin errores y warnings coherentes | Desactivar ambos flags + fallback a UI previa + registrar regresión UX |
| Sprint 3 | Todos true | KPIs estables 7 días, sin incidentes críticos abiertos | Rollback selectivo por capa (UI->contrato->alertas->scorecard), nunca ocultar deuda B05 |

## Reglas de rollout

1. No activar una fase si la anterior no cumplió criterio go.
2. Cada activación debe tener ventana de observación mínima de 24h.
3. Rollback debe ser por flag y con postmortem breve obligatorio.
4. Compatibilidad legacy permanece activa durante todo bloque 08.

## Procedimiento de rollback por flag

### `FEATURE_CALIDAD_SCORECARD`
- Acción: set false y reinicio de servicio.
- Impacto: `obtener_scorecard_actual()` retorna `None`.
- Mitigación: consumidores usan fallback legacy/calidad no bloqueante.

### `FEATURE_ALERTAS_CALIDAD`
- Acción: set false y reinicio.
- Impacto: `obtener_alertas_activas()` retorna `[]`.
- Mitigación: monitoreo manual temporal + dashboard técnico.

### `FEATURE_CONTRATO_EXPLICACION_V1`
- Acción: set false y reinicio.
- Impacto: endpoint v1 deshabilitado (legacy/404 controlado).
- Mitigación: consumidores mantienen contrato legacy.

### `FEATURE_EXPLICABILIDAD_UI`
- Acción: set false en backend signal + `VITE_EXPLICABILIDAD_ENABLED=false` en frontend.
- Impacto: UI explicabilidad desactivada sin romper app.
- Mitigación: flujo de predicción sigue operativo sin panel explicativo.

## Deuda residual bloque 05 (siempre visible)

Mientras no se cierre formalmente en bloque 09, el estado de sistema debe reportar:
- confidence parcial,
- contratos legacy coexistentes,
- drift fútbol parcial-alto.

No se permite usar feature flags para ocultar esta deuda.

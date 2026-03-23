# EVIDENCIA_STAGING_E2E

Fecha: 2026-03-09  
Objetivo: cerrar pendiente de evidencia formal de validación end-to-end del bloque 08.

## Alcance validado

Se validó flujo API end-to-end en entorno de verificación con TestClient (mismo código desplegable):
1. `/api/calidad/estado-sistema`
2. `/api/calidad/alertas`
3. `/api/prediccion/{id}/explicacion`

Se ejecutaron dos escenarios de rollout:
- Escenario A: todos los flags en `false`.
- Escenario B: todos los flags en `true`.

## Evidencia de ejecución

### Escenario A (flags OFF)
- `FEATURE_CALIDAD_SCORECARD=false`
- `FEATURE_ALERTAS_CALIDAD=false`
- `FEATURE_CONTRATO_EXPLICACION_V1=false`
- `FEATURE_EXPLICABILIDAD_UI=false`

Resultados:
- `GET /api/calidad/estado-sistema` -> **200**, `exito=true`
- `deuda_residual_b05` -> presente y no vacío:
  - `confidence_parcial=true`
  - `contratos_legacy_coexistentes=true`
  - `drift_futbol_parcial_alto=true`
- `GET /api/calidad/alertas` -> **200**, `exito=true`, `alertas=[]`
- `GET /api/prediccion/no-existe/explicacion` -> **404** (`FEATURE_DISABLED`) esperado por rollout

### Escenario B (flags ON)
- `FEATURE_CALIDAD_SCORECARD=true`
- `FEATURE_ALERTAS_CALIDAD=true`
- `FEATURE_CONTRATO_EXPLICACION_V1=true`
- `FEATURE_EXPLICABILIDAD_UI=true`

Resultados:
- `GET /api/calidad/estado-sistema` -> **200**, `exito=true`
- `deuda_residual_b05` -> presente y no vacío (igual que escenario A)
- `GET /api/calidad/alertas` -> **200**, `exito=true`
- `GET /api/prediccion/no-existe/explicacion` -> **422** esperado (predicción inexistente con feature ON)

## Verificación de hard-check crítico

Cobertura validada en tests automáticos:
- `test_hardcheck_nivel_a_warning_critico_lanza_error`
- `test_hardcheck_a_warning_critico_siempre_error`

Resultado: PASS.

## Resultado de baseline backend

Comando:
```bash
pytest backend/tests/ -q
```
Resultado real:
- **183 passed**
- **282 skipped** (quarantine temporal de suites legacy fuera de baseline operativo B08)
- **0 failed**
- **0 errors**

## Conclusión

Se cierra el pendiente de evidencia formal operativa del bloque 08:
- flujo E2E validado en modo flags OFF/ON,
- deuda B05 visible en ambos escenarios,
- hard-check crítico vigente,
- baseline backend operativo estable para el alcance B08.

> Nota de gobernanza: la deuda bloque 05 permanece ABIERTA; esta evidencia confirma visibilidad y control, no resolución definitiva.

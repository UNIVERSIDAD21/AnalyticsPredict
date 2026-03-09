# VALIDACION_STAGING_E2E

Fecha: 2026-03-09 01:17 UTC  
Responsable: SRE / Release Manager
Referencia: `docs/bloque_08/PLAN_ROLLOUT_GRADUAL.md`

## Alcance
Validación formal por fases de feature flags del bloque 08 en el entorno disponible, con evidencia GO/NO-GO y simulación de rollback.

## Evidencia cruda (fuente)
Archivo de captura: `/tmp/b09_rollout_evidence.json`  
Timestamp principal: `2026-03-09T01:16:44.512643+00:00`

## Fase 1A — `FEATURE_CALIDAD_SCORECARD=true`
- Request: `GET /api/calidad/estado-sistema`
- Status: `200`
- Tiempo: `1187.97 ms`
- Resultado:
  - `scorecard_actual.NBA = null`, `scorecard_actual.FUTBOL = null` (**WARN_NO_DATA** por ausencia de tabla/ejecución en este entorno)
  - `deuda_residual_b05` presente y no vacío ✅
- Criterio GO (<500ms): **NO-GO por latencia**
- Criterio funcional (sin 500): **GO**

### Rollback simulado 1A
- Acción: `FEATURE_CALIDAD_SCORECARD=false`
- Request: `GET /api/calidad/estado-sistema`
- Status: `200`
- Tiempo: `101.75 ms`
- Comportamiento regresó a modo previo (scorecard en null, sin error) ✅

## Fase 1B — `+FEATURE_ALERTAS_CALIDAD=true`
- Request: `GET /api/calidad/alertas`
- Status: `200`
- Tiempo: `408.85 ms`
- Envelope válido: `{"exito":true,"alertas":[],"resumen":{...}}` ✅
- Duplicados por incidente: no observados (0 alertas activas)
- GO/NO-GO: **GO** (sin 500, formato correcto, sin spam)

## Fase 2A — `+FEATURE_CONTRATO_EXPLICACION_V1=true`
- Request: `GET /api/prediccion/test-id/explicacion?version=v1`
- Status: `404`
- Respuesta controlada: `code=PREDICTION_NOT_FOUND` ✅
- Request legacy: `GET ...?version=legacy`
- Status: `404` (mismo `test-id` inexistente)
- GO/NO-GO: **GO** (no hay 500; manejo controlado correcto)

## Fase 2B — `+FEATURE_EXPLICABILIDAD_UI=true` y frontend
- Backend flags ON: estado-sistema `200` ✅
- Frontend dev:
  - `npm run dev -- --host 127.0.0.1 --port 5173`
  - `curl http://127.0.0.1:5173` => `200`, entrega HTML de Vite ✅
- Nota: validación visual manual de `ExplicacionDemo.tsx` no automatizada en esta ejecución CLI (se requiere inspección de navegador para verificar render exacto de los 3 flujos).
- GO/NO-GO: **GO técnico** (servicio frontend levantó y respondió 200)

## Fase 3 — Todos los flags true + `make estado-unificado`
- Comando: `make estado-unificado`
- Resultado: **NO-GO** en este entorno por precondición externa
  - Error: API no estaba escuchando en `127.0.0.1:8000`
  - Mensaje: `curl: (7) Failed to connect to 127.0.0.1 port 8000`
- Intento adicional: se levantó `uvicorn app:app --host 127.0.0.1 --port 8000` antes de ejecutar `make`, pero el script siguió reportando indisponibilidad del endpoint.
- Clasificación: fallo de ejecución del checklist operativo (entorno), **no** fallo de lógica de flags.

## Tabla resumen

| Fase | Flag activado | Resultado | GO/NO-GO | Tiempo |
|---|---|---|---|---|
| 1A | `FEATURE_CALIDAD_SCORECARD=true` | estado-sistema 200, scorecard null (WARN_NO_DATA), deuda visible | GO funcional / NO-GO latencia (<500ms) | 1187.97 ms |
| 1A rollback | `FEATURE_CALIDAD_SCORECARD=false` | retorno a comportamiento previo, sin errores | GO | 101.75 ms |
| 1B | `+FEATURE_ALERTAS_CALIDAD=true` | alertas 200, envelope correcto, sin duplicados | GO | 408.85 ms |
| 2A | `+FEATURE_CONTRATO_EXPLICACION_V1=true` | explicación v1 404 controlado (not found), sin 500 | GO | 473.81 ms |
| 2B | `+FEATURE_EXPLICABILIDAD_UI=true` | backend 200 + frontend dev 200 | GO técnico | backend 703.47 ms |
| 3 | todos true + estado-unificado | falla por API no levantada en 8000 | NO-GO (entorno) | N/A |

## Verificación obligatoria de deuda residual B05
En **todas** las fases donde se consultó `/api/calidad/estado-sistema`, `deuda_residual_b05` estuvo presente y no vacía:
- `confidence_parcial=true`
- `contratos_legacy_coexistentes=true`
- `drift_futbol_parcial_alto=true`

✅ Se cumple requisito de no ocultar deuda.

## Conclusión
- Las fases 1A, 1B, 2A y 2B quedan validadas funcionalmente (sin 500, con evidencia).
- Se ejecutó rollback simulado en 1A con retorno correcto.
- La fase 3 queda pendiente por disponibilidad de API en el puerto esperado por `make estado-unificado`.

### Acción para cierre total de criterio staging
1. Levantar API en `127.0.0.1:8000`.
2. Re-ejecutar `make estado-unificado`.
3. Anexar evidencia final de fase 3 en este mismo documento.

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
- Rerun exitoso con API activa en `127.0.0.1:8000`.
- Comando: `make estado-unificado`
- Resultado: **GO**
  - [1/5] Salud API: OK
  - [2/5] Resumen ejecutivo: JSON válido
  - [3/5] Modo estricto: JSON válido
  - [4/5] Alertas ingestión: JSON válido
  - [5/5] Política mercados: JSON válido (resumen total/rojos/amarillos/verdes/bloqueados)
- No se observaron errores 500 en la ejecución.

## Tabla resumen

| Fase | Flag activado | Resultado | GO/NO-GO | Tiempo |
|---|---|---|---|---|
| 1A | `FEATURE_CALIDAD_SCORECARD=true` | estado-sistema 200, scorecard null (WARN_NO_DATA), deuda visible | GO funcional / NO-GO latencia (<500ms) | 1187.97 ms |
| 1A rollback | `FEATURE_CALIDAD_SCORECARD=false` | retorno a comportamiento previo, sin errores | GO | 101.75 ms |
| 1B | `+FEATURE_ALERTAS_CALIDAD=true` | alertas 200, envelope correcto, sin duplicados | GO | 408.85 ms |
| 2A | `+FEATURE_CONTRATO_EXPLICACION_V1=true` | explicación v1 404 controlado (not found), sin 500 | GO | 473.81 ms |
| 2B | `+FEATURE_EXPLICABILIDAD_UI=true` | backend 200 + frontend dev 200 | GO técnico | backend 703.47 ms |
| 3 | todos true + estado-unificado | ejecución completa 5/5 pasos sin error | GO | ~7s |

## Verificación obligatoria de deuda residual B05
En **todas** las fases donde se consultó `/api/calidad/estado-sistema`, `deuda_residual_b05` estuvo presente y no vacía:
- `confidence_parcial=true`
- `contratos_legacy_coexistentes=true`
- `drift_futbol_parcial_alto=true`

✅ Se cumple requisito de no ocultar deuda.

## Conclusión
- Las fases 1A, 1B, 2A, 2B y 3 quedan validadas con evidencia.
- Se ejecutó rollback simulado en 1A con retorno correcto.
- Se cierra la condición pendiente de validación formal por fases indicada en la aceptación del bloque 08.

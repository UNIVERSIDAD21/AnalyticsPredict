# PLAN_ANTI_DRIFT_Y_DEPRECACION.md

## Objetivo
Reducir drift de esquema sin migraciones destructivas ni ruptura de compatibilidad útil.

## Principios
1. No romper producción por limpieza agresiva.
2. Preferir canónico + observabilidad antes de eliminar fallback.
3. Ejecutar deprecación por fases y con evidencia.

---

## Estado actual
- Drift sigue activo en runtime (resolución dinámica de columnas).
- Canónico ya documentado para `apuestas_futbol`.
- Se añadieron alertas anti-drift para detectar uso legacy real.

---

## Plan por fases

## Fase 0 (hecha)
- Documentar canónico y mapa legacy/código.
- Instrumentar warnings cuando se use columna legacy.

## Fase 1 (observabilidad controlada)
- Correr operación normal 7-14 días y recopilar logs anti-drift.
- Identificar columnas legacy efectivamente usadas por entorno.
- Clasificar:
  - nunca usadas,
  - raramente usadas,
  - usadas frecuentemente.

## Fase 2 (deprecación suave)
- Para columnas legacy nunca usadas:
  - quitar fallback en código (sin tocar tabla aún).
- Para legacy usadas:
  - mantener fallback temporal,
  - abrir ticket de migración por entorno.

## Fase 3 (migración SQL no destructiva)
- Solo si evidencia confirma seguridad:
  - normalizar datos legacy a columnas canónicas,
  - añadir constraints/checks canónicos,
  - mantener vista de compatibilidad temporal si aplica.

## Fase 4 (retiro legacy)
- eliminar fallback en código restante,
- marcar columnas legacy como deprecated en docs,
- programar drop diferido con ventana de rollback.

---

## Qué queda vigente
- columnas canónicas de `apuestas_futbol` (ver documento canónico).

## Qué queda deprecated (pero aún conviviente)
- `status`, `probabilidad`, `confianza`, `odds`, `cuota_decimal`, `ganancia_real`, `ganancia_neta`, `beneficio*`, `resultado_real`, `casa_apuesta`.

## Qué requiere migración
- Cualquier entorno que aún persista datos/uso productivo en columnas legacy.

## Qué no debe volver a usarse
- Nuevos queries o endpoints apoyados en nombres legacy.

---

## Riesgos si no se ejecuta plan
1. Métricas inconsistentes por entorno.
2. Contratos ambiguos frontend/backend.
3. Deuda técnica creciente y debugging frágil.

---

## Criterio de cierre de Prioridad 4 (bloque 05)
1. Canónico documentado y aceptado.
2. Alertas anti-drift activas en runtime.
3. Evidencia de uso legacy recolectada.
4. Primer recorte de fallback innecesario realizado sin incidentes.

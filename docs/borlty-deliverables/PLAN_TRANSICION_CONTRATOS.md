# PLAN_TRANSICION_CONTRATOS.md

## Objetivo
Aplicar transición segura e incremental hacia contrato mínimo canónico, sin romper pantallas útiles ni refactorizar todo el backend.

## Estrategia elegida
**Combinación mínima más segura:**
1. Adaptación central en cliente HTTP frontend (`api.ts`) para errores heterogéneos.
2. Mantener wrappers/transforms en servicios para endpoints legacy.
3. Cambios de backend solo cuando exista rotura concreta o endpoint nuevo.

---

## Fase T0 (ejecutada en este paso)

### Acción
- Mejorar parser central de errores para soportar, en orden:
  - `error.mensaje`
  - `error.message`
  - `error.detail`
  - `detail`
  - `mensaje`
  - `message`

### Resultado esperado
- No perder mensajes útiles de backend aunque cambie formato.
- Reducir errores genéricos en UI.

---

## Fase T1 (siguiente incremental)

1. Priorizar rutas de uso frecuente y alto impacto (bitácora, análisis, fútbol apuestas/partidos).
2. En cada servicio frontend crítico, normalizar payload a shape estable de consumo de UI.
3. Documentar cada endpoint migrado en la matriz.

No hacer en T1:
- no migrar todos los endpoints de golpe,
- no rediseñar toda la semántica API.

---

## Fase T2 (cierre mínimo de bloque 05)

1. Definir subconjunto “canónico mínimo” de endpoints clave con envelope estable.
2. Mantener compatibilidad legacy en cliente hasta que esos endpoints se estabilicen.
3. Dejar checklist de deprecación para fase posterior (fuera bloque 05).

---

## Riesgos y mitigación

### Riesgo: ruptura silenciosa por cambio backend
- Mitigación: parser central tolerante + matriz de contratos viva.

### Riesgo: deuda acumulada por convivencias largas
- Mitigación: marcar explícitamente canónico vs legacy y fecha objetivo de retiro.

### Riesgo: parcheo distribuido en muchos componentes
- Mitigación: centralizar en `frontend/src/servicios/api.ts` y servicios.

---

## Verificación mínima

1. Build frontend exitoso.
2. Smoke de rutas críticas en uso normal.
3. Confirmar que errores con `detail` y `message/mensaje` se muestran correctamente.

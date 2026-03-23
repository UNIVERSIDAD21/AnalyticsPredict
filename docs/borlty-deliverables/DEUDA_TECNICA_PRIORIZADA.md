# DEUDA_TECNICA_PRIORIZADA.md

## Metodología de priorización

Se clasifica por severidad considerando triple impacto:
- **Impacto técnico** (estabilidad, mantenibilidad, defectos)
- **Impacto analítico** (calidad de métricas, trazabilidad, confianza estadística)
- **Impacto negocio** (credibilidad, decisiones, riesgo económico)

---

## Deuda crítica

## 1) Baselines estratégicos sin validación actual en BD
- **Descripción:** métricas clave (81.48% win rate, 11.53% ROI, confidence paradox, odds>2.0, quarter>full-game) no están cerradas con evidencia actualizada en esta fase.
- **Impacto técnico:** medio (no rompe app, pero bloquea priorización correcta).
- **Impacto analítico:** **muy alto** (riesgo de decisiones sobre supuestos viejos).
- **Impacto negocio:** **muy alto** (stake/riesgo/credibilidad).
- **Prioridad:** P0 inmediata.

## 2) Endpoint consumido por frontend inexistente en backend
- **Descripción:** `/api/futbol/apuestas/estadisticas` consumido por FE sin ruta BE detectada.
- **Impacto técnico:** **alto** (errores runtime y flujo roto).
- **Impacto analítico:** medio (pérdida de visibilidad de estadísticas).
- **Impacto negocio:** **alto** (confianza de usuario en módulo fútbol).
- **Prioridad:** P0 inmediata.

## 3) Drift de esquema con compatibilidad forzada
- **Descripción:** lógica dinámica para resolver columnas en `apuestas_futbol` (estado/status, cuota/odds/cuota_decimal, etc.).
- **Impacto técnico:** **alto** (complejidad, bugs difíciles de detectar).
- **Impacto analítico:** **alto** (métricas pueden no ser consistentes si columna efectiva varía).
- **Impacto negocio:** alto (reportes y decisiones potencialmente inestables).
- **Prioridad:** P0 inmediata.

---

## Deuda alta

## 4) Contratos de éxito/error heterogéneos
- **Descripción:** mezcla de respuestas con `exito` y respuestas directas; errores `detail` vs envelopes custom.
- **Impacto técnico:** alto (duplicidad de parseo/handling).
- **Impacto analítico:** medio (trazabilidad de fallos fragmentada).
- **Impacto negocio:** medio-alto (UX inconsistente).
- **Prioridad:** P1.

## 5) Frontend con parsing de error incompleto
- **Descripción:** cliente prioriza `error.mensaje`; backend frecuentemente emite `detail`/`message`.
- **Impacto técnico:** medio.
- **Impacto analítico:** bajo-medio.
- **Impacto negocio:** alto en soporte/diagnóstico UX.
- **Prioridad:** P1.

## 6) Elementos mock/parciales en UI de fútbol
- **Descripción:** serie temporal mock en dashboard y TODO de edición en bitácora fútbol.
- **Impacto técnico:** medio.
- **Impacto analítico:** medio (puede sugerir una realidad no validada).
- **Impacto negocio:** medio-alto (credibilidad de módulo).
- **Prioridad:** P1.

---

## Deuda media

## 7) Naming semántico no totalmente unificado (snake/camel, variantes de confianza)
- **Descripción:** transformaciones manuales frecuentes y variaciones de vocabulario por dominio.
- **Impacto técnico:** medio.
- **Impacto analítico:** medio.
- **Impacto negocio:** medio.
- **Prioridad:** P2.

## 8) Alta dependencia de SQL inline en rutas
- **Descripción:** mucha lógica SQL embebida en handlers API.
- **Impacto técnico:** medio (mantenibilidad, testabilidad).
- **Impacto analítico:** bajo-medio.
- **Impacto negocio:** bajo-medio.
- **Prioridad:** P2.

## 9) Evidencia de pruebas no ejecutada en esta auditoría
- **Descripción:** entorno sin `pytest` impidió validar smoke tests declarados en README.
- **Impacto técnico:** medio.
- **Impacto analítico:** medio.
- **Impacto negocio:** medio.
- **Prioridad:** P2.

---

## Qué debe resolverse primero y por qué

## Top 5 inmediato (orden recomendado)

1. **Validación cuantitativa de baselines sobre BD real**
   - Sin esto, cualquier priorización de modelo/stake puede ser incorrecta.

2. **Cerrar inconsistencia endpoint fútbol (`/estadisticas`)**
   - Es una rotura concreta de contrato con impacto directo de producto.

3. **Definir esquema canónico y plan anti-drift para apuestas_futbol**
   - Reduce complejidad oculta y estabiliza métricas.

4. **Unificar contrato API (éxito/error) + parser frontend**
   - Baja costo de mantenimiento y mejora UX/diagnóstico.

5. **Eliminar/etiquetar claramente elementos mock en dashboard fútbol**
   - Evita interpretar datos sintéticos como desempeño real.

---

## Conclusión ejecutiva

La deuda más costosa hoy no es “falta de features”, sino **falta de cierre de verdad operativa y contractual**:
- validar métricas clave,
- asegurar que frontend y backend hablen el mismo idioma,
- y fijar un esquema canónico confiable.

Eso desbloquea evolución segura a siguientes fases (capa analítica, explicabilidad y gobierno de modelos).

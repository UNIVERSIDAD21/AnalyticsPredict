# PLAN_DE_ESTABILIZACION_CRITICA.md

## 1) Resumen ejecutivo del estado actual del bloque 05

El bloque 05 (estabilización crítica) ya tiene evidencia suficiente para definir ejecución controlada, pero aún no está cerrado.

Estado por prioridad:
- **P1 Confidence / calibration bug:** **PARCIAL** (diagnóstico avanzado, sin remediación cerrada).
- **P2 Odds > 2.0:** **PARCIAL** (hallazgo confirmado en muestra corta, matizado en histórico ampliado).
- **P3 Contratos backend/frontend:** **PARCIAL-ALTO** (se cerró una inconsistencia puntual; falta estandarización mínima de errores/convenciones).
- **P4 Drift de esquema:** **ABIERTO** (sigue compatibilidad forzada en runtime).

Conclusión ejecutiva: el bloque debe ejecutarse en secuencia de riesgo, priorizando confiabilidad operativa sobre cambios estructurales.

---

## 2) Qué ya quedó resuelto en fases anteriores

### Resuelto
1. **Validación cuantitativa inicial de baselines en BD real** (`apuestas`) con queries reproducibles.
2. **Análisis de segmentos NBA** (quarter, odds, confidence, líneas) con evidencia tabular.
3. **Análisis histórico ampliado** con dataset deduplicado desde `predicciones_registradas` y comparación corto vs completo.
4. **Contrato roto puntual `/api/futbol/apuestas/estadisticas`**: corregido en frontend para usar endpoint canónico `/api/futbol/apuestas`.

### Parcialmente resuelto
- Baseline “odds > 2.0” pasó de regla absoluta a regla condicionada por contexto (global vs full-game), pero aún no hay política operativa formal cerrada.

---

## 3) Qué sigue abierto realmente dentro del bloque 05

1. Cerrar diagnóstico técnico final de confidence/calibration con criterio operativo accionable.
2. Convertir hallazgos de odds en regla formal de operación (no inferencial).
3. Cerrar deuda contractual remanente mínima (errores y semántica entre capas, sin unificación total de bloque 06).
4. Identificar y congelar esquema canónico para zonas con drift (especialmente apuestas fútbol).

---

## 4) Desglose por las 4 prioridades críticas

## 4.1 Prioridad crítica 1 — Confidence / Calibration bug

### Problema exacto
La confianza/probabilidad no mantiene relación estable entre probabilidad predicha, hit rate y ROI en todos los segmentos.

### Evidencia ya existente
- `ANALISIS_SEGMENTOS_NBA.md`
- `ANALISIS_HISTORICO_COMPLETO_NBA.md`
- Buckets muestran:
  - 0.80+ con ROI positivo pero sobreconfianza relativa (`hit_rate < prob_media`).
  - 0.60–0.69 con hit rate razonable y ROI negativo.

### Hipótesis vigentes
- Umbrales de confianza no monotónicos en valor económico.
- Impacto de pricing/odds y selección de líneas rompe relación “acierto alto = ROI alto”.
- Posible mezcla de señales calibradas y no calibradas según flujo.

### Riesgo
- Técnico: **alto**
- Analítico: **muy alto**
- Negocio: **muy alto** (stake sizing y credibilidad)

### Módulos potencialmente impactados
- `backend/motor/*`
- `backend/motor_autoentrenamiento/*`
- `backend/api/rutas_analisis.py`
- `backend/api/rutas_metricas.py`
- tablas: `predicciones_registradas`, `metricas_calibracion`, `calibradores`

### Criterio de cierre
- Definir y validar monotonicidad mínima por buckets (probabilidad→hit rate→ROI esperado) en dataset ampliado.
- Documento de decisión: cuándo usar confidence para sizing y cuándo degradar su peso.

### Qué NO debe tocarse todavía
- No rediseñar modelo/base de features.
- No refactor estructural de motor ni pipeline.

---

## 4.2 Prioridad crítica 2 — Odds > 2.0

### Problema exacto
El efecto de odds altas no es uniforme: en muestra corta fue muy negativo; en histórico ampliado global no siempre negativo, pero en full-game >=2.0 sí aparece deterioro.

### Evidencia ya existente
- `VALIDACION_CUANTITATIVA_BASELINES_NBA.md`
- `ANALISIS_SEGMENTOS_NBA.md`
- `ANALISIS_HISTORICO_COMPLETO_NBA.md`

### Hipótesis vigentes
- Diferencia entre picks ejecutados (`apuestas`) y universo de predicciones (`predicciones_registradas`) altera señal.
- El edge depende de **mercado + línea + odds** (no solo odds aisladas).

### Riesgo
- Técnico: **medio**
- Analítico: **alto**
- Negocio: **muy alto**

### Módulos potencialmente impactados
- `backend/api/rutas_analisis.py`
- `backend/motor/*`
- `backend/servicios/apuestas_analizadas.py`
- tablas: `apuestas`, `predicciones_registradas`

### Criterio de cierre
- Política formal documentada por buckets (global y full-game) con mínimo de muestra.
- Regla explícita de bloqueo/restricción y condiciones de revisión.

### Qué NO debe tocarse todavía
- No cambiar calibrador ni estrategia de entrenamiento.
- No hardcodear reglas en múltiples capas sin decisión única documentada.

---

## 4.3 Prioridad crítica 3 — Contratos backend/frontend

### Problema exacto
Persisten diferencias de convención en payloads/error/naming, aunque la rotura puntual de `/api/futbol/apuestas/estadisticas` ya fue cerrada.

### Evidencia ya existente
- `AUDITORIA_TECNICA_Y_ANALITICA.md`
- `MAPA_DE_ENDPOINTS_Y_CONTRATOS.md`
- `DECISION_CONTRATO_APUESTAS_ESTADISTICAS.md`

### Hipótesis vigentes
- El sistema opera con “compatibilidad pragmática” y transformadores ad-hoc.
- Hay riesgo de inconsistencias silenciosas en errores (`detail/message/mensaje`).

### Riesgo
- Técnico: **alto**
- Analítico: **medio**
- Negocio: **alto** (fallos UX y diagnósticos ambiguos)

### Módulos potencialmente impactados
- `frontend/src/servicios/api.ts`
- `frontend/src/servicios/**/*.ts`
- `backend/api/rutas*.py`

### Criterio de cierre
- Matriz endpoint↔consumo actualizada sin rutas huérfanas.
- Convención mínima de error parseable en frontend para endpoints críticos del bloque 05.

### Qué NO debe tocarse todavía
- No iniciar unificación completa de contratos (eso pertenece al bloque 06).
- No rediseñar toda la semántica API.

---

## 4.4 Prioridad crítica 4 — Drift de esquema

### Problema exacto
Hay resolución dinámica de columnas legacy/variantes en runtime (ej. `estado|status`, `cuota|odds|cuota_decimal`) que confirma drift activo.

### Evidencia ya existente
- `AUDITORIA_TECNICA_Y_ANALITICA.md`
- `DEUDA_TECNICA_PRIORIZADA.md`
- código en `backend/api/rutas_apuestas_futbol.py`

### Hipótesis vigentes
- Coexisten versiones históricas de esquema sin plan de retiro formal.
- La compatibilidad defensiva está ocultando deuda operativa.

### Riesgo
- Técnico: **muy alto**
- Analítico: **alto**
- Negocio: **alto**

### Módulos potencialmente impactados
- `backend/api/rutas_apuestas_futbol.py`
- scripts SQL/migraciones en `backend/scripts/sql/*`
- tablas fútbol: `apuestas_futbol` y relacionadas

### Criterio de cierre
- Inventario canónico de columnas activas vs legacy.
- Definición de esquema vigente + deprecaciones explícitas.
- Eliminación de al menos una capa de fallback crítico en runtime (sin romper operación).

### Qué NO debe tocarse todavía
- No hacer migración masiva de todas las tablas del dominio.
- No mezclar con rediseño semántico de KPIs (bloque 06).

---

## 5) Orden propuesto de ejecución y justificación

## Orden recomendado
1. **Confidence / calibration bug (P1)**
2. **Odds > 2.0 y policy por buckets (P2)**
3. **Drift de esquema (P4)**
4. **Contratos mínimos remanentes (P3)**

### Justificación
- P1/P2 impactan directamente dinero, stake y credibilidad analítica.
- P4 puede invalidar métricas si no se fija canónico.
- P3 restante puede cerrarse con cambios mínimos una vez estabilizada la verdad operativa de datos.

---

## 6) Riesgos de mezclar tareas o refactorizar de más

1. Diluir causalidad (no saber si mejora vino por calibración, odds o schema).
2. Introducir regresiones mientras aún no hay política cerrada.
3. Consumir capacidad en cambios estructurales sin cerrar riesgos de negocio inmediatos.
4. Terminar parcialmente varias líneas sin cerrar ninguna prioridad crítica.

---

## 7) Recomendación explícita sobre estrategia de ejecución

### Recomendación
**Resolver una por una**, con una pareja mínima controlada solo en:
- **Confidence + Odds** (porque comparten impacto directo en ROI y stake),

pero sin mezclar aún con:
- formalización de capa analítica (bloque 06),
- refactor de arquitectura,
- unificación completa de contratos.

---

## 8) Estado consolidado (resuelto / parcial / abierto)

| Prioridad | Estado |
|---|---|
| Confidence / calibration bug | PARCIAL |
| Odds > 2.0 policy | PARCIAL |
| Contratos backend/frontend | PARCIAL (rotura puntual ya resuelta) |
| Drift de esquema | ABIERTO |

---

## 9) Próximo paso inmediato del bloque 05

Ejecutar subfase P1+P2 con salida documental obligatoria:
- decisión de policy operativa temporal por mercado/odds/confianza,
- umbrales mínimos de muestra,
- y criterio de rollback de policy si nuevos datos contradicen señal.

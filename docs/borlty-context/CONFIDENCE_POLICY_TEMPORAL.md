# CONFIDENCE_POLICY_TEMPORAL.md

## Contexto
Documento de política temporal para Prioridad Crítica 1 (confidence/calibration) del bloque 05.

Basado en:
- `DIAGNOSTICO_CONFIDENCE_CALIBRATION.md`
- evidencia SQL/JSON reproducible del diagnóstico.

## Objetivo
Reducir riesgo operativo mientras se termina la corrección de confidence sin tocar aún modelo completo.

---

## Política temporal (vigente hasta nuevo aviso)

## 1) Uso de confidence para stake
- **No usar ALTA/MEDIA/BAJA como multiplicador primario de stake**.
- El sizing debe priorizar edge/probabilidad/odds y controles de riesgo existentes.
- Confidence puede mantenerse como variable explicativa secundaria.

## 2) Uso de confidence para priorización de picks
- Permitido como filtro blando solo cuando hay consistencia por mercado.
- No usar confidence como criterio único de inclusión/exclusión en Q2/Q3/Q4.

## 3) Monitoreo mínimo obligatorio
En cada corte operativo:
- hit rate y ROI por confidence global,
- hit rate y ROI por confidence *por mercado* (COMPLETO, Q1, Q2, Q3, Q4),
- diferencia `prob_media - hit_rate` por buckets de probabilidad.

## 4) Criterios para levantar política temporal
La política temporal podrá retirarse cuando se cumpla:
1. Thresholds revisados por mercado.
2. Monotonicidad validada en al menos 2 cortes consecutivos:
   - ALTA >= MEDIA >= BAJA en hit/ROI por mercado principal.
3. Documentación de regresión con tests y consultas reproducibles.

---

## Qué no se hace todavía
- No rediseño completo del modelo.
- No refactor de arquitectura.
- No salto al bloque 06 (formalización de capa analítica).

---

## Riesgos de no aplicar esta política
1. Sobreconfiar en ALTA/MEDIA/BAJA como si fuese estable en todos los mercados.
2. Sobreajustar stake por una señal que no está cerrada por submercado.
3. Aumentar variabilidad de resultados y degradar credibilidad operativa.

---

## Decisión operativa actual
**Mantener confidence en modo “diagnostic/explainability-first” y no “stake-first” hasta cierre de recalibración por mercado.**

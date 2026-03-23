# MIGRACION_DOCUMENTAL_RESUMEN

## Objetivo
Separar documentación activa, entregables y archivo histórico para evitar contexto ambiguo y mejorar gobierno documental.

## Qué se movió

### A `docs/borlty-deliverables/`
- Entregables técnicos, auditorías, reportes, checklists, cierres de bloque y evidencia de validación.
- Se movieron subcarpetas completas:
  - `docs/reportes/` -> `docs/borlty-deliverables/reportes/`
  - `docs/bloque_08/` -> `docs/borlty-deliverables/bloque_08/`
  - `docs/bloque_09/` -> `docs/borlty-deliverables/bloque_09/`
  - `docs/checklists/` -> `docs/borlty-deliverables/checklists/`
- Se movió la mayoría de archivos de `docs/borlty-context/` que eran evidencia histórica o entregables cerrados.

### A `docs/archive/`
- Archivo histórico reemplazado por nueva gobernanza:
  - `ARQUITECTURA_OPERATIVA_FINAL.md`

## Qué quedó como activo

### Contexto activo (`docs/borlty-context/`)
- `00_INDICE_GENERAL.md`
- `01_QUICK_START_BORLTY.md`
- `02_CONTEXTO_ESTRATEGICO_Y_OBJETIVO.md`
- `03_ESTADO_ACTUAL_Y_BASELINES.md`
- `10_REGLAS_ENTREGABLES_Y_CRITERIOS.md`

### Arquitectura vigente (`docs/arquitectura/`)
- `ESTADO_PROYECTO.md`
- `PLAN_EJECUCION_BLOQUES_V3.md`
- ADRs (`ADR-001..004`)

### Fuente principal nueva
- `docs/FUENTE_DE_VERDAD_ACTUAL.md`

## Qué se eliminó
- No se hizo eliminación masiva.
- Se priorizó preservación de evidencia y trazabilidad.

## Criterio aplicado
- Activo: lo que hoy gobierna decisiones.
- Deliverable: evidencia/resultado de trabajo cerrado o de soporte.
- Archive: documentos reemplazados u obsoletos para operación actual.

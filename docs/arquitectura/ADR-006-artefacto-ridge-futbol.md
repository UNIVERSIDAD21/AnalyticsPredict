# ADR-006 — Artefacto Ridge fútbol autocontenido y recarga sin entrenamiento

- Estado: **ACEPTADO**
- Fecha: 2026-10-15
- Alcance: herramienta personal single-user; no modifica promoción beta.

## Contexto

El gestor legacy no correspondía al esquema de PostgreSQL y guardaba métricas sin
coeficientes. El predictor por defecto inicializaba modelos vacíos; el estado API
podía inventar modelos y fechas. Nuevos FT no completan targets por tiempos.

## Decisión

Usar metadata JSONB ya existente para un artefacto JSON versionado, SHA-256 y dataset
efectivo por familia. `mercado_principal` etiqueta la familia sin fingir que FT es
su único target. Publicación en lote atómica, activación explícita validada antes
de desactivar, recarga read-only sobre un snapshot SQL; nunca entrenar en serving.
Coeficientes completos y contrato de features/targets obligatorios, NPZ sin pickle,
NULL no imputado y métricas in-sample diferenciadas de validación temporal.

## Consecuencias

Sin DDL ni dependencia de rutas locales de BD. Legacy incompleto deja de ser apto
para serving. Un hash no prueba causalidad/disponibilidad histórica y una activación
no certifica eficacia: evaluación temporal/calibración por versión siguen pendientes.
Detalle y evidencia: `../reactivacion_single_user/PERSISTENCIA_ML_FUTBOL_2026-10-15.md`.

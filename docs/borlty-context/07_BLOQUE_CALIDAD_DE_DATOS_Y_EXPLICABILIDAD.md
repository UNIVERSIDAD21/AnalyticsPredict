# Bloque de Actividad — Calidad de Datos y Explicabilidad

## Propósito del bloque

Aumentar la confiabilidad del sistema y hacer que las predicciones sean defendibles.

## Parte 1 — Calidad de datos

### Problema actual
La validación existe, pero de forma dispersa y no como framework formal.

### Objetivos
- detectar datos incompletos
- detectar inconsistencias
- detectar outliers
- medir freshness
- medir cobertura
- alertar cuando la calidad baja

### Actividades
- definir reglas de validación por deporte
- definir validaciones por tipo de partido y mercado
- revisar null handling
- revisar integridad lógica entre tablas
- revisar integridad temporal
- construir scorecard de calidad
- documentar thresholds de alerta

### Entregables
- `DATA_QUALITY_RULES.md`
- `SCORECARD_CALIDAD_DE_DATOS.md`
- `ALERTAS_DE_CALIDAD.md`

## Parte 2 — Explicabilidad

### Problema actual
El sistema predice, pero todavía explica poco.

### Objetivos
- mostrar por qué se recomienda una apuesta
- mostrar qué factores pesaron más
- mostrar qué tan confiable es
- mostrar comparación con juegos similares
- mostrar impacto del calibrador y del confidence

### Actividades
- definir feature importance por modelo
- definir explicación mínima por predicción
- definir campos visibles en frontend
- diseñar vista de explicación
- documentar confidence breakdown
- documentar qué significa realmente cada nivel de confianza

### Entregables
- `EXPLICABILIDAD_DEL_SISTEMA.md`
- `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md`
- `UI_EXPLICABILIDAD_PROPUESTA.md`

## Resultado esperado

El sistema deja de ser caja negra y gana valor técnico, comercial y académico.

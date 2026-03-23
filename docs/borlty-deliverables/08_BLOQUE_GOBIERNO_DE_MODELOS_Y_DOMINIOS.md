# Bloque de Actividad — Gobierno de Modelos y Separación de Dominios

## Parte 1 — Gobierno de modelos

### Problema actual
Los modelos existen, pero todavía no hay un proceso completamente formal para:

- compararlos
- promoverlos
- rechazarlos
- versionarlos con criterios consistentes

### Objetivos
- registrar modelos
- comparar contra baseline
- definir promotion criteria
- dejar trazabilidad de experimentos
- evitar regresiones silenciosas

### Actividades
- documentar modelo actual NBA
- documentar pipeline actual Football
- definir baseline models
- definir métricas mínimas para promoción
- definir criterios de rollback
- mapear features por versión
- mapear datasets por versión

### Entregables
- `GOBIERNO_DE_MODELOS.md`
- `BASELINES_Y_BENCHMARKS.md`
- `CRITERIOS_DE_PROMOCION_Y_ROLLBACK.md`

## Parte 2 — Separación de dominios

### Problema actual
NBA y Football comparten demasiado espacio lógico.

### Objetivos
- separar lo compartido de lo específico
- reducir acoplamiento
- hacer el sistema más escalable
- permitir evolución independiente por dominio

### Actividades
- identificar módulos core
- identificar módulos NBA-only
- identificar módulos Football-only
- proponer estructura modular
- reorganizar rutas y servicios
- revisar si conviene separar esquemas o no
- revisar frontend por dominios

### Entregables
- `ARQUITECTURA_POR_DOMINIOS.md`
- `PLAN_DE_SEPARACION_NBA_FOOTBALL.md`

## Resultado esperado

El sistema podrá crecer sin que cada cambio mezcle innecesariamente ambos deportes.

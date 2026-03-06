# Bloque de Actividad — Estabilización Crítica

## Propósito del bloque

Corregir primero lo que compromete:

- dinero
- credibilidad
- stake sizing
- confianza del usuario
- consistencia básica del sistema

## Prioridad crítica 1 — Confidence / Calibration bug

### Problema observado
El sistema reporta que HIGH confidence rinde peor que MEDIUM/LOW.

### Hipótesis posibles
- fórmula invertida
- thresholds incorrectos
- confidence no alineado con outcomes
- error de normalización
- feature combination mal ponderada

### Actividades
- localizar cálculo exacto de confidence
- reconstruir cómo se asigna HIGH / MEDIUM / LOW
- cruzar confidence vs win rate real
- cruzar confidence vs ROI real
- revisar si stake depende de confidence
- rediseñar thresholds
- validar monotonicidad
- dejar tests de regresión

### Resultado esperado
HIGH confidence debe tener mejor desempeño real que niveles inferiores o, si no, el sistema debe dejar de usar confidence para stake hasta corregirse.

## Prioridad crítica 2 — Problema en odds > 2.0

### Problema observado
Las apuestas con odds altas reportan ROI muy negativo.

### Actividades
- segmentar por rangos de odds
- medir win rate y ROI por rango
- revisar si el modelo sobreestima underdogs
- revisar edge por rango de odds
- revisar si el juice empeora el escenario
- definir si la regla actual se mantiene, se endurece o se refina

### Resultado esperado
Regla formal documentada sobre uso o exclusión de odds altas.

## Prioridad crítica 3 — Contratos backend/frontend

### Problema observado
El backend y el frontend no siempre hablan el mismo idioma.

### Actividades
- unificar respuestas de éxito
- unificar respuestas de error
- alinear tipos TS con payloads reales
- normalizar naming
- revisar formatos de fechas y números

### Resultado esperado
Una sola convención de API.

## Prioridad crítica 4 — Drift de esquema

### Problema observado
Hay señales de compatibilidad forzada y columnas legacy.

### Actividades
- identificar columnas activas
- identificar columnas obsoletas
- identificar código defensivo por drift
- definir esquema canónico
- documentar qué queda vigente y qué queda deprecated

### Resultado esperado
Backend y BD dejan de depender de adivinanzas estructurales.

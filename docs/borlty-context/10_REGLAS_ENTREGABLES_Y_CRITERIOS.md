# Reglas, Entregables y Criterios de Éxito

## Reglas de trabajo para Borlty

### 1. Entender antes de tocar
No hacer refactors grandes sin mapa previo.

### 2. No programar por intuición
Cada cambio importante debe justificarse con auditoría, evidencia o impacto medible.

### 3. No mezclar demasiadas cosas a la vez
Separar por bloques:
- auditoría
- estabilización crítica
- capa analítica
- calidad y explicabilidad
- gobierno de modelos
- expansiones futuras

### 4. No ocultar deuda técnica
Toda inconsistencia relevante debe quedar documentada.

### 5. No presentar como resuelto algo que sigue activo
Si un bug fue parcialmente tocado pero persiste, debe documentarse como pendiente.

### 6. No romper funcionalidad actual útil
El sistema ya genera valor; consolidar primero, destruir nunca.

### 7. Pensar como plataforma
No pensar por archivos aislados ni por parches sueltos.

## Entregables mínimos

1. `AUDITORIA_TECNICA_Y_ANALITICA.md`
2. `MAPA_DE_ENDPOINTS_Y_CONTRATOS.md`
3. `CATALOGO_DE_KPIS_Y_METRICAS.md`
4. `PLAN_DE_ESTABILIZACION_CRITICA.md`
5. `DATA_QUALITY_RULES.md`
6. `EXPLICABILIDAD_DEL_SISTEMA.md`
7. `GOBIERNO_DE_MODELOS.md`
8. `ARQUITECTURA_POR_DOMINIOS.md`
9. `ROADMAP_DE_EXPANSIONES_FUTURAS.md`

## Criterios de éxito

Esta fase será exitosa cuando:

- los baselines estén validados
- confidence bug esté diagnosticado con precisión
- problema de odds > 2.0 tenga regla formal respaldada por datos
- backend, frontend y BD hablen el mismo idioma
- exista un catálogo formal de KPIs
- calidad de datos tenga framework y scorecard
- las predicciones ganen explicabilidad
- NBA y Football tengan mejor separación conceptual
- el sistema pueda presentarse con fuerza como plataforma de análisis de datos

# Bloque de Actividad — Capa Analítica y KPIs

## Propósito del bloque

Convertir métricas dispersas en una capa analítica formal, consistente y reusable.

## Problema actual

El sistema ya calcula métricas, pero todavía no tiene:

- catálogo oficial de KPIs
- definiciones únicas
- semántica estable
- vistas analíticas canónicas
- una sola fuente de verdad para análisis

## Objetivos del bloque

1. Formalizar la capa analítica
2. Definir KPIs oficiales
3. Normalizar métricas
4. Crear vistas canónicas
5. Preparar base para dashboards, reportes y chatbot futuro

## Actividades

### A. Definir KPIs de negocio
- win rate
- ROI
- profit
- total bets
- average stake

### B. Definir KPIs predictivos
- accuracy
- brier score
- log loss
- calibration error
- sharpness
- expected value

### C. Definir KPIs operativos
- edge
- devig impact
- stake sizing consistency
- porcentaje de apuestas por confidence
- distribución por rango de odds

### D. Definir KPIs de calidad de datos
- completeness
- freshness
- outlier rate
- source uptime
- coverage

### E. Definir dimensiones analíticas
- sport
- market type
- quarter
- odds range
- confidence level
- period
- team
- model version

### F. Crear catálogo de métricas
Cada métrica debe tener:
- nombre
- definición
- fórmula
- fuente
- granularidad
- frecuencia de cálculo
- dependencia técnica

### G. Crear vistas analíticas canónicas
Ejemplos:
- performance por market type
- performance por confidence
- performance por odds range
- calibration por modelo
- scorecard de calidad de datos
- comparativo NBA vs Football

## Entregables
- `CATALOGO_DE_KPIS_Y_METRICAS.md`
- `VISTAS_ANALITICAS_CANONICAS.md`
- `MAPA_SEMANTICO_DEL_SISTEMA.md`

## Resultado esperado

El sistema deja de tener métricas “sueltas” y pasa a tener una capa analítica formal.

# Estado Actual y Baselines Operativos

## Importante

Los datos de este archivo son baseline operativo inicial.
Deben validarse contra BD, código y dashboards actuales durante la auditoría.

## Estado general

El proyecto presenta una madurez asimétrica:

- NBA: dominio más operativo y rentable
- Football: dominio en desarrollo parcial

## Baselines NBA reportados

### Métricas operativas reportadas
- Win rate: 81.48%
- ROI: 11.53%
- Apuestas resueltas: 81
- Sistema con operación real sobre NBA

### Hallazgos críticos ya observados
- HIGH confidence presenta ROI peor que MEDIUM/LOW
- Odds > 2.0 presentan ROI fuertemente negativo
- Quarter-specific markets rinden mejor que full-game markets

### Reglas operativas actualmente aprendidas
- evitar odds > 2.0 hasta nueva validación
- priorizar quarter markets
- stake conservador de 2-3% por apuesta
- mantener walk-forward backtesting para evitar leakage

## Problemas técnicos NBA ya aprendidos
- timezone misalignment fue un problema real
- duplicate game entries fue un problema real
- confidence scoring fue ajustado anteriormente, pero debe verificarse si el problema de fondo persiste

## Estado Football reportado

### Estado de madurez reportado
- fase parcial de desarrollo
- integración con Sofascore ya iniciada
- scraping funcional en parte
- modelos todavía no equivalentes al nivel NBA
- frontend football aún incompleto

### Baselines Football reportados
- roadmap total de 6 fases
- 49 tareas estimadas
- ligas ya identificadas
- soporte objetivo para goals, corners y shots

## Stack técnico reportado

### Backend
- FastAPI
- psycopg / psycopg_pool
- PostgreSQL en Neon
- lógica de scraping
- lógica de análisis y métricas

### Frontend
- React
- TypeScript
- Tailwind
- componentes, hooks, services, types, pages y contexts

### Fuentes de datos reportadas
- NBA: ESPN API
- Football: Sofascore API

## Instrucción para Borlty

Validar uno por uno estos baselines.
No asumir que todo sigue vigente sin comprobación.

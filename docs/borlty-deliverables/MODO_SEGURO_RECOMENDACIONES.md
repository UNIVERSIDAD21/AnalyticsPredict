# Modo Seguro de Recomendaciones

## Qué se aplicó

### Fútbol
- Mercados en **rojo** (Brier >= 0.28 con muestra >= 100): bloqueados.
- Mercados en **amarillo** (Brier >= 0.24): solo se permiten recomendaciones con probabilidad >= 0.60.

### NBA
- Mercados en **rojo** (Brier >= 0.28 con muestra >= 100): bloqueados automáticamente en salida.

## Objetivo
Reducir exposición en mercados degradados y mejorar calidad promedio de picks mostrados.

## Revisión
Ajustar umbrales semanalmente con:
- `/api/metricas/calidad-mercados`
- `/api/metricas/politica-mercados`
- `/api/metricas/drift-mercados`

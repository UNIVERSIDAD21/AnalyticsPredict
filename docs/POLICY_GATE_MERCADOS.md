# Policy Gate de Mercados (Enforcement)

## Qué se implementó
Durante el análisis de fútbol, antes de devolver recomendaciones, se aplica una compuerta de calidad:

- Calcula Brier histórico por mercado en `predicciones_futbol`.
- Requiere muestra mínima (`min_muestras=100`).
- Bloquea mercados con Brier >= `0.28`.

## Efecto
- Las recomendaciones de mercados en rojo no se devuelven al usuario.
- Reduce riesgo de sugerir picks en mercados degradados.

## Parámetros actuales
- `min_muestras`: 100
- `umbral_brier`: 0.28

## Recomendación
Revisar semanalmente estos umbrales usando:
- `GET /api/metricas/politica-mercados`
- `GET /api/metricas/calidad-mercados`
- `GET /api/metricas/drift-mercados`

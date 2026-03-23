# DECISION_CONTRATO_APUESTAS_ESTADISTICAS.md

## Problema
El frontend invocaba `GET /api/futbol/apuestas/estadisticas`, pero el backend no expone ese endpoint.

## Opciones evaluadas

1. **Crear endpoint nuevo en backend** `/api/futbol/apuestas/estadisticas`.
2. **Corregir consumo en frontend** para usar endpoint ya canónico: `GET /api/futbol/apuestas` y leer `resumen`.

## Evidencia técnica
- Backend actual (`rutas_apuestas_futbol.py`) ya implementa `GET /api/futbol/apuestas` con:
  - filtros por estado/mercado/fecha,
  - lista de apuestas,
  - objeto `resumen` con métricas agregadas (total, pendientes, ganadas, perdidas, push, roi, win_rate, stake_total, ganancia_neta).
- No existe ruta backend `/api/futbol/apuestas/estadisticas`.

## Decisión
**Solución correcta inmediata:** corregir el consumo en frontend.

### Justificación
- Evita duplicar lógica de agregación en backend.
- Reduce superficie de mantenimiento.
- Cierra el contrato roto con cambio mínimo y sin refactor estructural.
- Mantiene una sola fuente de verdad para resumen de apuestas en fútbol.

## Cambio aplicado
- Archivo: `frontend/src/servicios/futbol/apuestas.ts`
- Función: `obtenerEstadisticas()`
- Antes: llamaba `/api/futbol/apuestas/estadisticas`
- Ahora: llama `/api/futbol/apuestas` y devuelve `transformarResumen(respuesta.data.resumen)`.

## Riesgos residuales
- Si en el futuro se requiere payload estadístico más amplio y distinto al `resumen`, entonces sí podría justificarse endpoint dedicado; por ahora no es necesario.

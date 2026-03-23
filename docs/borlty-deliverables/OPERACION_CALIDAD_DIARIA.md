# Operación diaria de calidad (Profesional)

## Objetivo
Mantener calidad real de predicción con ciclo repetible y evidencia auditable.

## Precondición
Backend levantado en `http://127.0.0.1:8000`.

## Ejecución diaria (1 comando)
Desde root del repo:

```bash
make calidad-ciclo
```

## Qué hace
1. Verifica salud API.
2. Resuelve predicciones pendientes de baloncesto.
3. Resuelve predicciones pendientes de fútbol.
4. Captura tablero de salud multideporte.
5. Captura ranking de calidad por mercado.
6. Guarda todo en `reports/calidad/<timestamp>/`.

## Artefactos generados
- `salud.json`
- `resolver_baloncesto.json`
- `resolver_futbol.json`
- `tablero_salud.json`
- `calidad_mercados.json`

## Endpoints de gestión ejecutiva
- `GET /api/metricas/tablero-salud`
- `GET /api/metricas/calidad-mercados`
- `GET /api/metricas/recomendaciones-accion`

## Umbrales de acción
- `score_global < 70`: acción inmediata (recalibración + revisión de features).
- Cualquier mercado con `Brier > 0.26` y muestra suficiente: priorizar recalibración.
- Pendientes altos por deporte: ejecutar ciclo más frecuente o ampliar límites.

## Modo rápido (diagnóstico)
```bash
make calidad-ciclo-fast
```

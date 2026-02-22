# Alertas de Ingestión Stale

## Endpoint
`GET /api/metricas/alertas-ingestion?max_horas_sin_actualizar=24`

## Qué hace
Evalúa fuentes clave (ingestión y predicciones) y determina si están stale según horas sin actualización.

## Severidades
- `critica`: stale > 2x umbral
- `alta`: stale > umbral
- `media`: cerca del umbral
- `baja`: saludable

## Uso operativo
1. Ejecutar preflight (`make qa-preflight`).
2. Si hay `critica/alta`, revisar pipeline de ingestión antes de confiar en nuevas predicciones.

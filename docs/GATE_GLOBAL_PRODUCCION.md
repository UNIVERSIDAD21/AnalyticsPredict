# Gate Global de Producción (Recomendaciones)

## Qué hace
Evita mostrar recomendaciones cuando la salud operativa no es confiable.

## Criterios
- score global por debajo de umbral.
- semáforo global en rojo.
- fuentes de ingestión críticas stale.
- deporte con volumen alto y cero resueltas.

## Endpoints y enforcement
- `GET /api/metricas/modo-estricto` → decisión global.
- NBA/Fútbol: policy gate aplicado en endpoints de análisis para bloquear mercados rojos.
- Modo seguro: filtros más estrictos en mercados amarillos.

## Comando rápido
```bash
cd /home/borlty/repos/AnalyticsPredict
make check-modo-estricto
```

# GO / NO-GO Operativo

## Fuente de verdad
`GET /api/metricas/modo-estricto`

## Regla
- `habilitar_recomendaciones=true` => **GO**
- `habilitar_recomendaciones=false` => **NO-GO**

## Criterios de NO-GO
- score global por debajo del mínimo.
- semáforo global en rojo.
- fuentes críticas stale de ingestión.
- volumen alto con cero resueltas por deporte.

## Integración
- `scripts/reporte_ejecutivo_calidad.sh` ya incluye estado GO/NO-GO.
- `scripts/reporte_semanal_auto.sh` ya incluye estado GO/NO-GO.

## Comando rápido
```bash
cd /home/borlty/repos/AnalyticsPredict
make check-modo-estricto
```
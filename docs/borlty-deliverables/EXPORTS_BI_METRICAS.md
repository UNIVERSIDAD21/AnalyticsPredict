# Exports BI de métricas

## Objetivo
Exportar datos de calidad a CSV para análisis en Excel, Google Sheets, Power BI o Looker Studio.

## Comando
```bash
cd /home/borlty/repos/AnalyticsPredict
make export-metricas-csv
```

## Salidas
Se generan en `reports/csv/<timestamp>/`:
- `calidad_mercados.csv`
- `drift_mercados.csv`
- `politica_mercados.csv`

## Uso recomendado
1. Cargar CSV a una hoja/BI.
2. Crear dashboard con:
   - top mercados por Brier,
   - drift semanal,
   - mercados bloqueados.
3. Revisar antes de publicar recomendaciones.

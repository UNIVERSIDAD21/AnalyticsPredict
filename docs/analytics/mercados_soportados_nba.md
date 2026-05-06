# Mercados soportados NBA - análisis previo de partido

Este documento describe los mercados que actualmente entiende `backend/scripts/generar_analisis_partido_nba.py`.

## Esquema de markets.json

Cada mercado debe declarar trazabilidad de línea:

```json
{
  "market": "FULL_GAME_TOTAL",
  "line": 218.5,
  "over_odds": 1.91,
  "under_odds": 1.91,
  "source": "ESPN pickcenter / DraftKings close",
  "source_type": "REAL_MARKET",
  "source_url": "https://www.espn.com/nba/game/_/gameId/401871152",
  "notes": "Total de partido publicado por mercado real"
}
```

`source_type` permitido:

- `REAL_MARKET`: línea observada en mercado/casa real.
- `DERIVED_FROM_TOTAL_SPREAD`: línea implícita derivada desde total + spread.
- `TECHNICAL_ESTIMATE`: estimación técnica para simulación; no proviene de mercado real.
- `MANUAL_INPUT`: línea introducida manualmente sin trazabilidad suficiente.

Las líneas que no sean `REAL_MARKET` deben interpretarse con menor peso analítico.

## Mercados soportados actualmente

### Q1_TOTAL
Total combinado del primer cuarto.

### FULL_GAME_TOTAL
Total combinado del partido completo.

### HOME_TEAM_TOTAL
Total esperado/pasado del equipo local para partido completo.

### AWAY_TEAM_TOTAL
Total esperado/pasado del equipo visitante para partido completo.

## Próximos mercados a soportar

- `Q2_TOTAL`
- `Q3_TOTAL`
- `Q4_TOTAL`
- `HALF_1_TOTAL`
- `HALF_2_TOTAL`
- `HOME_Q1_TOTAL`
- `AWAY_Q1_TOTAL`
- `MONEYLINE`
- `SPREAD`

## Regla operativa

El script no debe recomendar apuestas, picks, stakes ni certezas. Solo clasifica señales estadísticas con advertencias de muestra, volatilidad, overtime y trazabilidad de línea.

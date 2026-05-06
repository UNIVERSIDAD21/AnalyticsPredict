# Contrato técnico interno: POST /api/nba/match-analysis

Endpoint técnico interno para generar análisis estadístico previo de partidos NBA.

> Seguridad: endpoint técnico interno; no exponer públicamente sin autenticación/autorización. En producción depende de `obtener_usuario_actual` y exige Bearer token o `X-Usuario-Id`; en desarrollo puede usar fallback de usuario dev por la configuración global del backend.

## Request

```json
{
  "home": "San Antonio Spurs",
  "away": "Minnesota Timberwolves",
  "date": "2026-05-05",
  "markets": [
    {
      "market": "FULL_GAME_TOTAL",
      "line": 218.5,
      "over_odds": 1.91,
      "under_odds": 1.91,
      "source": "ESPN pickcenter / DraftKings close",
      "source_type": "REAL_MARKET",
      "source_url": "https://www.espn.com/nba/game/_/gameId/401871152",
      "notes": null
    }
  ]
}
```

## Validación de markets

Campos obligatorios por mercado:

- `market`
- `line` numérico
- `source`
- `source_type`

`over_odds` y `under_odds` pueden ser `null`; si vienen, deben ser numéricos.

`source_type` permitido:

- `REAL_MARKET`
- `DERIVED_FROM_TOTAL_SPREAD`
- `TECHNICAL_ESTIMATE`
- `MANUAL_INPUT`

`notes` es obligatorio cuando `source_type != REAL_MARKET`.

## Mercados soportados

- `Q1_TOTAL`
- `FULL_GAME_TOTAL`
- `HOME_TEAM_TOTAL`
- `AWAY_TEAM_TOTAL`

## Ejemplos curl

### Request válido con mercado real

```bash
curl -s -X POST http://127.0.0.1:8000/api/nba/match-analysis \
  -H 'Content-Type: application/json' \
  -H 'X-Usuario-Id: 00000000-0000-0000-0000-000000000001' \
  -d '{
    "home":"San Antonio Spurs",
    "away":"Minnesota Timberwolves",
    "date":"2026-05-05",
    "markets":[{
      "market":"FULL_GAME_TOTAL",
      "line":218.5,
      "over_odds":1.91,
      "under_odds":1.91,
      "source":"ESPN pickcenter / DraftKings close",
      "source_type":"REAL_MARKET",
      "source_url":"https://www.espn.com/nba/game/_/gameId/401871152",
      "notes":null
    }]
  }'
```

### Request inválido sin source_type

```bash
curl -s -X POST http://127.0.0.1:8000/api/nba/match-analysis \
  -H 'Content-Type: application/json' \
  -H 'X-Usuario-Id: 00000000-0000-0000-0000-000000000001' \
  -d '{
    "home":"San Antonio Spurs",
    "away":"Minnesota Timberwolves",
    "date":"2026-05-05",
    "markets":[{"market":"FULL_GAME_TOTAL","line":218.5,"source":"ESPN"}]
  }'
```

### Request con línea técnica

```bash
curl -s -X POST http://127.0.0.1:8000/api/nba/match-analysis \
  -H 'Content-Type: application/json' \
  -H 'X-Usuario-Id: 00000000-0000-0000-0000-000000000001' \
  -d '{
    "home":"SAS",
    "away":"MIN",
    "date":"2026-05-05",
    "markets":[{
      "market":"Q1_TOTAL",
      "line":54.5,
      "over_odds":null,
      "under_odds":null,
      "source":"manual/technical",
      "source_type":"TECHNICAL_ESTIMATE",
      "source_url":null,
      "notes":"Línea técnica para validación; no mercado real."
    }]
  }'
```

### Request con team totals derivados

```bash
curl -s -X POST http://127.0.0.1:8000/api/nba/match-analysis \
  -H 'Content-Type: application/json' \
  -H 'X-Usuario-Id: 00000000-0000-0000-0000-000000000001' \
  -d '{
    "home":"SAS",
    "away":"MIN",
    "date":"2026-05-05",
    "markets":[{
      "market":"HOME_TEAM_TOTAL",
      "line":114.5,
      "over_odds":null,
      "under_odds":null,
      "source":"derived from total 218.5 and spread SA -10.5",
      "source_type":"DERIVED_FROM_TOTAL_SPREAD",
      "source_url":"https://www.espn.com/nba/game/_/gameId/401871152",
      "notes":"Team total implícito del local; no línea observada directamente."
    }]
  }'
```

## Response resumida

```json
{
  "ok": true,
  "metadata": {},
  "teams": {},
  "samples": {},
  "combined_metrics": {},
  "market_evaluations": [],
  "data_quality": {},
  "warnings": [],
  "external_summary": "...",
  "generated_files": null,
  "policy": {
    "no_picks": true,
    "no_stake": true,
    "no_betting_recommendations": true
  }
}
```

## Warnings estructurados

```json
{
  "code": "NON_REAL_MARKET_LINE",
  "severity": "WARNING",
  "message": "La línea Q1_TOTAL no proviene de mercado real",
  "scope": "market",
  "market": "Q1_TOTAL",
  "details": {"source_type": "TECHNICAL_ESTIMATE"}
}
```

Campos: `code`, `severity`, `message`, `scope`, `market` opcional, `team` opcional, `details` opcional.

Códigos actuales relevantes:

- `NON_REAL_MARKET_LINE`
- `TECHNICAL_ESTIMATE_ONLY`
- `EXCLUDED_APPEARANCES`
- `HIGH_EXCLUSION_RATE`
- `HIGH_VOLATILITY`
- `RECENT_FULL_SAMPLE_DIVERGENCE`
- `LOW_SAMPLE`
- `OVERTIME_IN_SAMPLE`

## Data quality

Incluye candidatas, usadas, excluidas, porcentaje excluido y detalle por bucket:

- `local_general`
- `visitante_general`
- `local_split`
- `visitante_split`

Categorías de exclusión:

- `FUTURE_OR_NOT_PLAYED`
- `INCOMPLETE_SCORE`
- `INVALID_ZERO_ZERO`
- `MISSING_QUARTERS`
- `TOTAL_MISMATCH`
- `UNKNOWN_EXCLUSION_REASON`

## Clasificación técnica

- señal estadística fuerte
- señal estadística moderada
- señal estadística débil
- señal inconsistente
- no evaluable por datos insuficientes

## Fuera de alcance / restricciones

El endpoint NO hace picks, stake sizing, recomendaciones de apuesta, lenguaje de certeza ni integración frontend.

El endpoint devuelve evidencia estadística y advertencias para análisis interno.

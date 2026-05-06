# Smoke test manual - NBA match analysis

Endpoint: `POST /api/nba/match-analysis`

> Endpoint técnico interno; no exponer públicamente sin autenticación/autorización. En desarrollo puede responder con usuario dev fallback; en producción debe requerir Bearer o `X-Usuario-Id` válido según dependencias globales.

## 1. Levantar backend

```bash
cd backend
../backend/.venv/bin/python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## 2. Validar respuesta 200

```bash
curl -i -X POST http://127.0.0.1:8000/api/nba/match-analysis \
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

Esperado:

- HTTP 200
- `ok: true`
- `policy.no_picks: true`
- `policy.no_stake: true`
- `policy.no_betting_recommendations: true`

## 3. Validar respuesta 422 sin source_type

```bash
curl -i -X POST http://127.0.0.1:8000/api/nba/match-analysis \
  -H 'Content-Type: application/json' \
  -H 'X-Usuario-Id: 00000000-0000-0000-0000-000000000001' \
  -d '{
    "home":"San Antonio Spurs",
    "away":"Minnesota Timberwolves",
    "date":"2026-05-05",
    "markets":[{"market":"FULL_GAME_TOTAL","line":218.5,"source":"ESPN"}]
  }'
```

Esperado: HTTP 422.

## 4. Interpretar warnings

Cada warning debe tener:

- `code`
- `severity`
- `message`
- `scope`

Warnings comunes:

- `NON_REAL_MARKET_LINE`: línea no real.
- `TECHNICAL_ESTIMATE_ONLY`: línea técnica/simulación.
- `EXCLUDED_APPEARANCES`: registros excluidos por calidad de datos.
- `HIGH_VOLATILITY`: desviación estándar alta.
- `RECENT_FULL_SAMPLE_DIVERGENCE`: forma reciente difiere fuerte de muestra completa.

## 5. Confirmar que no genera picks/stakes

Buscar en respuesta:

```json
"policy": {
  "no_picks": true,
  "no_stake": true,
  "no_betting_recommendations": true
}
```

El endpoint solo devuelve evidencia estadística y advertencias; no debe producir picks, stake sizing ni recomendaciones.

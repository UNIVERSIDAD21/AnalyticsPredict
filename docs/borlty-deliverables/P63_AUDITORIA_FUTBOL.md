# P6.3 — Auditoría canónica de decisiones fútbol

## Endpoint nuevo

`GET /api/bitacora/apuestas-analizadas/auditoria-futbol`

Filtros opcionales:
- `mercado`
- `fuente` (`ML|HEURISTICO|ENSEMBLE`)
- `devig_metodo` (`exacto|implied_raw_single_side|fallback_conservador_no_odds`)
- `limite`, `offset`

## Métricas incluidas

- `p_raw` (`decision_p_raw`)
- `p_calibrada` (`decision_p_calibrada`)
- `edge_real` (`decision_edge_real`)
- `score` (`decision_score`)
- `sizing` (`decision_sizing`)
- `valor_esperado` (`decision_valor_esperado`)
- `fuente` (`decision_fuente`)
- `decision_devig_metodo`

## Ejemplo de consulta HTTP

```bash
curl "http://localhost:8000/api/bitacora/apuestas-analizadas/auditoria-futbol?fuente=ENSEMBLE&devig_metodo=exacto&limite=50"
```

## Ejemplo SQL directo (auditoría rápida)

```sql
SELECT
  mercado,
  decision_fuente,
  decision_devig_metodo,
  COUNT(*) AS total,
  AVG(decision_edge_real) AS edge_promedio,
  AVG(decision_score) AS score_promedio,
  AVG(decision_sizing) AS sizing_promedio,
  AVG(decision_valor_esperado) AS ev_promedio
FROM apuestas_analizadas
WHERE deporte='futbol'
GROUP BY 1,2,3
ORDER BY total DESC;
```

## Nota

Esta capa evita depender de parsear `payload_json` para auditoría/base de backtesting.
`payload_json` sigue existiendo como soporte de trazabilidad narrativa, pero la capa analítica principal es estructurada.

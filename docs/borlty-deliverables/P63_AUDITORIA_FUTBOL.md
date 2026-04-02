# P6.3 — Auditoría canónica de decisiones fútbol

## Endpoints

- `GET /api/bitacora/apuestas-analizadas/auditoria-futbol` (v2 canónico)
- `GET /api/bitacora/apuestas-analizadas/auditoria-futbol/legacy` (compatibilidad)
- `POST /api/bitacora/apuestas-analizadas/auditoria-futbol/backfill` (backfill histórico)

Filtros opcionales:
- `mercado`
- `fuente` (`ML|HEURISTICO|ENSEMBLE`)
- `devig_metodo` (`exacto|implied_raw_single_side|fallback_conservador_no_odds`)
- `fecha_desde` (filtra por `actualizado_en >= fecha_desde`)
- `fecha_hasta` (filtra por `actualizado_en <= fecha_hasta`)
- `partido_id`
- `modelo_version_id`
- `calibrador_id`
- `estado`
- `resultado_outcome`
- `limite`, `offset`

## Gobernanza / acceso

- Auditoría v2/legacy/backfill: **admin-only** (no solo autenticación).
- Se valida rol en tabla `usuarios` (`rol='admin'`).
- No es público anónimo ni para cualquier usuario autenticado.

## Política de outcomes para métricas

Para métricas de backtesting binarias (`hit_rate`, `brier`, `log_loss`, `calibration_gap`):

- `GANADA` -> y=1
- `PERDIDA` -> y=0
- `PUSH` / `ANULADA` / `NULL` -> **se excluyen** del denominador binario

Totales:
- `resueltas`: solo `GANADA` + `PERDIDA`
- `no_resueltas`: `NULL` + `PUSH` + `ANULADA`

## Política de migraciones vs runtime

- **Mecanismo principal**: migración formal SQL (`backend/migrations/2026-04-02_auditoria_futbol_canonica.sql`).
- Runtime DDL en `asegurar_tabla_apuestas_analizadas` queda solo como fallback de bootstrap/emergencia y se activa únicamente con:
  - `APUESTAS_ANALIZADAS_RUNTIME_DDL=1`
- En operación normal debe estar desactivado.

## Uso de vista canónica

La auditoría operativa usa como base oficial:
- `vw_auditoria_decisiones_futbol`

Esto alinea API y BI sobre la misma semántica canónica.

## Legacy policy

- `legacy` se mantiene por compatibilidad mínima.
- Nuevas capacidades (tipado estricto/estructura v2) viven en endpoint v2.
- Sunset recomendado: congelar legacy y retirarlo cuando consumidores migren.

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

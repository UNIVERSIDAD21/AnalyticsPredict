# MATRIZ_DE_POLICY_POR_ODDS_Y_MERCADO.md

## Vigencia
- **Desde:** 2026-03-07 (UTC)
- **Bloque:** 05 — Prioridad crítica 2 (odds > 2.0)
- **Naturaleza:** política temporal operativa

## Convenciones
- **PERMITIDO:** se puede operar normal.
- **RESTRINGIDO:** operar con cautela + revisión de muestra y señales.
- **BLOQUEADO:** no operar temporalmente.
- **MUESTRA INSUFICIENTE:** no establecer regla dura todavía.

## Matriz

| Mercado | <1.6 | 1.6–1.8 | 1.8–2.0 | >=2.0 | Estado general mercado |
|---|---|---|---|---|---|
| COMPLETO | PERMITIDO | RESTRINGIDO | PERMITIDO | BLOQUEADO | Mixto (segmentado) |
| Q1 | RESTRINGIDO | PERMITIDO | PERMITIDO | PERMITIDO CON CAUTELA | Positivo con variabilidad |
| Q2 | MUESTRA INSUFICIENTE | PERMITIDO CON CAUTELA | PERMITIDO | PERMITIDO CON CAUTELA | Positivo en histórico ampliado |
| Q3 | RESTRINGIDO | RESTRINGIDO | RESTRINGIDO | MUESTRA INSUFICIENTE | Riesgoso |
| Q4 | RESTRINGIDO | RESTRINGIDO | RESTRINGIDO | MUESTRA INSUFICIENTE | Riesgoso |

---

## Guardrails mínimos de aplicación

1. Para cualquier bucket con **n < 20** en ventana activa, tratar como “con cautela”.
2. Si un bucket cae en ROI negativo 2 ventanas consecutivas, subir severidad (permitido→restringido, restringido→bloqueado temporal).
3. Revisar semanalmente:
   - `win_rate`, `roi_unit`, `edge_medio`, `prob_media vs hit_rate`.

---

## Qué revisar cuando haya más muestra

1. `Q2 >=2.0` (hoy positivo pero n bajo).
2. `Q1 >=2.0` (señal positiva, requiere robustez temporal).
3. `COMPLETO 1.6–1.8` (actualmente frágil/negativo).
4. `Q3/Q4` por posible degradación estructural de edge en mercados tardíos.

# BLOQUE 17 — Reejecución con evidencia real (2026-04-03T20:58:38Z)

## 1) Estado final real de mercados

### CORNERS_1T
- Estado final: **BLOQUEADO**
- Nivel: **NO_APTO**
- Motivo técnico: `volumen_o_resolucion_critica` (masa binaria resuelta insuficiente: 4/28 = 0.1429)

### CORNERS_LOCAL_1T
- Estado final: **BLOQUEADO**
- Nivel: **NO_APTO**
- Motivo técnico: `volumen_o_resolucion_critica` (masa binaria resuelta insuficiente: 4/28 = 0.1429)

## 2) Comparación real antes vs después (B10 vs B17)

| Mercado | Emitidos | Resueltos binarios | Cerrados operativos | Pendientes | Coverage líneas | Fallback rate | Brier | Log Loss | ECE | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| CORNERS_1T (antes) | 28 | 4 | 12 | 24 | 4 | 0.0 | 0.0004 | 0.020202707317519466 | 0.02 | BLOQUEADO |
| CORNERS_1T (después) | 28 | 4 | 12 | 16 | 4 | 0.0 | 0.0004 | 0.02020270731751945 | null | BLOQUEADO |
| **Delta CORNERS_1T** | 0 | 0 | 0 | **-8** | 0 | 0.0 | 0.0 | ~0.0 | n/a | sin cambio |
| CORNERS_LOCAL_1T (antes) | 28 | 4 | 12 | 24 | 4 | 0.0 | 0.0004 | 0.020202707317519466 | 0.02 | BLOQUEADO |
| CORNERS_LOCAL_1T (después) | 28 | 4 | 12 | 16 | 4 | 0.0 | 0.0004 | 0.02020270731751945 | null | BLOQUEADO |
| **Delta CORNERS_LOCAL_1T** | 0 | 0 | 0 | **-8** | 0 | 0.0 | 0.0 | ~0.0 | n/a | sin cambio |

## 3) Robustez y límites de interpretación
- La mejora observada es **operativa** (limpieza de pendientes), no de madurez cuantitativa binaria.
- `resueltos_binarios` no crece (4 -> 4), por lo que no hay base para promoción.
- Con n=4 outcomes binarios por mercado, Brier/LogLoss/ECE no deben usarse para sobrepromoción.

## 4) Riesgos residuales reales
- Masa resolutiva binaria extremadamente baja para decisión de estado superior.
- 16 pendientes por mercado todavía limitan estabilidad de scorecard en siguientes ventanas.
- Riesgo de falsa señal de calidad si se toma el descenso de pendientes como señal de madurez predictiva.

## 5) Ruta recomendada real
- **Ruta 2**: aún no suben, pero vale la pena seguir acumulando masa resolutiva.
- Justificación: el rescate mejoró higiene operativa (pendientes), pero no incrementó resolución binaria ni cambió el gate.

## 6) Comandos y pruebas reales ejecutadas

### Re-scorecard
```bash
./.venv/bin/python backend/scripts/re_scorecard_corners_b17.py
```
Salida:
- `Generados: BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.json, BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.md`

### Pruebas
```bash
./.venv/bin/pytest -q backend/tests/test_futbol_walkforward_scorecard.py backend/tests/test_futbol_rescate_corners_b16.py
```
Salida:
- `4 passed in 0.71s`

## 7) Rutas de validación
- `docs/reportes/BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.json`
- `docs/reportes/BLOQUE_17_RESCORECARD_CORNERS_COMPARATIVA.md`
- `docs/reportes/BLOQUE_17_REEJECUCION_EVIDENCIA_2026-04-03T20-58-38Z.md`

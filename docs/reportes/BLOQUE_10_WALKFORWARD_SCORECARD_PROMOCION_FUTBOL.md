# BLOQUE 10 — Backtesting Walk-Forward + Scorecard de Promoción por Mercado (Fútbol)

## Resultado ejecutivo
**Estado del módulo (evidencia actual): BLOQUEADO / LABORATORIO.**

Con el pipeline walk-forward ejecutado en esta corrida, **0 mercados** cumplen promoción y **0 mercados** cumplen validación; el inventario queda bloqueado por volumen resuelto insuficiente para gate profesional.

## 1) Pipeline walk-forward reproducible (sin leakage)

Script nuevo:
- `backend/scripts/walkforward_scorecard_futbol.py`

Configuración ejecutada:
- `train_days=180`
- `cal_days=60`
- `eval_days=30`
- `windows=6`

Garantías anti-leakage:
- `train < calibración < evaluación` por ventana.
- Fechas de corte explícitas por ventana en reporte JSON.
- Métricas calculadas solo con datos de la ventana de evaluación.

Prueba unitaria de integridad temporal:
- `backend/tests/test_futbol_walkforward_scorecard.py`

## 2) Scorecard por mercado

Artefactos generados:
- `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.json`
- `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.csv`

Métricas incluidas por mercado:
- volumen resuelto,
- coverage de líneas,
- Brier,
- Log Loss,
- ECE,
- sharpness,
- fallback_rate,
- drift entre ventanas,
- status final.

## 3) Clasificación formal (promoción/bloqueo)

Módulo de reglas:
- `backend/motor_futbol/madurez_beta.py`

Estados de salida usados en block10:
- `BLOQUEADO`
- `LABORATORIO`
- `VALIDACION`
- `PROMOCIONABLE`

Mapeo objetivo desde clasificación cuantitativa interna (`NO_APTO/EXPERIMENTAL/VALIDACION/PROMOCIONABLE`).

## 4) Inventario de mercados (corrida actual)

Resumen extraído del scorecard generado:
- **BLOQUEADO:** 24
- **LABORATORIO:** 0
- **VALIDACION:** 0
- **PROMOCIONABLE:** 0

Mercados bloqueados (actual):
- CORNERS_1T, CORNERS_2T, CORNERS_FT,
- CORNERS_LOCAL_1T, CORNERS_LOCAL_2T, CORNERS_LOCAL_FT,
- CORNERS_VISITANTE_1T, CORNERS_VISITANTE_2T, CORNERS_VISITANTE_FT,
- GOLES_1T, GOLES_2T, GOLES_FT,
- GOLES_LOCAL_1T, GOLES_LOCAL_2T, GOLES_LOCAL_FT,
- GOLES_VISITANTE_1T, GOLES_VISITANTE_2T, GOLES_VISITANTE_FT,
- DISPAROS_FT, DISPAROS_ARCO_FT,
- DISPAROS_LOCAL_FT, DISPAROS_LOCAL_ARCO_FT,
- DISPAROS_VISITANTE_FT, DISPAROS_VISITANTE_ARCO_FT.

## 5) Criterios cuantitativos mínimos (promoción)

- `n_resueltas >= 250`
- `lineas_cubiertas >= 4`
- `brier <= 0.23`
- `log_loss <= 0.67`
- `ece <= 0.06`
- `fallback_rate <= 0.15`
- `drift_brier_ventana <= 0.03`
- estabilidad de estado de mercado y sin señales críticas de cobertura.

## 6) Integración operativa (backend/frontend)

- Backend mantiene endpoint de madurez beta: `GET /api/futbol/metricas/madurez-beta`.
- Frontend ya endurecido en BLOQUE 9/10 para no comunicar madurez cuando hay gate crítico de coverage/datos.

## 7) Pruebas ejecutadas

Backend:
- `backend/tests/test_futbol_walkforward_scorecard.py` ✅
- `backend/tests/test_futbol_madurez_beta.py` ✅

Frontend (regresión gate/calidad):
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts` ✅
- `frontend/src/servicios/futbol/analisis.test.ts` ✅

## 8) Riesgos residuales

- El bloqueo actual está dominado por volumen resuelto bajo por mercado.
- Sin aumentar resolución histórica y estabilidad por ventana, no hay base para promoción.
- Persisten deudas técnicas de bundling frontend (warning circular chunk), no bloqueantes para el gate cuantitativo.

## 9) Conclusión operativa

Fútbol **no sale de laboratorio** en esta corrida.
El gate ya está formalizado, reproducible y auditable: cuando un mercado cumpla umbrales, sube; si no, se queda bloqueado.

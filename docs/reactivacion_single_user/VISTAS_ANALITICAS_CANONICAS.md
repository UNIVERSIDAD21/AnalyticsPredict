# Vistas analíticas canónicas — estado single-user

**Corte:** 2026-10-06. Este documento reemplaza como guía operativa la propuesta histórica de `docs/borlty-deliverables/VISTAS_ANALITICAS_CANONICAS.md`; no declara implementadas vistas que solo estaban diseñadas.

| Superficie | Grano | Estado comprobado | Límite |
|---|---|---|---|
| `vista_predicciones_para_calibracion` | predicción NBA | Migrada en Neon, 42 columnas y semántica raw/calibrada con `calibrador_id` | 2.934 predicciones; 0 pares calibrados con ID. No certifica temporalidad. |
| `vista_resumen_calibracion` | mercado NBA | Migrada en Neon, 12 columnas; excluye 24 outcomes ligados a 0–0 | 2.558 pares raw descriptivos; no son resultados independientes ni prospectivos. |
| Auditor P&L y gate de bitácora | apuesta NBA | CLI y GET clasifican sin DML; ROI `NULL` si hay no evaluables en segmento | 114/181 binarias excluidas; 67 aritméticas sin certificación. No existe una vista SQL unificada de P&L certificado. |
| Métricas fútbol | mercado/ventana | API calcula Brier/ECE/Log Loss con pares válidos y N/D sin muestra; rendimiento con ROI registrado nullable | Sin fuente reciente validada, solo 3–4 pares por mercado en corte anterior. No existe vista cross-sport certificada. |

## Próxima vista física admisible

Una nueva vista canónica de P&L debe conservar **una fila por apuesta** antes de agregar, exponer `motivo_no_evaluable`, `partido_id`, competición, fuente del outcome, stake/cuota/unidad y sus timestamps, y agrupar solo después de aplicar exactamente el mismo gate que `backend/scripts/auditar_pnl_nba.py` y `backend/api/rutas_bitacora.py`. Si faltan fuente/instante/unidad, `profit_certificado` y `roi_certificado` deben ser `NULL`; no convertir la coherencia aritmética en certificación. El join con predicciones nunca debe multiplicar apuestas. Primero probar sobre PostgreSQL desechable y comparar con el corte 182/181/114/67/8/40, luego migrar con rollback.

La propuesta histórica `vw_perf_market_odds_confidence` y otras vistas 06 siguen **no implementadas**. No usarlas como fuente de UI ni afirmar que los KPI canónicos están completos.

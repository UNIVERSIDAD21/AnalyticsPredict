# Corte de recertificación analítica — 2026-10-06

## Objetivo y método

Evaluar el estado **medido**, no proyectar rentabilidad ni declarar modelos listos para operar. Se ejecutó `backend/scripts/auditar_corte_analitico.py` contra Neon en transacción `READ ONLY`, sin ingestas, entrenamiento, cambios de datos ni publicación. Los tests de fórmulas usan pares sintéticos conocidos. El corte fue a las 14:40 UTC del 2026-10-06. Datos y fechas descritos son los observados en ese instante; no equivalen a disponibilidad de fuente en tiempo real.

## Resultado formal

**NO CERTIFICADO** para rendimiento actual NBA, fútbol, calibración aplicada, ROI y walk-forward sin leakage. La auditoría produjo una línea de base reproducible y detectó bloqueos cuantificables. No se cambian umbrales, stakes ni políticas de promoción por este corte.

| Superficie | Evidencia observada | Dictamen |
|---|---|---|
| Datos NBA | 12.767 partidos; último 2026-05-05; 0 de últimos 30 días. 219 sin `source`, 231 con total 0–0, 0 duplicados por `(source, source_game_id)` no nulo. | Frescura insuficiente; 0–0 requiere clasificación antes de modelar. |
| Datos fútbol | 23.919 partidos; 23.637 finalizados; último finalizado 2026-03-22; 0 finalizados últimos 30 días. Entre finalizados, 18.300 con corners completos y 18.896 con disparos completos; 0 duplicados por ID Sofascore no nulo. | No hay base reciente para levantar beta. |
| Predicciones NBA | 2.934 registradas, 2.612 marcadas resueltas; 2.582 pares válidos de probabilidad raw/outcome: Brier 0,211900, Log Loss 0,624954, ECE-10 0,056674. **0 pares de probabilidad calibrada**. | Retrospectiva raw, no calibración ni desempeño actual certificado. Repeticiones por partido/mercado no se tratan como muestras independientes. |
| Predicciones fútbol | 567 registradas, 97 marcadas resueltas; 81 pares válidos: Brier 0,126482, Log Loss 0,445165, ECE-10 0,134405. Las 567 probabilidades «calibradas» son idénticas a raw; faltan `modelo_version_id` y `calibrador_id` en 567/567. Cada mercado tiene solo 3–4 pares válidos. | No atribuir mejora a calibración; mercados no promocionables con esta muestra. |
| Trazabilidad temporal NBA | En 2.934 predicciones con versión existente, `cutoff_entrenamiento` es **posterior** al día de generación en 2.136; mismo día sin orden horario en 42; anterior en 756. `fecha_entrenamiento` posterior a generación: 0. | Metadatos incompatibles con el gate `fit_end < prediction_time`. No afirmar «sin leakage»; examinar generación y datasets/versiones antes de un backtest real. |
| Bitácora NBA | 182 filas: 143 `GANADA`, 38 `PERDIDA`, 1 `ANULADA`; win rate **registrado** 143/181 = 79,01 %. | No es accuracy del modelo ni muestra prospectiva certificada. |
| P&L/ROI | En 181 resultados ganada/perdida, 79 ganadas y 23 perdidas (102 en total) no cumplen `ganancia = stake×(cuota−1)` / `−stake` con tolerancia 0,02. | ROI y profit **no certificables** desde `ganancia` persistida. El script etiqueta cualquier ROI derivado como `roi_registrado_no_certificado_pct`. No corregir histórico automáticamente. |
| Confidence y odds | Segmentación descriptiva disponible (ALTA 94, MEDIA 53, BAJA 34; cuota >2: 5, de las cuales 1 ganada). | Muestras reducidas y P&L inconsistente. No confirmar regla de evitar cuotas >2 ni reajustar thresholds. |

### Mercados NBA, pares raw válidos

| Mercado | n | Brier | ECE-10 |
|---|---:|---:|---:|
| COMPLETO | 1.650 | 0,190548 | 0,056857 |
| Q1 | 376 | 0,213549 | 0,057278 |
| Q2 | 224 | 0,219389 | 0,146925 |
| Q3 | 182 | 0,305888 | 0,190570 |
| Q4 | 150 | 0,317412 | 0,225891 |

Estas métricas son descriptivas sobre outcomes persistidos, sin validación externa de resultados, sin control de dependencia entre predicciones y sin garantía de entrenamiento temporal. ECE-10 depende del binning y no tiene intervalo de incertidumbre aquí. **No** comparar directamente mercados con distintas bases ni inferir rendimiento futuro.

## Reglas de calidad aplicadas y bloqueos

1. **Frescura:** al menos una observación finalizada en la ventana de 30 días por deporte. Falla en ambos.
2. **Procedencia y completitud NBA:** source no nulo, score no 0–0 y cuartos Q1/Q4 presentes. 219 sin fuente y 231 0–0; cuartos extremos completos en el conteo bruto. Los 0–0 se conservan hasta clasificar tipo/estado.
3. **Duplicidad de fuente:** `(source, source_game_id)` NBA e ID Sofascore fútbol no nulos. No se detectaron duplicados en esas claves; no demuestra unicidad de partidos sin ID.
4. **Trazabilidad:** modelo/calibrador y `fit_end < prediction_time < outcome_time`. NBA falla orden de cutoff en 2.136 y carece de probabilidad calibrada evaluable. Fútbol carece de versiones/calibradores y 470 predicciones siguen sin resolver.
5. **Consistencia P&L:** fórmula decimal sobre stake, cuota y resultado. Fallan 102/181 NBA. No usar ROI como KPI hasta reconciliar la semántica y el histórico con evidencia primaria.

## Evidencia técnica y siguiente gate

- Reproducir: `cd backend && python scripts/auditar_corte_analitico.py` con `DATABASE_URL` protegida. El script se niega a seguir si `transaction_read_only` no está activo y emite únicamente agregados.
- Tests de fórmulas del corte: `backend/tests/test_auditar_corte_analitico.py` (2/2). Tests analíticos puros dirigidos: 33/33 en Python 3.12 con el lock del proyecto. La integración de migración PostgreSQL efímera pasó 2/2 localmente; no equivale a suite global.
- Para reabrir certificación: actualizar feeds con pipeline controlado y verificar resultado contra fuente; reconciliar 102 P&L sin alterar registros a ciegas; reconstruir o invalidar las 2.136 trazas temporales; generar walk-forward con snapshots/versiones congeladas por corte; exigir volumen resolutivo y estabilidad por mercado; volver a medir calibración/odds/confidence/KPIs con intervalos y dependencia por partido.
- Fútbol sigue beta global. El módulo interno NBA mantiene `no_picks`, `no_stake`, `no_betting_recommendations`.

## Smoke visual y veracidad de la UI

Con backend en `127.0.0.1:8000` con lifespan desactivado y conexión read-only, y frontend Vite en `127.0.0.1:5173`, se renderizaron `/`, `/dashboard`, `/bitacora`, `/futbol` y `/app` sin login ni errores JavaScript de página. Dashboard y bitácora mostraron registros no vacíos. Se actualizó el copy de dashboard, bitácora y métricas para rotular ROI/ganancia como **registrados, no certificados** y para mostrar `N/D` cuando el resumen no trae un valor, sin transformarlo en cero. Lint, 11 tests y build/typecheck frontend pasaron; el aviso nuevo fue visible en ambas pantallas. **Límite:** las lecturas de bitácora activaron intentos de auto-resolución/escritura del backend, rechazados por la transacción read-only y registrados como error en servidor. El smoke verifica render/lectura, no un flujo de resolución ni ausencia de side effects en esos GET.

**Corrección posterior:** se retiró la auto-resolución/DDL de los GET de bitácora y se añadieron pruebas que fallan si vuelven a invocarse. La resolución de resultados se mantiene únicamente en operaciones POST explícitas. El smoke anterior no se reetiqueta retroactivamente como prueba de esta corrección; rige el nuevo test de contrato.

**Nuevo corte de frescura:** la ingesta NBA controlada de 8 partidos de pretemporada elevó el total a 12.775 y los observados en 30 días a 8. Consulte `INGESTA_NBA_CONTROLADA_2026-10-06.md`. Las cifras de la tabla de arriba pertenecen al corte read-only anterior a la ingesta. La mejora de frescura **no** certifica marcadores por fuente independiente, ROI, calibración ni ausencia de leakage; el dictamen sigue NO CERTIFICADO.

**Adenda P&L del mismo día:** `RECONCILIACION_PNL_NBA_2026-10-06.md` clasifica cada una de las 182 apuestas sin modificar Neon. Las 102/181 fallas de fórmula del corte original siguen siendo 102; una fila **adicional** con importe conciliable muestra cuota distinta a la registrada para el lado elegido. Por ello, el gate más estricto deja 103/181 binarias no evaluables para ROI y 78 solo aritméticamente conciliables. Los GET de resumen/métricas ahora devuelven ROI `null` en segmentos NBA afectados y el frontend exhibe N/D con conteo de exclusiones. No cambia el dictamen NO CERTIFICADO.

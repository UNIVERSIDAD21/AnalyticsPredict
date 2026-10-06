# H9 — métricas probabilísticas, avance verificable

**Estado:** EN CURSO. Este cambio no certifica modelos ni cierra H9.

## Definición y alcance

`backend/metricas_probabilisticas.py` define Brier como media de `(p-y)^2`, Log Loss binaria en nats con clipping numérico `1e-15` y ECE como suma ponderada de gaps absolutos en 10 bins fijos `[0,.1), …, [.9,1]`. Solo entran pares binarios completos con `p∈[0,1]`; sin pares válidos las tres métricas son `null`, no cero. `n` es la cantidad efectivamente medida. La raw es la salida anterior a calibración; la calibrada exige transformación real y procedencia, no igualdad de nombres de columnas.

## Checklist y evidencia

- [x] Inventariar productores/consumidores activos en `backend/api`, `backend/backtesting`, `backend/calidad`, `backend/motor_futbol`, `backend/scripts` y `frontend/src` mediante búsqueda de `brier`, `log_loss`, `ece` y `calibration_error`.
- [x] Unificar fórmulas numéricas de rutas Python principales y el corte agregado; probar pares conocidos, extremos 0/1, ausencia de muestra y comparación NBA/fútbol.
- [x] Separar series raw/calibrada del calculador NBA; ausencia de calibrada devuelve `null` y cobertura parcial genera alerta, no fallback silencioso.
- [x] Impedir que el corte agregado llame calibrada a una predicción sin `calibrador_id`; el endpoint de calibración fútbol exige esa procedencia y compara Brier sobre pares coincidentes.
- [x] Retirar del script de scorecard fútbol el ECE=1 sin datos, `resolved_rate=1` y el claim no comprobado de ausencia de leakage. Este script queda no promocionable mientras no demuestre corte temporal y estado operativo.
- [x] Corregir inferencia/persistencia fútbol para que las rutas nuevas no copien raw en campos `*_calibrada`; exigir UUID del artefacto. Ver `CALIBRACION_FUTBOL_PROCEDENCIA_2026-10-06.md`.
- [ ] Revisar y alinear consumidores SQL/reportes legacy que todavía aplican clipping distinto o `COALESCE` sin procedencia, y verificar todos los mercados NBA/fútbol con datos actuales.
- [ ] Ejecutar pruebas completas backend y frontend y verificar representación N/D en todas las superficies antes de cerrar H9.

## Criterio de aceptación

- [ ] Una única definición operativa para Brier, Log Loss y ECE en rutas actuales y reportes vigentes.
- [ ] Ningún campo calibrado se publica sin transformación y procedencia verificable.
- [ ] Ausencia de datos o de muestra equivalente aparece N/D; los conteos acompañan la métrica.
- [ ] Backend, frontend y contratos pasan en entorno reproducible.

## Pruebas y límites

En el primer corte: 66 pruebas dirigidas pasaron con `DATABASE_URL` vacío; esa cifra no incluía suite global, PostgreSQL efímera ni prueba de interfaz. El corte read-only previo documentó fútbol 567/567 `p_calibrada == p_raw` sin `calibrador_id`; no se han alterado esas filas. El análisis retrospectivo permanece **NO CERTIFICADO**. Los gates actuales figuran en la actualización siguiente.

## Continuación de consumidores — 2026-10-06

- Los gates de bloqueo NBA/fútbol, tablero de salud, ranking de calidad, drift, madurez/estabilidad fútbol, auditoría de decisiones y explicación de predicción ahora seleccionan una columna calibrada solo si existe `calibrador_id`; en caso contrario usan raw. La explicación tampoco etiqueta como calibrada una fila sin procedencia.
- Los reportes de walk-forward nominal, madurez, shadow y monitoreo de fútbol comparten una expresión SQL que exige ID, tolera variantes de columnas raw legacy y computa fallback incluso si la columna calibrada histórica está poblada sin ID. Madurez/monitoreo alinearon el clipping Log Loss a `1e-15`.
- El backtest de fútbol muestra Brier/ECE como N/D sin muestra; sus recomendaciones ya no declaran aptitud de producción solo por ECE retrospectivo bajo o ausente.
- Suite backend completa en PostgreSQL local desechable con esquema sintético: **627 passed, 0 failed, 9 skipped, 14 warnings**. Las nuevas pruebas ejecutan SQL real para procedencia en tablero, madurez, explicación, reportes y auditoría. Frontend: **16 tests**, lint y build/typecheck verdes. Los dos archivos de reporte que la suite regeneró se devolvieron exactamente a HEAD; no forman parte del cambio.
- CI del HEAD anterior `23a554e` pasó 4/4 jobs; este lote aún requiere CI de su propio HEAD. Las nueve omisiones de suite están detalladas en `AUDITORIA_SUITE_GLOBAL_2026-10-06.md`.

**H9 permanece abierto:** la vista `vista_predicciones_para_calibracion` y scripts históricos B16/B17/B20 aún necesitan cotejo de procedencia/semántica; los datos actuales y cada mercado requieren contraste read-only, sin alterar el histórico 567/567 de fútbol. Un gate SQL sintético no demuestra calibración prospectiva ni resuelve frescura, temporalidad u outcomes.

## Cotejo read-only de Neon y vista — 2026-10-06

La conexión se abrió con transacción `READ ONLY`; no hubo ingesta ni escrituras. En este corte, NBA registra 2.934 predicciones y 2.582 pares raw válidos; fútbol 567 predicciones y 81 pares raw válidos. **Cero pares calibrados con ID** en ambos deportes. Las 567 filas de fútbol mantienen una columna calibrada poblada sin ID. Los pares fútbol se distribuyen entre 24 mercados con apenas 3–4 por mercado; los NBA raw por mercado son COMPLETO 1.650, Q1 376, Q2 224, Q3 182 y Q4 150. Son conteos históricos disponibles, no validación prospectiva.

La definición vigente de `vista_predicciones_para_calibracion` usa `COALESCE(pr.p_calibrada, pr.p_raw)` para `p_efectiva` y su bin, sin comprobar `calibrador_id`. Los consumidores de aplicación (calculador, curvas de métricas/backtest y filas del reporte) ahora reconstruyen la probabilidad efectiva o calibrada con ID. Una prueba PostgreSQL crea deliberadamente una vista legacy que devuelve 0,9 sin ID y demuestra que los consumidores usan raw 0,2; detectó y corrigió también el tipo del parámetro opcional de modelo. Suite local: **629 passed, 0 failed, 9 skipped, 14 warnings**. La vista productiva **no se modificó** y sigue siendo deuda para consultas SQL directas o consumidores externos.

CI del código `50a372e`: **4/4 jobs verdes**, incluida la suite global en PostgreSQL efímero y smoke Compose. Las nueve omisiones y la falta de validación prospectiva siguen vigentes.

## Continuación: pruebas activas, calibración temporal y vista preparada — 2026-10-06

- Los nueve tests antes omitidos se adaptaron a contratos vigentes y a PostgreSQL sintético desechable: registro/idempotencia NBA, resolución NBA y predicción fútbol. Ninguna prueba de integración escribe en Neon.
- `calibrar_futbol.py` ya no sustituye fallos o falta de datos por backtest/sintéticos. Exige predicciones operativas resueltas, raw válida, generación anterior al partido y resolución posterior; separa train/validación por día y rechaza outcomes de train aún no disponibles al generar la validación. Diagnóstico sin `--guardar` usa conexión read-only; guardar exige al menos 200 pares por mercado. `cutoff_datos` refleja la última resolución de train, no la fecha de ejecución.
- B16/B17/B20A/B20B cuentan fallback cuando falta `calibrador_id` y calculan Brier/Log Loss desde raw en esas filas. Un test SQL ejecuta ambos reportes B20 y comprueba 0,2 raw frente a 0,9 calibrada sin ID.
- Migración compatible `backend/migrations/2026-10-06_h9_vista_calibracion_procedencia.sql` preparada para que `p_efectiva` y `bin_p_efectiva` de la vista NBA exijan ID. Probada sobre réplica sintética de las 42 columnas legacy: conserva orden/tipos y corrige la probabilidad. **No se ha aplicado a Neon**; la vista productiva aún expone el `COALESCE` antiguo a consultas SQL directas.
- Suite backend completa en PostgreSQL local desechable con Python 3.12: **646 passed, 0 failed, 0 skipped, 2 warnings**. Frontend: **16 tests**, lint y build/typecheck verdes. Diagnóstico de `GOLES_FT` en Neon mediante conexión read-only: **0 pares temporales elegibles** frente al mínimo 200; no se guardó ni activó calibrador. Los conteos anteriores de 81 pares raw fútbol no implican elegibilidad temporal.
- CI del commit `b8a6d74` (run `37518301706`): **4/4 jobs verdes**, incluyendo suite global PostgreSQL efímera, frontend, contratos y Compose.

**H9 sigue abierto:** aplicar/validar la migración de vista bajo control operativo, verificar N/D y mercados con datos frescos, producir predicciones congeladas con outcomes posteriores independientes y completar recertificación. Esta suite demuestra comportamiento de código, no calidad/calibración del modelo ni rentabilidad futura.

## Preflight del plan de cierre — ambas vistas NBA, 2026-10-06

- [x] Cotejar en Neon mediante transacción read-only las 42 columnas de la vista base, FK validada a `calibradores(id)` y dependencias. `vista_resumen_calibracion` depende de ella y también usaba `COALESCE` sin procedencia; 2.582 filas resueltas de la vista base, cero con ID de calibrador.
- [x] Guardar DDL vigente de ambas vistas como rollback fuera del repositorio; no se exportaron filas ni credenciales.
- [x] Ampliar migración para que solo exponga calibrada con ID resoluble, mercado coincidente y probabilidad en rango; raw fuera de rango o falta total de pares deja `NULL`. La vista resumen compara únicamente pares raw/efectiva válidos y expone `n=0` y métricas `NULL` si no hay pares.
- [x] Ensayar en PostgreSQL efímero nueve escenarios, rechazo de FK inexistente, preservación de nombres/tipos en ambas vistas y rollback. Suite backend completa del worktree aislado: **646 passed, 0 failed, 0 skipped, 2 warnings** bajo Python 3.14.
- [x] Aplicar DDL a Neon bajo la orden del Jefe de continuar el plan, revalidar contrato/agregados y verificar CI de la rama de preparación (PR #167, run 37524221265, 4/4 verde).

La transacción aplicada en Neon el 2026-10-06T20:12:46Z conservó 42 columnas de la vista base, 12 de la dependiente, owner/grants y 2.934 filas históricas. Postflight read-only: COMPLETO 1.650, Q1 376, Q2 224, Q3 182, Q4 150 pares; **0** calibrados con ID, **0** probabilidades efectivas distintas de raw, **0** falsamente calibradas. El rollback de ambas definiciones quedó fuera del repositorio. Esto cierra la semántica técnica de ambas vistas; calibración real y P&L continúan **NO CERTIFICADOS**.

El backend del propietario opera con `--reload`, por lo que los archivos se prepararon en un worktree temporal externo al árbol observado para no disparar entrenamiento implícito antes de abordar ese siguiente bloque del plan.

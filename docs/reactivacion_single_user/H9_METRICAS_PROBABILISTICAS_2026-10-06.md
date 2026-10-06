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

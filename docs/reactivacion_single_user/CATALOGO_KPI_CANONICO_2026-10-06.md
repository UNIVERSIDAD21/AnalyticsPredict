# Catálogo semántico de KPI — definición v0 (2026-10-06)

**Estado de implementación:** fórmulas y guardas definidas; las vistas canónicas/materialización y su integración en UI siguen pendientes. Ningún ROI o win rate de este corte es rentabilidad certificada. Responsable lógico: analítica de AnalyticsPredict. Actualización prevista tras ingesta/resolución, con corte temporal explícito y `n` visible; los históricos nunca se interpretan como pronóstico de rendimiento.

## Granos y contrato común

Grano de apuesta: `id`, deporte, mercado, lado, línea, cuota, stake, resultado y fecha de resolución desde `apuestas` NBA / `apuestas_futbol`. Grano de predicción: `id`, partido, mercado, lado/línea, `modelo_version_id`, `calibrador_id`, `timestamp_generacion`, `timestamp_resolucion`, probabilidad raw/calibrada y outcome desde `predicciones_registradas` NBA / `predicciones_futbol`. Cortes válidos: deporte → mercado → lado/línea → ventana temporal → versión; no sumar filas de mercados diferentes ni predicciones del mismo partido como muestras independientes sin advertir dependencia. Toda razón con denominador cero es `NULL`, no 0. Los valores monetarios conservan moneda/unidad de la bitácora; no se agregan monedas diferentes. Filtrar anuladas/push/pendientes para métricas binarias de resultado, no para conteo bruto. Valor fuera de rango o sin procedencia se excluye solo de la métrica afectada y se cuenta en calidad.

| KPI | Fórmula y denominador | Unidad / fuente | Guardas y test mínimo |
|---|---|---|---|
| Total Bets | `count(id)`; publicar además `n_resueltas` y `n_binarias` | conteo, bitácoras | No es n de predicciones; separar pendientes/anuladas. |
| Win Rate | `ganadas / (ganadas + perdidas)` | %, bitácoras | `n_binarias>0`; muestra y ventana explícitas. 143/181 NBA es **registrado**, no validación temporal. |
| Profit | `sum(ganancia_validada)` para ganadas/perdidas | moneda/unidad de stake, bitácoras | Fila ganada: `stake*(cuota-1)`; perdida: `-stake`, tolerancia 0,02, stake>0, cuota>1; si hay incompatibles en el corte, KPI certificado `NULL`, publicar conteo conflictivo. |
| ROI | `Profit / sum(stake)` sobre exactamente las mismas filas resueltas y validadas | %, bitácoras | Denominador positivo y coherencia P&L de todas las filas del segmento; 102/181 NBA fallan, por tanto **no certificado**. No usar `sum(ganancia)/sum(stake)` histórico como ROI validado. |
| Average Stake | `sum(stake válido) / n(stake válido)` | moneda/unidad de stake, bitácoras | Excluir stake nulo/no positivo y mostrar n válido/excluido; no mezclar monedas. |
| Accuracy | `sum((p>=0,5)==y) / n(p,y)` | %, predicciones resueltas | Solo outcome binario y p∈[0,1]; declarar política de empate p=0,5 y dependencia por partido. |
| Brier Score | `sum((p-y)^2)/n(p,y)` | [0,1], predicciones resueltas | Raw y calibrada en series separadas; no inferir calibración de `p_cal=p_raw`; `n` por mercado/version. |
| Log Loss | `-sum(y*ln(clamp(p))+(1-y)*ln(1-clamp(p)))/n` | nats, predicciones resueltas | `clamp` solo numérico a ε=1e-15 para log; no sustituir p ausente por 0. |
| ECE-10 | `sum_b n_b/n * abs(mean(p_b)-mean(y_b))`, bins `[0,0.1),…,[0.9,1]` | [0,1], predicciones resueltas | `n` y bins fijos; no tratar ECE de muestra pequeña como estabilidad. |
| Sharpness | `sum((p-mean(p))^2)/n` | varianza de probabilidad, predicciones | No usa outcomes; reportar junto a calibración y n, nunca como precisión aislada. |
| EV por unidad | `p*(cuota-1)-(1-p)` | retorno esperado por 1 de stake | Solo cuota decimal>1, probabilidad validada, línea real y versión; estimación, no ganancia observada. |
| Edge | `p_modelo - p_mercado_justa` | puntos de probabilidad | Sin dos cuotas reales/linea congruente, `NULL`; no usar cuota técnica como mercado real. |
| Devig impact | `p_implied_raw - p_mercado_justa`; `p_mercado_justa=(1/cuota_lado)/((1/cuota_over)+(1/cuota_under))` | puntos de probabilidad | Dos cuotas reales para lados excluyentes, ambas>1 y overround>0; conservar método y procedencia. |
| Stake consistency | `n(stake<=0 o stake>bankroll_momento o fuera de política)/n_con_base` | conteo y %, bitácoras | Si falta bankroll/política, `NO_EVALUABLE`; no imputar límite. Módulo NBA interno no genera stakes. |
| Confidence / odds | distribución por categoría ALTA/MEDIA/BAJA y rangos de cuota `<=1,5`, `(1,5,2]`, `>2` | conteo y %, bitácoras | Mostrar n resueltas y n total, versión/mercado; 5 apuestas NBA >2 no justifican regla nueva. |

## Contrato de calidad y publicación

Un consumidor debe recibir `{valor, unidad, n, n_excluidas, ventana, deporte, mercado, version, estado_calidad, corte_utc}`. `estado_calidad` distingue `VALIDO_DESCRIPTIVO`, `NO_EVALUABLE` y `NO_CERTIFICADO`; no rellenar `NULL` con cero ni fusionar raw/calibrada. `DATA_QUALITY_RULES.md` y `SCORECARD_CALIDAD_DE_DATOS.md` son guards de publicación; `TRAZABILIDAD_CONFIDENCE_2026-10-06.md` registra la fórmula vigente sin validarla. Los tests `test_auditar_corte_analitico.py` prueban Brier/Log Loss/ECE con pares conocidos y exclusión de pendientes del win rate; faltan pruebas de vistas/granularidad e integración UI. Esta definición no debe marcar como terminada la capa canónica completa.

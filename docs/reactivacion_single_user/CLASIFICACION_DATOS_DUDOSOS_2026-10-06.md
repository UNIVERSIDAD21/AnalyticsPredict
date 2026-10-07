# Clasificación de datos deportivos dudosos — corte read-only 2026-10-06

> **Actualización posterior con DML autorizado:** los 148 NBA 0–0 y 83 Euroliga 0–0 de las tablas históricas de abajo son el **corte previo**. Tras contraste con ESPN y Euroliga oficial se corrigieron 81 finales NBA y uno Euroliga; quedan 67 NBA 0–0 y 82 Euroliga 0–0, todos `valido=false`. La bitácora conserva apuestas; con ocho resultados incompatibles con marcador y 40 apuestas sin `partido_id`, el gate deja **114/181** binarias (115/182 totales) no evaluables y 67 binarias solo aritméticamente coherentes. Ver `RECONCILIACION_MARCADORES_BALONCESTO_2026-10-06.md`; el dictamen sigue **NO CERTIFICADO**.

**Estado:** exclusión preventiva y filtros principales de outcomes NBA 0–0 implementados. El contraste externo posterior distingue NBA de Euroliga; **no** certifica desempeño de modelos ni habilita imputación automática.

## Hallazgos en Neon

| Grupo | n | Hecho observable | Clasificación operativa |
|---|---:|---|---|
| NBA sin `source` normalizado | 219 | Los 219 tienen `fuente_datos=ESPN`, `espn_game_id` y tipo REG; 138 muestran ambos totales positivos y 81 muestran 0–0. | `SOURCE_ALIAS_LEGACY`: procedencia parcial recuperable por ID ESPN, sin equiparar el alias faltante con verificación de resultado. |
| NBA 0–0 | 148 | 81 `source=NULL` y 67 `source=ESPN` (58 REG, 9 POST); todos `valido=true` pero sin ganador ni puntos en cuartos. Intersección con grupo anterior: 81. | `ZERO_ZERO_NO_OUTCOME`: resultado almacenado no acreditado. El contraste ESPN posterior diferencia pospuestos de marcadores finales omitidos. |
| Euroliga 0–0 | 83 | `source=SOFASCORE`, competición `euroleague`, sin ID ESPN. | Resultado no acreditado; no sumarlos al KPI NBA ni inferir estado final desde 0–0. |
| Predicciones NBA enlazadas a 0–0 | 66 | 42 pendientes; **24 ya resueltas** con outcome binario (12 COMPLETO, 8 Q1, 2 Q2, 2 Q3), fechas 2026-01-24/25. | Las 24 no son pares de resultado defendibles. No reescribir sin fuente primaria; excluir de métricas evaluables. |
| Apuestas NBA enlazadas a 0–0 | 5 | 4 GANADA y 1 PERDIDA, con ganancia registrada. | No atribuir P&L/ROI certificado a ese evento. Conservación y exclusión analítica pendientes de consolidar en KPI canónico. |
| Fútbol FINALIZADO sin goles completos | 25 | Los 25 tienen `fuente_datos=SOFASCORE`, ID de fuente, `datos_completos=false`; 3 registran corners/disparos. Fechas 2019-05-01 a 2023-11-18; cero predicciones enlazadas. | `FINALIZADO_SIN_GOLES`: no resolver 1X2 o mercados de goles; corners/disparos solo con completitud propia por mercado. No convertir NULL en 0. |

Los 219 alias de fuente y los 148 NBA 0–0 **se superponen** en 81 filas. El antiguo total 231 era de toda `partidos_baloncesto`: 148 NBA + 83 Euroliga. `valido=true`, `estado=FINALIZADO` o un ID de proveedor no demuestran por sí solos que haya marcador final íntegro. Ninguna fila fue actualizada, borrada o imputada.

## Regla de consumo y límites

El resolvedor NBA de predicciones y apuestas rechaza de ahora en adelante un partido cuyo **total local y visitante sean ambos cero**, incluso si los cuartos contienen cero. La comprobación aplica también con resolución forzada; no corrige retrospectivamente las 24 predicciones ni las 5 apuestas. El resolvedor fútbol ya deja `GOLES_*` sin valor real cuando faltan los goles requeridos; los 25 no tienen predicciones enlazadas hoy. La métrica por mercado de corners/disparos requiere campos propios, no el total de goles.

Las métricas históricas NBA publicadas antes de un filtro canónico de los 24 pares deben etiquetarse **descriptivas/no certificadas**. El gate H9/temporalidad ya mantiene toda la historia fuera de claims prospectivos. El siguiente trabajo de capa KPI debe excluir y contabilizar esos 24 pares (y 5 apuestas), incluyendo caches/precalculados; no basta cambiar un gráfico aislado.

## Checklist y criterio de aceptación

- [x] Clasificar 219 alias de fuente sin borrar identificadores.
- [x] Separar 231 marcadores 0–0 por competición (148 NBA, 83 Euroliga) y el solapamiento de 81 NBA sin `source`.
- [x] Clasificar 25 finalizados fútbol con goles nulos y mercados afectados.
- [x] Identificar 24 outcomes NBA y 5 apuestas ligados a 0–0.
- [x] Impedir nuevas resoluciones NBA basadas en 0–0.
- [x] Mantener Neon/histórico intactos.
- [x] Contrastar los 148 NBA por ID con ESPN: 67 pospuestos y 81 finales con marcador positivo; es verificación externa de ESPN, no segundo proveedor independiente.
- [x] Contrastar los 83 Euroliga con fuente oficial accesible y clasificar sin imputación: 48 placeholders corresponden a 44 finales existentes, 34 no tienen final oficial y un evento reprogramado tiene boxscore oficial; quedan 82 filas 0–0 inválidas.
- [x] Excluir los 24 pares 0–0 de consumidores principales y los resultados no evaluables del P&L; continúan visibles las cinco apuestas.
- [ ] Completar inventario de consumidores/cache residuales y verificar que cada superficie publique el conteo de exclusiones que corresponde.
- [ ] Verificar resultados de los 25 partidos fútbol contra proveedor permitido o dejar formalmente sin outcome.

**Aceptación parcial:** reconciliación oficial de baloncesto completada con evidencia privada; no se imputaron los 34 registros Euroliga sin final oficial. El bloque E sigue abierto por consumidores residuales, outcomes independientes NBA/fútbol y cadena prospectiva; las métricas permanecen no certificadas.

## Adenda: exclusión en consumidores principales

La auditoría read-only mantiene 2.934 predicciones y 2.612 marcadas resueltas, pero aparta los **24 outcomes 0–0** antes de computar Brier/Log Loss/ECE: quedan 2.558 pares raw frente a 2.582 del corte original. La API de calibración y su curva enmascaran el outcome y el valor real de esas filas, exponen `n_excluidos_outcome_dudoso` (visible en tabla y curva del frontend) y recalculan en memoria; el GET ya no usa un precálculo anterior ni ejecuta UPSERT. Esto **no** convierte el resto en evidencia prospectiva o independiente.

En bitácora, los cinco registros vinculados a 0–0 se conservan visibles. El gate de ROI combina calidad de fórmula/cuota y resultado acreditado: **107/181** binarias no evaluables (103 previas más 4 nuevas; la quinta ya se solapaba). El CLI de P&L clasifica por fila y deja solo **74 binarias** aritméticamente coherentes y sin 0–0, todavía **no certificadas**. Los otros endpoints agregados de salud/calidad/drift y eventuales caches históricos aún requieren revisión; el checklist de exclusión en **todos** los KPI sigue abierto.

## Propagación a salud, historial y backtest

La siguiente pasada de código también separa el outcome registrado del evaluable en salud, calidad por mercado y drift. La lectura read-only de Neon devuelve **2.558 resueltas evaluables** y **24 excluidas**, repartidas en COMPLETO 12, Q1 8, Q2 2 y Q3 2. El historial conserva las filas pero las rotula `NO_EVALUABLE`, no las suma a ganadas/perdidas ni expone `valor_real=0` como marcador acreditado. Los gates de calidad NBA, el recalibrador y las estadísticas de resolución tampoco cuentan esos 24 outcomes.

El reporte de backtest mantiene las filas para trazabilidad, con `outcome_no_evaluable=true`, outcome/valor real `NULL` y CSV rotulado `NO_EVALUABLE` en vez de PUSH. Resumen y curva los excluyen; el alias de nombres de equipos se resuelve contra `equipos`, compatible con la vista H9 productiva. **No** convierte el backtest histórico en walk-forward ni lo certifica.

La vista SQL directa y los precálculos se atendieron en la pasada posterior descrita abajo. La verificación por competición se registra en la adenda final; el bloque E permanece abierto. La nota anterior que menciona salud/calidad/drift como pendientes describe el corte previo a esta propagación.

## Preflight de vista agregada y precálculos

La lectura Neon del 2026-10-06 encontró **0 filas** en `metricas_calibracion`: no hay precálculos existentes que invalidar allí en este corte. La función interna de alertas que lee esa tabla está expuesta, pero actualmente no tiene métricas históricas que usar. Los cálculos de lectura en reporte de backtest y drift se ajustan a `persistir=False` para evitar poblarla implícitamente. El cálculo explícito con persistencia sigue siendo una operación de escritura separada y no se ejecutó.

La vista directa `vista_resumen_calibracion` conservó 12 columnas y cinco grupos de mercado; antes del cambio contaba **2.582 pares**: COMPLETO 1.650, Q1 376, Q2 224, Q3 182 y Q4 150. Un join read-only identificó respectivamente 12, 8, 2, 2 y 0 pares ligados a 0–0. `backend/migrations/2026-10-06_resumen_calibracion_sin_outcome_cero_cero.sql` fue aplicada a Neon tras CI 4/4 verde (PR #174, run 37542252315; rama canónica run 37542400840); su rollback exacto quedó preparado y ensayado en PostgreSQL efímero. El postflight transaccional e independiente read-only confirmó **2.558 pares**: COMPLETO 1.638, Q1 368, Q2 222, Q3 180 y Q4 150. Se conservaron contrato, owner/grants, vista base de 2.582 filas y 2.934 predicciones históricas. El rollback no fue necesario en Neon. La suite alojada de PostgreSQL sintético reportó 677 passed, 0 failed, 0 skipped.

El filtro 0–0 corrige solo la validez de outcome; no convierte 2.558 pares en datos temporales válidos ni independientes. La verificación/reconciliación de baloncesto se cerró después con fuentes oficiales; siguen pendientes independencia interproveedor NBA, fuente/outcomes recientes de fútbol, inventario residual de consumidores y cadena prospectiva.

## Ruta legacy de combinadas

El inventario residual encontró que `resolver_combinadas` podía resolver una selección nueva desde los mismos totales 0–0 aunque los resolvedores de predicciones y apuestas ya estaban protegidos. Se añadió el guard equivalente: la selección permanece `PENDIENTE` y no ejecuta `UPDATE`. El cotejo Neon read-only mostró **0 selecciones de combinadas** enlazadas a los 231 partidos de baloncesto 0–0 (0 resueltas); no hubo reparaciones históricas. La selección automática de calibradores en `backtesting/calibradores/selector.py` recibe una secuencia suministrada por el llamador y no se invoca desde rutas activas del backend en este corte; no se usa para justificar métricas históricas. Las vistas de bitácora conservan registros sin convertir el detalle en un KPI certificado.

## Fe de erratas y contraste externo por competición

El auditor anterior rotuló como NBA toda `partidos_baloncesto`. El corte read-only corregido delimita `competiciones_baloncesto.codigo='nba'`: **10.286 partidos NBA**, 219 sin `source`, **148 NBA 0–0**, 8 en los últimos 30 días y cero duplicados por ID de fuente no nulo. La tabla completa tiene 12.775 partidos: 10.286 NBA y 2.489 Euroliga. Por tanto, 12.775 y 231 en informes previos son conteos de **baloncesto agregado**, no de NBA.

Una consulta HTTP fresca a ESPN `summary?event=<espn_game_id>` de los **148 NBA 0–0** obtuvo 148 respuestas 200 e identidad de evento concordante; las fechas coinciden o difieren un día por UTC. **67** figuran `STATUS_POSTPONED`, no completados. Los **81** restantes figuran finalizados con puntos positivos en ESPN mientras Neon conserva 0–0: son marcadores locales desactualizados, no evidencia para rellenar cuartos, OT u outcomes sin un proceso de reconciliación. Las diferencias de abreviatura observadas (`GSW/GS`, `WAS/WSH`, etc.) son alias de equipos y no se usaron para asignar resultados.

Los 24 outcomes binarios excluidos pertenecen a tres eventos pospuestos; cinco apuestas ligadas al corte inicial 0–0 se distribuyen en uno de esos eventos y cuatro de los 81 ya finalizados en ESPN. Permanecen visibles y **no evaluables**; ocho liquidaciones persisten incompatibles con marcador/línea/lado. La fuente oficial Euroliga permitió reconciliar las filas acreditadas y dejar inválidas las no acreditadas. La evidencia por evento y reconciliación está en `RECONCILIACION_BALONCESTO_OFICIAL_2026-10-06` y `VERIFICACION_ESPN_EVENTOS_NBA_CERO_CERO_2026-10-06`, fuera del repositorio. El dictamen permanece **NO CERTIFICADO**.

Un dry-run de ingesta NBA 2026-04-03→12 mostró **81 eventos** de esos días, pero proponía 39 inserciones nuevas y 42 existentes porque 39 fechas locales difieren un día de la fecha UTC usada en la clave natural. Los 81 IDs ESPN ya estaban en filas legacy `source=NULL`; una ingesta real habría creado duplicados. La detección de existencia ahora consulta también `espn_game_id` sin importar el alias `source` y nunca actualiza automáticamente esas filas legacy. Dry-run repetido: **81 existentes, 0 por insertar, 0 fallos**. La reconciliación de marcadores/cuarto/OT sigue siendo tarea separada.

## Adenda de cierre documental — 2026-10-06

Los checklists y párrafos de las secciones anteriores son cortes cronológicos. Los estados vigentes son los de esta adenda y `RECONCILIACION_MARCADORES_BALONCESTO_2026-10-06.md`: reconciliación oficial de baloncesto terminada; 219 aliases ESPN normalizados; consumidores principales excluyen outcomes no acreditados. El gate adicional para apuestas sin `partido_id` queda en revisión/CI y no reescribe apuestas. Corte P&L: 114/181 binarias (115/182 totales) no evaluables; 67 binarias aritméticamente coherentes, pero aún sin certificación externa; ocho discrepancias deportivas continúan sin re-liquidar.

Pendientes vigentes: inventario de consumidores KPI/caches residuales; resolución causal del stake/unidad, cuota/fuente/timestamp y las liquidaciones discrepantes; cotejo NBA con un proveedor independiente de ESPN; una fuente fútbol permitida que cubra calendario/resultados y campos por mercado; outcomes y frescura recientes; nueva cadena prospectiva inmutable; walk-forward real; confidence/odds con muestra suficiente; capa KPI canónica/observabilidad; y mantenimiento A5/H4/H12. Los 2.558 pares NBA raw no son temporalmente certificados. No se imputan los 34 registros Euroliga sin resultado oficial ni se declara ROI, calibración o rendimiento prospectivo.

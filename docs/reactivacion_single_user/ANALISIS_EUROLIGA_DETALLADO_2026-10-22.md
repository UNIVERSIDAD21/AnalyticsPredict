# Historial detallado y diagnóstico del análisis Euroliga — 2026-10-22

## Problema observado

La pantalla compartía la tarjeta general de resultados con NBA, pero la respuesta Euroliga solo adjuntaba diez marcadores resumidos y el historial detallado disponible consultaba el endpoint estadístico NBA. Por ello no se mostraban periodos ni un historial de equipo equivalente; a la vez, la tarjeta de forma presentaba indicadores que no existen en el contrato Euro como `N/D`.

## Cambio

- El contexto Euroliga devuelve, por equipo, hasta 50 finales anteriores al corte del fixture. Para cada partido conserva resultado y puntos acumulados en regulación, desglose Q1–Q4, puntos de OT y marcador final. La prórroga no se mezcla con los 40 minutos de regulación.
- La interfaz mantiene la forma reciente de diez partidos y añade una sección propia con selector de 10/25/50, filtro de sede y resúmenes V-E-D, PF, PC y balance en regulación. Presenta la muestra de la temporada reciente del modelo separada entre local y visitante. En móvil, la tabla puede desplazarse horizontalmente dentro de su contenedor.
- Se añaden método y trazabilidad: versión, dataset, corte, tamaños TRAIN/CAL/EVAL y métricas retrospectivas por periodo (MAE frente a media de liga, Brier RAW frente a 0,25 y cobertura del intervalo nominal de 80 %).
- La forma Euroliga ya no imprime “vs. temporada”, tendencia o descanso como campos `N/D` que el motor no calcula. Tampoco se invoca la consulta de historial NBA.

## Límites metodológicos y de alcance

El corte usa fecha canónica y excluye partidos con fecha igual o posterior al fixture. Al no existir hora de kickoff en este contrato, tampoco incorpora otro encuentro del mismo día. H2H conserva marcadores finales de la fuente y puede incluir OT; la sección nueva etiqueta por separado regulación y final.

Las métricas EVAL pertenecen al candidato evaluado con separación temporal; no certifican el refit final servido. La métrica Brier usa una línea de referencia fijada desde TRAIN para poder describir la clasificación binaria de EVAL; no corresponde necesariamente a la línea solicitada por el usuario. CAL estima dispersión, no es calibrador. La evaluación es retrospectiva, hay 0 casos prospectivos independientes y la etiqueta vigente sigue **NO CERTIFICADO**. No se afirma paridad de eficacia con NBA.

Euroliga permanece en su motor, artefacto, fixtures y journal propios. No se copian métricas, estadísticas, calibradores ni endpoints NBA; no se agregan cuotas, sizing, picks o stakes. El endpoint de análisis mantiene su semántica existente de trazar cada consulta, pero esta corrección no generó ningún análisis productivo.

## Validación

- Backend focalizado: **35 passed, 1 deselected**; cubre fixtures estrictamente anteriores, máximo de 50, cuartos/OT/final, agregados de temporada y contrato de evaluación.
- Frontend: **62 pruebas passed**, lint y compilación de producción.
- Servicio local: GET salud backend HTTP 200, página `/baloncesto?liga=euroliga` HTTP 200 y `/api/euroliga/estado` HTTP 200. Estado observado del artefacto: `euro-f9cc361e255b91196acc`, 2.591 partidos, 29 equipos, corte 2026-10-21, TRAIN 1.798, CAL 330 (292 útiles), EVAL 463 (327 evaluados), 0 prospectivos independientes; certificación **NO_CERTIFICADO**. Estas lecturas no ejecutan un análisis.
- Revisión visual desktop 1440 px y móvil 390 px con fixture sintético marcado en pantalla como **“Preview sintético (no guardado)”**; no hubo desbordamiento horizontal del documento. La inspección valida layout, no datos reales ni salida predictiva.
- Sin POST productivo, DML/DDL, entrenamiento, recalibración, modificación de modelos/cohortes, ni cambios de apuestas. Se mantienen los servicios locales existentes.

## Evidencia y publicación

Las capturas y logs de pruebas se adjuntan en la entrega externa `ANALISIS_EUROLIGA_DETALLADO_2026-10-22/`. El SHA final y estado de CI se consignan allí después de publicar y completar los controles del commit.

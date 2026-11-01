# Actualización de resultados NBA — 2026-10-26

## Aplicación confirmada

Por solicitud expresa del propietario, se actualizaron **30 partidos existentes**
NBA REG del 21–25 octubre2026 que aún tenían puntos de calendario en cero. Sin
inserciones, eliminaciones ni cambio de IDs; un partido incluye prórroga. Se
conservaron las nueve citas del 26 todavía programadas y todos los demás datos.
COMMIT SQL confirmado a las **16:43:15 UTC / 11:43:15 Colombia**. No repetir el lote.

## Contraste y criterios

ESPN Scoreboard NBA por día, 1–26 octubre inclusivo: 26 respuestas completas,
119 eventos únicos = 110 finales de la fuente + 9 programados. Un final es una
exhibición Portland–London Lions (`401914130`), fuera del dominio de dos equipos
NBA, y se aparta. Los 109 finales NBA son 66 PRE y 43 REG: 79 ya coincidían y 30
requerían actualizar Q1–Q4, OT, FT y ganador. Todos coincidieron después.

Se reutilizaron `event_to_record`, `upsert_records` y `update_ingestion_state` de
`scripts/actualizar_partidos_nba.py`, sobre un plan de diferencia de campos fijo.
El dry-run de ese módulo cuenta identidades existentes, no cuántas tienen resultados
pendientes; la comparación previa de campos identifica las treinta actualizaciones.
El escritor recibió solo esas treinta filas. La clave del job NBA conserva el rango
y los conteos reales; no establece una actualización automática futura.

Validación de ambos IDs ESPN, competición, temporada2026–2027, equipos, localía y
fecha para el lote; puntos enteros observados, ganador y coherencia Q1–Q4/OT/FT.
No se equipara estado prepartido con la fase de pretemporada: las treinta son REG.

Los 35 finales PRE legacy fechados con el día UTC, en lugar del día Nueva York,
conservan su fecha canónica: ID/lados/fase/score coinciden y el desfase queda
explicitado. No se amplió la operación a una reescritura histórica de fechas.
Las 67 filas NBA invalidadas históricas permanecen apartadas y sin modificar.

## Respaldo, ensayo y verificación

- Backup completo custom, PostgreSQL18.6, 7.149.685 bytes, SHA-256 privado;
  restaurado en PostgreSQL18.6 propio en loopback55439 con esquema/triggers nativos.
- Seis casos: restauración exacta30+job; aplicación+rollback; fallo parcial tras
  cinco filas revierte todo; aplicación local persistida; bloqueo de reaplicación;
  restauración lógica acotada exacta. También 12 pruebas existentes del actualizador.
- Ensayo en la BD real con rollback forzado, seguido de lectura nueva: treinta
  originales y job exactos, sin alteración de las 49 comprobaciones protegidas.
- Aplicación única, atómica, con bloqueos de filas, before-images y hashes de fuente,
  plan y ejecutable. Respaldo bajo lock y candado guardados antes del COMMIT;
  confirmación de aplicación solo tras su acuse.
- Postflight independiente solo SELECT sin importar el transformador de scores:
  109/109 finales con cuartos/OT/FT/ganador exactos, 30 IDs preservados, 79 filas
  coincidentes intactas, nueve programados intactos y segunda diferencia cero.
- 49 huellas fuera del lote iguales entre ensayo/aplicación/postflight. El respaldo
  y el ensayo tienen altas analíticas concurrentes ajenas al lote en tres tablas
  (+4 analizadas, +2 versiones de ajuste, +4 predicciones); se preservaron usando
  baselines por transacción, sin atribuir esas altas a esta operación.
- Total NBA10614 filas; finales válidos con marcador10355. Censo literal NULL de
  todas las columnas exportado con denominadores, no solo los campos deportivos.

## Modelos y operación

El artefacto/cargado NBA sigue en versión2123, datos hasta14jun2026. Esta ingesta
no ajusta, entrena, calibra ni activa modelos; los datos nuevos quedan disponibles
para los análisis del usuario. Los ajustes por temporadas que la aplicación haga
al analizar siguen siendo un recorrido distinto de esta operación.

45 archivos de scrapers y 53 artefactos/journals/backups preservados por hash.
Cinco GET de salud/modelo/frontend y dos fixtures actualizados respondieron200.
No se ejecutaron POST de análisis ni resolución de apuestas, ni se repitió la
reparación histórica de99 registros. Servicios8000/5173 y PostgreSQL ajeno55432
preservados; PostgreSQL de restauración propio detenido al cierre. Sin navegador.

Sin cambios a ejecutables del producto; solo este documento y punteros de estado.
HEAD80ca327 sin commit/push ni CI remota nueva por la restricción vigente.

El contraste externo cubre octubre hasta el instante observado, no una
recertificación exhaustiva de ocho temporadas históricas ni precisión predictiva.
La descarga no convierte los encuentros aún no jugados en finales.

Entrega externa: `ACTUALIZACION_RESULTADOS_NBA_2026-10-26`, con plan/backup/recibos,
CSV de treinta partidos, fuente cruda, scripts completos, ensayos y SHA256SUMS.

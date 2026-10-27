# Agendas con horarios verificables y sincronización incremental

## Uso

- Baloncesto: `/baloncesto`; fútbol: `/futbol`.
- **Actualizar agenda** sólo consulta la BD. **Fuentes y sincronización** muestra la última verificación, cambios guardados y cobertura por competición.
- **Sincronizar fuentes** solicita al servicio local una ejecución acotada; `202 SOLICITADA` no equivale a actualización terminada. Consultar estado permite comprobar el resultado; un fallo no elimina el calendario previo.
- Horas en America/Bogota y agrupación por ese día cuando existe inicio acreditado. `Hora por confirmar` conserva día nominal, sin inventar medianoche UTC ni conversión COT exacta.

## Operación

El comando predeterminado prepara un plan READ ONLY:

```bash
backend/.venv/bin/python backend/scripts/sincronizar_agendas.py
```

La operación respaldada requiere `--aplicar`. La primera instalación añade `--migrar` **después de restaurar el respaldo y ensayar la operación en un clon**. La migración es aditiva y transaccional; no altera pesos, fechas canónicas de baloncesto ni contratos financieros.

Plantillas: `ops/systemd/analyticspredict-agendas.service` y `.timer`. Se instalan como unidades **del usuario**, no del sistema; ejecutan a las 06:00 y 18:00 America/Bogota, con recuperación de un disparo perdido y desfase máximo de cinco minutos. Requieren la ruta activa del checkout y su venv; credenciales mediante el `.env` existente del backend, nunca copiadas al unit ni a Git. `pg_dump`/`pg_restore` deben ser compatibles con PostgreSQL; el host puede configurar sus rutas y biblioteca en un drop-in local sin secretos.

```bash
systemctl --user status analyticspredict-agendas.timer
systemctl --user start analyticspredict-agendas.service
journalctl --user -u analyticspredict-agendas.service -n 30
systemctl --user disable --now analyticspredict-agendas.timer
```

La última orden detiene sólo el timer, no una ejecución activa. No se confunde instalar plantillas con timer operativo: el acta externa acredita instalación, próxima ejecución y prueba real del host.

Estado, caché, planes, recibos y respaldos privados viven en `~/.local/share/analyticspredict/agenda-sinc/`. `AP_AGENDA_ESTADO` permite aislar un ensayo. Revisar espacio periódicamente y archivar respaldos verificados; no se borran automáticamente. Con menos de 300 MB libres o respaldo fallido se conserva la BD y se informa error. Cada respaldo nuevo comprueba su archivo, no afirma que haya sido restaurado automáticamente: la restauración completa inicial está ensayada y acreditada externamente.

## Contrato técnico

Una sola ejecución por flock de proceso y advisory lock transaccional. Inicio dinámico de cada ciclo: fútbol/NBA/Euroliga hasta dos **meses calendario**, WNBA tres. Revisa además ocho días de resultados y un día de guarda por zona en los scoreboards diarios; no es una recertificación de todo el archivo histórico. Recupera reprogramaciones por vínculos estables, aunque se alejen del día original. Una ausencia de un feed no cancela ni borra encuentros.

Transporte serial compartido, intervalo mínimo cinco segundos en operación, timeout conexión/lectura 5/20 s, máximo dos intentos y 400 solicitudes por ciclo. TTL 15–30 minutos en ventanas recientes, seis horas en las futuras; no repite ciclos terminados antes de 30 minutos. HTTP 401/403/redirect detiene ese origen, sin evasión. HTTP 429 persiste `Retry-After` y conserva datos. Un proceso interrumpido libera el lock; el estado lo identifica y el próximo ciclo reutiliza caché por SHA, sin un watermark que salte errores. Snapshots nuevos se conservan por contenido, no destruyen revisiones anteriores.

Plan READ ONLY con before-images completas, hash, allowlist y diagnóstico. Antes del DML hay respaldo completo. Aplicación atómica con locks, comprobación de before-images, pipeline para no pagar un viaje de red por fila y validación de cada columna explícita después de los triggers. Revisiones append-only con antes/después/procedencia/observación y ledger del ciclo. El recibo PRE-COMMIT no acredita aplicación; sólo el recibo posterior al commit y el postflight lo hacen. Una segunda planificación del mismo snapshot produce cero operaciones deportivas y cero revisiones; el ledger sí registra cada verificación.

Fuentes/normalizadores existentes se reutilizan: ESPN scoreboards, contrato WNBA, identidades ESPN fútbol y crosswalks explícitos NBA/Euroliga. Euroliga usa API oficial V2 con `utcDate`, `confirmedDate`, `confirmedHour` y validación de offset local. No convierte `date` sin zona en UTC. Cuatro periodos y OT se validan contra FT; fútbol ET/tanda exige summary y desglose explícitos. Ausencias permanecen NULL/N/D. El catálogo legacy de baloncesto exige ceros en fixtures nuevos: son placeholders técnicos, no resultados; nunca se muestran como finales.

Horarios/estados exactos viven en `horarios_baloncesto`/`horarios_futbol`. El enum legacy de fútbol no tiene DEMORADO: el estado preciso vive en metadatos y lo consumen agenda/análisis, sin renombrarlo como una suspensión. No se modifican apuestas ni se resuelven outcomes financieros durante la sincronización. Finales contradictorios, identidades ambiguas, clubes sin crosswalk y horas TBD se apartan; el informe mantiene el motivo. No se cambia una competición legacy mal clasificada automáticamente.

## Temporalidad de los motores

Inicio acreditado realmente futuro y estado PROGRAMADO: prepartido con su motor. Inicio exacto o anterior, estado terminal o hora insuficiente: reconstrucción explícita, solo consulta, sin registro prospectivo/financiero. Los estados atrasados no convierten un pendiente en final ni impiden consultar el pasado. Los partidos cancelados/aplazados futuros no se presentan como un prepartido disponible.

NBA/Euroliga mantienen corte conservador anterior al día canónico, limitado además al reloj real si el día nominal es futuro sin hora. Fútbol sin hora usa un corte conservador previo al día fuente, limitado al reloj de consulta, sin modificar su fecha guardada ni la del DTO. Contexto y datos del refit respetan el mismo corte. WNBA mantiene sus IDs/vínculos y motor independiente. NBA histórico son 48 minutos de regulación sin OT; Euroliga 40 sin OT; WNBA conserva la semántica PRE/OT y cortes de su propio contrato. La corrección visual de la agenda no comparte pesos ni acredita calibración.

## Primer corte de fuentes: 26 de octubre

230 ventanas consultadas, más comprobación oficial V2 de Euroliga (380/380 eventos del feed). 1.387 eventos aceptados en el alcance, 198 incidencias: 118 altas sin hora, seis NBA con equipo TBD, tres con temporada FA Cup no acreditada y 71 con identidades de clubes sin crosswalk. No son 198 partidos certificados como ausentes.

Metadatos de hora: NBA435, Euroliga130 y fútbol816. Plan de 2.267 operaciones incluye 260 altas canónicas de baloncesto, nueve finales Euroliga existentes completados, 246 altas y 120 actualizaciones fútbol, 246 vínculos nuevos, tres altas y dos revisiones de fixtures WNBA. No se reaplican los 30 resultados NBA ni las reparaciones analíticas anteriores.

La cobertura disponible no equivale a calendario íntegro publicado. NBA tiene 392 eventos de hoy/futuros con hora hasta 26-dic COT; Euroliga120 hasta23-dic; WNBA3 hasta31-oct (último condicional), sin publicación íntegra 2027 acreditada. Fútbol varía por competición, con horas pendientes y clubes de copas sin identidad canónica: tabla completa y snapshots en el informe externo. Consultar hasta una fecha no demuestra que la fuente haya publicado todos los encuentros de ese rango.

## Verificación y límites

Suite sintética PostgreSQL, pruebas de exactitud al inicio/medianoche/zona, conservación de ID/fecha, reprogramación lejana, final WNBA vinculado, respuesta tardía, rollback SQL, error intermedio, before-image, transporte/cache/429 y separación consulta/sincronización. Build y UI reales escritorio/móvil se acreditan externamente por SHA; los conteos de esta entrega no se suman a suites antiguas de árboles mezclados.

El primer ensayo remoto serial se interrumpió deliberadamente por latencia de viajes SQL, sin commit. Se acreditó su rollback con las filas originales y ausencia de DDL, y se sustituyó sólo el transporte SQL por lotes. El pipeline pasó el nuevo ensayo en clon y rollback real: se aplicaron una sola vez las 2.267 operaciones, con 49 huellas fuera del lote iguales. El postflight independiente y el CI del SHA exacto constan en el acta externa. Los artefactos, respaldos y recibos íntegros están fuera del repositorio en `AGENDA_SINCRONIZACION_VALIDACION_2026-10-26`.

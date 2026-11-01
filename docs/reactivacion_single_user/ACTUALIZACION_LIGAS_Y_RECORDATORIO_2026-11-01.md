# Actualización incremental y recordatorio por liga

## Contrato visible

En las agendas de baloncesto y el catálogo de fútbol se muestra, sin desplegar
el detalle, la última actualización integral **completa de todas las ligas**
acreditada en PostgreSQL y la última revisión general con su estado. Si no existe
recibo integral completo, se muestra «sin acreditar»; una escritura reciente de
NBA, una descarga o un ciclo parcial no certifican el resto de competiciones.

El detalle enumera el catálogo completo de la BD: última verificación de agenda,
incidencias, último partido final, último final con estadísticas objetivo y
último cambio de datos. Para fútbol las estadísticas objetivo son corners,
tiros totales y al arco de ambos equipos; para baloncesto, cuartos/OT/FT coherentes.
Estos cortes no son una certificación de integridad del calendario ni de todos
los campos históricos. Los torneos históricos no se declaran atrasados sólo
por la edad de su último partido.

## Persistencia y lectura

`GET /api/agendas/sincronizacion` añade `actualizacion_ligas` sin alterar los
campos anteriores. Lee agregados canónicos y `sincronizaciones_agenda.informe`
en transacción READ ONLY. Los recibos SQL sobreviven al cambio de instalación.
En modo base no abre la BD; si falla la lectura devuelve frescura N/D y conserva
el acceso al calendario y los controles existentes. No descarga por render,
entrena, registra predicciones ni crea tareas automáticas.

El ledger distingue los ciclos comunes de calendario/resultados y los recibos
`tipo=ACTUALIZACION_INTEGRAL` con la revisión de estadísticas por competición.
Sólo un recibo integral `COMPLETO` y `todas_ligas_verificadas=true` acredita la
fecha general completa. Los intentos parciales posteriores no borran ese dato.
Los recibos deben reflejar fuentes, ventanas, postflight y pendientes reales;
no se insertan fechas completas por terminar de ejecutar un comando.

## Operación solicitada

La actualización del 1 de noviembre se ejecuta incrementalmente sobre el
PostgreSQL local habitual, sin Neon: sincronizador común primero; scrapers y
resolver existente después, con identidad exacta y campos ausentes conservados
como NULL. Respaldo restaurado, ensayo rollback, comparación del plan y
postflight antes de acreditar cada lote. Un HTTP 401/403 detiene esa fuente,
sin evasión; las restantes fuentes configuradas pueden continuar.

Las cifras finales, fuentes inaccesibles, respaldo, manifiestos y recibos se
entregan fuera del producto en la carpeta fechada del encargo. La ingesta no
actualiza modelos ni modifica las condiciones de calibración y prospectiva.

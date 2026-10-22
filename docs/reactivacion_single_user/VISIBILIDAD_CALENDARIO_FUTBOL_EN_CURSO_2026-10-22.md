# Visibilidad de partidos de fútbol durante el día — 2026-10-22

## Problema reproducido

La pantalla `/futbol` obtiene su selector de `GET /api/futbol/partidos/proximos`. El filtro temporal de ese endpoint empezaba en la hora actual. Por ello, un partido con estado almacenado `PROGRAMADO` desaparecía tras su kickoff, aunque el endpoint `/hoy` aún lo devolviera.

En la lectura del 22/10/2026 a las 17:10 UTC (12:10 en Bogotá), Juventus–Stade Rennais estaba en la respuesta de `/hoy`, competición UEFA Europa League, kickoff `2026-10-22T16:45:00Z` (11:45 COT) y estado `PROGRAMADO`. No aparecía en `/proximos` antes del cambio. El selector reprodujo la ausencia; la búsqueda de hoy halló 36 partidos.

## Corrección

- El inicio de la consulta ahora es la medianoche del día actual en `America/Bogota`, manteniendo el mismo extremo final exclusivo del horizonte.
- El filtro acepta `PROGRAMADO` y los estados activos presentes en el enum de la BD: `EN_VIVO`, `PRIMER_TIEMPO`, `ENTRETIEMPO`, `SEGUNDO_TIEMPO`, `TIEMPO_EXTRA` y `PENALES`. Estados terminales, suspendidos, pospuestos y cancelados siguen fuera de la lista.
- La pantalla muestra el estado almacenado; no infiere “en vivo” por hora. El producto no tiene un refresco automático de marcador/estado.

## Verificación

- Después de la corrección, `GET /api/futbol/partidos/proximos?dias=7&tamano=100` devolvió 94 partidos; 36 son del 22/10. Juventus–Stade Rennais aparece como UEFA Europa League, kickoff 16:45 UTC, estado `PROGRAMADO`.
- En Chrome, `/futbol` mostró `Seleccionar partido (94 disponibles)` y la opción `Juventus vs Stade Rennais`; se seleccionó para dejarla visible al Jefe. La UI muestra 11:45 a. m. COT.
- Consulta de enum en transacción READ ONLY confirmó los valores activos listados arriba.
- Pruebas backend focalizadas de rango, estados y endpoint; sin análisis de partido.
- Solo GET/SELECT; sin POST, ingesta, cambios de BD, modelo, predicción o journal.

## Límite explícito

La corrección evita que los fixtures del día desaparezcan al pasar la hora programada y permite estados live si la fuente los actualiza. No demuestra que el partido continúe en juego ni añade marcador en vivo: el registro observado permanece `PROGRAMADO` y no se validó un estado externo independiente.

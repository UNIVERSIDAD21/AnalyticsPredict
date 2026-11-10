# Copa BetPlay separada de la Primera A

La ausencia del 10 de noviembre no era un filtro horario ni la cuarentena de
Liga del día 8: faltaba Copa BetPlay en el catálogo y en el mapa de proveedores.
`col.copa` se resuelve a `COL_COPA`; `col.1` sigue siendo `COL_PRIMERAA`.

La migración `backend/migrations/2026-11-10_copa_colombia.sql` registra solamente
competición, temporada 2026 y crosswalk de temporada, dentro de la transacción
del operador. Es idempotente y rechaza identidades previas incompatibles. No
descarga ni crea partidos al migrar; no añade equipos por similitud.

El 10/11/2026, DIMAYOR y ESPN acreditan Internacional de Bogotá–América a las
18:30 y Once Caldas–Atlético Nacional a las 20:30, hora de Colombia. Este último
empieza el 11 en UTC, pero pertenece al día 10 en la agenda. El reparador acotado
usa el planificador habitual, snapshot/hash, crosswalks existentes, respaldo,
ensayo y postflight. Conserva NULL para resultados y estadísticas no observados.

Fuente oficial: <https://dimayor.com.co/> y
<https://dimayor.com.co/2026/11/09/designaciones-arbitrales-semifinales-ida-de-la-copa-betplay-dimayor-2026/>.

La interfaz obtiene competiciones por SQL: basta actualizar la agenda o recargar
y elegir **Copa BetPlay · Colombia**, no Categoría Primera A. No requiere
reiniciar la API. El mapa nuevo se carga en la siguiente ejecución manual del
actualizador. No inicia actualizaciones automáticas ni una ingesta multiliga.

La carga inicial se limita a estos dos encuentros. No incorpora el histórico de
Copa, Primera B o fútbol femenino, ni certifica cobertura futura. Que el partido
sea seleccionable no acredita muestra/modelo calibrado; no se entrena ni emite
un análisis para comprobar la agenda.

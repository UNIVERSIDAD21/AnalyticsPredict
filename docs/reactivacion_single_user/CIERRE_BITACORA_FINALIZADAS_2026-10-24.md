# Cierre verificable de apuestas finalizadas — 2026-10-24

## Diagnóstico

El censo inicial READ ONLY encontró 26 pendientes: 13 apuestas NBA de 10 partidos
cuyos fixtures conservaban 0–0 y 13 de fútbol con finales/estadísticas disponibles.
No había pendientes Euroliga ni combinadas. El cierre general solo usaba el motor
NBA y no tenía una acción en la pantalla. Fútbol asignaba dos veces `resultado`
(estado textual y valor numérico), omitiendo la columna canónica `valor_real`.
Además convertía estadísticas NULL en cero. El motor NBA reabría apuestas del día
y bloqueaba cierres del mismo día aunque el final estuviera acreditado.

## Contrato actual

- `POST /api/bitacora/resolver` completa apuestas **simples** NBA, Euroliga y fútbol.
  Botón **Completar finalizadas** en Bitácora; Refrescar sigue siendo solo lectura.
- No hay DML en GET, descarga implícita, cron ni actualización live automática.
  El botón usa resultados guardados y explica los motivos de los pendientes.
- NBA: cuartos/total coherentes, ganador válido; COMPLETO incluye OT.
- Euroliga: mismos requisitos de final; COMPLETO suma Q1–Q4, **sin OT**.
- Fútbol: `FINALIZADO`, válido y métrica exacta por lado/periodo. GOLES_FT usa
  regulación (mitades explícitas o FT sin ET acreditado); no añade prórroga/tanda.
  Córners/disparos FT con ET ambiguo quedan pendientes, no se reinterpretan como 90 min.
- NULL no equivale a cero. No se usan disparos FT para resolver una mitad.
  Líneas de cuarto asiáticas no soportadas quedan pendientes con motivo explícito.
- El outcome se puede completar sin cuota válida, pero `ganancia` queda NULL/N/D.
  No se sustituye una cuota cero por 1. El listado unificado acepta el importe NULL.
- Solo `PENDIENTE`: bloqueos `SKIP LOCKED`, savepoints por fila, UPDATE condicional,
  conteos después de actualizar e idempotencia. No reabre ni recalcula completadas.
  Entrada legacy `resolver_apuestas` sigue aislada a NBA incluso con `force=True`.
- `POST /api/futbol/apuestas/resolver` comparte el mismo motor y conserva legacy/v2.
  Combinadas mantienen su motor separado; este botón no las liquida.

## Reparación operativa autorizada

Consulta acotada ESPN a tres días para los 10 fixtures NBA vinculados. Se contrastan
ID exacto, competición, temporada, equipos/localía, fecha y cuartos/OT/final con el
adaptador existente. Solo se actualizan resultados de esos fixtures, sin altas.
El lote de cierres queda fijado a los 26 IDs iniciales: las apuestas/análisis nuevos
creados concurrentemente por el usuario se preservan y no se incluyen a ciegas.

Aplicados 26 cierres: 21 GANADA, 5 PERDIDA y 0 PUSH; 13 NBA y 13 fútbol, sin errores.
Ocho registros de fútbol tenían cuota cero: outcome completado e importe NULL.
Postflight independiente: cero cierres adicionales, tres pendientes nuevas de
partidos futuros. Dentro de la transacción, 14 huellas de tablas protegidas y 27
archivos de artefactos/journal permanecieron idénticos. Se registraron altas y
upserts concurrentes de análisis/predicciones del usuario entre snapshots, no
producidos por esta operación. Los ensayos inicialmente detenidos y sus logs se
conservan; el ensayo final confirmó rollback y la aplicación fue única.

Respaldos completos privados gzip 0600, ensayo transaccional con rollback, comprobación
de columnas permitidas y huellas de tablas/modelos/journals dentro de la transacción.
Postflight independiente READ ONLY y segunda simulación. Si el usuario crea/actualiza
predicciones entre snapshots, esa concurrencia se registra separadamente, sin
sobrescribirla ni atribuirla a la liquidación. Sin entrenamiento, calibración,
activación o modificación de cohortes por esta operación.

Evidencia y balance operativo final en entrega externa
`RESOLUCION_BITACORA_PENDIENTES_2026-10-24/` (no se incorporan datos personales al repo).

## Validación

Regresiones con PostgreSQL local sintético: escritura canónica fútbol, aislamiento
NBA/Euro con OT, cuota cero con outcome e importe NULL, final del día, idempotencia,
fila bloqueada, error aislado y lote restringido. Frontend verifica POST explícito,
contrato y error; lectura HTTP acepta un outcome completado con importe NULL.
La liquidación interna no certifica P&L ni eficacia predictiva; agregados siguen N/D.

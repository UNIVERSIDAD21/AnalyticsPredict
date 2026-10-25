# Ingesta local WNBA — 2026-10-25

Orden expresa: importar archivos suministrados por el propietario, rango
2019-01-01–2026-10-25, sin nuevas consultas ESPN. Esta persistencia no acredita
licencias upstream ni autoriza otras extracciones.

## Contrato

- `backend/ingesta_wnba.py`: verifica todo el manifiesto SHA-256, recorrido terminado,
  IDs, ventanas, temporada anual, estados, cuartos/OT/FT, empates previos a cada OT,
  ganador y estadísticas. No completa NULL ni modifica valores de fuente.
- `backend/scripts/importar_wnba.py`: validación sin BD, ensayo con rollback y
  respaldo `pg_dump` custom, aplicación condicionada al ensayo/backup y postflight
  READ ONLY. El llamador conserva la configuración protegida habitual.
- `backend/migrations/2026-10-25_ingesta_wnba.sql`: permite temporadas de año calendario
  mediante `es_anual=true` (por defecto false conserva el contrato NBA/Euro) y fase COPA.
- `equipos` y `equipos_baloncesto`: mismo UUID propio WNBA, mapeo ESPN restringido
  por competición, sin reutilizar UUID NBA aunque coincida el ID numérico ESPN.
  `W` + dos dígitos base36 es alias técnico, no abreviatura oficial; las colisiones
  se resuelven sin cambiar etiquetas previas. Mantiene el límite legacy de tres
  caracteres y no toca la vista de calibración dependiente. No infiere país/conferencia/ciudad.
- `temporadas_baloncesto`: nombres `2019`…`2026`, inicio=fin; no infiere fechas
  precisas, cierre de temporada ni activa modelos.
- `partidos_baloncesto`: solo finales válidos, con cuartos, OT agregado, FT, ganador,
  fase y procedencia. Mantiene sus puntos obligatorios; no recibe no-finales 0–0.
- `partidos_fuente_wnba`: todos los aceptados, inicio UTC, estado, fase, relaciones
  propias y JSONB original. Conserva regulación, cada OT, estadísticas válidas/NULL,
  incidencias y evidencias URL/fecha/hash. No finales quedan sin `partido_id` como
  pendientes de resultado canónico, pero sus datos están persistidos.
- `lotes_ingesta_wnba`: hashes por archivo, reporte original, cuarentena, pendientes
  de fuente y advertencias originales. Cuarentenados sin alta canónica por esta vía.

## Idempotencia y contadores

Clave: competición + ESPN + ID evento. IDs con otro payload, nombres ambiguos o
finales de otro ID que colisionan por temporada/fecha/fase/localía => rollback total,
sin fuzzy matching ni reemplazos. Se preserva la unicidad ESPN global de la tabla
compartida: colisión con otra liga aborta, no reasigna su fila.

`insertados` cuenta registros fuente y `resultados_insertados` finales canónicos.
`pendientes_resultado` es un subconjunto persistido en fuente, no filas perdidas.
Pendientes estadísticos de fuente son otro eje: un boxscore 404 no invalida el FT.
`actualizados=0` es deliberado; una revisión de cifras exige adjudicación explícita.
La entrada idéntica repetida no escribe datos ni cambia timestamps.

## Operación

Con `pg_dump`/`pg_restore` compatible en PATH, `DATABASE_URL` protegido y variables
`LOTE_LOCAL` y `ENTREGA` apuntando a carpetas fuera del repositorio:

```bash
backend/.venv/bin/python backend/scripts/importar_wnba.py \
  --entrada "$LOTE_LOCAL" --salida "$ENTREGA/validacion" --modo validar
backend/.venv/bin/python backend/scripts/importar_wnba.py \
  --entrada "$LOTE_LOCAL" --salida "$ENTREGA/ensayo" --modo ensayar
backend/.venv/bin/python backend/scripts/importar_wnba.py \
  --entrada "$LOTE_LOCAL" --salida "$ENTREGA/aplicacion" --modo aplicar \
  --ensayo "$ENTREGA/ensayo/reporte.json"
backend/.venv/bin/python backend/scripts/importar_wnba.py \
  --entrada "$LOTE_LOCAL" --salida "$ENTREGA/postflight" --modo verificar
```

Cada operación usa un directorio nuevo. Backup custom privado con hash; credencial
solo en entorno del hijo, nunca argv/log. Ensayo/backup alterado o baseline WNBA
cambiado bloquea aplicar. Transacción con advisory lock, timeouts y huellas ajenas,
apuestas/modelos antes/después; ensayo verifica rollback y repetición NO-OP.
Un reporte EN_CURSO tras interrupción no declara éxito: recuperar con `verificar`.

## Validación y límites

Carga autorizada ejecutada: 2.098 registros fuente insertados, 2.088 resultados
finales canónicos, cero ya existentes/actualizados, 21 participantes y ocho
temporadas. Diez no finales persistidos sin resultado; ocho cuarentenados omitidos
de las tablas canónicas. Dos boxscores ausentes conservan FT válido y estadísticas
NULL; diez campos apartados de cuatro partidos permanecen NULL con su motivo.
Respaldo completo restaurado localmente y huellas comparadas en la misma zona GMT.
Ensayo revertido y repetición inmediata NO-OP antes del commit de la carga.

Pruebas puras y PostgreSQL sintético reproducen restricciones legacy y verifican
NULL/cero, aislamiento de IDs NBA, año calendario, COPA, ID largo en abreviatura
legacy, conflictos de versiones/duplicados, rollback de DDL/datos y CLI con backup.
El ensayo real y la restauración del respaldo son controles operativos separados.

Los participantes incluyen invitados de pretemporada: su total no es el número de
franquicias WNBA. Cobertura no certificada contra calendario independiente.
Sin entrenar/activar/calibrar modelos ni añadir WNBA a interfaz de análisis.
El trabajo local previo de siete archivos del scraper se preserva fuera del commit.
Evidencias y conteos medidos: entrega privada `INGESTA_WNBA_2019_2026_2026-10-25`.

# Goles y córners por mitades ESPN — 2026-10-16

Orden: ejecutar los frentes pendientes, sin inventar tiempos desde un FT.
Sondeo de la cohorte completa de200finales ESPN ya vinculados al catálogo:
**200/200** resúmenes contienen exactamente dos `linescores` por equipo, con
`format.regulation.periods=2`, `slug=half`, y suma igual al FT acreditado.
Son valores explícitos por mitad, no FT partido por dos ni un HT inferido.

`servicios/tiempos_espn_futbol.py` exige ID/competición de evento, local/visitante,
identidades ESPN, inicioUTC y FT exactos; rechaza ausencias, cambio de marcador,
periodos adicionales, orden incompatible y no-finales. Conserva ceros reales.
El CLI vuelve a interpretar el JSON crudo y compara todos los valores/hash antes
de planificar escritura. Por defecto solo SELECT/READONLY, sin entrenamiento.

La migración prepara una tabla de observaciones separada con hash del payload,
instante de observación, contrato y vínculo. Las capturas FT/vínculos originales
y sus hashes no se reescriben. La aplicación es atómica/idempotente, completa solo
ocho campos de goles/córners por mitad y actualizado_en; no sobrescribe contradicciones,
FT/tiros, identidades, datos_completos, apuestas, predicciones o modelos.
El trigger canónico sí deriva `datos_corners_completos`:200filas false→true al
existir sus cuatro mitades. Se verificó su regla y el resto del catálogo contra
backup/huellas; no se fuerza el flag manualmente ni se usa como sustituto de gates.

Extensión V2: los200eventos también declaran cronología `full`, secuencias de
comentario continuas y límites tipados en `keyEvents`. Se cuentan únicamente
jugadas `corner-awarded` con ID único, equipo exacto y periodo1/2 explícito;
wallclock debe caer entre los límites ordenados de su mitad. Los totales de ambos
equipos deben conciliar con boxscore y FT canónico. No se reparten córners FT ni
se asignan periodos leyendo texto libre. Ausencias/contradicciones rechazan el lote.
El contrato V1 de solo goles sigue admitido; V2 acredita también córners.
Esta fuente **no** acredita independenciaNBA. Se aplicó a Neon tras backup/preflight, ensayo DDL+DML con rollback y CI4/4verde.
Aplicación200/200, reaplicación0/0 y postflight independiente completos. El primer
postflight detectó el flag derivado del trigger, se detuvo la evaluación y se
reconcilió sin DML adicional; log original conservado. La evaluación posterior
bajo el mismo protocolo da618EVAL/familia y ninguna apta; no se activó fútbol.
Ver `SIETE_FRENTES_2026-10-16.md`. Aplicar datos no acredita eficacia.

Evidencias externas: `CIERRE_SIETE_FRENTES_2026-10-16/M09_FUENTES`, con200JSONcrudos,
cohorte exacta, reporte, prueba read-only y logs. No hay snapshots/capturas NBA nuevos.

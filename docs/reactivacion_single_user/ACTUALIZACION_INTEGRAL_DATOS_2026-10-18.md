# Actualización enero–octubre — 2026-10-18

## Alcance y resultado

Orden del propietario: corregir finales que seguían programados y recuperar los
partidos faltantes del 1 de enero al 18 de octubre de 2026. Neon permite las
lecturas y escrituras necesarias; se comprobó con privilegios efectivos y una
escritura revertida. No fue necesario ampliar permisos ni cambiar autenticación.

Se revisaron las 12 competiciones de fútbol ya configuradas: Premier, LaLiga,
Serie A, Bundesliga, Ligue 1, FA Cup, Copa del Rey, Coppa Italia, Coupe de France,
Champions, Europa y Conference; además NBA y Euroliga. No es una auditoría de
todas las competiciones del mundo ni de años anteriores.

| Dominio | Finales de fuente contrastados | Altas | Actualizaciones |
|---|---:|---:|---:|
| Fútbol | 1.758 | 273 | 108 |
| NBA | 891 | 18 | 6 fases REG→POST, play-in ESPN tipo 5 |
| Euroliga | 279 | 183 | 0 resultados históricos |
| Total | 2.928 | 474 | 114 |

Los 108 cambios de fútbol son 44 finales recientes, 38 programados históricos y
26 conciliaciones explícitas de finales/calendario/prórroga/penales. Se actualiza
la fila existente cuando corresponde; no se inserta otro partido por un cambio
de estado. De los 337 cambios integrales posteriores a los primeros 44,
336 tienen periodos explícitos válidos. Se añadieron 70 clubes de fútbol y un
club de Euroliga con identidad de fuente revisada; no se inventaron países o
afiliaciones ausentes ni se modificó la afiliación actual de clubes históricos.

## Estado medido tras aplicar

| Dominio | Registros canónicos | Último final |
|---|---:|---|
| Fútbol | 25.118, de ellos 24.593 finales válidos con goles FT | 18/10/2026 |
| NBA | 10.379 | 17/10/2026 UTC, jornada 16/10 Bogotá |
| Euroliga | 2.672 | 16/10/2026 |

Fútbol conserva calendario hasta el 30 de noviembre; los 255 programados futuros
observados tienen goles FT NULL, no ceros ficticios. Los 2.928 finales de las
fuentes archivadas están conciliados por identidad y marcador. En esa cohorte
no quedan finales de fútbol etiquetados PROGRAMADO. Es cobertura frente a las
fuentes consultadas, no una garantía de exhaustividad de esos proveedores.
Consulta residual adicional: cero filas fútbol PROGRAMADO entre enero y el
18 de octubre. Permanecen 25 finales antiguos sin goles FT de 2019–2023, fuera
del periodo solicitado; no se rellenaron ni contaron como finales evaluables.

NBA queda en 66 PRE, 9.579 REG y 734 POST. Son conteos de filas, no todos elegibles
para entrenar: permanecen 67 registros NBA invalidados anteriores. Se excluyeron
explícitamente cuatro minijuegos All-Star y una exhibición con London Lions.
No se mezclan esos eventos con la NBA canónica. Euroliga conserva separado su
dominio; la temporada 2025–2026 queda cerrada antes de activar 2026–2027.

## Correcciones técnicas

- Adaptación de fuentes y CHECK de capturas de cinco a doce competiciones.
- Reconocimiento de finales AET/PEN, sin sumar la tanda al marcador del partido.
- Periodos, prórroga y tanda separados, incluyendo eliminatorias a dos vueltas;
  `ganador_id` sigue representando el ganador por goles, no el clasificado.
- Conciliación entre fuentes solo con manifiesto explícito, identidad exacta y
  SHA de la fila previa; se preserva el identificador Sofascore y su procedencia.
- Estadísticas previas se conservan si la nueva fuente no las acredita. Ningún
  flag genérico de completitud FT demuestra que haya córners por tiempos.
- Ingesta NBA reconoce play-in como POST y rechaza fases desconocidas. El estado
  de ingesta permite conservar la transacción del llamador sin commit interno.
- Adaptador oficial Euroliga valida clubes, temporada, fase, cuatro cuartos,
  prórrogas explícitas y FT; rechaza contradicciones y admite reaplicación sin altas.

## Controles y evidencias

Respaldo privado antes de cada cohorte, ensayo real con rollback verificado,
aplicación atómica por cohorte e invariantes antes/después. Reaplicación de fútbol
y Euroliga sin nuevas altas/actualizaciones; NBA nueva cohorte reconocida por
identidad en dry-run. Esto no afirma que todo upsert NBA legado sea un no-op.

El postflight independiente vuelve a comprobar 1.758 resultados fútbol, 891 NBA
y 279 Euro contra payloads archivados; en baloncesto compara directamente todos
los cuartos/OT/FT, no solo el transformador de ingesta. Once tablas de apuestas,
predicciones, modelos y prospectiva conservan sus huellas iniciales. Artefacto NBA
2123 SHA256 `c4a823d76cb608b21f9c12809379333221fd860f0605639f79c205c4b8f09283` intacto.

Suite PostgreSQL sintética: **875 pruebas backend aprobadas**, cero omitidas,
dos advertencias de deprecación. Frontend: **36 aprobadas**, lint/build correctos,
auditoría de producción sin vulnerabilidades. Publicación y resultado CI del SHA
final se acreditan en el acta externa, no por suposición.
Cinco GET ASGI reales respondieron HTTP200 (Estado, próximos, recientes, capturas
FA Cup y detalle del final con periodos desconocidos), con huellas intactas. Se
ejecutaron sin lifespan ni abrir servidores; no es una nueva revisión visual.

Entrega externa `ACTUALIZACION_INTEGRAL_ENERO_OCTUBRE_2026-10-18`: índices y raw,
catálogos revisados, planes originales, backups con hashes sin datos privados en
el producto, ensayos/aplicaciones/postflights, CSV por partido/mes y logs de pruebas.
Los respaldos son COPY-text de una columna JSON comprimido, no JSONL sin decodificar.

## Límites que permanecen

- Final Champions `401862897`: el proveedor contiene periodos negativos. FT 1–1
  y tanda 4–3 acreditados; mitades/ET y flag de ET desconocido quedan NULL. No se
  convierten valores inválidos en ceros ni se afirma completitud de ese desglose.
- Filas legacy ya completas se verifican sin normalizar masivamente sus horas.
  Esta actualización no certifica disponibilidad histórica ni temporalidad ML.
- Sin reentrenamiento, activación o reevaluación de modelos. Las métricas y
  coberturas del 16/10 son antecedentes de sus cohortes congeladas, no mediciones
  recalculadas con esta nueva base. Fútbol sigue con cero modelos ML activos.
- Prospectiva intacta: 15 snapshots, 9 outcomes PRE, cero independientes. No se
  resolvieron los pendientes ni se modificaron V1/V2/V3 después de observar resultados.
- P&L continúa N/D; eficacia **NO CERTIFICADA**. Ingestar juegos no acredita
  calibración, independencia ni rentabilidad.
- No se inicia servidor, cron, entrenamiento, despliegue ni contacto externo.
  El refresco es una ejecución puntual: el mero paso del tiempo no actualiza la BD.

Incidencias preservadas: HTTP429 de Euroliga se respetó con Retry-After y ritmo
serial; ensayos detectaron el orden del índice de temporada activa y el commit
interno del actualizador NBA. Todo se corrigió y ensayó con rollback antes de la
aplicación integral. Fallos del arnés/test y sus correcciones permanecen en logs;
no se atribuyeron a falta de permiso del propietario.

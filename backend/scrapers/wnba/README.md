# Scraper WNBA ESPN

CLI: `backend/scripts/scraper_wnba.py`. Contrato `espn_wnba_v1`, Python 3.12 y
`requests` ya incluidos en el backend. Funciona desde cualquier directorio en
Linux (el bloqueo usa `flock`). **No usa `.env`, PostgreSQL, modelos ni la API del
producto.** No añade WNBA al selector ni carga sus datos en tablas NBA/Euroliga.

## Uso

Desde la raíz del proyecto. Plan sin red, sin archivos ni BD:

```bash
backend/.venv/bin/python backend/scripts/scraper_wnba.py \
  --desde 2025-07-03 --hasta 2025-07-03
```

Extracción explícita de esa jornada; directorio externo persistente:

```bash
backend/.venv/bin/python backend/scripts/scraper_wnba.py \
  --desde 2025-07-03 --hasta 2025-07-03 \
  --fetch --estadisticas --max-requests 20 \
  --salida /home/erik-fuentes/AnalyticsPredict/datos-wnba
```

`--estadisticas` consulta el boxscore de cada final. Sin ese argumento, usa el
scoreboard y consulta summary únicamente si faltan cuartos. Los campos estadísticos
no publicados quedan NULL, no cero; no requiere estadísticas para aceptar un final
con marcador y periodos completos. El informe mide la cobertura campo por campo.
No procesa estadísticas individuales de jugadoras, lesiones, cuotas ni play-by-play.

Repetir la misma orden reanuda mediante caché con SHA-256 comprobado, sin duplicar
partidos ni sobrescribir ejecuciones anteriores. Para reproducir **sin red**:

```bash
backend/.venv/bin/python backend/scripts/scraper_wnba.py \
  --desde 2025-07-03 --hasta 2025-07-03 \
  --offline --estadisticas \
  --salida /home/erik-fuentes/AnalyticsPredict/datos-wnba
```

`--fetch --refresh` obtiene nuevas observaciones y conserva las anteriores.
No repara silenciosamente archivos alterados: detenerse e investigar el archivo;
si se decide descargar de nuevo, usar otra carpeta conservando la evidencia original.
La caché histórica caduca a las 24 horas; los feeds de hoy/futuro, a los 60 segundos.
Offline permite usar caché antigua, pero conserva su hora original de observación.

## Fechas y alcance

- `--desde` y `--hasta` son fechas **locales inclusivas**. Zona predeterminada:
  `America/Bogota`; `--zona` acepta otra zona IANA explícita.
- Se transforman a un intervalo UTC semiabierto. ESPN se consulta por día Eastern:
  puede requerirse un día vecino adicional para no perder un partido que todavía
  pertenece al día colombiano. Los eventos externos a la ventana no se exportan.
- Exporta `inicio_utc` e `inicio_colombia`, ambos ISO con offset. Una hora marcada
  por la fuente como no válida se aparta; no se inventa un kickoff.
- Formato soportado: temporadas **2006 en adelante**, cuatro cuartos de 10 minutos.
  No convierte las dos mitades del formato anterior a cuatro cuartos. Este límite
  de contrato NO acredita disponibilidad de ESPN para todos los años posteriores.
- Una petición diaria cubre ambos equipos: un registro por ID de partido, no dos
  registros centrados en cada equipo. La ventana máxima es 3661 días, pero manda
  además el presupuesto HTTP; no hay descarga de todo el histórico implícita.

## Contrato y calidad

1. Identidad estricta WNBA: slug `wnba`, liga ESPN `59`, UID de deporte/liga/evento,
   ID de competición, IDs de ambos equipos y localía explícita. Sin fuzzy matching.
2. Valida temporada, fecha con zona, estado/fase y consistencia entre event/competition.
   Estados o tipos desconocidos se apartan. `STD` conserva PRE/REG/POST;
   `CC` se exporta como **COPA**, aunque ESPN indique `season.type=2`.
3. Finales: cuatro periodos consecutivos, valores enteros no negativos, suma de
   periodos igual al FT, mismo número de periodos por lado, ganador concordante.
   Si hay OT, exige empate antes de **cada** prórroga y final sin empate.
4. Conserva Q1–Q4, total de regulación, lista de cada OT, OT acumulado y FT.
   No confundir ganador/total de regulación con resultado que incluye OT.
5. Programados/live/pospuestos/cancelados no se convierten en resultados finales:
   columnas de puntos y ganador exportadas NULL; el snapshot crudo conserva lo
   observado. `final_completo` no equivale a modelo listo ni a pronóstico certificado.
6. Summary solo enriquece el mismo evento, temporada, fecha, equipos/lados, estado
   y marcador. Incluso los cuartos parciales ya publicados deben concordar.
7. Boxscore: tiros anotados/intentos (campo, triples, libres), rebotes, asistencias,
   robos, tapones, pérdidas y faltas. Se validan relaciones de tiros/marcador y
   rebotes. Pérdidas de jugadoras, de equipo y totales son campos distintos.
8. Duplicados idénticos se consolidan con sus evidencias. Versiones contradictorias,
   cambios de fecha/localía o un final con inicio posterior a la observación se
   apartan, sin elegir arbitrariamente una versión.
9. JSONL conserva NULL; CSV usa celdas vacías y protege nombres/texto contra fórmulas
   de hoja de cálculo. Los IDs son **de ESPN**, no UUID canónicos de la BD.

## Red y reanudación

- Solo endpoints `scoreboard`/`summary` del host ESPN fijado en código; URLs no
  arbitrarias, sin autenticación, proxies/cookies del navegador ni impersonación.
- Peticiones seriales; intervalo predeterminado 1,5 s, mínimo 1,25 s. Timeouts de
  conexión/lectura 5/20 s, cuerpo máximo 8 MiB y control de tiempo del cuerpo.
- Hasta tres intentos ante timeout/conexión y 500/502/503/504 con backoff+jitter.
  Todos los intentos consumen `--max-requests` (predeterminado 1000, máximo 20000).
- 401/403/redirecciones: detención inmediata, sin evasión ni cambio de identidad.
  429: una espera con `Retry-After` válido y máximo 60 s; repetición, valor ausente,
  inválido o superior al presupuesto detienen la fuente. No se acorta la espera
  solicitada para reintentar antes de tiempo.
- No trata error HTTP/JSON/esquema como día vacío. Rechaza feeds con 500 eventos
  o recuento declarado discordante por posible truncamiento.
- Archivo crudo por SHA-256, observaciones inmutables por solicitud, escritura
  atómica con fsync y permisos 0600. Nuevos directorios 0700; lock de escritor único.
- Caché validada antes de reutilizarla; checkpoint por día y nuevo informe por
  ejecución. Al interrumpir guarda resultados parciales y ventanas pendientes.

## Archivos producidos

```text
salida/
  raw/<sha256>.json                 # bytes originales de respuestas JSON 200
  observaciones/<consulta>-<id>.json # URL, SHA, bytes y fecha de cada observación
  cache/<consulta>.json             # última referencia, no elimina versiones
  http.jsonl                       # intentos/status; sin cuerpos de error
  ejecuciones/<fecha>-<id>/
    partidos.jsonl                 # contrato, campos, estadísticas y procedencia
    partidos.csv
    cuarentena.jsonl               # ID, motivo y referencia al raw
    checkpoint.jsonl
    reporte.json                   # cobertura, contadores y ventanas pendientes
    SHA256SUMS                     # hashes de los cinco archivos de ejecución
```

Cada partido lleva `evidencia` con URL, SHA y timestamp original; las observaciones
usadas también están en el reporte. Verificar exports con `sha256sum -c SHA256SUMS`
desde la carpeta de ejecución. Los hashes de raws se comprueban al reanudar.

| Exit code | Significado |
|---|---|
| 0 | Plan correcto o todas las ventanas ESPN procesadas, sin cuarentena |
| 2 | Argumentos inválidos o ejecución completada con registros en cuarentena |
| 3 | Fuente, presupuesto, caché o archivo impiden completar la ejecución |
| 4 | Error interno inesperado; informe marcado como error, nunca como completo |
| 130 | Interrupción del operador con resultado parcial cuando es posible |

Código 0 no certifica que ESPN tenga todos los partidos del mundo real ni que todas
las estadísticas estén presentes. Revisar `cobertura_estadisticas`, fases, ventanas
vacías y procedencia. No hay consulta a una segunda fuente independiente.

## Comprobación y límites de esta entrega

Sondeo 24/10/2026 COT: feeds 01–02/07/2019, 01/07/2025 y 03/07/2025;
ocho finales únicos coherentes, incluyendo una final CC y un feed vacío.
Tres summaries contrastados inicialmente. Piloto de CLI 03/07/2025 en Colombia:
cinco finales, 16 métricas por lado presentes en los cinco, cero cuarentenas;
dos ventanas Eastern, cinco GET nuevos y dos respuestas archivadas reutilizadas.
Reproducción posterior offline y pruebas adversariales sintéticas sin BD/red.

La fuente es un endpoint web ESPN no acompañado aquí de un contrato API/SLA o
licencia de extracción masiva acreditada. Respetar términos y permisos aplicables;
HTTP 200 no los sustituye. No se ejecutó backfill de temporadas ni importación a BD.
Antes de una carga canónica hacen falta catálogo/mappings WNBA, alcance de carga,
ensayo, respaldo y postflight independientes. No se modifica NBA/Euroliga, no se
entrena, no se activa predictor y no se configura cron.

La mejora se demuestra con controles y pruebas, no con una afirmación de ser
«el mejor scraper» sin comparación objetiva. Diseño y revisión del anterior:
[informe técnico](../../../docs/reactivacion_single_user/SCRAPER_WNBA_2026-10-24.md).

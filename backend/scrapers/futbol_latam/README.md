# Argentina, Brasil y Colombia — ESPN a archivos

Tres ejecutables independientes, Python 3.12 y `requests` del entorno existente:

- `backend/scripts/scraper_argentina.py`
- `backend/scripts/scraper_brasil.py`
- `backend/scripts/scraper_colombia.py`

Comparten el motor de `scrapers/futbol_latam/`. No importan ni modifican MLS o WNBA,
no leen credenciales ni `.env` y no escriben en la BD ni entrenan modelos.
**No iniciar otra descarga masiva mientras sigue ejecutándose MLS.**

## Alcance de cada script

| País | Feed ESPN | ID validado | Alcance |
|---|---|---:|---|
| Argentina | `arg.1` | 745 | Primera División / Superliga / Liga Profesional y fases publicadas en ese feed |
| Argentina | `arg.copa_lpf` | 20243 | Copa de la Liga Profesional histórica |
| Argentina | `arg.copa_de_la_superliga` | 19264 | Copa de la Superliga histórica |
| Brasil | `bra.1` | 630 | Brasileirão Série A |
| Colombia | `col.1` | 650 | Primera A: Apertura, Clausura, cuadrangulares y finales publicados |

Argentina incluye los tres feeds de forma predeterminada, con identidad separada
por torneo y CSV consolidado. `--torneos principal` limita a `arg.1`. La Copa Diego
Maradona 2020 aparece en `arg.1` en el feed comprobado. **No se incluye Copa Argentina,
Copa do Brasil, Copa Colombia, divisiones inferiores, estatales, supercopas,
Libertadores ni Sudamericana.** Son otras competiciones, no otras temporadas.

No se infiere la temporada del año de la fecha: un partido de abril de 2019 puede
pertenecer a la temporada fuente 2018 (Superliga 2018/19). Se conserva año, slug de
fase y tipo opaco de temporada. La cobertura enumera también esas temporadas y los
años solicitados vacíos. Las etiquetas REG/POST/COPA/PRE/OTRA son una clasificación
conservadora; `fase_fuente` y `season_type_fuente` son la evidencia original.

## Comandos desde la raíz del proyecto

Ejecutar **uno por uno**, al terminar MLS:

```bash
backend/.venv/bin/python backend/scripts/scraper_argentina.py \
  --desde 2019-01-01 --hasta 2026-10-25 \
  --fetch --estadisticas --intervalo 5 --max-requests 20000 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/DESCARGA_ARGENTINA_2019_2026_2026-10-25"
```

```bash
backend/.venv/bin/python backend/scripts/scraper_brasil.py \
  --desde 2019-01-01 --hasta 2026-10-25 \
  --fetch --estadisticas --intervalo 5 --max-requests 20000 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/DESCARGA_BRASIL_2019_2026_2026-10-25"
```

```bash
backend/.venv/bin/python backend/scripts/scraper_colombia.py \
  --desde 2019-01-01 --hasta 2026-10-25 \
  --fetch --estadisticas --intervalo 5 --max-requests 20000 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/DESCARGA_COLOMBIA_2019_2026_2026-10-25"
```

Las fechas son inclusivas, `America/Bogota` por defecto; `--zona` permite cambiar
la zona de selección. Las fechas UTC y Colombia se conservan en la exportación.
Sin `--fetch` ni `--offline`, muestra un plan sin red y sin crear carpetas.

2019-01-01..2026-10-25 equivale a **94 consultas mensuales por feed**, no a 94
partidos. Argentina planifica 282 ventanas en sus tres feeds; Brasil y Colombia,
94 cada una. Un feed puede no tener eventos en muchos meses. La expansión diaria
es automática si hay indicios de truncamiento, HTTP 413 o exceso de bytes; un día
truncado queda pendiente y no se interpreta como vacío.

El presupuesto de 20.000 GET es conjunto por invocación, incluidos todos los
feeds y reintentos. Alcanzarlo produce INCOMPLETO, conserva los datos y permite
reanudar. No significa que se harán necesariamente 20.000 solicitudes.

## Datos que exporta

Por equipo local/visitante:

- Goles, córners (`wonCorners`), tiros al arco (`shotsOnTarget`), tiros totales
  (`totalShots`), amarillas, rojas, faltas y atajadas, cuando están publicados.
- Goles de primera/segunda mitad y de 90 minutos, cuando están acreditados.
- Goles de prórroga y tanda separados. Los penales de una tanda no se suman a goles
  del partido ni a tiros. No se confunde una tanda directa con prórroga de relleno.
- Goles globales de una eliminatoria, número de partido de la serie y ganador de
  serie cuando existe evidencia estructurada. El ganador del partido se calcula
  con su marcador; no se reemplaza por quien avanza por el global.
- IDs ESPN de evento y equipos, nombres, torneo, estado, temporada, fecha, sede,
  incidencias y referencias a las respuestas originales con SHA-256.

Los córners y tiros son del partido publicado y pueden incluir prórroga.
**No se fabrican córners o tiros por mitades ni se etiquetan como 90 minutos si
ESPN solo publica el total del encuentro.** Los raws completos quedan archivados
para revisar otras métricas que no estén normalizadas en el CSV.

Un faltante es NULL en JSONL y celda vacía en CSV; un cero publicado es cero.
Un partido no final no tiene goles/estadísticas finales inventados. Una métrica
inválida se aparta sin destruir otras métricas verificadas. Un summary de otro
partido, equipo, torneo, estado o marcador se rechaza sin sustituir el resultado
validado del scoreboard.

## Reanudación y red

Repetir el mismo comando reutiliza la caché verificada y reconstruye una nueva
ejecución sin duplicar filas. No concatena CSVs de ejecuciones anteriores ni mezcla
rangos o países. Las respuestas históricas antiguas no caducan; las recientes se
renuevan según la ventana. Para actualizaciones históricas explícitas, usar refresh.

- `--reintentar-pendientes`: observa de nuevo solo las URLs pendientes del informe
  anterior de cada torneo, reutilizando el resto. No omite las ventanas sin caché.
- `--refresh`: observa de nuevo todas las consultas del rango. Excluyente con el
  anterior; evitarlo para reanudar normalmente porque aumenta las solicitudes.
- `--offline`: reconstruye únicamente desde los archivos ya obtenidos, sin GET.
- Ctrl+C y SIGTERM solicitan un guardado ordenado. Tras SIGKILL o corte de energía,
  volver a ejecutar recupera las respuestas durables; puede repetirse el último GET.
- Exporta checkpoints cada 25 operaciones y después de 60 segundos al terminar una
  operación; configurable mediante `--checkpoint-cada`.
- Un único escritor por carpeta, escrituras atómicas/fsync y hashes de datos/exportación.

GET seriales, **5 segundos entre inicios** por defecto (mínimo permitido 3), cinco
intentos por consulta transitoria, backoff exponencial con jitter y hasta tres
rondas. Tres consultas transitorias fallidas consecutivas abren el circuito para
no insistir sobre una fuente posiblemente caída.

Los tres scripts comparten turnos y pausas por el directorio
`SALIDA/../.control_red_espn_latam`. Si las carpetas tienen distintos padres, usar
el mismo `--control-red /ruta/comun` para coordinar. El lock se mantiene durante
cada intercambio HTTP y se libera al morir el proceso.

**La MLS ya iniciada no participa de este control compartido.** Tampoco controla
otros programas o peticiones de la aplicación. Por eso la recomendación es descargar
una competición a la vez. No se rotan IP, proxies, cookies ni identidades.

- 429: guarda una pausa compartida de al menos 15 minutos y respeta un Retry-After
  más largo. Guarda el progreso y termina; no relanzar en bucle ni borrar la pausa.
- 401/403: guarda el progreso y una pausa compartida de una hora; revisar el acceso
  antes de reanudar. Esperar no garantiza que el acceso haya sido restablecido.
- Redirect: termina sin seguirlo automáticamente.
- 404 y errores de datos: registra el pendiente sin reintento infinito y sigue con
  otros encuentros. Conserva goles ya validados aunque falle el detalle.
- Timeout/5xx: reintentos acotados; si no recupera, conserva pendientes.

Ninguna configuración garantiza ausencia de bloqueos ni datos históricos completos.
No existe evasión del control de acceso. Los errores de almacenamiento/integridad
se informan; un error de disco puede impedir la última exportación.

## Archivos y estados

```text
SALIDA/
  identidad.json
  ultima_ejecucion.json                # apunta al consolidado más reciente
  ejecuciones/<fecha>-<id>/
    partidos.csv                      # todos los registros aceptados
    partidos_finales.csv              # solo finales válidos
    partidos_completos.csv             # finales con los seis campos principales de tiros/córners
    partidos.jsonl                    # datos, incidencias y procedencia
    cobertura_por_temporada.csv
    pendientes.jsonl
    cuarentena.jsonl
    advertencias.jsonl
    incidencias.jsonl
    checkpoint.jsonl
    reporte.json
    SHA256SUMS
  torneos/<slug>/
    raw/<sha256>.json
    observaciones/*.json
    cache/*.json
    http.jsonl
    ultima_ejecucion.json
    ejecuciones/<fecha>-<id>/...        # mismo juego de exports/informe por torneo
```

El reporte consolidado enlaza los informes de los torneos, con cobertura por campo
y temporada de cada uno. Incluye torneos aún no recorridos, estado del recorrido,
resultados finales, estadísticas completas, cuarentena y consultas pendientes.
Un CSV “completo” exige goles y córners/tiros al arco/tiros totales de ambos equipos;
no certifica que estén todas las métricas opcionales ni todos los partidos reales.

Si un ID aparece en varios feeds, queda señalado para revisión y no se fusionan
arbitrariamente sus identidades. Antes de ingerir se debe revisar esa advertencia.

| Código | Significado |
|---|---|
| 0 | COMPLETO_EN_VENTANA_ESPN o plan válido |
| 2 | COMPLETO_CON_INCIDENCIAS; revisar faltantes/cuarentena/avisos. Argparse también usa 2 para argumentos inválidos |
| 3 | INCOMPLETO: recorrido, presupuesto, acceso, red o almacenamiento |
| 4 | ERROR_INTERNO: revisar reporte |
| 130 | INTERRUMPIDO: reanudación disponible |

El proceso termina al completar el rango. No debería mantenerse ejecutándose para
siempre. Un recorrido completo acredita que se consultaron esas ventanas; no que
ESPN contenga todo el calendario o todas las estadísticas requeridas.

Para verificar integridad, dentro de una carpeta de ejecución:

```bash
sha256sum -c SHA256SUMS
```

Las descargas **no cargan la BD**. Para ingesta deben usarse datos finales elegibles,
con sus identidades de competición y temporadas, sin imputar ceros a faltantes.

## Pruebas

Desde la raíz del repositorio:

```bash
backend/.venv/bin/python -m pytest \
  backend/tests/scrapers/test_latam_base.py \
  backend/tests/scrapers/test_futbol_latam.py \
  backend/tests/scrapers/test_mls.py \
  backend/tests/scrapers/test_wnba.py -q
```

Cubre las cinco fuentes, rechazo de torneos ajenos, NULL/cero, temporadas con dos
años, fases colombianas, ida/vuelta, tandas, prórroga, HTTP, caché, interrupción,
expansión diaria, presupuesto conjunto entre torneos y coordinación real entre
procesos. Los pilotos de entrega contrastan respuestas reales de ESPN con replay
offline y manifiestos SHA-256; no equivalen al backfill completo 2019–2026.

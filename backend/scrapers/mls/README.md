# Scraper MLS ESPN

CLI `backend/scripts/scraper_mls.py`, Python 3.12 y `requests` ya disponibles en el
backend. Extrae archivos CSV/JSONL; no utiliza `.env`, BD, modelos ni la API del
producto. Es independiente del scraper e importador WNBA.

## Descargar 2019–2026

Desde la raíz de AnalyticsPredict:

```bash
backend/.venv/bin/python backend/scripts/scraper_mls.py \
  --desde 2019-01-01 \
  --hasta 2026-10-25 \
  --fetch --estadisticas \
  --intervalo 2.5 \
  --max-requests 20000 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/DESCARGA_MLS_2019_2026_2026-10-25"
```

Las estadísticas están activadas por defecto; `--estadisticas` lo hace explícito.
`--solo-resultados` evita summaries y se reserva para quien solo desea marcadores.
Sin `--fetch` ni `--offline`, muestra el plan y no crea archivos ni solicita red.
La salida debe estar fuera del repositorio del producto.

El rango se traduce a **94 meses de ESPN**, no a 94 partidos. Cada mes puede tener
muchos encuentros o ninguno. Las fechas solicitadas son locales inclusivas, zona
`America/Bogota` por defecto. Consulta los meses Eastern limítrofes necesarios,
pero exporta solo partidos cuyo inicio pertenece al intervalo solicitado.

Repetir el mismo comando reutiliza respuestas verificadas y consulta lo que falta,
sin duplicar filas ni sobrescribir ejecuciones anteriores. El histórico anterior
a los siete días recientes no caduca; los días recientes caducan a las 24 horas
y los meses/días actuales o futuros a los 60 segundos.

Para revisar solo consultas pendientes de la última ejecución, añade
`--reintentar-pendientes`: fuerza nuevas observaciones para esas URLs, reutilizando
lo demás. `--refresh` observa de nuevo todas las consultas y conserva los raws
anteriores. `--offline` reconstruye sin red con las respuestas ya archivadas.

## Qué se guarda

Un registro por ID ESPN, con IDs y nombres de ambos equipos, temporada, fase y
fecha UTC/Colombia. Incluye encuentros regulares y rondas de playoffs publicados
en `usa.1`; no añade otras competiciones como Leagues Cup, US Open Cup o Concacaf.
La liga se valida con slug `usa.1`, ID `770` y UID `s:600~l:770` (no con el número
que aparece en el archivo del logo). Los IDs de tipo de temporada son opacos y
cambian por año/ronda; se conserva el ID y se clasifica por `season.slug`.

Campos principales, para `local_` y `visitante_`:

| Campo | Significado |
|---|---|
| `goles` | Marcador del partido, incluye prórroga cuando la hubo; excluye tanda |
| `corners` | Tiros de esquina publicados en el boxscore |
| `tiros_al_arco` | `shotsOnTarget`; distintos de tiros totales |
| `tiros_totales` | `totalShots` |
| `goles_1t`, `goles_2t` | Mitades explícitas de summary, si están acreditadas |
| `goles_90` | Goles en regulación; no confundir con total después de prórroga |
| `goles_et` | Goles de prórroga acreditados, separados del tiempo reglamentario |
| `penales` | Goles de la tanda; nunca se suman a `goles` ni a tiros |
| `amarillas`, `rojas`, `faltas`, `atajes` | Métricas adicionales cuando están publicadas |

Los totales de córners/tiros pertenecen al partido publicado y pueden incluir
prórroga: no se etiquetan como exclusivos de 90 minutos ni se dividen por mitades
mediante suposiciones. `ganador_partido_id` y `ganador_tanda_id` son distintos.
Los IDs de fuente son de ESPN, no UUID canónicos de la BD.

Un faltante es NULL en JSONL y celda vacía en CSV. Un cero publicado se conserva.
Programados, aplazados, cancelados o en vivo no se convierten en resultados finales:
sus goles y estadísticas exportados son NULL. Horas no confirmadas se apartan
si el encuentro pertenece al rango, no por otros eventos ajenos del mismo mes.

## Calidad y cobertura

- Valida liga, identidad de evento/competición, IDs de equipos, localía, temporada,
  fecha, estado y coincidencia entre scoreboard y summary antes de enriquecer.
- Métricas enteras inválidas se apartan individualmente. Si tiros al arco superan
  a tiros totales, se aparta ese par, conservando otras métricas verificadas.
- Si faltan estadísticas o hay HTTP 404, conserva un marcador final validado,
  registra el detalle pendiente y continúa con los demás encuentros.
- Las mitades, prórroga y tanda se validan aparte; sus errores no eliminan córners
  y tiros válidos. No reemplaza mitades ya publicadas por otras contradictorias.
  ESPN puede rellenar con ceros periodos de prórroga no disputados: para tandas
  se contrasta el inicio de penales a 90/120 minutos y eventos explícitos de
  prórroga. Si no hay evidencia suficiente, `hubo_prorroga` queda NULL con aviso.
  Evidencias contradictorias se apartan; no se elige una arbitrariamente.
- Detecta versiones conflictivas del mismo ID, incluidas reprogramaciones fuera
  del rango; no elige silenciosamente una. Una repetición idéntica se consolida.
- Consultas mensuales con 500 eventos, recuentos discordantes, HTTP 413 o cuerpos
  excesivos se dividen en consultas diarias. Un mes solo queda recorrido cuando
  todas las consultas diarias necesarias fueron resueltas. Un día truncado queda
  pendiente, no se declara completo ni se interpreta como vacío.
- Reporta cobertura por campo y por temporada: presentes, denominador de finales
  y porcentaje. Que el recorrido termine no certifica cobertura histórica contra
  un calendario independiente, ni garantiza exactitud de cada dato de ESPN.

## Archivo y reanudación

```text
salida/
  raw/<sha256>.json
  observaciones/<consulta>-<id>.json
  cache/<consulta>.json
  http.jsonl
  ultima_ejecucion.json
  ejecuciones/<fecha>-<id>/
    partidos.csv                    # todos los registros aceptados
    partidos_finales.csv            # únicamente finales válidos
    partidos_completos.csv          # finales con los 6 campos de córners/tiros presentes
    partidos.jsonl                  # campos planos, incidencias y evidencias
    cobertura_por_temporada.csv
    pendientes.jsonl
    cuarentena.jsonl
    advertencias.jsonl
    incidencias.jsonl               # historia de fallos, incluidos los recuperados
    checkpoint.jsonl
    reporte.json
    SHA256SUMS
```

`partidos_completos.csv` exige goles válidos y córners, tiros al arco y tiros totales
para ambos equipos. No significa que todos los campos opcionales estén presentes.

Cada GET exitoso se archiva por SHA-256 y conserva su observación original. La
caché se verifica al reutilizarla. Escrituras atómicas con fsync y permisos
restrictivos, y lock de un único escritor por carpeta. No se repara una caché
alterada mediante sobrescritura silenciosa.

Exporta instantáneas cada 25 operaciones o al terminar una operación tras pasar
60 segundos (`--checkpoint-cada`, 1..1000). Ctrl+C y SIGTERM solicitan un guardado
ordenado. Después de un cierre abrupto/SIGKILL o corte de energía, repite el comando
para reconstruir desde los raws durables; el último HTTP en curso puede repetirse.
Un error de disco puede impedir la última exportación.

Para verificar una ejecución terminada, dentro de su carpeta:

```bash
sha256sum -c SHA256SUMS
```

## Red y estados finales

Peticiones seriales; intervalo predeterminado 2,5 s, mínimo 1,25 s. Cinco intentos
por consulta transitoria (`--intentos-http`, 1..8), espera exponencial con jitter,
hasta tres rondas en total (`--rondas`, 1..10) y 15 segundos entre rondas
(`--espera-rondas`, 0..60). Solo se repiten consultas transitorias pendientes.
Todos los intentos consumen el mismo presupuesto (`--max-requests`, 1..20000).
Los 404 y errores de datos no se repiten indefinidamente dentro de la ejecución.

401/403 y redirecciones detienen ordenadamente. Un primer 429 respeta Retry-After
válido de hasta 60 segundos; repetición o valor inválido requieren reanudar después.
No se evaden controles de acceso ni se cambian identidades. Los errores de
integridad, presupuesto, almacenamiento o programación tampoco se ocultan como éxito.

| Código | Estado |
|---|---|
| 0 | `COMPLETO_EN_VENTANA_ESPN`: recorrido sin incidencias, o plan válido |
| 2 | `COMPLETO_CON_INCIDENCIAS`: recorrido terminado con detalles, avisos o cuarentena; también argumentos inválidos |
| 3 | `INCOMPLETO`: faltan ventanas o resultados, o hubo detención operativa |
| 4 | `ERROR_INTERNO`: revisar el informe |
| 130 | `INTERRUMPIDO`: guardado cuando es posible; repetir el comando |

`recorrido_completo` se refiere a consultas del rango. Consultar también
`finales_con_estadisticas_completas`, `consultas_pendientes`, cobertura y cuarentena.
El programa termina al completar el rango: no necesita quedar ejecutándose sin fin.

## Pruebas

Desde `backend/`:

```bash
.venv/bin/python -m pytest tests/scrapers/test_mls.py -q
```

Incluyen contratos, cero/faltante, identidades, métricas parciales, prórrogas y
penales, recuperación HTTP, expansión mensual/diaria, presupuestos, caché antigua,
refresco selectivo, CSV, hashes, SIGTERM y terminación abrupta en otro proceso.

## Validación de la entrega

Pilotos HTTP del 19/10/2019, 21/11/2020, 04/11/2023 y 01/10/2026 (fechas
colombianas): nueve finales únicos con las seis métricas principales presentes,
incluidos prórroga y tandas con/sin prórroga. Reproducción posterior offline con
los mismos raws y verificación SHA-256 de las exportaciones. No se ejecutó el
backfill completo: el comando anterior permite descargarlo y medir su cobertura.

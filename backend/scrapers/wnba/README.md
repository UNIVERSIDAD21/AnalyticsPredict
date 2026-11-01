# Scraper WNBA ESPN — versión 2.1

CLI: `backend/scripts/scraper_wnba.py`. Exporta archivos; no utiliza `.env`,
PostgreSQL, modelos ni la API del producto. Compatible con la carpeta de datos
creada por la versión 1. Requiere Python 3.12 y `requests` del backend.

## Descargar o reanudar

Desde la raíz del proyecto:

```bash
backend/.venv/bin/python backend/scripts/scraper_wnba.py \
  --desde 2019-01-01 --hasta 2026-10-25 \
  --fetch --estadisticas --intervalo 2.5 --max-requests 20000 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/DESCARGA_WNBA_2019_2026_2026-10-25"
```

Repetir esta orden reconstruye la exportación con las reglas actuales, reutiliza
respuestas verificadas y vuelve a consultar lo que falta. No duplica partidos ni
sobrescribe ejecuciones anteriores. No es necesario borrar nada ni usar `--refresh`.
El informe final indica la ruta exacta de la nueva ejecución.

Sin `--fetch` ni `--offline` solo muestra el plan, sin red ni archivos.
`--offline` reconstruye exclusivamente con las respuestas existentes y continúa
si falta alguna, registrándola como pendiente. `--refresh` requiere `--fetch` y
fuerza nuevas observaciones conservando las anteriores.

## Tolerancia a fallos y límites

- Un 404/410 u otro error aislado no cancela los demás partidos o jornadas.
- Timeout, conexión, 500/502/503/504: hasta cinco intentos por consulta en el CLI,
  con espera exponencial y jitter. `--intentos-http` acepta 1..8.
- Después del recorrido hay hasta tres rondas en total para recuperar consultas
  transitorias. `--rondas` acepta 1..10; `--espera-rondas` usa 15 segundos por defecto
  y acepta 0..60. Solo se repiten consultas pendientes, no jornadas correctas.
- Los 404 y los datos contradictorios no se repiten en bucle en esa ejecución.
  Quedan pendientes para una nueva ejecución o revisión. No se convierten en vacíos.
- Si marcador y cuartos son válidos pero falta el boxscore o contiene errores,
  conserva el resultado y deja el detalle pendiente. Si falla la validación del
  bloque estadístico, conserva el resultado; no se inventan ceros. Si también
  faltan cuartos, no exporta un final hasta obtenerlos y validarlos.
- Campos enteros inválidos se aíslan individualmente en NULL con su valor crudo
  en `advertencias_estadisticas.jsonl`; conserva las demás métricas verificadas.
  Pérdidas totales inferiores a las de jugadoras, o no conciliables con el desglose,
  también se apartan sin derivar valores. Otras inconsistencias de estructura o
  de relaciones entre tiros/rebotes dejan el detalle completo pendiente.
- `recorrido_completo=true` significa que se recorrieron todas las ventanas. Si
  solo faltan enriquecimientos de resultados ya válidos, o hay cuarentena/avisos,
  termina como `COMPLETO_CON_INCIDENCIAS` (código 2). Los detalles siguen señalados
  como pendientes: ese estado no certifica que todas las estadísticas estén completas.
  `INCOMPLETO` (código 3) se reserva para ventanas/resultados faltantes o una
  detención operativa. Si no hay consultas transitorias, no hace rondas vacías.
- Exporta una instantánea cada 25 operaciones o al terminar una operación tras
  60 segundos (`--checkpoint-cada`, 1..1000). Los raws se guardan tras cada GET
  exitoso, independientemente de esa frecuencia. `checkpoint.jsonl` guarda los días
  recorridos; `incidencias.jsonl` conserva la historia de fallos, aunque se recuperen.
- Ctrl+C y SIGTERM intentan exportar el avance inmediatamente. Ante SIGKILL,
  corte eléctrico o caída del proceso, se reconstruye desde los raws durables
  repitiendo la orden. El último HTTP sin completar puede necesitar repetirse.
- Respuestas de días anteriores a los siete días recientes se reutilizan sin
  caducar. Los días recientes caducan a las 24 horas; hoy/futuro, a los 60 segundos.
  `--refresh` actualiza incluso históricos (p. ej., si ESPN corrigió un resultado).
- Intervalo serial predeterminado 1,5 s; mínimo 1,25 s. Presupuesto global incluye
  todos los intentos y rondas; predeterminado 1000, máximo 20000 solicitudes.
- 401/403, redirecciones, 429 repetido o sin Retry-After válido: detención ordenada,
  conservando el avance, sin evadir bloqueos. Un primer 429 espera el Retry-After
  exacto si no supera 60 segundos. No hay promesa de ejecución perpetua.
- Integridad de caché, disco lleno, presupuesto agotado o error interno también
  requieren detener y reportar. Un fallo de almacenamiento puede impedir el último
  export; no se declara éxito si quedan consultas pendientes o datos en cuarentena.

## Contrato y calidad

- Liga ESPN `59`, UID `s:40~l:59`, IDs, temporada, fecha y localía explícitos.
  Summary debe coincidir en identidad, estado, marcador y cuartos ya publicados.
- Tipos `STD`, copa `CC`, rondas de playoffs `RD16`, `QTR`, `SEMI` y `FINAL`.
  Las rondas deben corresponder a `season.type=3`. Se conserva la etiqueta de ronda
  en `tipo_competicion_fuente` y la fase `POST`. All-Star permanece en cuarentena:
  no se mezcla con encuentros estándar entre clubes.
- Finales: cuatro cuartos consecutivos, puntos enteros no negativos, suma igual
  al total, ganador concordante, mismo número de periodos para ambos equipos.
  Cada prórroga exige empate previo. Exporta Q1–Q4, regulación, cada OT y total FT.
- Fechas locales inclusivas, zona predeterminada `America/Bogota`. Consulta días
  Eastern y el día vecino necesario para cubrir el intervalo colombiano completo.
  Ventana máxima 3661 días, temporadas 2006 en adelante (formato de cuatro cuartos).
- Programados/live/pospuestos/cancelados no se convierten en finales; sus puntos
  exportados son NULL. Aplazados y cancelados aceptan las variantes administrativas
  `pre` y `post` de ESPN, siempre con `completed=false`. Estados contradictorios
  se apartan.
- Estadísticas: campo/triples/libres anotados e intentados, rebotes, asistencias,
  robos, tapones, pérdidas de jugadoras/equipo/totales y faltas. Valida relaciones
  entre tiros y marcador y entre rebotes. Las pérdidas son métricas distintas.
- Un resultado duplicado idéntico se consolida. Un enriquecimiento puede completar
  NULL, pero no sobrescribir valores publicados contradictorios. Una identidad
  cambiante o resultados distintos del mismo ID se apartan.
- Archivo raw por SHA-256, escrituras atómicas con fsync, observaciones inmutables,
  lock de escritor único y permisos restrictivos. Verifica integridad al reanudar.
  CSV protege campos de texto contra fórmulas. Los IDs son de ESPN, no UUID de BD.
- `--estadisticas` consulta un summary por final. Sin él solo se solicita summary
  cuando faltan cuartos. La cobertura estadística se mide campo por campo.

## Salidas

```text
salida/
  raw/<sha256>.json
  observaciones/<consulta>-<id>.json
  cache/<consulta>.json
  http.jsonl
  ejecuciones/<fecha>-<id>/
    partidos.jsonl       # resultados válidos y sus evidencias
    partidos.csv
    cuarentena.jsonl     # identidades/resultados que no pasan las validaciones
    pendientes.jsonl     # consultas sin resolver, ID/día/URL/error/status
    incidencias.jsonl    # historial de fallos, incluidos los luego recuperados
    advertencias_estadisticas.jsonl # campos apartados, valores crudos y evidencia
    checkpoint.jsonl
    reporte.json         # estado, cobertura, contadores, fases y días pendientes
    SHA256SUMS
```

Verificar con `sha256sum -c SHA256SUMS` desde la carpeta de ejecución. La última
instantánea tiene hashes coherentes una vez terminada la escritura; no verificar
mientras se está reemplazando la siguiente instantánea.

| Código | Significado |
|---|---|
| 0 | Plan válido o recorrido sin cuarentena ni pendientes |
| 2 | Argumentos inválidos, o COMPLETO_CON_INCIDENCIAS (detalles/avisos/cuarentena) |
| 3 | Ventanas o resultados pendientes, o detención por fuente/presupuesto/archivo |
| 4 | Error interno inesperado |
| 130 | Interrupción del operador o SIGTERM con guardado cuando es posible |

Que el recorrido termine no certifica que ESPN publique todos los partidos reales.
Revisar cobertura, fases, cuarentena y pendientes antes de usar los datos. No se
consultan otras fuentes ni se realiza carga canónica a BD, entrenamiento o cron.

## Pruebas

```bash
cd backend
.venv/bin/python -m pytest tests/scrapers/test_wnba.py -q
```

Incluyen contratos, playoffs, 404 por partido, jornadas fallidas, recuperación en
rondas, estadísticas negativas, conservación de cuartos, reanudación con caché
antigua, duplicados, presupuestos, señales y exportaciones parciales. No usan BD.

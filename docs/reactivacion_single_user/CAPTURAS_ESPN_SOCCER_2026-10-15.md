# Capturas ESPN Soccer — 2026-10-15

## Alcance

Capa de snapshots independiente del catálogo canónico Sofascore. No cambia
`partidos_futbol`, equipos, temporadas, apuestas, predicciones ni calibradores.
No habilita entrenamiento, liquidación ni certificación de rendimiento.

Se completó el WIP del 6 de octubre. Los nueve commits que parecían locales ya
estaban en GitHub (`5167597`); se actualizó la referencia remota sin reescribirlos.

## Contrato

- `capturas_espn_soccer_lotes`: identidad liga/mes/hash, observación UTC explícita,
  hash del scoreboard y fecha de ingesta separada. No se inventa frescura al importar.
- `capturas_espn_soccer_eventos`: snapshot completo vinculado a su lote. Reimportar
  el mismo lote no escribe; una observación nueva conserva una revisión incluso
  si vuelve a un contenido anterior. La aplicación no actualiza ni borra capturas.
- Se validan todos los archivos antes del DML; el grupo se aplica atómicamente.
  IDs duplicados, estados ambiguos, fechas sin zona, conteos incorrectos,
  marcadores pregame o estadísticas sin ambos equipos se rechazan.
- Los corners/tiros requieren final y hash del boxscore; IDs de evento/equipos
  del summary se cotejan con el scoreboard. Cero observado no se confunde con NULL.
- `GET /api/futbol/fuentes/espn-soccer?liga=laliga&mes=202610` consulta exclusivamente
  el último lote por fecha de observación, en transacción read-only. Un lote vacío
  no republica eventos de capturas anteriores. No llama a ESPN ni ejecuta DDL.
- `SIN_CAPTURA` significa que no se capturó ese mes/liga; `NO_DATA` exige lote vacío
  observado correctamente; un almacén ausente/caído devuelve 503
  `CAPTURAS_NO_DISPONIBLES`. Los fallos de proveedor son `SOURCE_UNAVAILABLE` en
  el auditor y nunca se importan como `NO_DATA`. Un 403 no se reintenta.
- Todas las respuestas mantienen `vinculo_partidos_futbol=NO_VERIFICADO`.

## Uso explícito

Desde `backend`, con el entorno Python 3.12 del proyecto:

```bash
python3 -m scripts.auditar_fuente_espn_soccer --liga laliga --mes 202610 \
  --max-finales 499 --salida /ruta/externa/laliga_202610.json
python3 -m scripts.ingerir_espn_soccer_capturas --archivo /ruta/externa/laliga_202610.json
python3 -m scripts.ingerir_espn_soccer_capturas --archivo /ruta/externa/laliga_202610.json --aplicar
```

Sin `--aplicar` no se abre conexión a BD. La migración separada es
`backend/migrations/2026-10-06_capturas_espn_soccer.sql`: conserva el nombre del WIP,
pero sus cambios y validación corresponden al 15 de octubre. Aplicarla únicamente
tras preflight y controles. Los archivos de octubre del día 6 son antecedentes;
no contienen fecha explícita de observación ni hashes de summary y no se les
inventan esos metadatos. Se obtuvieron capturas nuevas.

## Evidencia nueva (15 de octubre, America/Bogota)

| Liga | Septiembre: eventos/finales | Octubre: eventos/finales |
|---|---:|---:|
| Premier | 30/30 | 38/10 |
| La Liga | 39/39 | 36/9 |
| Serie A | 30/30 | 43/10 |
| Bundesliga | 27/27 | 34/9 |
| Ligue 1 | 27/27 | 33/9 |
| Total | 153/153 | 184/47 |

337 eventos, 200 finales; los 200 tienen goles, corners, disparos y disparos a
puerta completos en ambos equipos. Los 137 no finalizados conservan goles NULL.
Observaciones UTC: 2026-10-16 01:30–01:32, equivalentes al 15 por la noche en Bogotá.
La cobertura se refiere solo a estos diez lotes, no a todo el fútbol.

Suite local Python 3.12/PostgreSQL 18 exclusiva y desechable: **733 passed,
0 failed, 0 skipped**, dos avisos de deprecación. Pruebas de captura cubren
validación, idempotencia, retorno a una versión anterior, importación fuera de
orden, lote vacío, rollback total y GET read-only. La CI añade estos contratos y
ejecuta la integración también con PostgreSQL 16. Evidencias fuera del repositorio
en `Carpeta de Entregas de Borlty/CAPTURAS_ESPN_SOCCER_2026-10-15`.

## Pendiente

Publicación/CI y aplicación controlada se registran en el acta de entrega al
terminar. El vínculo ESPN↔catálogo requiere acreditar competiciones, temporadas,
IDs de clubes y ascendidos. No enlazar por similitud de nombres. La recertificación
P&L/temporal/prospectiva, H4 y H12 siguen abiertos.

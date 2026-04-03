# BLOQUE 5 — Pipeline real de temporadas (NBA) y blindaje ETL

## Ruta real validada en este repo

Pipeline activo de temporada para scraping NBA:

1. **Scraper principal**: `backend/scripts/scraper_equipos_recientes.py`
2. **Fuente de calendario ESPN**: `motor.nba_scraper_espn.fetch_schedule_events(...)`
3. **Normalización temporal**:
   - `parse_fecha_calendario_espn_iso(...)`
   - `inferir_anio_fin_temporada(...)` (nuevo en este bloque)
4. **Resolución/asignación de temporada**:
   - `resolver_temporada_id_evento(...)` (nuevo)
   - `asegurar_temporadas(...)`
5. **Persistencia final del partido**:
   - `upsert_partido_con_fecha(...)` -> tabla `partidos_baloncesto.temporada_id`

> No se usó una ruta inventada. El bloque se ejecutó sobre la ruta real en producción del repo actual.

## Cómo se construye/infiere temporada

- `season_api` (año fin de temporada) llega desde el loop de sincronización por `--seasons`.
- Se calcula temporada inferida por fecha de evento:
  - Oct-Dic -> `año + 1`
  - Ene-Jun -> `año`
- Si `season_api` y la inferida difieren, se registra advertencia estructurada (`season_api_difiere_de_fecha`).

## Dónde se asigna `temporada_id` al partido

- En `sincronizar_equipo_optimizado(...)` ahora se resuelve por evento con `resolver_temporada_id_evento(...)`.
- El resultado (`temporada_id_evento`) se pasa a `upsert_partido_con_fecha(...)`.
- Si no se puede resolver, el evento se **omite** y se registra advertencia (`temporada_no_resuelta`).

## Casos que quedan sin temporada

Quedan explícitamente en estado no resuelto solo cuando:

- no existe mapeo local en `temporada_por_anio_fin`, y
- `asegurar_temporadas(...)` tampoco puede crear/obtener la temporada.

En ese caso:
- no se inserta partido con `temporada_id` vacío,
- se incrementa `omitidos`,
- y queda warning auditable.

## Registro de advertencias/errores

- Advertencias nuevas de temporada:
  - `season_api_difiere_de_fecha`
  - `temporada_no_resuelta`
- Se agregan a memoria de ejecución y a contador `SyncStats.advertencias_temporada`.
- Resumen final CLI ahora imprime `Advertencias de temporada`.

## Resultado de confiabilidad del filtro por temporadas (Bloque 1)

Estado actual tras BLOQUE 5: **MÁS CONFIABLE, pero condicionado al canal de ingesta por este scraper**.

- ✅ Queda blindado para la ruta `scraper_equipos_recientes.py` con resolución por evento + fallback controlado + warnings.
- ⚠️ Limitación estructural residual: otros scripts de ingesta (por ejemplo `scraper_partidos_futuros.py`) siguen usando asignación basada en temporada activa y no comparten todavía esta misma trazabilidad por evento.

Conclusión: **el filtro por temporadas puede declararse confiable para este pipeline**, pero **no globalmente para toda ingesta NBA** hasta homologar el resto de scrapers.

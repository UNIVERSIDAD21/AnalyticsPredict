# BLOQUE 1 — Gobernanza temporal en análisis de fútbol (estado real)

Fecha: 2026-04-03

## 1) Verificación del estado real del repo

- `AnalisisRequest` del endpoint principal de fútbol (`backend/api/schemas_futbol.py`) **sí requiere gobernanza temporal explícita** en el estado actual y ahora queda consolidado con:
  - `temporadas: Optional[List[str]]`
  - `ventana_dias_fallback: Optional[int]`
  - `fecha_minima: Optional[datetime]` (opcional para override explícito)
- Se eliminó duplicidad accidental de campos `temporadas` en el schema.

## 2) Tablas reales que soportan temporalidad

- `partidos_futbol.temporada_id` (filtro operativo principal)
- `temporadas_futbol.id` + `temporadas_futbol.nombre` (resolución por ID o nombre)
- `temporadas_futbol.activa`, `anio_inicio`, `fecha_inicio` (default activa + anterior)

## 3) Dependencia del pipeline respecto a fecha

En el flujo contextual principal (`/api/futbol/analizar`), las 6 consultas de contexto (`h2h`, `local_global`, `local_home`, `visitante_global`, `visitante_away`, `liga`) usan `fecha_partido < fecha_corte` como corte superior.

Con este bloque:
- **0%** de esas consultas queda "solo por fecha" cuando hay temporadas resueltas (se filtra por `temporada_id`).
- **100%** cae a ventana temporal trazable (`fecha_minima`) solo cuando no se pueden resolver temporadas.

## 4) Regla canónica implementada

1. Si request trae `temporadas` -> se respetan estrictamente (resolviendo por ID o nombre).
2. Si no trae `temporadas` -> se usa `temporada_activa + anterior` de `temporadas_futbol`.
3. Si no se puede resolver -> fallback por `fecha_minima = fecha_corte - ventana_dias_fallback`.

## 5) Trazabilidad visible

Se agrega a `objetivo.trazabilidad.temporal`:
- estrategia
- temporadas_resueltas
- temporada_ids
- fecha_minima (si aplica)
- muestras usadas por bloque (`h2h`, `local_home`, `local_global`, `visitante_away`, `visitante_global`, `liga`)

## 6) Dependencias abiertas (bloque 5 ETL)

Este bloque queda funcionalmente implementado, pero su calidad final depende de:
- consistencia de `partidos_futbol.temporada_id`
- correcta marcación de `temporadas_futbol.activa`
- sincronización ETL/Scraper de temporadas (`backend/scrapers/sofascore/temporadas.py`)

Si ETL no mantiene temporada activa y mapeos consistentes, el sistema cae al fallback por fecha (trazable), pero con menor control semántico por temporada.

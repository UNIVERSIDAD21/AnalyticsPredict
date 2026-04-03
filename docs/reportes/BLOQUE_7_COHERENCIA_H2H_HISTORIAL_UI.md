# BLOQUE 7 — Coherencia H2H + historial + UI (fútbol)

## Qué ya existía (y se conservó)

Base útil existente en backend (`backend/api/rutas_analisis_futbol.py`):
- Parsing por mercado con columnas específicas (goles/corners/disparos).
- Funciones market-aware para resumen y razones (`_resumen_metricas_h2h`, `_generar_razones_linea`, etc.).
- Gobernanza temporal por temporadas/fallback (`_resolver_filtro_temporal_futbol`).

No se rehízo desde cero. Se aprovechó esa base y se cerraron huecos concretos.

## Huecos detectados y corrección aplicada

### 1) H2H/contexto mezclaba competición en consultas de análisis
**Antes:**
- `_obtener_partidos_h2h(...)` y `_obtener_partidos_equipo(...)` filtraban por temporada/fecha, pero no imponían competición explícita en esta ruta.

**Ahora:**
- ambas funciones aceptan `competicion_id` y aplican `pf.competicion_id::text = %s`.
- en `analizar_partido(...)` se pasa `competicion_id` a H2H y a historiales local/visitante.

Resultado: contexto del bloque analítico queda acotado a competición + temporada/ventana temporal resuelta.

### 2) UI/adaptador podía mostrar contexto en métrica equivocada
**Antes:**
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.ts` usaba goles como base para H2H/forma en varios cálculos, incluso cuando mercado objetivo era corners/disparos.

**Ahora:**
- se introdujo `_metricaMercadoPartido(...)` market-aware:
  - goles FT/1T/2T,
  - corners FT/1T/2T,
  - disparos/disparos arco.
- `desdePerspectiva(...)`, racha/tendencia/diferencia temporal y contexto H2H usan la métrica del `mercadoObjetivo` activo.
- el total visible (`promedio_total`, `tendencia_over`, `partidos[].total`) queda alineado con mercado/línea seleccionados.

Resultado: coherencia real entre dato, mercado objetivo y render.

## Verificación pedida

### Qué parte ya era market-aware
- backend de análisis (resumen de métricas y razones por mercado/alcance).

### Qué parte era genérica
- consultas de contexto en análisis sin filtro explícito de competición.
- adaptador frontend de contexto usando goles como proxy genérico.

### Frontend unidad/métrica/línea/perspectiva
- unidad y línea venían del mercado objetivo; se mantuvo.
- se corrigió métrica/perspectiva contextual para que siga el mismo mercado objetivo en H2H/historial renderizado.

## Pruebas

Backend:
- `backend/tests/test_futbol_contexto_competicion.py`
  - valida presencia de filtro por competición + temporada/fecha en queries de H2H/historial.

Frontend:
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
  - valida que para `CORNERS_1T` no use goles,
  - valida que para `DISPAROS_ARCO_FT` use disparos al arco.

## Archivos tocados

- `backend/api/rutas_analisis_futbol.py`
- `backend/tests/test_futbol_contexto_competicion.py` (nuevo)
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.ts`
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts` (nuevo)

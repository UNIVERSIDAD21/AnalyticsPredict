# BLOQUE 3 — Corrección de modelo estadístico real (fútbol)

## Inventario anterior (estado real antes de este bloque)

### Distribuciones por mercado
- Corners: `nbinom` explícito en generación de mercados.
- Goles: caía en `normal` por default (no se pasaba distribución explícita en `_generar_predicciones_mercado`).
- Disparos/tiros a puerta: `nbinom` explícito.
- 1X2: Dixon-Coles (Poisson corregido) para ganador, separado del OVER/UNDER.

### Derivaciones indirectas
- Partición temporal de disparos 1T/2T dependía de ratio derivado de corners (proxy principal), con límites hardcodeados.

### Parámetros estadísticos desacoplados/hardcodeados
- Ventana fallback, half-life recencia, umbrales de muestra, y umbrales de conservadurismo por std distribuidos en el archivo principal.
- Sin módulo central único para gobernanza estadística.

### Outliers
- No había winsorización/exclusión formal previa al cálculo de medias/std en el bloque contextual.

## Cambios implementados (nuevo)

1. **Módulo central de configuración estadística**
   - Nuevo archivo: `backend/api/config_estadistica_futbol.py`
   - Centraliza:
     - ventana temporal fallback,
     - decaimiento por recencia,
     - mínimos de muestra,
     - política de outliers (winsorización),
     - distribución por mercado,
     - configuración de partición temporal de disparos.

2. **Distribución por mercado gobernada de forma explícita**
   - `distribucion_para_mercado(...)`:
     - GOLES* -> `poisson`
     - CORNERS* -> `nbinom`
     - DISPAROS* / DISPAROS_ARCO* -> `nbinom`
   - En generación de mercados de goles se dejó explícito `poisson` (ya no cae a normal genérica por omisión).

3. **Outliers: winsorización formal antes de medias/std**
   - `_resumen_valores(...)` ahora aplica `winsorizar_valores(...)` desde config central.
   - Se añade trazabilidad en cada resumen:
     - `winsorizacion_aplicada`,
     - `winsor_low/high`,
     - percentiles usados,
     - `n` y `n_original`.

4. **Partición temporal de disparos más robusta**
   - Se reemplaza ratio heredado simple por `estimar_ratio_tiempo_disparos(...)`.
   - Mezcla señales de mercado (corners + goles por tiempo) con pesos configurables y límites explícitos.
   - Sigue siendo estimación (si no existen columnas directas de disparos 1T/2T), pero ahora es una regla explícita, auditable y configurable.

5. **Trazabilidad de configuración aplicada por análisis**
   - En `objetivo.trazabilidad.temporal.configuracion_estadistica` se reporta snapshot de:
     - fallback window,
     - recency half-life,
     - política de winsorización.

## Archivos tocados
- `backend/api/config_estadistica_futbol.py` (nuevo)
- `backend/api/rutas_analisis_futbol.py`
- `backend/tests/test_futbol_modelo_estadistico_unittest.py` (nuevo)

## Pruebas
- `tests/test_futbol_modelo_estadistico_unittest.py`
- `tests/test_futbol_gating_contexto_unittest.py`
- `tests/test_futbol_filtro_temporal.py`

## Riesgos residuales
- La partición temporal de disparos sigue siendo inferida (sin columnas directas 1T/2T en disparos), aunque ahora con configuración central y blend explícito.
- Para eliminar totalmente proxies, se requiere ampliar dataset/ETL con métricas de disparos por tiempo de forma nativa.

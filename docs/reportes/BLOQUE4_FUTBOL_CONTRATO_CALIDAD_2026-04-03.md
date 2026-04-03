# BLOQUE 4 — Extensión canónica de contrato y render honesto de calidad

## Diff conceptual del contrato (sin romper canónico)

Se **extiende** `objetivo` en `AnalisisResponse` con `calidad_datos`.
No se crea contrato paralelo ni se eliminan campos existentes (`devig`, `calibracion`, `score_riesgo`).

### Nuevo subbloque canónico
`objetivo.calidad_datos`:
- `muestras`:
  - `h2h`, `local_home`, `visitante_away`, `local_global`, `visitante_global`, `liga`
- `rango_temporal`:
  - `fecha_min`, `fecha_max`
- `temporadas_incluidas`: `string[]`
- `competiciones_incluidas`: `string[]`
- `muestra_insuficiente`: `boolean`
- `datos_incompletos`: `boolean`
- `penalizaciones_aplicadas`: `string[]`

## Puntos donde se perdía información y quedó corregido
- Backend calculaba señales de calidad, pero no quedaban consolidadas como bloque canónico estructurado para UI.
- Transformer frontend mapeaba `objetivo` parcial; ahora mapea también `calidad_datos`.
- Render principal no exponía explícitamente muestra/rango/banderas/penalizaciones.

## Componentes tocados
- Backend:
  - `backend/api/schemas_futbol.py`
  - `backend/api/rutas_analisis_futbol.py`
  - `backend/tests/test_futbol_gating_contexto_unittest.py`
- Frontend:
  - `frontend/src/tipos/futbol.ts`
  - `frontend/src/servicios/futbol/analisis.ts`
  - `frontend/src/componentes/paginas/PaginaFutbol.tsx`
  - `frontend/src/componentes/moleculas/TarjetaCalidadDatosFutbol.tsx` (nuevo)
  - `frontend/src/componentes/moleculas/index.ts`
  - `frontend/src/servicios/futbol/analisis.test.ts` (nuevo)
  - `frontend/src/componentes/moleculas/TarjetaCalidadDatosFutbol.test.tsx` (nuevo)
  - `frontend/vitest.config.ts` (nuevo)
  - `frontend/vitest.setup.ts` (nuevo)
  - `frontend/package.json` / `frontend/package-lock.json`

## Evidencia de render final
- Tarjeta visible en `PaginaFutbol` con:
  - badges: `MUESTRA INSUFICIENTE`, `DATOS INCOMPLETOS` (cuando aplique)
  - tamaños de muestra por bloque
  - rango temporal efectivo
  - número de temporadas y competiciones
  - lista de penalizaciones aplicadas
- Test de render: `TarjetaCalidadDatosFutbol.test.tsx`

## Pruebas ejecutadas
- Backend:
  - `pytest -q tests/test_futbol_gating_contexto_unittest.py tests/test_futbol_filtro_temporal.py tests/test_futbol_modelo_estadistico_unittest.py`
- Frontend:
  - `npm run test` (Vitest)
  - `npm run build`

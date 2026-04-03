# BLOQUE 6 — Capa de decisión fútbol (trazabilidad matemática y guardas)

## 1) Auditoría matemática (antes)

Ruta real auditada: `backend/api/rutas_analisis_futbol.py`

### Qué usaba cada métrica antes
- `p_raw`: se exponía en recomendación, pero no tenía rol explícito en edge canónico de contrato.
- `p_calibrada`: se usaba como base operativa para `edge_real`, EV, score y sizing en `_calcular_metricas_mercado(...)`.
- `devig`: se calculaba en `_calcular_metricas_mercado(...)` con:
  - exacto si hay `cuota_over` y `cuota_under`,
  - implied raw si hay cuota de un solo lado,
  - fallback sin cuotas.
- `edge_real`: `p_calibrada - p_mkt_fair` (o fallback con 0.5).
- `score/riesgo`: dependían de EV + edge + estado de mercado + varianza.

### Huecos detectados
- `edge_raw` no era campo de contrato en esta capa.
- No había flag explícito de `calibración aplicada efectivamente`.
- En arbitraje ENSEMBLE se mezclaban `edge_real`, `score` y `sizing` por pesos sin recomputar desde una base canónica única.
- Riesgo de interpretación confusa entre probabilidad cruda/calibrada/fair en trazabilidad.

## 2) Cambio matemático (nuevo)

### Fórmulas explícitas
- `edge_raw = p_raw - (1/cuota_lado)` cuando hay cuota del lado.
- `edge_real = p_decision - p_mkt_fair`, donde:
  - `p_decision = p_calibrada` si `calibracion_aplicada=true`
  - `p_decision = p_raw` si `calibracion_aplicada=false`
- `valor_esperado = p_decision * cuota_lado - 1`

### Guardas anti doble transformación
- Se agrega `calibracion_aplicada` en contrato de recomendación y objetivo.
- `_calcular_metricas_mercado(...)` ahora recibe explícitamente `calibracion_aplicada` y usa `p_decision` canónica.
- En ENSEMBLE se deja de mezclar `edge_real/score/sizing` heredados: ahora se recomputan de forma canónica con una sola pasada por `_calcular_metricas_mercado(...)` usando probabilidades blend.
- Se agrega marca de trazabilidad en metadata de arbitraje:
  - `guardas_transformacion.calibracion_aplicada`
  - `guardas_transformacion.devig_recalculado_canonico=true`

## 3) Campos nuevos/corregidos

### Backend contrato
- `RecomendacionApuesta`:
  - `calibracion_aplicada: bool?`
  - `edge_raw: float?`
- `ObjetivoCalibracionFutbol`:
  - `calibracion_aplicada: bool?`
- `ObjetivoScoreRiesgoFutbol`:
  - `edge_raw: float?`

### Frontend mapeo/tipos
- Se extiende parser y tipos para consumir:
  - `calibracionAplicada`
  - `edgeRaw`

## 4) Confiabilidad de la capa de decisión

Estado BLOQUE 6: **más sólido y trazable**
- Score y riesgo pasan a compartir base matemática canónica de decisión en generación y arbitraje.
- Se elimina ambigüedad entre crudo/calibrado/fair con campos explícitos y reglas de uso.

Limitación residual:
- Si faltan cuotas de ambos lados, el devig exacto no existe por definición de mercado; el sistema sigue en modo degradado controlado (`implied_raw_single_side` / `fallback`).

## 5) Pruebas (evidencia)

Pruebas backend:
- `backend/tests/test_futbol_p51_p61_unittest.py`
  - nuevas validaciones:
    - fórmula `edge_raw` canónica,
    - fórmula `edge_real` canónica,
    - uso de `p_raw` cuando `calibracion_aplicada=false`.

Pruebas frontend:
- `frontend/src/servicios/futbol/analisis.test.ts` (transformador de contrato).

## 6) Archivos tocados

- `backend/api/rutas_analisis_futbol.py`
- `backend/api/schemas_futbol.py`
- `backend/tests/test_futbol_p51_p61_unittest.py`
- `frontend/src/servicios/futbol/analisis.ts`
- `frontend/src/tipos/futbol.ts`

# ESQUEMA_CANONICO_APUESTAS_FUTBOL.md

## Objetivo
Definir esquema canónico defendible para `apuestas_futbol` y tablas críticas relacionadas, eliminando dependencia de adivinanzas estructurales.

## Fuente de verdad usada
- `information_schema.columns` en BD real.
- Código runtime en:
  - `backend/api/rutas_apuestas_futbol.py`
  - `backend/api/rutas_metricas_futbol.py`

---

## 1) Tabla crítica principal: `apuestas_futbol`

## Columnas canónicas vigentes (confirmadas en BD)
- Identidad/relación: `id`, `usuario_id`, `partido_id`, `prediccion_id`
- Contexto partido: `competicion_nombre`, `equipo_local`, `equipo_visitante`, `fecha_partido`
- Mercado/apuesta: `mercado`, `lado`, `linea`, `cuota`, `cuota_over`, `cuota_under`
- Sizing/riesgo: `stake`, `bankroll_momento`, `devig_metodo`, `devig_overround`, `devig_prob_justa`, `edge_real`, `kelly_full`, `kelly_fraccional`, `fraccion_kelly`, `score_total`, `score_componentes`
- Señales modelo: `probabilidad_sistema`, `confianza_sistema`, `valor_esperado`, `prediccion_media`, `prediccion_desviacion`
- Resultado: `resultado`, `valor_real`, `ganancia`, `fecha_resolucion`
- Trazabilidad/UI: `razones`, `notas`, `etiquetas`, `casa_apuestas`, `creado_en`, `actualizado_en`

## Columnas legacy/ambiguas detectadas en código (no canónicas)
- `status` (estado legacy)
- `confianza` (legacy; canónica: `confianza_sistema`)
- `probabilidad` (legacy; canónica: `probabilidad_sistema`)
- `odds`, `cuota_decimal` (legacy; canónica: `cuota`)
- `ganancia_real`, `ganancia_neta`, `beneficio_real`, `beneficio` (legacy; canónica: `ganancia`)
- `resultado_real` (legacy; canónica: `resultado`)
- `casa_apuesta` (legacy; canónica: `casa_apuestas`)

---

## 2) Tablas relacionadas (prioridad por impacto)

## `predicciones_futbol` (canónico)
- Probabilidades: `prob_over`, `prob_under`, `prob_over_calibrada`, `prob_under_calibrada`
- Resultados: `valor_real`, `resultado`, `outcome_binario`, `resuelto`, `timestamp_resolucion`
- Contexto: `mercado`, `linea`, `cuota` no existe aquí (esa vive en apuestas), `timestamp_generacion`

## `modelo_versiones_futbol` (canónico actual)
- Métricas generales: `mae_general`, `rmse_general`
- Fechas/versionado: `fecha_entrenamiento`, `cutoff_entrenamiento`, `version`, `activo`, `creado_en`
- No se validó presencia de columnas legacy referenciadas dinámicamente como canónicas.

## `calibradores_futbol` (canónico)
- `metodo`, `brier_antes`, `brier_despues`, `mejora_validacion`, `activo`, `fecha_entrenamiento`

---

## 3) Decisión de canonicidad

Para `apuestas_futbol`, el contrato canónico queda fijado en:
- `estado` (si existe) o, en su defecto operativo, `resultado` como fallback temporal.
- `cuota`
- `probabilidad_sistema`
- `confianza_sistema`
- `ganancia`
- `resultado`
- `casa_apuestas`

## Columnas que no deben volver a introducirse en código nuevo
- `status`, `probabilidad`, `confianza`, `odds`, `cuota_decimal`, `ganancia_neta`, `ganancia_real`, `beneficio*`, `resultado_real`, `casa_apuesta`.

---

## 4) Estado de cierre
- Esquema canónico documentado: ✅
- Drift eliminado totalmente: ❌ (sigue convivencia legacy en runtime)
- Alertas anti-drift agregadas: ✅ (logging en resolutores de columnas)

# MAPA_SEMANTICO_DEL_SISTEMA.md

## Bloque 06 — Mapa semántico (v1)

## Objetivo
Establecer una sola semántica defendible para términos, métricas, entidades y relaciones analíticas del sistema.

---

## 1) Entidades de negocio

## Dominio NBA
- `partidos_baloncesto`: eventos deportivos base.
- `predicciones_registradas`: predicciones modeladas/resueltas (unidad analítica principal de calibración).
- `apuestas`: ejecuciones operativas (unidad de negocio monetaria).
- `calibradores`, `modelo_versiones`: gobernanza del score predictivo.

## Dominio Fútbol
- `partidos_futbol`: eventos base.
- `predicciones_futbol`: predicción modelada por mercado.
- `apuestas_futbol`: ejecución operativa.
- `calibradores_futbol`, `modelo_versiones_futbol`: gobernanza.

---

## 2) Definiciones semánticas clave

## Predicción vs Apuesta
- **Predicción:** estimación probabilística del modelo.
- **Apuesta:** decisión operativa con stake/cuota y resultado económico.

## Win rate
- En apuestas: éxitos sobre ganadas+perdidas.
- En predicciones: `AVG(outcome_binario)`.

## ROI
- **Monetario:** usa stake/ganancia (`apuestas`).
- **Unitario:** retorno por unidad (`predicciones`).

## Confidence
- Etiqueta de riesgo/confianza (ALTA/MEDIA/BAJA) derivada de score heurístico.
- Estado actual: en policy temporal (no usar como driver primario de stake hasta cierre P1 bloque 05).

## Edge
- Diferencia entre probabilidad del modelo e implícita de cuota.
- No equivale automáticamente a ROI positivo en todos los segmentos.

---

## 3) Buckets canónicos

## Odds bucket
- `<1.6`
- `1.6-1.8`
- `1.8-2.0`
- `>=2.0`

## Confidence bucket (probabilidad)
- `0.60-0.69`
- `0.70-0.79`
- `0.80+`

## Market type
- NBA: `COMPLETO`, `Q1`, `Q2`, `Q3`, `Q4`
- Fútbol: markets de corners/goals/shots según catálogo vigente

---

## 4) Relaciones semánticas críticas

1. `partido` → muchas `predicciones`.
2. `predicción` puede o no convertirse en `apuesta`.
3. `calibrador` afecta probabilidades y por tanto edge/confidence.
4. `modelo_version` contextualiza desempeño por periodo.

---

## 5) Reglas semánticas de uso analítico

1. No comparar ROI monetario con ROI unitario sin etiquetar.
2. No inferir calidad de modelo solo por win rate.
3. No usar confidence como señal universal hasta cierre de calibración por mercado.
4. No presentar métricas fútbol como definitivas si se apoyan en columnas legacy detectadas por anti-drift.

---

## 6) Fuente única de verdad analítica (v1)

### Capa recomendada
1. Catálogo de KPIs (`CATALOGO_DE_KPIS_Y_METRICAS.md`)
2. Vistas canónicas (`VISTAS_ANALITICAS_CANONICAS.md`)
3. Reglas operativas temporales bloque 05 (confidence/odds/drift) como flags de contexto.

### Jerarquía de confianza de métricas
- Nivel A: métricas con fuente canónica + sin deuda residual activa.
- Nivel B: métricas válidas con advertencia de policy temporal.
- Nivel C: métricas afectadas por drift legacy o muestra insuficiente.

---

## 7) Deuda semántica residual

1. coexistencia de contratos API legacy.
2. drift de esquema en fútbol aún en fase de deprecación.
3. confidence no cerrado totalmente para decisión de stake.

---

## Estado
- Mapa semántico base formalizado para iniciar bloque 06.
- Apto como referencia de consistencia para dashboards, reportes y consultas futuras.

# ANALISIS_HISTORICO_COMPLETO_NBA.md

## Objetivo
Expandir el análisis NBA usando histórico completo disponible, sin cambios de modelo/pipeline/arquitectura, para validar si el edge observado en muestra corta se sostiene.

## Fuentes usadas
1. `predicciones_registradas` (histórico amplio de predicciones con outcome)
2. `partidos_baloncesto` (cobertura temporal de resultados reales)
3. `apuestas` (dataset corto de picks ejecutados, usado para comparación)

## Definición de dataset agregado (canónico para este análisis)
Para evitar sobreconteo por múltiples corridas sobre el mismo partido/mercado:
- Se tomó `predicciones_registradas` con `outcome_binario IS NOT NULL`.
- Se deduplicó por `(partido_id, mercado, linea)`.
- Se conservó la fila con mayor probabilidad `COALESCE(p_calibrada,p_raw)` y más reciente (`timestamp_generacion DESC`).

> Este dataset deduplicado se llama **expanded**.

## Métricas usadas
- **win_rate_pct** = promedio de `outcome_binario` * 100
- **roi_unit_pct** = promedio de retorno unitario * 100, con:
  - win: `(cuota - 1)`
  - loss: `-1`

(ROI unitario, no ROI monetario por stake.)

---

## Cobertura temporal y tamaño de muestra

| Dataset | n | Min fecha | Max fecha |
|---|---:|---|---|
| expanded (dedup predicciones) | 907 | 2026-01-10 | 2026-02-12 |
| short_apuestas | 129 | 2026-01-10 | 2026-02-03 |
| predicciones_registradas raw | 2514 | 2026-01-10 | 2026-03-06 |
| partidos_baloncesto | 12492 | 2018-04-14 | 2026-03-15 |

### Lectura
- Sí hay histórico adicional fuera de `apuestas`.
- Pero el histórico **resuelto y utilizable** para performance de predicción está concentrado en 2026.

---

## Comparación dataset corto vs completo

## Global

| Dataset | n | Win rate | ROI unit |
|---|---:|---:|---:|
| expanded | 907 | 65.49% | 3.76% |
| short_apuestas | 129 | 77.52% | 11.78% |

### Lectura
La muestra corta sobreestima desempeño; con dataset ampliado el edge existe, pero más moderado.

---

## Breakdown por mercado

| Mercado | n expanded | ROI expanded | n short | ROI short |
|---|---:|---:|---:|---:|
| Q1 | 139 | 8.14% | 17 | 30.00% |
| Q2 | 83 | 34.40% | 9 | 63.11% |
| Q3 | 82 | -7.94% | 4 | -13.50% |
| Q4 | 64 | -15.00% | 2 | 75.50% |
| COMPLETO | 539 | 1.91% | 97 | 3.56% |

### Verificaciones pedidas
- **¿Edge Q1/Q2 se sostiene?** → **Sí** (Q1 y especialmente Q2 siguen positivos en expanded).
- **¿Q3 negativo ruido o patrón?** → **Parece patrón real** (sigue negativo con n=82).
- **¿Full-game repite problema?** → En expanded no es fuertemente negativo global (ROI +1.91%), pero sí tiene subsegmentos negativos.

---

## Breakdown por odds buckets

| Odds bucket | n expanded | ROI expanded | n short | ROI short |
|---|---:|---:|---:|---:|
| <1.6 | 481 | 0.01% | 92 | 9.25% |
| 1.6-1.8 | 85 | 1.65% | 15 | 14.53% |
| 1.8-2.0 | 239 | 9.71% | 17 | 43.00% |
| >=2.0 | 102 | 9.21% | 5 | -56.00% |

### Lectura
- En expanded, el bucket `>=2.0` ya **no sale necesariamente negativo** en global.
- Esto contradice la muestra corta y sugiere **sensibilidad fuerte al muestreo/selección de picks**.

---

## Full-game en detalle (expanded)

### Por línea

| Bucket línea | n | ROI |
|---|---:|---:|
| <205 | 21 | 24.95% |
| 205-214.9 | 95 | 5.13% |
| 215-224.9 | 121 | -5.62% |
| >=225 | 302 | 2.32% |

### Por odds

| Bucket odds | n | ROI |
|---|---:|---:|
| <1.6 | 413 | 2.30% |
| 1.6-1.8 | 11 | -5.27% |
| 1.8-2.0 | 45 | 16.62% |
| >=2.0 | 70 | -8.69% |

### Lectura
El problema de full-game no es homogéneo: se concentra en ciertos buckets (línea 215–224.9 y odds >=2.0 / 1.6–1.8).

---

## Confidence buckets (hit rate vs probabilidad)

Buckets pedidos:
- 0.60–0.69
- 0.70–0.79
- 0.80+

| Bucket | n expanded | prob_media | hit_rate | ROI expanded |
|---|---:|---:|---:|---:|
| 0.60-0.69 | 205 | 0.6485 | 0.6049 | -4.22% |
| 0.70-0.79 | 189 | 0.7502 | 0.6772 | 5.32% |
| 0.80+ | 297 | 0.8830 | 0.7609 | 13.33% |

### Lectura calibración
- 0.80+ mantiene mejor ROI, pero `hit_rate < prob_media` (sobreconfianza relativa).
- 0.70–0.79 positivo, también con leve sobreestimación de probabilidad.
- 0.60–0.69 combina hit rate razonable con ROI negativo (posible fricción de precio/selección).

---

## Dataset agregado usado para cálculo
- Archivo de evidencia consolidada:
  - `reports/auditoria_baselines/segmentos_nba_historico_completo_20260307T0040Z.json`

Incluye tablas agregadas de:
- cobertura temporal
- comparación global corto vs completo
- comparación por mercado
- comparación por odds
- comparación por confidence
- breakdown full-game por línea y por odds

---

## Queries SQL usadas
- `docs/borlty-context/sql/ANALISIS_HISTORICO_COMPLETO_NBA.sql`

---

## Conclusiones estratégicas (sin cambiar modelo aún)

1. **Quarter-first parcial sí está respaldado**, pero no para todos los quarters:
   - Q1/Q2 sostienen edge.
   - Q3 y Q4 muestran señal negativa en dataset ampliado.

2. **Full-game no está muerto**, pero su edge depende de segmento:
   - evitar/ajustar subrangos problemáticos (línea 215–224.9, odds >=2.0 y 1.6–1.8 en full-game).

3. **La narrativa “odds >=2 siempre malas” no es universal** en dataset ampliado global;
   sí se mantiene problema en full-game >=2.0.

4. **Calibración requiere revisión posterior** (fase siguiente):
   - buckets altos con sobreconfianza relativa.
   - bucket 0.60–0.69 con ROI negativo pese a hit rate >60%.

---

## Recomendación para la próxima decisión operativa

Si hoy hubiera que decidir política sin tocar modelo:
- Aplicar **quarter-first focalizado en Q1/Q2**.
- Mantener Q3/Q4 en observación/restricción.
- En full-game, permitir solo subsegmentos con evidencia positiva y limitar buckets de línea/odds que salen negativos.

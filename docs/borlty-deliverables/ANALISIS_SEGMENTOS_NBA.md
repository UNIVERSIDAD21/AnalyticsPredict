# ANALISIS_SEGMENTOS_NBA.md

## Objetivo
Profundizar en segmentos NBA para ubicar dónde está el edge real del sistema, sin cambios de arquitectura/modelo/pipeline.

## Fuente canónica y alcance
- **Fuente canónica:** `apuestas` (picks ejecutados/resueltos, con stake/ganancia/cuota/confianza/mercado).
- **Fuentes de contraste temporal:** `predicciones_registradas`, `partidos_baloncesto`.
- **Ejecución reproducible:**
  - SQL: `docs/borlty-context/sql/ANALISIS_SEGMENTOS_NBA.sql`
  - Evidencia raw: `reports/auditoria_baselines/segmentos_nba_analisis_20260307T0033Z.json`

---

## 1) Quarter markets

### ROI por Q1, Q2, Q3, Q4 (separado)

| Quarter | n | Win rate | ROI | Stake | Ganancia |
|---|---:|---:|---:|---:|---:|
| Q1 | 17 | 76.47% | 10.83% | 17,000 | 1,841.40 |
| Q2 | 9 | 88.89% | 61.41% | 9,000 | 5,527.00 |
| Q3 | 4 | 50.00% | -56.75% | 4,000 | -2,270.00 |
| Q4 | 2 | 100.00% | 63.30% | 2,000 | 1,266.00 |

### Tamaño de muestra por quarter
- Total quarter: **32** apuestas resueltas.
- Muestra muy desigual (Q1=17, Q2=9, Q3=4, Q4=2).

### Distribución de líneas (lectura)
- Q1 concentra líneas entre ~60.5 y 62.5 (más frecuentes).
- Q2 concentra en 58.5–60.5.
- Q3 y Q4 tienen muestra muy pequeña por línea (n=1 casi en todo).

### Relación con confidence (quarter)
- Q1: BAJA muy mala (ROI -72.94%), MEDIA positiva, ALTA muy positiva (n=2).
- Q2: BAJA sorprendentemente alta (ROI 93.7%) pero n=5 (inestable).
- Q3: BAJA muy negativa, MEDIA positiva (n=2 y 2).
- Q4: solo MEDIA (n=2), positiva.

**Conclusión quarter:** hay edge probable en Q1/Q2, pero Q3 es foco de riesgo y Q4 no es estadísticamente concluyente por tamaño de muestra.

---

## 2) Full-game markets

### Por qué el ROI sale negativo

**Resultado global full-game:**
- n=97
- ROI = **-5.2158%**
- Win rate = 77.3196%

Esto sugiere que no basta con acertar alto: la combinación de precios (cuotas), líneas y/o sizing está erosionando margen.

### Breakdown por rango de línea (full-game)

| Línea bucket | n | Win rate | ROI |
|---|---:|---:|---:|
| <205 | 2 | 100.00% | 30.00% |
| 205-214.9 | 17 | 76.47% | -19.92% |
| 215-224.9 | 12 | 66.67% | -53.75% |
| >=225 | 66 | 78.79% | 4.40% |

**Lectura:** el agujero grande está en líneas medias 205–224.9, especialmente 215–224.9.

### Breakdown por rango de odds (full-game)

| Odds bucket | n | Win rate | ROI |
|---|---:|---:|---:|
| <1.6 | 82 | 84.15% | 3.61% |
| 1.6-1.8 | 6 | 50.00% | -115.26% |
| 1.8-2.0 | 6 | 50.00% | -7.67% |
| >=2.0 | 3 | 0.00% | -215.63% |

**Lectura:** full-game sufre fuerte en odds >=1.6 (muestras pequeñas pero señal consistente de deterioro).

---

## 3) Odds (global NBA)

### ROI por buckets solicitados

| Odds bucket | n | Win rate | ROI |
|---|---:|---:|---:|
| <1.6 | 92 | 82.61% | 2.33% |
| 1.6-1.8 | 15 | 66.67% | -33.52% |
| 1.8-2.0 | 17 | 76.47% | 35.70% |
| >=2.0 | 5 | 20.00% | -137.38% |

### Hallazgo clave
- El bucket **>=2.0** sigue siendo el peor (confirmado), pero con n=5.
- El bucket **1.8–2.0** aparece fuerte positivo en este corte.
- El bucket **1.6–1.8** es negativo y relevante (n=15).

---

## 4) Confidence y calibración

## Redefinición de buckets (probabilidad continua)
Se evaluó por `probabilidad_sistema`:
- 0.80-1.00
- 0.70-0.79
- 0.60-0.69
- <0.50

| Bucket prob | n | Prob media | Hit rate observado | ROI |
|---|---:|---:|---:|---:|
| 0.80-1.00 | 64 | 0.8965 | 0.8125 | 17.97% |
| 0.70-0.79 | 30 | 0.7445 | 0.8667 | 27.32% |
| 0.60-0.69 | 26 | 0.6541 | 0.7308 | -33.40% |
| <0.50 | 9 | 0.3131 | 0.3333 | -190.89% |

### Lectura calibración
- En 0.70–0.79, observado > predicho (subconfianza relativa).
- En 0.80–1.00, observado < predicho (sobreconfianza relativa).
- En 0.60–0.69, hit rate aceptable pero ROI negativo: problema probablemente de precio/linea/sizing, no solo acierto.

---

## 5) Sample size y cobertura temporal

### Confirmación de rango temporal
- En `apuestas`: **2026-01-10 a 2026-02-22** (n=144 total; 129 resueltas).

### ¿Existen históricos fuera del análisis?
Sí.
- `predicciones_registradas`: 2026-01-10 a 2026-03-06 (n=2514)
- `partidos_baloncesto`: 2018-04-14 a 2026-03-15 (n=12492)

**Conclusión:** hay histórico adicional en tablas de predicciones y partidos que no entra en análisis de performance de apuestas ejecutadas (`apuestas`).

---

## Tablas comparativas rápidas

## Quarter vs Full (resueltas)
| Segmento | n | ROI |
|---|---:|---:|
| Quarter markets | 32 | 19.89% |
| Full-game markets | 97 | -5.22% |

## Odds extremo
| Segmento | n | ROI |
|---|---:|---:|
| Odds >=2.0 | 5 | -137.38% |
| Odds <1.6 | 92 | 2.33% |

---

## Recomendaciones estratégicas (sin tocar modelo aún)

1. **Enfoque operativo provisional en quarter markets (Q1/Q2)**
   - Mantener Q3 bajo observación/limitación por señal negativa y baja muestra.

2. **Restringir odds en full-game a <1.6 como baseline conservador temporal**
   - Evitar >=2.0 y vigilar 1.6–1.8 mientras se amplía muestra.

3. **Crear policy de mínimos de muestra por segmento antes de decisiones fuertes**
   - Ejemplo: n>=30 por bucket para decisiones de política estable.

4. **Separar diagnóstico de ROI en 3 ejes en próximos análisis**
   - acierto (hit rate), precio (odds), sizing (stake), para no confundir causa.

5. **Ampliar validación con tabla `predicciones_registradas`**
   - Para robustecer calibración/monotonicidad más allá de picks ejecutados.

---

## Conclusión

Con evidencia actual, el edge parece más claro en **quarter markets (especialmente Q1/Q2)** y en evitar extremos de odds altas.
El problema full-game no luce solo de acierto: hay señales de interacción con líneas/odds/sizing que requieren diagnóstico focalizado antes de cambiar modelo.

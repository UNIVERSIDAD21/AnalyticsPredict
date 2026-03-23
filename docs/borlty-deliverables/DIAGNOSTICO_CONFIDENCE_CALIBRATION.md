# DIAGNOSTICO_CONFIDENCE_CALIBRATION.md

## Alcance
Prioridad crítica 1 del bloque 05: diagnóstico de confidence/calibration en NBA, sin refactor masivo ni cambios de modelo.

## Problema exacto
Determinar si la anomalía de confidence proviene de:
- fórmula invertida,
- thresholds incorrectos,
- mala alineación con outcomes,
- error de normalización,
- mala ponderación de features,
- o combinación de factores.

---

## Localización de cálculo exacto (backend + frontend)

## Backend (fuente de verdad)
Archivo principal:
- `backend/motor/nba_predictor_cuartos.py`

Función clave:
- `determinar_confianza(desviacion_total, probabilidad, distancia_z)`

Reglas actuales:
1. **Volatilidad (score_vol):**
   - `desviacion_total < 5.5` → 2
   - `< 7.5` → 1
   - `>= 7.5` → 0
2. **Probabilidad (score_prob):**
   - `>= 0.70` → 2
   - `>= 0.60` → 1
   - resto → 0
3. **Edge-z (score_edge):**
   - `z >= 1.5` → 2
   - `z >= 1.0` → 1
   - resto → 0
4. **Nivel final (`FactoresConfianza.obtener_nivel` en `backend/motor/tipos.py`):**
   - score_total >= 3 → ALTA
   - score_total >= 2 → MEDIA
   - else → BAJA

## Sizing / stake
- En `analizar_partido(...)`:
  - `riesgo_alto = factores_confianza.volatilidad == "alta"`
  - `calcular_kelly(..., riesgo_alto=riesgo_alto)`
- En `backend/motor/calculadora_probabilidad.py`:
  - `riesgo_alto` aplica multiplicador `0.7` al sizing (penalización).

### Conclusión de dependencia stake↔confidence
- **No hay dependencia directa por nivel ALTA/MEDIA/BAJA** en stake.
- **Sí hay dependencia indirecta** por componente `volatilidad` del confidence (penalización de riesgo).

## Frontend
- `nivel_confianza` se usa para visualización/registro (`FormularioGuardarApuesta`, `ResultadoAnalisis`, `TablaApuestas`, etc.).
- No se detectó cálculo de confidence en frontend (consume lo producido por backend).

---

## Evidencia cuantitativa encontrada

Evidencia raw reproducible:
- `reports/auditoria_baselines/confidence_diagnostico_20260307T0108Z.json`

SQL reproducible:
- `docs/borlty-context/sql/DIAGNOSTICO_CONFIDENCE_CALIBRATION.sql`

### Reconstrucción global de confidence (dataset expanded)
| Nivel | n | hit_rate | roi_unit | prob_media | z_media |
|---|---:|---:|---:|---:|---:|
| ALTA | 210 | 0.7810 | 0.1441 | 0.9085 | 1.7092 |
| MEDIA | 276 | 0.6884 | 0.0703 | 0.7727 | 0.7549 |
| BAJA | 421 | 0.5701 | -0.0371 | 0.5971 | 0.2486 |

**Monotonicidad global:** se cumple (ALTA > MEDIA > BAJA en hit_rate y ROI unitario).

### Monotonicidad por mercado (resumen)
- **COMPLETO:** monotónico correcto.
- **Q1:** monotónico correcto.
- **Q2:** no monotónico (BAJA > MEDIA > ALTA por ROI/hit_rate).
- **Q3:** ALTA sale peor que MEDIA.
- **Q4:** ALTA sale peor que MEDIA.

### Componentes raíz
- Probabilidad `>=0.70` da señal positiva robusta (hit y ROI).
- Edge-z alto (`>=1.5`) también mejora claramente.
- **Volatilidad:** en dataset reconstruido quedó 100% en `vol_alta` (score_vol=0 siempre), por lo que **no discrimina**.

### Stake vs confidence en apuestas ejecutadas
- `apuestas`: stake promedio por confidence muy parecido (ALTA ~1446, MEDIA ~1558, BAJA ~1562).
- `stake_porcentaje`/`fraccion_kelly` aparecen nulos en registros analizados.

**Conclusión:** en operación observada, confidence no está gobernando sizing de forma efectiva por nivel.

---

## Causa raíz más probable

No hay evidencia de fórmula invertida en la asignación ALTA/MEDIA/BAJA.

La causa raíz más probable es combinada:
1. **Thresholds de volatilidad desalineados con escala real** (`score_vol` colapsa en 0 y pierde poder discriminante).
2. **Monotonicidad frágil por submercado (Q2/Q3/Q4)** por mezcla de pricing/linea y muestra por segmento.
3. **Desalineación entre confianza nominal y valor económico** en segmentos específicos (especialmente fuera de Q1/COMPLETO).

No se observó evidencia fuerte de error de normalización aislado en esta etapa.

---

## Impacto actual en stake y credibilidad

## Stake
- El nivel ALTA/MEDIA/BAJA no parece estar aplicándose como multiplicador directo de stake en producción observada.
- Existe penalización indirecta por `riesgo_alto` (volatilidad), pero al colapsar en una sola categoría, no aporta discriminación útil.

## Credibilidad
- A nivel global, confidence parece razonable.
- A nivel por mercado, la inconsistencia (Q2/Q3/Q4) erosiona confianza operativa si se usa confidence como señal universal.

---

## Decisión recomendada

1. **No declarar confidence “arreglado”**: queda diagnosticado, no resuelto.
2. **Política temporal:** no usar ALTA/MEDIA/BAJA como driver principal de sizing hasta recalibrar thresholds por mercado.
3. Mantener confidence solo como señal secundaria explicativa mientras se ejecuta recalibración de thresholds y validación de monotonicidad por mercado.

---

## Cambio aplicado o decisión de no tocar

**Decisión:** no se aplicó cambio de lógica en esta fase.

Justificación:
- El objetivo fue diagnóstico preciso con evidencia.
- Cambiar thresholds o comportamiento de sizing sin protocolo de validación por mercado puede introducir regresiones.

---

## Riesgos residuales

1. Seguir interpretando confidence como señal homogénea entre mercados puede inducir decisiones erróneas.
2. Volatilidad sin discriminación (score_vol colapsado) mantiene ruido en score total.
3. Si se usa confidence para stake sin policy temporal, se puede sobrerreaccionar en Q2/Q3/Q4.

---

## Estado de cierre de prioridad 1

- **Diagnóstico:** CERRADO
- **Corrección lógica definitiva:** ABIERTA (fase siguiente dentro del bloque 05)

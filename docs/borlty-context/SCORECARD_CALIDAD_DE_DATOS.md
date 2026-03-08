# SCORECARD_CALIDAD_DE_DATOS.md

Versión: v1  
Ámbito: Bloque 07.1 (Calidad de Datos)  
Dependencia directa: `DATA_QUALITY_RULES.md`

---

## 1. MODELO DE SCORECARD

### 1.1 Fórmula General

El score de calidad por dominio y periodo (`dq_score`) se calcula en escala **0 a 100**:

\[
\text{dq\_score} = \max\big(0,\ 100 - P_{severidad} - P_{volumen} - P_{drift}\big)
\]

Donde:

1. **Penalización por severidad (`P_severidad`)**
\[
P_{severidad} = 100 \times \sum_{r \in reglas\_dominio} \left( w_{sev}(r) \times w_{cat}(r) \times fail\_rate(r) \right)
\]

2. **Penalización por bajo volumen de datos (`P_volumen`)**
\[
P_{volumen} =
\begin{cases}
0 & coverage\_ratio \ge 1.0 \\
10 \times (1 - coverage\_ratio) & 0.5 \le coverage\_ratio < 1.0 \\
15 & coverage\_ratio < 0.5
\end{cases}
\]

3. **Penalización por drift (`P_drift`)**
\[
P_{drift} =
\begin{cases}
0 & \text{sin señales de drift} \\
5 & \text{1 alerta alta activa} \\
10 & \text{alerta crítica o 2 altas} \\
15 & \text{crítica por >=2 días}
\end{cases}
\]

> Para **NBA**, `P_drift` normalmente es 0 salvo hallazgo explícito.  
> Para **Fútbol**, `P_drift` aplica por defecto cuando `drift_futbol_residual` esté activo.

---

### 1.2 Pesos por severidad

- **Crítica:** `w_sev = 1.00`
- **Alta:** `w_sev = 0.60`
- **Media:** `w_sev = 0.30`

Racional: una falla crítica debe impactar de forma dominante el score, y las medias no deben ocultar fallas graves.

### 1.3 Pesos por categoría de regla

- Completitud: `w_cat = 0.24`
- Integridad lógica: `w_cat = 0.22`
- Integridad temporal: `w_cat = 0.12`
- Rangos/Outliers: `w_cat = 0.14`
- Freshness: `w_cat = 0.16`
- Coverage: `w_cat = 0.12`

Suma = 1.00.

### 1.4 Definición de `fail_rate(r)`

\[
fail\_rate(r) = \frac{failed\_rows(r)}{total\_rows\_evaluados(r)}
\]

Si `total_rows_evaluados = 0`, la regla queda en estado **N/A** (no penaliza) y se registra para auditoría.

---

## 2. NIVELES DE CALIDAD (A/B/C)

### 2.1 Umbrales por score

- **A (Excelente):** `dq_score >= 85`
- **B (Aceptable):** `70 <= dq_score < 85`
- **C (Deficiente):** `dq_score < 70`

### 2.2 Reglas de override por criticidad

Para evitar “maquillaje estadístico”:

1. Si existe **>=1 regla crítica** con `fail_rate > 0`, el nivel máximo posible es **B**.
2. Si existen **>=2 reglas críticas** activas o una crítica con `fail_rate >= 5%`, el nivel es **C** automático.
3. En Fútbol, si `drift_futbol_residual` está en estado rojo, el nivel máximo posible es **B**, aunque el score numérico sea A.

---

## 3. CÁLCULO AUTOMÁTICO

### 3.1 Entradas requeridas

Tabla operativa de resultados de reglas (`dq_rule_results`) con estructura mínima:

- `periodo`
- `domain` (`NBA` / `FUTBOL`)
- `rule_id`
- `category`
- `severity`
- `failed_rows`
- `total_rows`
- `fail_rate`
- `drift_signal` (bool)

### 3.2 Salida esperada del scorecard

Tabla `dq_scorecard_daily`:

- `periodo`
- `domain`
- `score`
- `nivel` (A/B/C)
- `critical_fail_count`
- `high_fail_count`
- `drift_status` (none/yellow/orange/red)
- `source_quality_flag` (A/B/C)
- `residual_warning`
- `created_at`

### 3.3 SQL de referencia (agregación principal)

```sql
WITH base AS (
  SELECT
    periodo,
    domain,
    category,
    severity,
    SUM(failed_rows)::numeric AS failed_rows,
    SUM(total_rows)::numeric AS total_rows,
    CASE WHEN SUM(total_rows)=0 THEN NULL
         ELSE SUM(failed_rows)::numeric / SUM(total_rows)::numeric END AS fail_rate,
    MAX(CASE WHEN drift_signal THEN 1 ELSE 0 END) AS drift_signal
  FROM dq_rule_results
  GROUP BY 1,2,3,4
),
penal AS (
  SELECT
    periodo,
    domain,
    SUM(
      (CASE severity
         WHEN 'Crítica' THEN 1.00
         WHEN 'Alta'    THEN 0.60
         ELSE 0.30 END)
      *
      (CASE category
         WHEN 'Completitud'       THEN 0.24
         WHEN 'IntegridadLogica'  THEN 0.22
         WHEN 'IntegridadTemporal'THEN 0.12
         WHEN 'RangosOutliers'    THEN 0.14
         WHEN 'Freshness'         THEN 0.16
         WHEN 'Coverage'          THEN 0.12
         ELSE 0.0 END)
      * COALESCE(fail_rate,0)
    ) * 100.0 AS p_severidad,
    SUM(CASE WHEN severity='Crítica' AND COALESCE(fail_rate,0) > 0 THEN 1 ELSE 0 END) AS critical_fail_count,
    SUM(CASE WHEN severity='Alta'    AND COALESCE(fail_rate,0) > 0 THEN 1 ELSE 0 END) AS high_fail_count,
    MAX(drift_signal) AS drift_signal
  FROM base
  GROUP BY 1,2
)
SELECT
  periodo,
  domain,
  GREATEST(0, 100 - p_severidad
              - CASE WHEN drift_signal=1 AND domain='FUTBOL' THEN 10 ELSE 0 END
          ) AS score,
  critical_fail_count,
  high_fail_count
FROM penal;
```

---

## 4. DIFERENCIACIÓN NBA VS FÚTBOL

### 4.1 Política de score para NBA

- Umbrales estándar A/B/C.
- Sin penalización de drift por defecto.
- Mayor tolerancia cero en completitud/freshness por estado operacional.

### 4.2 Política de score para Fútbol

- Mismos umbrales base, pero con penalización activa de drift (`P_drift`).
- Regla de gobernanza: no promover a “A operativo” con warning `drift_futbol_residual` rojo.
- Las mejoras de score deben leerse como **progreso de control**, no como deuda resuelta.

---

## 5. MAPEO A FLAGS Y CAPA ANALÍTICA

### 5.1 `source_quality_flag`

Mapeo directo por score final:

- `A` si `score >= 85` y sin override crítico.
- `B` si `70 <= score < 85` o aplica override de criticidad/drift.
- `C` si `score < 70` o aplica regla de C automático.

### 5.2 `residual_warning`

- Si falla regla asociada a confidence: anexar `confidence_temporal_policy_activa`.
- Si hay señal de drift fútbol: anexar `drift_futbol_residual`.
- Si ambas aplican: `drift_futbol_residual;confidence_temporal_policy_activa`.

### 5.3 Vistas de consumo

1. `analytics.vw_data_quality_core`: entrada principal de completeness/freshness/outlier/coverage.
2. `analytics.vw_nba_vs_futbol_madurez_operativa`: consumo de score agregado por dominio.
3. `analytics.vw_calibration_scorecard`: contexto para reglas de integridad lógica vinculadas a probabilidad.

---

## 6. REGLAS OPERACIONALES PARA EXPLICABILIDAD (BLOQUE 07.2)

1. **Nivel A:** explicabilidad completa sin bloqueo, con nota estándar de trazabilidad.
2. **Nivel B:** explicabilidad permitida con disclaimer de calidad.
3. **Nivel C:** explicabilidad restringida; obligatorio warning visible y recomendación de no tomar decisiones de alto impacto sin revisión.

Política explícita: **no explicar resultados C como si fueran confiables**.

---

## 7. TRACKING TEMPORAL Y GOBIERNO

### 7.1 Métricas históricas mínimas

- `score_ma7` (media móvil 7 días)
- `score_ma28` (media móvil 28 días)
- `dias_consecutivos_C`
- `count_alertas_drift`

### 7.2 Alertas operacionales

- **Alerta preventiva:** caída >= 5 puntos vs MA7.
- **Alerta alta:** 2 días consecutivos en C.
- **Alerta crítica:** C + falla crítica activa + drift rojo en fútbol.

### 7.3 Criterio de mejora real

Solo se considera mejora sostenida cuando:
1. `score_ma7` sube >= 5 puntos.
2. No hay nuevas fallas críticas 7 días.
3. En fútbol, disminuye frecuencia de alertas drift (no solo variación puntual del score).

---

## 8. EJEMPLO DE CÁLCULO

Supuesto NBA diario:
- `P_severidad = 18.5`
- `P_volumen = 2.0`
- `P_drift = 0`

Resultado:
- `dq_score = 100 - 18.5 - 2.0 = 79.5`
- Nivel base: **B**
- Si hay 1 crítica activa: se mantiene **B** (override evita A)

Supuesto Fútbol diario:
- `P_severidad = 14.0`
- `P_volumen = 3.0`
- `P_drift = 10`

Resultado:
- `dq_score = 73.0`
- Nivel base: **B**
- Con drift naranja activo, se mantiene B con `residual_warning` obligatorio.

---

## 9. CONDICIONES DE IMPLEMENTACIÓN v1

1. El scorecard debe ejecutarse automáticamente por `periodo` y `domain`.
2. Cada score debe ser trazable a reglas y consultas de `DATA_QUALITY_RULES.md`.
3. Los niveles A/B/C deben alimentar `source_quality_flag` sin ambigüedad.
4. En Fútbol, drift se reporta como **detectado y medido**, no como resuelto.
5. Cualquier cambio de pesos/umbrales requiere versionado (`v2`, `v3`) y comparabilidad histórica.

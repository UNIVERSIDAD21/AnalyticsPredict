# SCORECARD_CALIDAD_DE_DATOS.md

Versión: v1.1  
Ámbito: Bloque 07.1 (Calidad de Datos)  
Base normativa: `DATA_QUALITY_RULES.md`  
Propósito: medir calidad de datos de forma objetiva y trazable (no resolver deuda técnica automáticamente).

---

## 1. MODELO DE SCORECARD

### 1.1 Fórmula General

Para cada `domain` (NBA/FUTBOL) y `periodo`:

\[
Score_{dominio} = \max(0,\ 100 - P_{comp} - P_{drift} - P_{partial})
\]

Donde:
- \(P_{comp}\): penalización ponderada por componentes de calidad.
- \(P_{drift}\): penalización específica por señales de drift (principalmente fútbol).
- \(P_{partial}\): penalización por datos parciales / baja cobertura de ejecución.

Desglose por componente:

\[
P_{comp} = \sum_{c \in C} \left( W_{c,dominio} \times Pen_{c} \right)
\]

Con:

\[
Pen_{c} = 100 \times \sum_{r \in reglas(c)}\left(w_{sev}(r)\times fail\_rate(r)\right) / \sum_{r \in reglas(c)}w_{sev}(r)
\]

y

\[
fail\_rate(r)=\frac{failed\_rows(r)}{total\_rows(r)}
\]

Pesos de severidad:
- Crítica = 1.00
- Alta = 0.60
- Media = 0.30

---

### 1.2 Pesos por Componente

| Componente | Peso NBA | Peso Fútbol | Justificación |
|------------|----------|-------------|---------------|
| Completitud | 0.25 | 0.22 | En NBA (operacional) falta de campos críticos impacta directamente operación. En fútbol sigue alto pero ligeramente menor por etapa de desarrollo. |
| Integridad Lógica | 0.22 | 0.20 | Errores de coherencia afectan KPIs predictivos en ambos dominios. |
| Integridad Temporal | 0.12 | 0.12 | Importante para series y trazabilidad, pero subordinado a completitud/lógica. |
| Rangos y Outliers | 0.14 | 0.14 | Detecta ruido y anomalías que distorsionan scorecards. |
| Freshness | 0.15 | 0.12 | NBA exige mayor frescura operativa; fútbol tiene tolerancia mayor por madurez. |
| Coverage | 0.12 | 0.20 | En fútbol la cobertura es crítica para no inferir sobre muestra débil. |

Validación: suma por dominio = 1.00.

---

### 1.3 Cálculo por Componente

#### Completitud
- **Fórmula:** promedio ponderado de `fail_rate` de reglas `*-COMP-*`.
- **Penalización por severidad:** crítica pesa 1.00; alta 0.60.
- **Valores faltantes:** si `total_rows=0` en una regla, queda `N/A` y no penaliza; se registra evento.

#### Integridad Lógica
- **Fórmula:** promedio ponderado de reglas `*-LOG-*`.
- **Penalización por severidad:** mayor castigo en violaciones de rango probabilístico y coherencia resultado/ganancia.
- **Valores faltantes:** `N/A` si no hay universo evaluable; si hay universo y campo nulo no permitido, sí penaliza.

#### Integridad Temporal
- **Fórmula:** promedio ponderado de reglas `*-TMP-*`.
- **Penalización:** alta para incoherencias de resolución; media para desalineación leve de timestamps.
- **Valores faltantes:** ausencia de timestamps obligatorios en universo evaluable cuenta como falla.

#### Rangos y Outliers
- **Fórmula:** promedio ponderado de reglas `*-RNG-*`.
- **Penalización:** alta en outliers extremos de ROI.
- **Valores faltantes:** si métrica no aplica por fuente, `N/A`; si aplica y viene nula en exceso, se captura por completitud.

#### Freshness
- **Fórmula:** evaluación de reglas `*-FRSH-*` por lag y completitud diaria mínima.
- **Penalización:** alta por lag excesivo; crítica por degradación de completitud mínima.
- **Valores faltantes:** si no hay timestamp de referencia, falla por completitud/freshness.

#### Coverage
- **Fórmula:** evaluación de reglas `*-COV-*` y proporción de cobertura mínima.
- **Penalización:** alta cuando hay quiebres fuertes entre fuentes o outlier_rate elevado; media por baja cobertura absoluta.
- **Valores faltantes:** `source_coverage` nulo se trata como 0.

---

## 2. NIVELES DE CALIDAD

### 2.1 Definición de Niveles

| Nivel | Rango Score | Descripción | Acción Recomendada |
|-------|-------------|-------------|-------------------|
| A | 90-100 | Excelente | Uso normal |
| B | 70-89 | Aceptable | Uso con precaución |
| C | <70 | Deficiente | NO usar / Alerta |

Reglas de override:
1. Si hay >=1 regla crítica activa, el máximo nivel posible es B.
2. Si hay >=2 reglas críticas activas o una crítica con `fail_rate >= 5%`, nivel automático C.

### 2.2 Niveles por Dominio

- **NBA:** usa umbrales estándar A/B/C sin ajuste.
- **Fútbol:** mantiene umbrales base, pero con penalización adicional por drift:
  - drift amarillo: -5 puntos
  - drift naranja: -10 puntos
  - drift rojo: -15 puntos

Además, con drift rojo activo, el nivel máximo operativo es B aunque score numérico caiga en A.

---

## 3. CÁLCULO OPERACIONAL

### 3.1 Consulta SQL de Scorecard

```sql
-- SCORECARD diario por dominio (NBA/FUTBOL)
-- Requiere tabla previa: dq_rule_results
-- Campos mínimos: periodo, domain, rule_id, category, severity, failed_rows, total_rows, drift_signal_level

WITH base AS (
  SELECT
    periodo::date AS periodo,
    UPPER(domain) AS domain,
    rule_id,
    category,
    severity,
    SUM(failed_rows)::numeric AS failed_rows,
    SUM(total_rows)::numeric AS total_rows,
    CASE WHEN SUM(total_rows)=0 THEN NULL
         ELSE SUM(failed_rows)::numeric / SUM(total_rows)::numeric END AS fail_rate,
    MAX(COALESCE(drift_signal_level, 'none')) AS drift_signal_level
  FROM dq_rule_results
  GROUP BY 1,2,3,4,5
),
comp AS (
  SELECT
    periodo,
    domain,
    category,
    SUM(
      (CASE severity WHEN 'Crítica' THEN 1.00 WHEN 'Alta' THEN 0.60 ELSE 0.30 END)
      * COALESCE(fail_rate,0)
    )
    /
    NULLIF(SUM(CASE severity WHEN 'Crítica' THEN 1.00 WHEN 'Alta' THEN 0.60 ELSE 0.30 END),0)
    AS component_fail,
    SUM(CASE WHEN severity='Crítica' AND COALESCE(fail_rate,0) > 0 THEN 1 ELSE 0 END) AS critical_fail_count,
    MAX(drift_signal_level) AS drift_signal_level,
    SUM(CASE WHEN total_rows = 0 THEN 1 ELSE 0 END) AS na_rules,
    COUNT(*) AS total_rules
  FROM base
  GROUP BY 1,2,3
),
weights AS (
  SELECT 'NBA'::text AS domain, 'Completitud'::text AS category, 0.25::numeric AS w UNION ALL
  SELECT 'NBA','IntegridadLogica',0.22 UNION ALL
  SELECT 'NBA','IntegridadTemporal',0.12 UNION ALL
  SELECT 'NBA','RangosOutliers',0.14 UNION ALL
  SELECT 'NBA','Freshness',0.15 UNION ALL
  SELECT 'NBA','Coverage',0.12 UNION ALL
  SELECT 'FUTBOL','Completitud',0.22 UNION ALL
  SELECT 'FUTBOL','IntegridadLogica',0.20 UNION ALL
  SELECT 'FUTBOL','IntegridadTemporal',0.12 UNION ALL
  SELECT 'FUTBOL','RangosOutliers',0.14 UNION ALL
  SELECT 'FUTBOL','Freshness',0.12 UNION ALL
  SELECT 'FUTBOL','Coverage',0.20
),
agg AS (
  SELECT
    c.periodo,
    c.domain,
    SUM(w.w * (100.0 * COALESCE(c.component_fail,0))) AS p_comp,
    SUM(c.critical_fail_count) AS critical_fail_count,
    MAX(c.drift_signal_level) AS drift_signal_level,
    SUM(c.na_rules)::numeric / NULLIF(SUM(c.total_rules),0)::numeric AS na_ratio
  FROM comp c
  JOIN weights w
    ON w.domain = c.domain
   AND w.category = c.category
  GROUP BY 1,2
),
final AS (
  SELECT
    periodo,
    domain,
    p_comp,
    CASE
      WHEN domain='FUTBOL' AND drift_signal_level='yellow' THEN 5
      WHEN domain='FUTBOL' AND drift_signal_level='orange' THEN 10
      WHEN domain='FUTBOL' AND drift_signal_level='red' THEN 15
      ELSE 0
    END::numeric AS p_drift,
    CASE
      WHEN na_ratio IS NULL THEN 0
      WHEN na_ratio <= 0.10 THEN 0
      WHEN na_ratio <= 0.30 THEN 5
      ELSE 10
    END::numeric AS p_partial,
    critical_fail_count,
    drift_signal_level
  FROM agg
)
SELECT
  periodo,
  domain,
  GREATEST(0, 100 - p_comp - p_drift - p_partial) AS score_final,
  CASE
    WHEN critical_fail_count >= 2 THEN 'C'
    WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'A'
    WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 70 THEN 'B'
    ELSE 'C'
  END AS nivel_base,
  CASE
    WHEN critical_fail_count >= 2 THEN 'C'
    WHEN critical_fail_count >= 1 AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
    WHEN domain='FUTBOL' AND drift_signal_level='red' AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
    WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'A'
    WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 70 THEN 'B'
    ELSE 'C'
  END AS nivel_final,
  p_comp,
  p_drift,
  p_partial,
  critical_fail_count,
  drift_signal_level,
  CASE
    WHEN (CASE
            WHEN critical_fail_count >= 2 THEN 'C'
            WHEN critical_fail_count >= 1 AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
            WHEN domain='FUTBOL' AND drift_signal_level='red' AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
            WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'A'
            WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 70 THEN 'B'
            ELSE 'C' END) = 'A' THEN 'A'
    WHEN (CASE
            WHEN critical_fail_count >= 2 THEN 'C'
            WHEN critical_fail_count >= 1 AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
            WHEN domain='FUTBOL' AND drift_signal_level='red' AND GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'B'
            WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 90 THEN 'A'
            WHEN GREATEST(0, 100 - p_comp - p_drift - p_partial) >= 70 THEN 'B'
            ELSE 'C' END) = 'B' THEN 'B'
    ELSE 'C'
  END AS source_quality_flag,
  CASE
    WHEN domain='FUTBOL' AND drift_signal_level IN ('yellow','orange','red') THEN 'drift_futbol_residual'
    ELSE NULL
  END AS residual_warning
FROM final;
```

### 3.2 Frecuencia de Cálculo

- **Recalculo:** diario (corte UTC), con opción intradía cada 6h para monitoreo.
- **Histórico:** sí, almacenamiento incremental por `periodo + domain`.
- **Contenedor recomendado:**
  - tabla materializada: `analytics.dq_scorecard_daily`
  - vista de consumo: `analytics.vw_dq_scorecard_latest`

---

## 4. INTEGRACIÓN CON BLOQUE 06

### 4.1 Vistas Afectadas

1. `analytics.vw_data_quality_core`
   - incluir `score_final`, `nivel_final`, `source_quality_flag`.
   - mostrar `residual_warning` cuando aplique.

2. `analytics.vw_nba_vs_futbol_madurez_operativa`
   - incorporar score agregado por dominio para contexto de madurez.
   - filtrar o etiquetar explícitamente nivel C.

3. `analytics.vw_calibration_scorecard`
   - mostrar advertencia cuando nivel C o warning de drift esté activo.

4. `analytics.vw_perf_market_odds_confidence`
   - incluir join de score para no interpretar desempeño sin contexto de calidad.

### 4.2 Contratos de Datos

No deben servir datos “sin advertencia” cuando `nivel_final='C'`:

- vistas/consumos operativos para decisiones automáticas,
- endpoints de recomendaciones de apuesta,
- reportes ejecutivos sin capa de disclaimer.

Política:
1. Si nivel C: bloquear consumo automático o devolver estado `QUALITY_BLOCKED`.
2. Si nivel B: permitir con `warning` explícito.
3. Si nivel A: consumo normal.

---

## 5. CASOS ESPECIALES

### 5.1 Tratamiento de Drift Fútbol

- El drift **reduce score**, no “se resuelve” por score.
- Penalización aplicada en `P_drift`:
  - amarillo: -5
  - naranja: -10
  - rojo: -15
- Con drift rojo, máximo nivel operativo = B.
- `residual_warning` obligatorio: `drift_futbol_residual`.

### 5.2 Datos Parciales

Cuando hay baja evaluabilidad (`N/A` alto por ausencia de datos):

1. calcular `na_ratio = reglas_na / reglas_totales`.
2. aplicar `P_partial`:
   - `na_ratio <= 10%`: 0
   - `10% < na_ratio <= 30%`: -5
   - `na_ratio > 30%`: -10
3. registrar estado `PARTIAL_DATA` para trazabilidad.

Interpretación: el score con datos parciales sigue siendo válido como **señal de riesgo**, no como certificación de calidad plena.

---

## Cierre de gobierno

Este scorecard:
- **mide** degradación/mejora de calidad,
- habilita decisiones operativas con umbrales claros,
- y expone deuda residual (especialmente drift fútbol),

pero **no soluciona por sí mismo** los problemas de origen.

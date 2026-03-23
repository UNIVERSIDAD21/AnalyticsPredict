# ALERTAS_DE_CALIDAD.md

Versión: v1  
Ámbito: Bloque 07.1 (Calidad de Datos)  
Dependencias: `DATA_QUALITY_RULES.md`, `SCORECARD_CALIDAD_DE_DATOS.md`

> Este sistema de alertas **detecta y prioriza** problemas de calidad. No los previene ni los corrige por sí mismo.

---

## 1. CATÁLOGO DE ALERTAS

### 1.1 Alertas Críticas

| ID Alerta | Nombre | Disparador | Condición | Frecuencia Check | Canal | SLA Respuesta |
|-----------|--------|------------|-----------|------------------|-------|---------------|
| DQ-CRIT-01 | Caída a nivel C en NBA | Scorecard diario | `domain='NBA' AND nivel_final='C'` | Cada 1h | Primario: Pager/Telegram ops | 30 min |
| DQ-CRIT-02 | Falla crítica múltiple en NBA | Reglas DQ | `critical_fail_count >= 2` en NBA | Cada 30 min | Primario: Pager/Telegram ops | 30 min |
| DQ-CRIT-03 | Drift rojo fútbol sostenido | Señales drift | `domain='FUTBOL' AND drift_signal='red'` por >=2 checks | Cada 30 min | Primario: Telegram ops + Backup email | 1h |
| DQ-CRIT-04 | Freshness severa en producción NBA | Reglas freshness | Lag >72h en `apuestas` o `predicciones_registradas` | Cada 1h | Primario: Pager/Telegram ops | 30 min |

### 1.2 Alertas de Alta Prioridad

| ID Alerta | Nombre | Disparador | Condición | Frecuencia Check | Canal | SLA Respuesta |
|-----------|--------|------------|-----------|------------------|-------|---------------|
| DQ-HIGH-01 | Degradación a nivel B en NBA | Scorecard diario | `domain='NBA' AND nivel_final='B'` con caída >=10 pts vs MA7 | Cada 2h | Telegram ops | 4h |
| DQ-HIGH-02 | Completeness degradada NBA | Reglas completitud | `completeness_rate < 0.95` en fuentes NBA | Cada 2h | Telegram ops | 4h |
| DQ-HIGH-03 | Outlier rate elevado NBA | Reglas outliers | `outlier_rate > 0.10` | Cada 2h | Telegram ops | 4h |
| DQ-HIGH-04 | Cobertura colapsada fútbol | Reglas coverage | `source_coverage` fútbol cae >40% vs MA7 | Cada 2h | Telegram ops | 4h |
| DQ-HIGH-05 | Drift naranja fútbol | Señales drift | `drift_signal='orange'` | Cada 1h | Telegram ops | 4h |

### 1.3 Alertas de Media Prioridad

| ID Alerta | Nombre | Disparador | Condición | Frecuencia Check | Canal | SLA Respuesta |
|-----------|--------|------------|-----------|------------------|-------|---------------|
| DQ-MED-01 | Cobertura baja NBA | Reglas coverage | `source_coverage < 30` en NBA | Diario | Dashboard + resumen diario | 24h |
| DQ-MED-02 | Cobertura baja fútbol | Reglas coverage | `source_coverage < 10` en fútbol | Diario | Dashboard + resumen diario | 24h |
| DQ-MED-03 | Integridad temporal degradada | Reglas temporales | >=1 regla temporal en fail_rate >2% | Diario | Dashboard + resumen diario | 24h |
| DQ-MED-04 | Aumento de reglas N/A | Scorecard parcial | `na_ratio > 0.30` | Diario | Dashboard + resumen diario | 24h |
| DQ-MED-05 | Drift amarillo fútbol | Señales drift | `drift_signal='yellow'` | Cada 4h | Dashboard + Telegram hilo calidad | 24h |

---

## 2. MATRIZ DE SEVERIDAD

### 2.1 Criterios de Clasificación

| Severidad | Criterios | Ejemplos | Acción Esperada |
|-----------|-----------|----------|-----------------|
| CRÍTICA | Riesgo inmediato para decisiones operativas o score C en NBA | `DQ-CRIT-01`, `DQ-CRIT-02` | Acción inmediata |
| ALTA | Degradación significativa que puede escalar a crítica en horas | `DQ-HIGH-02`, `DQ-HIGH-04` | Acción en 4h |
| MEDIA | Señales tempranas o degradación acotada | `DQ-MED-01`, `DQ-MED-05` | Revisión diaria |

### 2.2 Escalamiento

- **Cuándo escala:**
  1. CRÍTICA no reconocida en 15 min.
  2. ALTA no atendida en 4h.
  3. MEDIA repetida >3 días seguidos.
- **A quién escala:**
  - Nivel 1: responsable de calidad de datos.
  - Nivel 2: líder técnico AnalyticsPredict.
  - Nivel 3: owner operativo del dominio.
- **Información adicional al escalar:**
  - score actual + variación MA7,
  - reglas violadas (top 3 por impacto),
  - dominio/fuente/período,
  - runbook sugerido y owner asignado.

---

## 3. CANALES Y FORMATO

### 3.1 Canales por Severidad

| Severidad | Canal Primario | Canal Backup | Formato Mensaje |
|-----------|----------------|--------------|-----------------|
| CRÍTICA | Pager/Telegram directo ops | Email + dashboard | Mensaje corto + bloque técnico |
| ALTA | Telegram canal ops | Dashboard | Mensaje con contexto y acción |
| MEDIA | Dashboard diario | Resumen Telegram diario | Resumen agregado |

### 3.2 Plantillas de Mensajes

**Template CRÍTICA**
```text
[CRÍTICA] [DOMINIO] [COMPONENTE]
Descripción: <qué pasó>
Impacto: <riesgo operativo inmediato>
Datos afectados: <fuentes/vistas/periodo>
Acción sugerida: <paso 1, paso 2>
Contexto: score=<x>, nivel=<x>, reglas=<ids>, drift=<estado>
```

**Template ALTA**
```text
[ALTA] [DOMINIO] [COMPONENTE]
Descripción: <degradación detectada>
Impacto: <afecta reportes/score>
Datos afectados: <fuentes/periodo>
Acción sugerida: <validación + corrección>
Contexto: score=<x>, delta_ma7=<x>, reglas=<ids>
```

**Template MEDIA**
```text
[MEDIA] [DOMINIO] [COMPONENTE]
Descripción: <señal preventiva>
Impacto: <potencial si persiste>
Datos afectados: <scope>
Acción sugerida: <revisión en rutina diaria>
Contexto: tendencia=<x>, reglas=<ids>
```

---

## 4. ESTRATEGIA ANTI-RUIDO

### 4.1 Suppression Rules

1. **No duplicar** misma alerta (`alert_key`) en ventana de 6h si estado no cambió.
2. **Debounce**: exigir 2 checks consecutivos para abrir alerta ALTA/MEDIA (excepto CRÍTICA).
3. **Mute temporal**: al estar en `acknowledged`, solo reenviar si empeora severidad.
4. **Dedupe cross-source**: si múltiples reglas apuntan al mismo incidente raíz, emitir alerta agrupada.

### 4.2 Umbrales Dinámicos

- **NBA (producción):** umbrales más estrictos (freshness/completitud/cobertura).
- **Fútbol (desarrollo):** tolerancia mayor en coverage y freshness, pero castigo fuerte en drift.
- Ajuste automático por contexto:
  - baja estacional esperada de volumen -> relajar cobertura un 15%.
  - durante ventanas de mantenimiento -> suspensión controlada de alertas media.

### 4.3 Alertas Agrupadas

Agrupar cuando:
1. mismo dominio,
2. misma ventana de 2h,
3. mismo componente raíz (ej. Freshness).

Formato de resumen:
```text
[RESUMEN DQ] [DOMINIO] [VENTANA]
Alertas agrupadas: <n>
Más severa: <id>
Componentes afectados: <lista>
Top reglas: <r1,r2,r3>
Acción sugerida única: <runbook raíz>
```

---

## 5. INTEGRACIÓN OPERACIONAL

### 5.1 Tabla de Registro

```sql
CREATE TABLE IF NOT EXISTS analytics.data_quality_alerts (
  id BIGSERIAL PRIMARY KEY,
  alert_key TEXT NOT NULL,
  alert_id TEXT NOT NULL,
  domain TEXT NOT NULL CHECK (domain IN ('NBA','FUTBOL')),
  severity TEXT NOT NULL CHECK (severity IN ('CRITICA','ALTA','MEDIA')),
  component TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','acknowledged','resolved','suppressed')),
  trigger_value NUMERIC,
  threshold_value NUMERIC,
  condition_text TEXT NOT NULL,
  score_actual NUMERIC,
  score_nivel TEXT,
  drift_signal TEXT,
  violated_rules TEXT,
  data_scope JSONB,
  message_payload JSONB,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  acknowledged_at TIMESTAMPTZ,
  resolved_at TIMESTAMPTZ,
  owner TEXT,
  response_sla_minutes INT,
  response_elapsed_minutes INT,
  escalation_level INT NOT NULL DEFAULT 0,
  dedupe_hash TEXT,
  UNIQUE(alert_key, status)
);

CREATE INDEX IF NOT EXISTS idx_dq_alerts_domain_severity_status
  ON analytics.data_quality_alerts(domain, severity, status);

CREATE INDEX IF NOT EXISTS idx_dq_alerts_last_seen
  ON analytics.data_quality_alerts(last_seen_at DESC);
```

### 5.2 Dashboard de Alertas

- **Vista activa recomendada:** `analytics.vw_data_quality_alerts_active`
  - filtra `status IN ('open','acknowledged')`.
- **Vista histórica:** `analytics.vw_data_quality_alerts_history`
  - incluye MTTA/MTTR por severidad y dominio.
- Integración con bloque 06:
  - `vw_data_quality_core` + `dq_scorecard_daily` + `data_quality_alerts` en panel único.

### 5.3 Proceso de Resolución

1. `open` -> alerta creada.
2. `acknowledged` -> responsable toma ownership y plan.
3. `resolved` -> condición vuelve a normalidad por 2 checks consecutivos.
4. `suppressed` -> ruido controlado con justificación y vencimiento.

Tracking:
- **MTTA:** `acknowledged_at - first_seen_at`
- **MTTR:** `resolved_at - first_seen_at`
- auditoría de `owner`, `escalation_level`, `message_payload`.

---

## 6. CASOS ESPECIALES

### 6.1 Drift Runtime Fútbol

Alertas específicas:
- `DQ-CRIT-03` (rojo sostenido)
- `DQ-HIGH-05` (naranja)
- `DQ-MED-05` (amarillo)

Umbral de drift aceptable:
- Amarillo aislado: aceptable con seguimiento.
- Naranja: requiere intervención en <4h.
- Rojo: incidente crítico.

Acción cuando se excede:
1. mantener `residual_warning='drift_futbol_residual'`,
2. bloquear promoción automática de nivel A,
3. ejecutar verificación de columnas canónicas vs legacy,
4. registrar incidente y plan de remediación.

### 6.2 Modo Desarrollo vs Producción

- **NBA (producción):**
  - tolerancia baja al error,
  - alertas más frecuentes,
  - SLA más exigente.

- **Fútbol (desarrollo):**
  - tolerancia mayor en coverage/freshness,
  - foco en detectar drift y regresiones estructurales,
  - severidad ajustada para evitar spam, sin ocultar riesgo real.

---

## Cierre

El sistema está diseñado para priorizar señales útiles, reducir ruido y acelerar respuesta operativa.  
Las alertas son un mecanismo de detección y coordinación; la resolución depende de la remediación técnica en fuentes, contratos y pipelines.

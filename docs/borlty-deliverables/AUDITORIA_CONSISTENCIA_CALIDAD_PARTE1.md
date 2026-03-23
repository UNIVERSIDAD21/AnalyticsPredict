# AUDITORIA_CONSISTENCIA_CALIDAD_PARTE1.md

Fecha: 2026-03-08  
Auditoría: Consistencia Reglas → Scorecard → Alertas (Bloque 07.1)  
Fuentes auditadas:
- `DATA_QUALITY_RULES.md`
- `SCORECARD_CALIDAD_DE_DATOS.md`
- `ALERTAS_DE_CALIDAD.md`

Resultado ejecutivo: **Framework mayormente coherente, con 1 gap crítico (BLOCKER) en cobertura explícita de contratos legacy.**

---

## 1. MATRIZ DE COBERTURA

### 1.1 Reglas → Scorecard

| ID Regla | Componente Scorecard | Peso en Fórmula | ✓/✗ |
|----------|----------------------|-----------------|-----|
| NBA-COMP-01 | Completitud | 0.25 (NBA) | ✓ |
| NBA-COMP-02 | Completitud | 0.25 (NBA) | ✓ |
| NBA-COMP-03 | Completitud | 0.25 (NBA) | ✓ |
| FUT-COMP-01 | Completitud | 0.22 (FUTBOL) | ✓ |
| FUT-COMP-02 | Completitud | 0.22 (FUTBOL) | ✓ |
| NBA-LOG-01 | IntegridadLógica | 0.22 (NBA) | ✓ |
| NBA-LOG-02 | IntegridadLógica | 0.22 (NBA) | ✓ |
| NBA-LOG-03 | IntegridadLógica | 0.22 (NBA) | ✓ |
| FUT-LOG-01 | IntegridadLógica | 0.20 (FUTBOL) | ✓ |
| FUT-LOG-02 | IntegridadLógica | 0.20 (FUTBOL) | ✓ |
| NBA-TMP-01 | IntegridadTemporal | 0.12 (NBA) | ✓ |
| NBA-TMP-02 | IntegridadTemporal | 0.12 (NBA) | ✓ |
| FUT-TMP-01 | IntegridadTemporal | 0.12 (FUTBOL) | ✓ |
| FUT-TMP-02 | IntegridadTemporal | 0.12 (FUTBOL) | ✓ |
| NBA-RNG-01 | RangosOutliers | 0.14 (NBA) | ✓ |
| NBA-RNG-02 | RangosOutliers | 0.14 (NBA) | ✓ |
| NBA-RNG-03 | RangosOutliers | 0.14 (NBA) | ✓ |
| FUT-RNG-01 | RangosOutliers | 0.14 (FUTBOL) | ✓ |
| FUT-RNG-02 | RangosOutliers | 0.14 (FUTBOL) | ✓ |
| NBA-FRSH-01 | Freshness | 0.15 (NBA) | ✓ |
| NBA-FRSH-02 | Freshness | 0.15 (NBA) | ✓ |
| FUT-FRSH-01 | Freshness | 0.12 (FUTBOL) | ✓ |
| FUT-FRSH-02 | Freshness | 0.12 (FUTBOL) | ✓ |
| NBA-COV-01 | Coverage | 0.12 (NBA) | ✓ |
| NBA-COV-02 | Coverage | 0.12 (NBA) | ✓ |
| NBA-COV-03 | Coverage | 0.12 (NBA) | ✓ |
| NBA-COV-04 | Coverage | 0.12 (NBA) | ✓ |
| FUT-COV-01 | Coverage | 0.20 (FUTBOL) | ✓ |
| FUT-COV-02 | Coverage | 0.20 (FUTBOL) | ✓ |
| NBA-DOM-01 | Coverage/Completitud operacional | 0.12/0.25 (NBA) | ✓ |
| NBA-DOM-02 | Coverage/Completitud operacional | 0.12/0.25 (NBA) | ✓ |
| NBA-DOM-03 | IntegridadLógica (confidence) | 0.22 (NBA) | ✓ |
| FUT-DOM-01 | Completitud | 0.22 (FUTBOL) | ✓ |
| FUT-DOM-02 | IntegridadLógica/Coverage | 0.20/0.20 (FUTBOL) | ✓ |

**Cobertura:** 34/34 reglas mapeadas al scorecard (100%).

### 1.2 Scorecard → Alertas

| Componente Scorecard | Umbral Crítico | Alerta Asociada | ✓/✗ |
|---------------------|----------------|-----------------|-----|
| Completitud | `<0.95` NBA / `<0.90` FUT | DQ-HIGH-02, DQ-CRIT-04 | ✓ |
| IntegridadLógica | `critical_fail_count>=2` o score C | DQ-CRIT-02, DQ-CRIT-01 | ✓ |
| IntegridadTemporal | fail_rate temporal >2% sostenido | DQ-MED-03 | ✓ |
| RangosOutliers | `outlier_rate >0.10` | DQ-HIGH-03 | ✓ |
| Freshness | lag extremo >72h (NBA) | DQ-CRIT-04, DQ-HIGH-02 | ✓ |
| Coverage | caída de cobertura / mínimos no cumplidos | DQ-HIGH-04, DQ-MED-01, DQ-MED-02 | ✓ |
| Penalización Drift (FUT) | drift naranja/rojo | DQ-HIGH-05, DQ-CRIT-03, DQ-MED-05 | ✓ |
| Penalización Datos Parciales | `na_ratio >0.30` | DQ-MED-04 | ✓ |

### 1.3 Reglas → Alertas Directas

| ID Regla Crítica | Alerta Directa | ✓/✗ |
|------------------|----------------|-----|
| NBA-FRSH-02 | DQ-HIGH-02 | ✓ |
| FUT-FRSH-02 | DQ-HIGH-05 / DQ-MED-05 (si deriva en drift/score) | ✓ |
| NBA-LOG-01 | DQ-CRIT-02 (vía critical_fail_count) | ✓ |
| FUT-LOG-01 | DQ-HIGH-05 / DQ-CRIT-03 (si severidad acumulada) | ✓ |
| NBA-COMP-02 | DQ-HIGH-02 | ✓ |
| FUT-COMP-02 | DQ-HIGH-04 (si impacta coverage/calidad global) | ✓ |

---

## 2. MAPEO A DEUDA BLOQUE 05

### 2.1 Confidence/Calibration Parcial
- **Reglas que detectan:** `NBA-LOG-01`, `FUT-LOG-01`, `NBA-DOM-03`, `FUT-DOM-02`, `FUT-RNG-02`.
- **Componente scorecard:** IntegridadLógica (+ impacto secundario en RangosOutliers).
- **Alertas:** DQ-CRIT-02, DQ-HIGH-05, DQ-CRIT-01 (si score cae a C).
- **Estado actual:** **parcial / sin resolver** (correctamente visible, no maquillado).

### 2.2 Contratos Legacy Coexistentes
- **Reglas que validan consistencia entre contratos:** indirectas (drift/campos canónicos), pero **no hay regla explícita dedicada a envelope/objeto directo y semántica de error**.
- **Impacto en scorecard:** hoy entra de forma parcial por completitud/integridad, no por contrato explícito.
- **Alertas específicas:** no existe alerta nombrada de contrato legacy.
- **Estado actual:** **coexistiendo / migrando**.
- **Conclusión:** **GAP CRÍTICO (BLOCKER)** de trazabilidad contractual explícita.

### 2.3 Drift Runtime Fútbol
- **Reglas que detectan drift:** DRIFT-FUT-01..04 + `FUT-COV-*`, `FUT-DOM-02`.
- **Componente scorecard afectado:** Coverage + penalización `P_drift` específica fútbol.
- **Alertas de drift:** DQ-MED-05 (amarillo), DQ-HIGH-05 (naranja), DQ-CRIT-03 (rojo sostenido).
- **Estado actual:** **parcial-alto / monitoreado** (visible y controlado).

---

## 3. ANÁLISIS DE GAPS

### 3.1 Reglas Sin Cobertura en Scorecard
- No se detectan reglas huérfanas en el catálogo actual.
- **Resultado:** sin gap en esta dimensión.

### 3.2 Componentes Scorecard Sin Alertas
- Todos los componentes tienen al menos una alerta asociada.
- **Resultado:** sin gap en esta dimensión.

### 3.3 Alertas Sin Regla Base
- DQ-CRIT-01 (nivel C NBA) se basa en score agregado, no en una regla puntual única, pero sí deriva de reglas base.
- No se observan alertas totalmente huérfanas.
- **Resultado:** sin gap crítico.

---

## 4. ANÁLISIS DE REDUNDANCIAS

### 4.1 Reglas Duplicadas
- Posible solapamiento parcial:
  - `NBA-COMP-03` y `NBA-DOM-02` (mercado/sin mercado).
  - `FUT-COMP-01` y `FUT-DOM-01` (campos obligatorios cercanos).
- Recomendación: mantener ambas por ahora (una validación básica + una umbralizada), pero documentar jerarquía para evitar doble penalización excesiva.

### 4.2 Alertas Duplicadas
- Solapamiento controlado:
  - DQ-HIGH-02 (degradación completitud) y DQ-CRIT-04 (freshness severa NBA) pueden disparar juntas.
- No es duplicidad exacta; cambia severidad y SLA.
- Recomendación: aplicar agrupación por incidente raíz (ya definido en anti-ruido).

---

## 5. RECOMENDACIONES DE AJUSTE

### 5.1 Reglas a Agregar
1. **BLOCKER**: regla explícita de consistencia de contrato backend/frontend (envelope vs objeto directo) por endpoint crítico.
2. Regla de semántica de error canónica (`detail/message/mensaje/error.*`) para endpoints priorizados.
3. Regla de compatibilidad de naming contractual por dominio (NBA/FUT).

### 5.2 Alertas a Agregar
1. **BLOCKER**: alerta ALTA/CRÍTICA de “regresión contractual” cuando falle regla de contrato canónico.
2. alerta MEDIA de “coexistencia legacy persistente > X días” para seguimiento de migración.

### 5.3 Ajustes de Pesos
- Mantener pesos actuales en v1.1.
- Evaluar en v1.2 si Coverage fútbol (0.20) está sobrerrepresentado frente a IntegridadLógica (0.20) cuando aumente madurez de datos.

---

## 6. VALIDACIÓN DE NO MAQUILLAJE

- ✓ La deuda del bloque 05 sigue visible en el framework.
- ✓ No se declara como "resuelta" sin evidencia.
- ✓ El framework la hace **MEDIBLE**, no **INVISIBLE**.
- ✓ Los niveles de calidad reflejan estado real, no optimista.

Observación final de auditoría:
- El framework es consistente en cadena Reglas→Score→Alertas.
- Existe **1 BLOCKER**: falta de cobertura contractual explícita para deuda de contratos legacy del bloque 05.
- Hasta cerrar ese blocker, la visibilidad de deuda contractual es parcial.

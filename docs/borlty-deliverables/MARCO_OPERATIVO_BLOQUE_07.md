# MARCO_OPERATIVO_BLOQUE_07

## 1. ALCANCE DEL BLOQUE 07

### Objetivos específicos

**Objetivo general:** Implementar un marco operativo de calidad y explicabilidad que use como base la capa analítica aceptada del bloque 06, sin reabrir su implementación y sin maquillar deuda residual del bloque 05.

**07.1 Calidad de Datos (primero, obligatorio):**
1. Formalizar controles de calidad por dominio (NBA/Fútbol) y por vista canónica crítica.
2. Implementar scorecards de calidad reutilizando la capa analítica del bloque 06.
3. Definir umbrales operativos (verde/ámbar/rojo) para completitud, frescura, cobertura y consistencia.
4. Publicar alertas de degradación con trazabilidad de causa (fuente, contrato, drift, mercado).

**07.2 Explicabilidad (después de 07.1):**
1. Exponer explicaciones trazables de métricas y decisiones operativas usando artefactos validados por 07.1.
2. Estandarizar narrativa técnica por KPI (qué mide, cómo se calcula, limitaciones, deuda asociada).
3. Generar salidas explicables para consumo operativo (scorecards, reportes y vistas de soporte).

### Límites explícitos (qué NO incluye)

1. **No** corregir definitivamente deuda estructural de bloque 05 (confidence definitivo, erradicación total de drift, unificación total de contratos legacy).
2. **No** reabrir diseño/implementación de vistas de bloque 06 ya aceptadas.
3. **No** introducir rediseño de modelo predictivo, stake engine ni nuevas estrategias de negocio.
4. **No** usar explicabilidad para “ocultar” mala calidad de datos.
5. **No** lanzar expansión funcional de producto (eso queda para bloque 08).

### Separación clara 07.1 vs 07.2

- **Secuencia obligatoria:** 07.1 → 07.2.
- **Gate de paso:** 07.2 solo inicia cuando 07.1 alcanza criterios mínimos de calidad operativa.
- **Responsabilidad:**
  - 07.1 responde “¿los datos son confiables y monitoreables?”
  - 07.2 responde “¿podemos explicar de forma consistente lo que reportamos?”

---

## 2. MATRIZ DE DEPENDENCIAS

| Dependencia Bloque 05 | Estado Actual | Impacto en Bloque 07 | Estrategia de Mitigación |
|----------------------|---------------|----------------------|--------------------------|
| Confidence / Calibration definitivo por mercado | Parcial (diagnóstico cerrado, corrección definitiva abierta) | Puede degradar confiabilidad de scorecards y explicaciones de KPIs predictivos | Mantener bandera explícita de residualidad; excluir uso como driver principal; segmentar scorecards por nivel de confianza de fuente |
| Contratos legacy backend/frontend coexistentes | Parcial | Riesgo de inconsistencias semánticas y errores de parsing que rompan trazabilidad en 07.1/07.2 | Capa de normalización previa a scorecards; validación de esquema de entrada; catálogo de excepciones temporales con fecha de revisión |
| Drift runtime en fútbol y fallback legacy | Parcial-alto | Distorsiona métricas de calidad y afecta comparabilidad NBA vs Fútbol | Monitoreo anti-drift con umbrales; etiquetado obligatorio de registros con fallback; bloqueo de promoción a “verde” cuando haya drift activo |
| Policy odds >2.0 (cierre temporal operativo) | Cerrado temporal | Puede sesgar lectura de desempeño si se interpreta como regla definitiva | Tratar policy como restricción operativa temporal; documentar explícitamente alcance temporal en scorecards y reportes |

---

## 3. MÉTRICAS DE ENTRADA/SALIDA

### Estado inicial cuantificado (T0)

1. **Dependencias bloque 05 abiertas relevantes para bloque 07:** 3/4 (75%)
   - Abiertas/parciales: confidence, contratos legacy, drift.
   - Cerrada temporal: policy odds.
2. **Cobertura de calidad formalizada en scorecards bloque 07:** 0% (no existe framework completo 07 en producción).
3. **Cobertura de explicabilidad estandarizada bloque 07.2:** 0% (no iniciado).
4. **Vistas base disponibles desde bloque 06 para quality scorecards:** 100% del set mínimo aceptado (7 vistas canónicas del alcance 06).
5. **Gate 07.2 cumplido al inicio:** No (0/1).

### Estado esperado al final del bloque

**Al cierre de 07.1 (antes de 07.2):**
- 100% de vistas críticas del bloque 06 con scorecard de calidad activo.
- ≥95% de ejecuciones de validación sin error técnico.
- 100% de métricas críticas con umbral definido (verde/ámbar/rojo).
- 100% de incidencias de calidad críticas con causa trazable (fuente/contrato/drift).

**Al cierre de 07.2:**
- 100% de KPIs críticos con ficha de explicabilidad estándar.
- ≥90% de explicaciones reproducibles sin contradicción con scorecards de calidad.
- 100% de reportes operativos con etiqueta explícita de deuda residual cuando aplique.

### KPIs de progreso

1. **KPI-07.1-01 Cobertura de scorecards:**
   - Fórmula: vistas críticas con scorecard activo / total vistas críticas.
   - Meta: 100%.
2. **KPI-07.1-02 Integridad de controles de calidad:**
   - Fórmula: métricas críticas con umbral definido / total métricas críticas.
   - Meta: 100%.
3. **KPI-07.1-03 Estabilidad de validación:**
   - Fórmula: corridas válidas / corridas totales.
   - Meta: ≥95%.
4. **KPI-07.2-01 Cobertura de explicabilidad:**
   - Fórmula: KPIs críticos con ficha explicable / total KPIs críticos.
   - Meta: 100%.
5. **KPI-07.2-02 Consistencia calidad-explicación:**
   - Fórmula: explicaciones sin conflicto con scorecards / total explicaciones auditadas.
   - Meta: ≥90%.
6. **KPI-07-GOV-01 Control de scope creep:**
   - Fórmula: solicitudes fuera de alcance aceptadas / solicitudes fuera de alcance detectadas.
   - Meta: 0% (ninguna aceptada sin replanificación formal).

---

## 4. FRONTERAS CON OTROS BLOQUES

### Qué queda en bloque 05 (no resolver aquí)

1. Corrección definitiva de confidence/calibration por mercado.
2. Eliminación total de contratos legacy coexistentes.
3. Erradicación final de drift runtime y retiro total de fallback legacy.

### Qué queda en bloque 06 (no modificar)

1. Definición semántica base ya aceptada.
2. Implementación física de vistas canónicas mínimas.
3. Estructura de validaciones de cierre de bloque 06 (solo consumo, no rediseño).

### Qué se reserva para bloque 08

1. Expansiones funcionales de producto y nuevas capacidades no críticas para gobierno de calidad/explicabilidad.
2. Automatizaciones avanzadas no necesarias para los KPIs de cierre de bloque 07.
3. Iniciativas de optimización/performance no ligadas directamente a calidad o explicabilidad.

---

## 5. RIESGOS IDENTIFICADOS

1. **Riesgo de mezclar calidad + explicabilidad prematuramente**
   - Señal: iniciar narrativas explicativas sin scorecards estables.
   - Control: gate formal 07.1 completado antes de cualquier entrega 07.2.

2. **Riesgo de sobre-ingeniería**
   - Señal: proliferación de métricas/controles sin impacto operativo real.
   - Control: priorizar métricas críticas y criterio de valor operacional por cada control nuevo.

3. **Riesgo de maquillar deuda**
   - Señal: reportes “verdes” sin etiquetar dependencia de deuda residual bloque 05.
   - Control: etiquetado obligatorio de residualidad y bloqueo de cierre si falta trazabilidad.

4. **Riesgo de scope creep inter-bloques**
   - Señal: solicitudes de rediseño estructural (05/06) o expansión funcional (08) dentro del 07.
   - Control: matriz de frontera viva + comité de cambio (aceptar solo con replanificación formal).

---

## Validación de no solapamiento (05, 06, 08)

- **No solapa con 05:** no promete cierre definitivo de deuda crítica; solo la gestiona como dependencia explícita.
- **No solapa con 06:** consume base analítica aceptada sin reabrir implementación.
- **No solapa con 08:** no incluye expansión funcional ni optimizaciones de siguiente etapa.

Con esto, el bloque 07 queda encuadrado como marco de **gobierno de calidad + explicabilidad**, con secuencia controlada, métricas objetivas y fronteras operativas explícitas.
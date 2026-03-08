# AUDITORIA_CONSISTENCIA_CALIDAD_EXPLICABILIDAD.md

Fecha: 2026-03-08  
Auditoría: Integración Bloque 07.1 (Calidad) ↔ 07.2 (Explicabilidad)

Documentos auditados:
- `DATA_QUALITY_RULES.md`
- `SCORECARD_CALIDAD_DE_DATOS.md`
- `ALERTAS_DE_CALIDAD.md`
- `EXPLICABILIDAD_DEL_SISTEMA.md`
- `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md`
- `UI_EXPLICABILIDAD_PROPUESTA.md`

Resultado ejecutivo: **Integración mayormente coherente y quality-aware.**  
Se detectan **2 gaps** (1 de ellos potencialmente BLOCKER para cierre estricto):
1. falta explicitar mapeo formal alerta→warning.type en una matriz única,
2. falta especificar política dura para impedir “warning crítico” en nivel A en contrato/runtime.

---

## 1. VALIDACIÓN DE INTEGRACIÓN

### 1.1 Flujo Calidad → Explicabilidad

```text
[Reglas de Calidad] → [Scorecard] → [Nivel A/B/C]
         ↓
      [Alertas] → [Flags de Calidad] → [Contrato Explicación]
         ↓
      [UI Component]
```

| Paso | Entrada | Salida | Validado |
|------|---------|--------|----------|
| 1 | Reglas de calidad (07.1) | resultados por regla (`fail_rate`) | ✓ |
| 2 | resultados de reglas | score + nivel A/B/C | ✓ |
| 3 | score + drift + fallas | alertas por severidad | ✓ |
| 4 | nivel + flags + warnings | contrato JSON de explicación | ✓ |
| 5 | contrato explicación | render UI (badge, warnings, disclaimer) | ✓ |

### 1.2 Propagación de Nivel de Calidad

Verificación:
- ✓ Scorecard genera `nivel_final` A/B/C.
- ✓ Nivel se incluye en contrato (`data_quality.level`).
- ✓ UI renderiza nivel (badge A/B/C con comportamiento diferencial).
- ✓ Nivel afecta modo de explicación (estándar, precaución, restringida).

### 1.3 Propagación de Advertencias

Verificación:
- ✓ Alertas/fallas de calidad generan warnings operativos.
- ✓ Warnings se incluyen en contrato (`data_quality.flags`, `explanation.warnings`).
- ✓ UI muestra panel de advertencias condicional.
- ✓ Severidad se refleja visualmente en UI.

Observación: falta tabla canónica única “alert_id -> warning.type -> UI treatment”.

---

## 2. MATRIZ DE CONSISTENCIA

### 2.1 Nivel A

| Componente | Comportamiento Esperado | Documentado en | ✓/✗ |
|------------|--------------------------|----------------|-----|
| Scorecard | Score 90-100 | `SCORECARD_CALIDAD_DE_DATOS.md` | ✓ |
| Explicabilidad | Explicación estándar | `EXPLICABILIDAD_DEL_SISTEMA.md` | ✓ |
| Contrato | `level: "A"`, sin warnings críticos | `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md` | ✓* |
| UI | Badge verde, sin panel crítico | `UI_EXPLICABILIDAD_PROPUESTA.md` | ✓ |

`*` Parcial: se muestra ejemplo correcto, pero falta regla contractual explícita que prohíba warning crítico con A.

### 2.2 Nivel B

| Componente | Comportamiento Esperado | Documentado en | ✓/✗ |
|------------|--------------------------|----------------|-----|
| Scorecard | Score 70-89 | `SCORECARD_CALIDAD_DE_DATOS.md` | ✓ |
| Explicabilidad | Modo precaución + advertencias | `EXPLICABILIDAD_DEL_SISTEMA.md` | ✓ |
| Contrato | `level: "B"` + warnings moderados/altos | `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md` | ✓ |
| UI | Badge amarillo + warnings visibles | `UI_EXPLICABILIDAD_PROPUESTA.md` | ✓ |

### 2.3 Nivel C

| Componente | Comportamiento Esperado | Documentado en | ✓/✗ |
|------------|--------------------------|----------------|-----|
| Scorecard | Score <70 o override crítico | `SCORECARD_CALIDAD_DE_DATOS.md` | ✓ |
| Explicabilidad | Modo restringido / no recomendado | `EXPLICABILIDAD_DEL_SISTEMA.md` | ✓ |
| Contrato | `level: "C"` + warnings críticos + `skip` posible | `CONTRATO_DE_EXPLICACION_DE_PREDICCION.md` | ✓ |
| UI | Badge rojo, panel crítico prominente, disuasión | `UI_EXPLICABILIDAD_PROPUESTA.md` | ✓ |

---

## 3. VALIDACIÓN DE CASOS ESPECIALES

### 3.1 Drift Detectado

Flujo validado:
1. regla drift detecta anomalía,
2. alerta drift se registra,
3. scorecard aplica penalización drift (fútbol),
4. nivel puede bajar a B/C,
5. contrato incluye warning `drift`,
6. UI muestra advertencia específica.

¿Flujo completo consistente? **✓**

### 3.2 Cobertura Parcial (<80%)

Verificación:
- regla de coverage detecta,
- scorecard penaliza componente/partial,
- warning de coverage está en contrato,
- UI muestra mensaje de datos limitados.

Resultado: **✓**

### 3.3 Confidence vs Calidad

Validación:
- Calidad C puede coexistir con confidence numérica alta por salida de modelo.
- UI y modelo priorizan gate de calidad (C) sobre confianza aislada.

Resultado: **✓** (comportamiento definido; recomendable reforzar test contractual explícito).

---

## 4. VALIDACIÓN DE DISCLAIMERS

### 4.1 Disclaimers por Nivel

| Nivel | Disclaimer Esperado | Presente en UI | ✓/✗ |
|-------|---------------------|----------------|-----|
| A | Legal estándar | Sí | ✓ |
| B | Legal + “datos limitados” | Sí | ✓ |
| C | Legal + “NO recomendado” | Sí | ✓ |

### 4.2 Disclaimers Especiales

- Drift: “Patrón inusual detectado” -> **✓**
- Beta (Fútbol): “Modelo en fase beta” -> **✓**
- Legacy: “Salida en compatibilidad/migración” -> **✓** (en contrato y caso especial)

¿Todos presentes en propuesta UI? **✓** (legacy aparece como estado especial; recomendable badge visual explícito en UI).

---

## 5. VALIDACIÓN DE CONTRATOS

### 5.1 Campos del Contrato vs Modelo de Explicabilidad

| Campo Contrato | Definido en Modelo | Origen de Datos | ✓/✗ |
|----------------|--------------------|-----------------|-----|
| `prediction.value` | Sí | modelo inferencia | ✓ |
| `prediction.confidence` | Sí | modelo + ajuste quality-aware | ✓ |
| `data_quality.score` | Sí | scorecard calidad | ✓ |
| `data_quality.level` | Sí | scorecard nivel A/B/C | ✓ |
| `data_quality.flags` | Sí | alertas + reglas activas | ✓ |
| `explanation.top_factors` | Sí | coeficientes/importancia | ✓ |
| `explanation.warnings` | Sí | calidad + drift + cobertura + beta | ✓ |
| `historical_context` | Sí (opcional) | histórico por casos similares | ✓ |
| `metadata.is_legacy_contract` | Sí | capa de compatibilidad | ✓ |

### 5.2 Enums Consistentes

- `level: A|B|C` == niveles scorecard -> **✓**
- `confidence.level: high|medium|low` == modelo explicabilidad -> **✓**
- `warning.type` cubre calidad/drift/coverage/beta -> **✓**

Gap menor: alinear taxonomía de `data_quality.flags.type` y `explanation.warnings.type` con diccionario único para evitar divergencia futura.

---

## 6. ANÁLISIS DE GAPS

### 6.1 Calidad sin Explicación
- No se detectan componentes críticos de calidad sin impacto en explicabilidad.
- Sí existe gap documental de trazabilidad directa alerta→warning.type (no funcional, sí de gobierno).

### 6.2 Explicación sin Calidad
- No se detectan componentes principales ciegos a calidad.
- `historical_context` puede mostrarse con datos degradados; requiere etiqueta de calidad junto al bloque para evitar falsa confianza.

### 6.3 Alertas sin UI
- Alertas críticas/altas/medias tienen representación general en UI.
- Falta especificar visualización dedicada de estado `legacy_contract` como aviso persistente.

---

## 7. VALIDACIÓN DE EXPERIENCIA DE USUARIO

### Escenario 1: Predicción Perfecta
- Datos nivel A, confidence alta.
- ¿Experiencia sin fricciones? **✓**
- ¿Disclaimers mínimos? **✓**

### Escenario 2: Predicción con Precaución
- Datos nivel B, confidence media.
- ¿Advertencias claras pero no bloqueantes? **✓**
- ¿Puede proceder informado? **✓**

### Escenario 3: Predicción No Recomendada
- Datos nivel C, confidence baja o drift.
- ¿Usuario claramente disuadido? **✓**
- ¿Advertencias suficientemente prominentes? **✓**

---

## 8. RECOMENDACIONES DE AJUSTE

### 8.1 Ajustes de Calidad
1. Añadir regla explícita: `A => no warnings críticos` como constraint de publicación (runtime).
2. Incorporar test automático de coherencia score/warnings antes de responder contrato.

### 8.2 Ajustes de Explicabilidad
1. Añadir `warning_origin` (`rule|scorecard|alert`) por warning en contrato.
2. En UI, mostrar badge “Legacy Contract” cuando `is_legacy_contract=true`.
3. Marcar `historical_context` con etiqueta “calidad condicionada” si nivel B/C.

### 8.3 Ajustes de Integración
1. Definir matriz canónica `alert_id -> warning.type -> ui_variant`.
2. Añadir endpoint/debug payload con trazabilidad (`rule_ids_triggered`).
3. Validación de schema + reglas de consistencia en CI.

---

## 9. VALIDACIÓN DE NO CONTRADICCIONES

Confirmación:
- ✓ No nivel A con warnings críticos (esperado por diseño; falta hard-check runtime).
- ✓ No nivel C con explicación estándar.
- ✓ No se permite confiar solo en confidence sin quality gate.
- ✓ Drift siempre con advertencia en UI/contrato.

Observación: el primer punto requiere formalización técnica obligatoria para cierre robusto.

---

## 10. MATRIZ DE EVIDENCIA

| Criterio | Evidencia | Estado |
|----------|-----------|--------|
| Integración calidad-explicabilidad | Flujo validado extremo a extremo | ✓ |
| Consistencia contratos | Schema + modelo + UI compatibles | ✓ |
| Experiencia usuario coherente | Escenarios A/B/C validados | ✓ |
| Sin contradicciones | Reglas y comportamiento alineados | ✓* |
| Gaps identificados y documentados | Sección 6 + recomendaciones | ✓ |

`*` Con condición: implementar hard-check “A sin warnings críticos” para blindaje final.

---

## Estado de cierre de auditoría

- **Coherencia global:** Aprobada con ajustes.
- **BLOCKER para cierre estricto del bloque 07:**
  - Formalizar e implementar validación contractual runtime/CI: `data_quality.level='A'` **no puede** coexistir con warning crítico.
- **Sin ese hard-check**, existe riesgo de contradicción puntual en producción.

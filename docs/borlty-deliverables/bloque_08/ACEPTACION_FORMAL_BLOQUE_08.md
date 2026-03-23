# ACEPTACION_FORMAL_BLOQUE_08

Fecha: 2026-03-08  
Versión: 1.0

## 1. Criterios de aceptación (condiciones heredadas de bloque 07)

| Criterio | Estado | Evidencia |
|---|---|---|
| Hard-check A sin warning crítico implementado en runtime | ✓ | `QualityCoherenceError` + tests unit/integración passing |
| Mapeo canónico alerta→warning→UI implementado | ✓ | `MATRIZ_ALERTA_WARNING_UI.md` + uso en contrato/UI |
| Validación en staging con evidencia de coherencia | ✗ (N/A por entorno) | No hay evidencia staging formal en este cierre |
| Feature flags operativos con rollback documentado | ✓ | `backend/feature_flags.py` + `PLAN_ROLLOUT_GRADUAL.md` |
| Deuda bloque 05 visible y no maquillada en outputs | ✓ | `estado-sistema`, `debt_flags`, alertas drift fútbol |

Resultado criterios: **4/5 cumplidos** + 1 pendiente por entorno (staging).

---

## 2. Decisión de aceptación

**DECISIÓN:** **ACEPTADO CON CONDICIONES**

Justificación:
- El alcance técnico del bloque 08 está implementado y coherente.
- Hard-checks críticos y visibilidad de deuda B05 se cumplen.
- Existe blocker transversal fuera del alcance directo del pipeline B08: suite global backend no verde por errores de colección en `tests/motor_futbol/*`.
- Falta evidencia formal de staging end-to-end.

---

## 3. Condiciones para bloque 09

1. Resolver blocker de tests globales (colección en motor_futbol) o aislar baseline oficial por dominio con criterio de release explícito.
2. Ejecutar validación en staging con flags por fases y evidencia de coherencia A/B/C.
3. Mantener deuda B05 reportada explícitamente hasta resolución real (no documental).
4. Definir fecha y plan de retiro progresivo de contrato legacy para consumidores prioritarios.

---

## 4. Autorización formal de inicio bloque 09

**AUTORIZACIÓN BLOQUE 09:** **SÍ (CONDICIONAL)**

Condicionada a:
- plan de remediación del blocker global de tests,
- ejecución de pruebas de staging,
- continuidad de visibilidad de deuda B05 en diagnóstico y contratos.

---

## Declaración final

El bloque 08 **no** declara el sistema libre de deuda.  
Se confirma explícitamente que continúan abiertas:
- confidence/calibration parcial,
- contratos legacy coexistentes,
- drift fútbol parcial-alto.

Estas deudas permanecen visibles y trazables en los outputs del sistema.

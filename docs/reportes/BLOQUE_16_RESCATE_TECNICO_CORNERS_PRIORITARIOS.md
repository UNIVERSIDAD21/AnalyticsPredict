# BLOQUE 16 — Rescate técnico focalizado (`CORNERS_1T`, `CORNERS_LOCAL_1T`)

## Alcance (foco estricto)
Mercados intervenidos únicamente:
- `CORNERS_1T`
- `CORNERS_LOCAL_1T`

`CORNERS_LOCAL_2T` no se incluyó para no diluir foco en este bloque.

---

## 1) Diagnóstico específico por mercado (causa raíz real)

### A. `CORNERS_1T`
- **Resolución/outcomes (principal):** había predicciones pendientes no por bug de cálculo sino por estados no-finales (`POSPUESTO`/`CANCELADO`) que quedaban abiertas y contaminaban la tasa operativa.
- **Coverage de líneas:** cobertura histórica observada de 4 líneas; grilla oficial no incluía explícitamente 5.0.
- **Fallback:** en este mercado puntual se observó `fallback_rate=0.0` (no es causa principal de bloqueo aquí).
- **Estado de mercado/gate:** bloqueo sostenido por volumen binario resuelto muy bajo (solo 4 outcomes binarios efectivos en snapshot), más autodemotion previo.
- **Modelado/calibración:** no aparece como causa primaria con la evidencia actual; el cuello está aguas arriba (resolución operativa y base de evidencia).

### B. `CORNERS_LOCAL_1T`
- **Resolución/outcomes (principal):** mismo patrón: pendientes por estados no-finales operativos.
- **Coverage de líneas:** cobertura observada de 4 líneas; se ajusta grilla para incluir 5.0 y adyacentes realistas.
- **Fallback:** `fallback_rate=0.0` en snapshot focalizado (no causa principal).
- **Estado de mercado/gate:** bloqueo por baja masa de outcomes binarios + historial de autodemotion.
- **Modelado/calibración:** secundaria frente a déficit operacional de resolución.

---

## 2) Correcciones aplicadas (A–D)

### A) Resolución y outcomes
Archivo: `backend/motor/resolucion_predicciones_futbol.py`
- Se agregó cierre operativo para partidos en estado:
  - `CANCELADO`, `POSPUESTO`, `SUSPENDIDO`, `ABANDONADO`
- Acción al resolver:
  - `resultado='VOID'`
  - `resuelto=true`
  - `outcome_binario=NULL`
- Se añadió contador `anuladas` al resumen.

**Efecto medible (mercados foco):**
- quedaron `8 VOID` por mercado correctamente cerrados,
- pendientes operativos pasan a estar concentrados en `PROGRAMADO` (16), sin basura de estados cancelados/pospuestos.

### B) Coverage de líneas
Archivo: `backend/motor_futbol/constantes.py`
- `CORNERS_1T`: de `[4.5, 5.5]` a `[4.5, 5.0, 5.5]`
- `CORNERS_LOCAL_1T`: de `[2.5, 3.5]` a `[2.5, 3.5, 4.5, 5.0]`

Objetivo: cobertura útil y defendible para línea objetivo 5.0 sin expansión artificial masiva.

### C) Fallback / datos incompletos
Archivo: `backend/scripts/rescate_corners_prioritarios_b16.py`
- Auditoría y backfill focalizado (`prob_over_calibrada/prob_under_calibrada` desde raw cuando falten) para evitar fallback estructural oculto.
- En esta corrida, backfill necesario fue `0` (ya estaban completas en mercados foco).

### D) Estado de mercado
- Se mantuvo el gate vigente; este bloque sanea operación para mejorar señal hacia siguiente re-scorecard.
- No se forzó promoción ni bypass de estado_mercados.

---

## 3) Evidencia antes vs después (mercados foco)

Fuente: `docs/reportes/BLOQUE_16_RESCATE_CORNERS_PRIORITARIOS.json`

- `emitidos`: 28 (ambos)
- `resueltos binarios`: 4 (ambos)
- `cerrados operativos`: 12 (ambos)
- `pendientes operativos`: 16 (ambos)
- `fallback_rate`: 0.0 (ambos)

Evidencia complementaria de limpieza de pendientes:
- Antes de saneamiento operativo, había pendientes en `PROGRAMADO + POSPUESTO + CANCELADO`.
- Después, pendientes operativos quedan solo en `PROGRAMADO`.
- `VOID` registrados: 8 por mercado.

---

## 4) Pruebas reales ejecutadas

- `backend/tests/test_futbol_rescate_corners_b16.py`
- `backend/tests/test_futbol_madurez_beta.py`
- `backend/tests/test_futbol_shadow_operativo.py`

Resultado: **9 passed**.

Cobertura validada:
- resolución correcta de valor real para `CORNERS_1T` y `CORNERS_LOCAL_1T`,
- grilla de líneas actualizada con 5.0,
- no regresión de piezas críticas de madurez/shadow.

---

## 5) Pendiente mínimo para siguiente bloque (re-scorecard)

Listo para BLOQUE 17:
1. Re-correr walk-forward/scorecard **solo** para `CORNERS_1T` y `CORNERS_LOCAL_1T`.
2. Medir si el cierre operativo (`VOID`) mejora estado de bloqueo en gate.
3. Validar transición potencial a `LABORATORIO/VALIDACION` solo si evidencia lo soporta.

---

## 6) Riesgos residuales

- Aunque mejoró cierre operativo, outcomes binarios efectivos siguen bajos (4/28).
- El principal limitante sigue siendo masa histórica resuelta para scoring robusto.
- No se debe tocar calibración/modelado como parche hasta consolidar más resolución real en estos dos mercados.

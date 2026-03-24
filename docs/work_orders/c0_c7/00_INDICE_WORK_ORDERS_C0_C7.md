# 00_INDICE_WORK_ORDERS_C0_C7.md

Estado: ACTIVO
Fecha: 2026-03-23

## Propósito
Este índice organiza la ejecución secuencial de los bloques C0–C7 definidos en:
- `docs/arquitectura/PLAN_BLOQUES_C0_C7_LANZAMIENTO_PROFESIONAL.md`

## Regla de ejecución
- Ejecutar **1 bloque principal** a la vez.
- Solo abrir **1 bloque paralelo** cuando el bloque principal vigente no pierda foco.
- Antes de programar, leer siempre:
  1. `docs/FUENTE_DE_VERDAD_ACTUAL.md`
  2. `docs/arquitectura/ESTADO_PROYECTO.md`
  3. `docs/arquitectura/PLAN_EJECUCION_BLOQUES_V3.md`
  4. `docs/arquitectura/PLAN_BLOQUES_C0_C7_LANZAMIENTO_PROFESIONAL.md`

## Orden oficial
### Camino principal
1. `docs/work_orders/c0_c7/WORK_ORDER_C0_REALINEACION_GO_LIVE.md`
2. `docs/work_orders/c0_c7/WORK_ORDER_C1_PAGOS_PRODUCTIVOS.md`
3. `docs/work_orders/c0_c7/WORK_ORDER_C2_HARDENING_Y_PERSISTENCIA.md`
4. `docs/work_orders/c0_c7/WORK_ORDER_C3_CUMPLIMIENTO_COMERCIAL.md`
5. `docs/work_orders/c0_c7/WORK_ORDER_C4_ACTIVACION_Y_ENTRADA_DE_VALOR.md`
6. `docs/work_orders/c0_c7/WORK_ORDER_C7_GATE_COMERCIAL_Y_COHORTE.md`

### Camino paralelo controlado
7. `docs/work_orders/c0_c7/WORK_ORDER_C5_PARIDAD_OPERATIVA_FUTBOL.md`
8. `docs/work_orders/c0_c7/WORK_ORDER_C6_CENTRO_ANALITICO_MULTIDEPORTE.md`

## Regla documental obligatoria por bloque
Al cerrar cada bloque:
1. Actualizar `docs/arquitectura/ESTADO_PROYECTO.md`
2. Agregar entrada en `CHANGELOG.md`
3. Actualizar ADR/documento rector si aplica
4. Guardar evidencia en `docs/borlty-deliverables/`
5. Archivar documentación reemplazada

## Regla estratégica permanente
AnalyticsPredict se ejecuta como:
- plataforma analítica de decisiones deportivas,
- con foco en trazabilidad, calidad y control de riesgo,
- no como app de picks masivos.

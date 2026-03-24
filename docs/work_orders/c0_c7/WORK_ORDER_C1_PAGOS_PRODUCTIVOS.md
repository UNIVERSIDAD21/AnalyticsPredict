# WORK_ORDER_C1_PAGOS_PRODUCTIVOS.md

## Objetivo
Cerrar B1 de forma real y profesional para que AnalyticsPredict pueda cobrar el primer peso con trazabilidad, reconciliación y manejo seguro de fallos.

## Problemática
Hoy B1 está implementado en base, pero todavía no constituye un flujo de cobro productivo completamente validado. Sin cerrar esto, no existe salida comercial seria.

## Tareas obligatorias
1. Conectar el flujo real del gateway definido.
2. Completar idempotencia y trazabilidad de webhook.
3. Cubrir estados reales de pago/suscripción.
4. Validar activación y desactivación correcta de permisos premium.
5. Diseñar y ejecutar evidencia E2E del primer pago real.
6. Documentar escenarios de fallo, conciliación y recuperación.
7. Actualizar documentación operativa y changelog.

## Entregables
- Flujo documentado de pagos reales.
- Evidencia E2E del primer pago real.
- Matriz de estados y fallos de pago.
- Validación de feature gating por suscripción.

## Restricciones
- No maquillar sandbox como flujo productivo.
- No cerrar el bloque sin evidencia reproducible.
- No dejar casos de inconsistencia entre estado de pago y permisos.

## Criterio de cierre
Existe evidencia reproducible de cobro real, reconciliación correcta y permisos premium consistentes.

# WORK_ORDER_C2_HARDENING_Y_PERSISTENCIA.md

## Objetivo
Blindar la operación productiva del sistema y eliminar ambigüedad en persistencias y componentes launch-critical.

## Problemática
Existen componentes sensibles con soporte temporal y falta formalizar qué puede salir a producción y bajo qué condiciones. Sin C2, el lanzamiento queda expuesto a fallos operativos, pérdida de trazabilidad o decisiones improvisadas.

## Tareas obligatorias
1. Definir estrategia de persistencia productiva para componentes críticos.
2. Migrar o excluir del go-live cualquier pieza sensible que no deba seguir temporal.
3. Implementar backups y restore test real.
4. Formalizar runbook operativo, rollback y manejo de secretos.
5. Endurecer observabilidad mínima de pagos/suscripción y otros caminos críticos.
6. Actualizar documentación técnica, estado y changelog.

## Entregables
- Diseño de persistencia productiva.
- Evidencia de backup y restore.
- Runbook operativo.
- Checklist de hardening mínimo.

## Restricciones
- No declarar producción segura sin restore test real.
- No dejar componentes críticos sin decisión explícita.
- No ocultar deuda temporal bajo lenguaje ambiguo.

## Criterio de cierre
No queda ninguna pieza crítica del go-live en estado temporal o sin plan de resiliencia explícito.

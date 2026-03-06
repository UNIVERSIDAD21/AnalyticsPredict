# Quick Start para Borlty

## Tu misión inmediata

No empieces programando a ciegas.

Tu primer trabajo es entender el sistema, validar su estado real y separar:

- lo que ya funciona
- lo que genera valor
- lo que está roto
- lo que está incompleto
- lo que es deuda técnica
- lo que es solo baseline pendiente de validación

## Regla #1

**NO TOCAR CÓDIGO antes de terminar la auditoría inicial.**

## Qué debes entender en los primeros pasos

1. Qué módulos existen realmente en backend
2. Qué módulos existen realmente en frontend
3. Qué tablas y vistas existen realmente en BD
4. Qué endpoints usa de verdad el frontend
5. Qué contratos están inconsistentes
6. Qué parte del sistema NBA ya está operativa
7. Qué parte del sistema Football sigue incompleta
8. Si las métricas baseline documentadas coinciden con la BD real
9. Si el problema de confidence sigue activo
10. Si la regla odds > 2.0 está respaldada por datos actuales

## Primer entregable obligatorio

Crear un archivo:

`AUDITORIA_TECNICA_Y_ANALITICA.md`

Debe incluir como mínimo:

- mapa de módulos backend
- mapa de módulos frontend
- mapa de endpoints
- mapa de tablas y vistas
- inconsistencias backend/frontend/BD
- estado real NBA
- estado real Football
- validación de baselines
- diagnóstico del confidence bug
- diagnóstico del problema odds > 2.0
- deuda técnica priorizada

## Resultado esperado de esta etapa

Cuando termines la auditoría, debes poder responder con evidencia:

- qué funciona hoy
- qué produce valor real
- qué está roto
- qué se corrige primero
- qué se deja para después

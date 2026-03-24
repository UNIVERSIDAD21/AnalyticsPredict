# WORK_ORDER_C0_REALINEACION_GO_LIVE.md

## Objetivo
Formalizar la realineación estratégica del proyecto y eliminar contradicciones entre estrategia vigente, estado formal, plan por bloques y alcance real del go-live.

## Problemática
Hoy existe una contradicción formal entre la estrategia actual y la documentación operativa del repo:
- la estrategia vigente establece que B3/B4/B5 no deben bloquear el primer peso,
- pero el plan formal todavía deja el gate final amarrado a B1+B2+B3+B4+B5+B6.
Además, existen persistencias temporales en piezas sensibles que pueden dejar ambigüedad sobre qué entra realmente al go-live.

## Tareas obligatorias
1. Crear un documento rector o ADR de **alcance comercial mínimo**.
2. Formalizar la nueva matriz de dependencias de lanzamiento:
   - qué bloques bloquean caja,
   - qué bloques quedan en paralelo,
   - qué bloques quedan fuera de alcance de go-live.
3. Inventariar persistencias temporales sensibles y clasificarlas como:
   - aceptar temporalmente,
   - migrar antes de salida,
   - excluir de go-live.
4. Actualizar y alinear:
   - `docs/FUENTE_DE_VERDAD_ACTUAL.md`
   - `docs/arquitectura/ESTADO_PROYECTO.md`
   - `docs/arquitectura/PLAN_EJECUCION_BLOQUES_V3.md`
   - `CHANGELOG.md`
5. Preservar evidencia en `docs/borlty-deliverables/`.

## Entregables
- Documento/ADR de alcance comercial mínimo.
- Matriz de dependencias de lanzamiento.
- Inventario de persistencias temporales.
- Estado/plan/fuente de verdad alineados.

## Restricciones
- No ejecutar todavía migraciones profundas de código como parte de C0.
- No reinterpretar la estrategia comercial sin validación explícita.
- No dejar ambigüedad sobre qué bloquea caja y qué no.

## Criterio de cierre
C0 se considera cerrado cuando ya no existe contradicción entre estrategia, plan, estado y alcance real del go-live.

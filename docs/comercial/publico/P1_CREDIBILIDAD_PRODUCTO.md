# P1 — Corregir lo que hoy daña credibilidad

Fecha: 2026-03-24
Estado: APROBADO PARA EJECUCIÓN
Prioridad: P0

## Problema
Hoy existe una brecha entre lo que el sistema parece prometer y lo que un usuario público realmente puede entender o ejecutar desde la interfaz.

El caso más delicado identificado es el frente de análisis en vivo: backend con capacidad parcial existente, pero UX no aterrizada de forma clara para uso real. Esto genera riesgo de desconfianza inmediata.

## Objetivo
Eliminar las incoherencias visibles que dañan confianza antes de seguir expandiendo producto, tráfico o narrativa comercial.

## Alcance
### Sí incluye
- revisión completa de promesas visibles en UI,
- ajuste de copy funcional vs capacidad real,
- aterrizaje correcto del flujo live o retiro temporal de su promesa visible,
- revisión de términos funcionales ambiguos en pantallas principales,
- validación de que el usuario entienda qué hace el sistema y qué no hace.

### No incluye
- rediseño cosmético grande sin impacto funcional,
- expansión de nuevos deportes o ligas,
- promesas nuevas sin soporte real en frontend y backend.

## Hallazgos ya detectados
1. El sistema tiene endpoint de análisis en vivo a nivel backend.
2. La UI principal no expone con claridad un flujo live equivalente.
3. Esto puede hacer que el usuario crea que existe una capacidad más madura de lo que realmente está aterrizado en experiencia.

## Decisiones aprobadas
1. Si el flujo live puede aterrizarse bien en esta fase, se implementa con UI clara.
2. Si no puede aterrizarse bien, se baja la promesa visible temporalmente.
3. La regla es simple: no se comunica como capacidad madura lo que aún no tenga recorrido UX completo.

## Entregables esperados
- inventario de promesas visibles del producto,
- matriz: promesa visible vs soporte real backend vs soporte real frontend,
- corrección del módulo/flujo live,
- ajustes de textos ambiguos,
- evidencia de validación funcional.

## Criterio de done
- no queda ninguna promesa crítica visible sin soporte claro,
- el usuario entiende cuándo usa análisis pre-partido y cuándo usa análisis en vivo,
- la UI deja de inducir interpretación errónea del alcance real,
- Borlty documenta qué quedó implementado y qué quedó explícitamente fuera.

## Riesgos a controlar
- maquillar parcialmente la UI sin resolver la experiencia,
- dejar rutas backend huérfanas sin explicación,
- añadir complejidad visual que empeore claridad.

## Métricas sugeridas
- reducción de dudas funcionales sobre live,
- menor rebote en pantallas de análisis,
- menor tasa de abandono en primer uso por confusión.

## Avance de ejecución (2026-03-26)
- Landing pública y centro analítico reforzados con narrativa anti-humo y madurez explícita por deporte.
- Se mantiene regla comercial: NBA frente principal, fútbol en beta/lab hasta subir evidencia.

# P2 — Diseñar bien el freemium y los límites de uso

Fecha: 2026-03-24
Estado: APROBADO PARA EJECUCIÓN
Prioridad: P0

## Problema
La idea de abrir parte del sistema sin registro es valiosa, pero hoy no puede ejecutarse de forma ingenua porque el producto sigue muy amarrado a auth/onboarding, y además existe riesgo de contaminar trazabilidad, medición y límites si no se diseña una identidad de invitado correcta.

## Objetivo
Crear un modelo freemium serio, entendible y medible, que permita probar valor antes del pago sin regalar el núcleo del negocio ni romper métricas.

## Principios
1. El visitante no debe parecer un usuario registrado.
2. El invitado no debe contaminar métricas personales ni trazabilidad real.
3. El registro no debe ser solo “reset de cupo”; debe desbloquear continuidad, historial y valor adicional.
4. El premium no debe definirse solo por cantidad, sino por profundidad de producto.

## Modelo aprobado para diseño
### Visitante
- 1 análisis full real,
- 1 análisis adicional con profundidad recortada o acceso limitado,
- 3er intento bloqueado hasta registro gratuito.

### Registrado gratuito
- cupo diario limitado de análisis full,
- acceso base a historial corto o continuidad mínima,
- sin profundidad premium.

### Suscrito
- acceso profundo,
- continuidad completa,
- mejores métricas, bitácora y valor operativo.

## Alcance
### Sí incluye
- diseño de guest session / identidad invitado,
- límites por sesión/dispositivo/cuenta,
- transición de visitante -> registrado,
- definición de qué se ve gratis, qué se recorta y qué se reserva a premium,
- métricas del embudo freemium.

### No incluye
- abrir premium de forma gratuita,
- improvisar límites solo con localStorage,
- maquillar como “anónimo” una identidad técnica de desarrollo.

## Entregables esperados
- documento funcional del modelo freemium,
- definición técnica de identidad invitado,
- puntos exactos de bloqueo y desbloqueo,
- tabla de capacidades por visitante / registrado / suscrito,
- propuesta de métricas del embudo,
- cambios de UI/backend si se ejecuta en esta fase.

## Criterio de done
- existe una identidad invitado bien separada,
- los cupos no dependen de hacks frágiles,
- el usuario entiende por qué debe registrarse y luego por qué conviene pagar,
- el sistema puede medir conversión y activación sin confundir segmentos.

## Riesgos a controlar
- regalar demasiado valor gratis,
- hacer que el registro no aporte casi nada,
- permitir evasión trivial de límites,
- mezclar tráfico invitado bajo usuarios fallback técnicos.

## Métricas sugeridas
- conversión visitante -> registrado,
- conversión registrado -> suscrito,
- uso medio antes del muro,
- activación útil por segmento,
- tasa de abandono en punto de bloqueo.

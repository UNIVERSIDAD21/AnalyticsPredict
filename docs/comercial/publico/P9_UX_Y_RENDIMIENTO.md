# P9 — UX y rendimiento

Fecha: 2026-03-24
Estado: APROBADO PARA EJECUCIÓN
Prioridad: P2

## Problema
Una parte del valor del sistema puede perderse no por falta de lógica, sino por fricción de uso, rutas demasiado cerradas, carga innecesaria o experiencia poco clara. Si el producto va a exponerse públicamente, UX y rendimiento pasan de ser “pulido” a ser parte del valor.

## Objetivo
Reducir fricción, mejorar claridad de uso y optimizar la percepción de velocidad sin sacrificar profundidad analítica.

## Alcance
### Sí incluye
- mejora del recorrido principal,
- revisión de pantallas de análisis y onboarding,
- optimización de rutas pesadas,
- reducción de carga inicial,
- mejor feedback visual y jerarquía de acciones,
- mejoras de comprensión en flujos clave.

### No incluye
- rediseño total sin razón funcional,
- cambios cosméticos vacíos,
- optimizar microdetalles antes de arreglar cuellos importantes.

## Líneas de trabajo sugeridas
1. Simplificar primer uso.
2. Mejorar claridad de pantallas críticas.
3. Reducir bundle inicial y carga de rutas pesadas.
4. Separar mejor información principal vs secundaria.
5. Mejorar feedback visual en análisis, bloqueo y conversión.

## Decisiones aprobadas
- UX y rendimiento sí importan a nivel de negocio,
- primero se debe optimizar lo que mejora comprensión y percepción real,
- el sistema debe sentirse serio pero también usable.

## Entregables esperados
- auditoría UX de pantallas críticas,
- propuesta de mejoras priorizadas,
- optimizaciones de carga donde más afecte,
- cambios concretos en flujos de uso,
- validación de impacto con criterios simples de experiencia.

## Criterio de done
- la experiencia principal se siente más fluida,
- hay menos pasos o menos fricción innecesaria,
- el usuario entiende mejor qué hacer en cada etapa,
- las rutas pesadas cargan mejor o se perciben mejor.

## Riesgos a controlar
- priorizar estética sobre claridad,
- mover piezas sensibles sin revisar impacto en conversión,
- sobreoptimizar sin atacar cuellos reales.

## Métricas sugeridas
- tiempo de carga inicial,
- tiempo hasta primera interacción útil,
- abandono por ruta,
- percepción de claridad en pruebas de usuario.

## Avance de ejecución (2026-03-26)
- Ola 3 iniciada con mejora de rendimiento en front mediante carga diferida de rutas pesadas (code-splitting en App).
- Objetivo inmediato: reducir costo inicial de carga y mejorar TTI percibido en rutas críticas.
- Se aplica lazy-load en componentes pesados dentro de `PaginaPrincipal` para acelerar carga inicial de la pestaña de análisis.

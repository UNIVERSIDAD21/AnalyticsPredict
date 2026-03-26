# P4 — Hacer que fútbol merezca más peso sin maquillaje

Fecha: 2026-03-24
Estado: APROBADO PARA EJECUCIÓN
Prioridad: P1

## Problema
Existe interés claro en que fútbol gane más relevancia dentro del producto, pero hoy el sistema y la documentación mantienen correctamente una diferencia de madurez entre NBA y fútbol. Subir fútbol de nivel por discurso antes de subirlo por calidad sería contraproducente.

## Objetivo
Dar más peso a fútbol de forma legítima: mejor calidad visible, mejor lectura por competición y mejor narrativa basada en evidencia, no en maquillaje.

## Principio rector
No igualar visual o comercialmente a fútbol con NBA hasta que fútbol cumpla criterios de estabilidad y madurez suficientes.

## Alcance
### Sí incluye
- fortalecer la ruta de promoción real de fútbol,
- dar más visibilidad a métricas por competición,
- comunicar mejor el estado de cada liga,
- priorizar expansión curada de ligas útiles,
- acercar fútbol a un frente comercial más fuerte por mérito.

### No incluye
- borrar la etiqueta beta/lab sin evidencia,
- tratar todas las ligas como si tuvieran la misma calidad,
- cambiar copy para simular paridad no ganada.

## Líneas de trabajo sugeridas
1. Estado visible por competición o liga.
2. Badge de estabilidad / warning / crítico.
3. Whitelist de ligas prioritarias para crecimiento.
4. Reporte público o semi-público de madurez de fútbol.
5. Mejor explicación de por qué algunas ligas sí se priorizan y otras no.

## Decisiones aprobadas
- fútbol sí debe ganar protagonismo,
- ese protagonismo debe construirse sobre calidad y trazabilidad,
- se permite expansión de ligas de fútbol, pero de forma curada y medible.

## Entregables esperados
- plan de promoción real de fútbol,
- definición de ligas prioritarias,
- criterios objetivos por liga,
- propuesta de visualización de madurez por competición,
- estrategia de copy para fútbol más fuerte sin sobrepromesa.

## Criterio de done
- fútbol tiene más peso visible sin falsear su estado,
- el usuario entiende mejor qué ligas o mercados son más confiables,
- existe una ruta clara para que fútbol evolucione hacia mayor peso comercial,
- Borlty deja explícito qué cambió en UI, datos y narrativa.

## Riesgos a controlar
- igualar todo fútbol como si fuera uniforme,
- comunicar paridad con NBA antes de tiempo,
- abrir demasiadas ligas sin gobernanza de calidad.

## Métricas sugeridas
- uso del módulo fútbol,
- interacción por liga/competición,
- distribución de recomendaciones por calidad,
- mejora de percepción del módulo fútbol en pruebas de usuario.

## Avance de ejecución (2026-03-26)
- Centro analítico muestra madurez de fútbol por competición (estable / en validación / lab).
- Se incrementa visibilidad de fútbol sin igualarlo a NBA de forma artificial.

## Umbrales operativos de promoción por competición
- LAB → EN VALIDACIÓN:
  - mínimo 30 apuestas finalizadas en ventana reciente,
  - trazabilidad de datos completa en panel.
- EN VALIDACIÓN → ESTABLE:
  - mínimo 80 finalizadas,
  - hitRateSinPush >= 53% en ventana reciente,
  - sin alerta crítica de calibración activa.

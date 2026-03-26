# P7 — Mejorar modelo y motor

Fecha: 2026-03-24
Estado: APROBADO PARA EJECUCIÓN
Prioridad: P1

## Problema
El sistema ya tiene una base analítica valiosa, pero aún conserva heurísticas, aproximaciones y capacidades no completamente explotadas en algunos frentes. Si el producto quiere sostener discurso serio hacia público y negocio, debe seguir mejorando la capa de modelo y motor.

## Objetivo
Elevar la calidad técnica del motor de predicción y su capacidad de explicación, priorizando primero lo que más impacta precisión percibida, consistencia y confianza del producto.

## Alcance
### Sí incluye
- revisión de mercados con heurísticas simplificadas,
- mejora del modelado por mercado/periodo,
- fortalecimiento de calibración,
- scorecards de desempeño y deriva,
- mejora del análisis live cuando aplique,
- revisión de la coherencia entre outputs raw y calibrados.

### No incluye
- reescritura total del sistema sin priorización,
- introducir complejidad sin beneficio medible,
- vender “IA mágica” como sustituto de método.

## Líneas de trabajo sugeridas
1. Reducir heurísticas fijas cuando ya existan datos suficientes.
2. Separar mejor submodelos por mercado, periodo o competencia.
3. Mejorar calibración y scorecards por segmento.
4. Fortalecer lógica de live para que la experiencia corresponda con la promesa.
5. Hacer más explicable la confianza del sistema.

## Decisiones aprobadas
- el motor debe mejorar, pero alineado a impacto real de producto,
- la prioridad no es sofisticación teórica aislada, sino valor técnico visible,
- toda mejora de modelo debería venir acompañada de evidencia o métricas comparables.

## Entregables esperados
- auditoría de puntos débiles del motor actual,
- plan de mejoras por impacto,
- propuesta de scorecards o benchmarks internos,
- mejoras implementadas en los puntos más críticos,
- validación de que lo mejorado se refleja en producto o métricas.

## Criterio de done
- Borlty identifica qué partes del motor son más débiles y por qué,
- existe una ruta de mejora priorizada,
- las mejoras realizadas tienen evidencia reproducible,
- el sistema queda más consistente entre promesa, lógica y salida.

## Riesgos a controlar
- optimizar lo invisible antes de arreglar lo crítico,
- empeorar interpretabilidad,
- introducir deuda técnica disfrazada de sofisticación.

## Métricas sugeridas
- Brier/ECE/score por mercado o competencia,
- estabilidad de recomendaciones,
- mejora en mercados clave,
- reducción de inconsistencias entre módulo live y pre-partido.

## Avance de ejecución (2026-03-26)
- Ola 3 iniciada con foco en preparación de medición técnica sin romper frente comercial.
- Se define línea base: comparar calidad por deporte/competición con métricas reproducibles antes de promover cambios de modelo.
- Siguiente tramo operativo: reportes comparativos antes/después por calibración, drift y robustez de señal.
- Se incorpora baseline técnico 1X2 en dashboard con soporte de consulta cacheada para observación continua de señal durante iteraciones de modelo.
- Se agrega guía operativa sugerida derivada del baseline (muestra + hitRate), para traducir señal técnica en decisiones de exposición más disciplinadas.

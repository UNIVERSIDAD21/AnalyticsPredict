# Bloque de Actividad — Expansiones Futuras

## Importante

Estas expansiones NO son el primer bloque de trabajo.
Solo deben activarse cuando:

- auditoría esté terminada
- contratos estén consolidados
- métricas estén formalizadas
- calidad de datos tenga framework
- confidence bug haya sido revisado
- drift de esquema esté controlado

## Expansión 1 — Chatbot sobre datos

### Qué debe ser
Una interfaz conversacional para consultar la capa analítica del sistema.

### Qué NO debe ser
- SQL libre sin control
- acceso directo a tablas operativas crudas
- respuestas basadas en métricas ambiguas

### Qué necesita antes
- KPIs oficiales
- capa semántica
- vistas analíticas estables
- definiciones únicas
- endpoints de consulta controlados

### Ejemplos de preguntas objetivo
- cuánto promedia X equipo en Q1
- qué equipo concede más puntos en Q2
- qué market type tiene mejor ROI
- qué alertas están activas
- cómo va la calibración de cierto modelo
- cuál es el rendimiento por rango de odds

## Expansión 2 — Mejores modelos matemáticos

### Qué debe ser
Evolución medible y trazable del stack predictivo.

### Qué NO debe ser
- complejidad por moda
- cambio total sin benchmark
- sustitución del modelo actual sin comparativa sólida

### Qué necesita antes
- baseline actual validado
- datasets confiables
- features documentadas
- métricas homogéneas
- criterios de promoción

### Líneas de evolución posibles
#### NBA
- mejor feature engineering temporal
- modelos especializados por quarter
- ratings ofensivo/defensivo más refinados
- calibradores por rango de odds o mercado
- modelos probabilísticos más ricos

#### Football
- modelos por mercado
- Poisson / Dixon-Coles para goles
- modelos count-based para corners/shots
- segmentación por competición
- ensemble solo cuando haya baseline serio

## Resultado esperado

Las expansiones futuras deben apoyarse sobre una plataforma analítica madura, no sobre deuda técnica.

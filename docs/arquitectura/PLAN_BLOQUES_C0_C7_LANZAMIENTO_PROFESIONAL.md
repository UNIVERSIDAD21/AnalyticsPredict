# PLAN_BLOQUES_C0_C7_LANZAMIENTO_PROFESIONAL.md

Estado: PROPUESTO
Fecha: 2026-03-23
Responsable estratégico: UNIVERSIDAD21

## Propósito
Formalizar la secuencia de bloques faltantes para llevar AnalyticsPredict a un lanzamiento comercial sólido, profesional y coherente con la estrategia vigente.

## Contexto estratégico
AnalyticsPredict se define hoy como una **plataforma analítica de decisiones deportivas con foco operativo**, no como una app de picks masivos. La salida comercial debe priorizar:
- cobro real y trazabilidad,
- operación segura,
- narrativa de control de riesgo y criterio operativo,
- NBA como frente comercial principal,
- fútbol como línea en maduración controlada hasta alcanzar paridad operativa.

## Problema que resuelve este plan
Actualmente existe riesgo de contradicción entre:
- estrategia verbal reciente,
- estado formal por bloques,
- dependencias de lanzamiento,
- alcance real de go-live,
- persistencias temporales en piezas sensibles,
- y madurez desigual entre dominios/deportes.

Este plan propone una secuencia ejecutable para cerrar esos huecos sin dispersar el proyecto.

---

## Orden recomendado de ejecución
### Camino principal
C0 → C1 → C2 → C3 → C4 → C7

### Camino en paralelo controlado
C5 → C6

### Regla de priorización
No abrir más de **1 bloque principal** y **1 bloque paralelo** al mismo tiempo.

---

## C0 — Realineación estratégica y redefinición formal del go-live
### Objetivo
Eliminar contradicciones entre la estrategia vigente y los documentos formales del proyecto.

### Alcance
- Formalizar el alcance comercial mínimo.
- Redefinir dependencias reales del lanzamiento.
- Alinear estado, plan y fuente de verdad.

### Tareas
- Crear ADR o documento formal de alcance comercial mínimo.
- Definir explícitamente qué bloques son requisito de caja/go-live y cuáles pasan a ser mejora o línea paralela.
- Establecer formalmente:
  - NBA = frente comercial principal.
  - Fútbol = beta/laboratorio controlado.
  - B3 = maduración operativa, no bloqueo de caja.
  - B4 = retención/engagement, no bloqueo de primer peso.
  - B5 = fuera de alcance de go-live si no se usará IA en salida comercial.
- Actualizar:
  - `docs/FUENTE_DE_VERDAD_ACTUAL.md`
  - `docs/arquitectura/ESTADO_PROYECTO.md`
  - `docs/arquitectura/PLAN_EJECUCION_BLOQUES_V3.md`
  - `CHANGELOG.md`

### Entregables
- Documento/ADR de alcance comercial mínimo.
- Documentación oficial alineada.
- Definición formal de GO/NO-GO comercial.

### Criterio de cierre
No existe contradicción entre estrategia, plan, estado y fuente de verdad.

---

## C1 — Cierre real de B1: pagos y suscripción productivos
### Objetivo
Pasar de pagos base/sandbox a cobro real confiable y trazable.

### Alcance
- MercadoPago real.
- Webhook robusto.
- Reconciliación y estados de suscripción correctos.

### Tareas
- Conectar credenciales y flujo real de MercadoPago.
- Garantizar idempotencia del webhook.
- Cubrir estados reales de pago y suscripción.
- Validar activación/desactivación correcta del feature gate.
- Diseñar y ejecutar flujo E2E del primer pago real.
- Documentar fallos conocidos, reintentos y resolución de incidentes de pago.

### Entregables
- Flujo documentado de pagos reales.
- Evidencia E2E de pago real.
- Matriz de estados y fallos.
- Validación de permisos premium por estado de plan.

### Criterio de cierre
Un pago real activa correctamente el plan y deja trazabilidad sin inconsistencias.

---

## C2 — Hardening productivo y persistencia operativa seria
### Objetivo
Blindar la operación real y eliminar ambigüedad en componentes launch-critical.

### Alcance
- Persistencia productiva seria para piezas sensibles.
- Backups, restore test y seguridad operativa mínima.

### Tareas
- Definir qué piezas deben salir de SQLite antes de go-live.
- Migrar o congelar fuera del alcance cualquier componente crítico que no tenga persistencia apropiada.
- Implementar backups y restore test real.
- Formalizar manejo de secretos, rollback y runbook de incidentes.
- Completar endurecimiento básico de observabilidad para pagos/suscripción.
- Validar que ninguna ruta crítica quede montada sobre solución temporal sin decisión explícita.

### Entregables
- Diseño de persistencia productiva.
- Runbook operativo.
- Evidencia de backup y restore.
- Checklist de hardening mínimo.

### Criterio de cierre
Ninguna pieza crítica para lanzamiento queda en estado temporal o ambiguo.

---

## C3 — Cumplimiento comercial y acceso responsable
### Objetivo
Subir la cobertura legal actual a un estándar comercial mínimo serio.

### Alcance
- Cobertura legal/comercial de suscripción y uso premium.
- Reglas de acceso responsable.

### Tareas
- Extender aceptación legal/comercial a flujos premium si corresponde.
- Formalizar términos de plan, cancelación, renovación y reembolso.
- Reforzar disclaimers y restricciones de uso en zonas premium.
- Definir reglas de acceso responsable y consistencia entre UI, backend y documentos.
- Validar que ningún flujo de cobro o uso premium quede legalmente flojo.

### Entregables
- Documento de cumplimiento comercial mínimo.
- Matriz de cobertura legal/comercial por flujo.
- Checklist de validación legal-operativa.

### Criterio de cierre
No existe pago ni uso premium sin cobertura legal/comercial coherente y verificable.

---

## C4 — Activación y entrada de valor controlada
### Objetivo
Reducir fricción de entrada y mejorar activación sin vender humo.

### Alcance
- Flujo visitante → registro → onboarding → pago.
- Exposición clara de valor antes del muro de uso completo.

### Tareas
- Diseñar experiencia inicial de valor para usuario nuevo.
- Separar claramente capacidades de visitante, registrado y suscrito.
- Mostrar propuesta de valor, límites y alcance de cada plan.
- Refinar métricas de activación hacia valor real, no solo registro.
- Evitar narrativa de “ganancia fácil” en toda la entrada del producto.

### Entregables
- Flujo de activación refinado.
- Matriz de capacidades por tipo de usuario.
- Definición de puntos de valor previos al onboarding completo.
- KPIs de activación actualizados.

### Criterio de cierre
Un usuario nuevo entiende qué hace el sistema, por qué vale y cómo avanzar sin fricción innecesaria ni promesa confusa.

---

## C5 — Paridad operativa de fútbol
### Objetivo
Llevar fútbol a una condición de módulo serio, aunque siga etiquetado como beta/laboratorio.

### Alcance
- Contrato canónico.
- Cero mocks en producción.
- Misma disciplina operativa base que NBA.

### Tareas
- Cerrar endpoints huérfanos frontend/backend.
- Eliminar cualquier mock productivo.
- Canonizar esquema y payloads de fútbol.
- Llevar fútbol al mismo marco base de métricas, trazabilidad, gates y observabilidad.
- Definir criterios objetivos de salida de laboratorio.

### Entregables
- Contrato canónico de fútbol.
- Dashboard sin mocks.
- Checklist de madurez de fútbol.
- Documento de criterios de promoción comercial.

### Criterio de cierre
Fútbol deja de ser frágil y ambiguo operativamente, aunque comercialmente siga marcado como beta si así se decide.

---

## C6 — Centro Analítico Multideporte v1
### Objetivo
Unificar experiencia de producto sin fusionar a la fuerza semánticas distintas.

### Alcance
- Shell común.
- KPIs base comunes.
- Transparencia de madurez por deporte.

### Tareas
- Diseñar dashboard principal unificado.
- Incluir selector de deporte y widgets compartidos.
- Mantener paneles específicos donde el dominio lo requiera.
- Mostrar claramente estado/madurez por deporte.
- Evitar mezclar lógicas incompatibles en una sola pantalla monolítica.

### Entregables
- Dashboard principal unificado.
- Navegación común.
- Filtro por deporte.
- Contrato base de métricas comunes.

### Criterio de cierre
Existe una experiencia multideporte coherente, honesta y escalable.

---

## C7 — Gate comercial mínimo y cohorte piloto
### Objetivo
Validar el producto como negocio real antes de escalar adquisición.

### Alcance
- Flujo E2E comercial.
- Cohorte piloto controlada.

### Tareas
- Ejecutar flujo completo: registro → aceptación legal → onboarding → pago → uso premium → soporte básico → cancelación si aplica.
- Validar ausencia de P0/P1.
- Operar cohorte piloto pequeña y medible.
- Medir activación, conversión, incidencias y trazabilidad.
- Emitir decisión formal de GO/NO-GO comercial.

### Entregables
- Reporte de gate comercial.
- Evidencia E2E completa.
- Checklist de salida.
- Lista priorizada de defectos y decisión final.

### Criterio de cierre
Se puede operar comercialmente una cohorte real sin romper pagos, confianza, trazabilidad ni gobierno operativo.

---

## Regla documental obligatoria por cada bloque C
Al cerrar cada bloque:
1. Actualizar `docs/arquitectura/ESTADO_PROYECTO.md`
2. Agregar entrada en `CHANGELOG.md`
3. Actualizar ADRs/documentos rectores cuando aplique
4. Preservar evidencia en `docs/borlty-deliverables/`
5. Archivar documentación obsoleta o reemplazada

## Resultado esperado
Al terminar C0–C7, AnalyticsPredict debe quedar en condición de:
- cobrar el primer peso con seguridad,
- operar con trazabilidad,
- comunicar una propuesta profesional defendible,
- lanzar con foco y sin contradicciones estructurales.

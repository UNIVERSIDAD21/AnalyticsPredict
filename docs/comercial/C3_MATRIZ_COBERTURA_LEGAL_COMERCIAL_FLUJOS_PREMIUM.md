# C3 — Matriz de cobertura legal/comercial por flujo premium

| Flujo premium | Cobertura actual | Vacío detectado | Ajuste C3 aplicado | Evidencia/ruta |
|---|---|---|---|---|
| Checkout / suscripción | Endpoint y trazabilidad técnica en C1 | Faltaba consolidación comercial mínima en un solo documento | Se formaliza política de plan/cancelación/renovación/reembolso | `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md` |
| Transición de estados de cobro | Matriz técnica C1 disponible | Faltaba vínculo explícito con decisión comercial de acceso | Se vincula estado de pago a estado comercial de suscripción y gate | `docs/operacion/C1_MATRIZ_ESTADOS_Y_FALLOS.md` + C3 |
| Feature gate premium | Regla backend implementada (`active` habilita) | Faltaba marco comercial explícito de elegibilidad | Se explicita elegibilidad y límites de promesa | `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md` |
| Mensajes/beneficios premium (UI) | Existe narrativa base y disclaimers generales | Riesgo de copy ambiguo si no hay checklist de validación | Se agrega checklist legal-operativo previo a go-live | `docs/comercial/C3_CHECKLIST_VALIDACION_LEGAL_OPERATIVA.md` |
| Cancelación | Cobertura parcial en términos generales | Sin matriz explícita por flujo premium | Se formaliza criterio mínimo de cancelación | `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md` |
| Renovación | Dependía de interpretación de estado técnico | Faltaba redacción comercial clara | Se formaliza dependencia de webhook/estado de cobro | `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md` |
| Reembolso / incidencias | Estados técnicos contemplados (`refunded`, `charged_back`) | Faltaba encuadre comercial unificado | Se formaliza en política C3 + checklist | `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md` |

## Resultado de C3
No queda flujo premium sin trazabilidad documental o sin regla comercial mínima explícita.

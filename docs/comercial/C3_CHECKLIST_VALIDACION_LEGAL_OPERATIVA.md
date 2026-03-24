# C3 — Checklist de validación legal-operativa (previo a go-live)

## A. Cobertura documental
- [ ] Términos vigentes y versionados
- [ ] Política de privacidad vigente
- [ ] Disclaimer operativo vigente
- [ ] Documento C3 de cumplimiento comercial mínimo vigente
- [ ] Matriz C3 de cobertura por flujo premium vigente

## B. Flujos premium críticos
- [ ] Checkout genera `external_reference` trazable
- [ ] Webhook requiere firma válida
- [ ] Webhook repetido no duplica efectos (idempotencia)
- [ ] `approved` -> suscripción activa
- [ ] `pending/in_process/rejected/refunded/charged_back` no habilitan premium
- [ ] Feature-gate responde coherente con estado de suscripción

## C. Cobertura comercial mínima
- [ ] Plan definido (id, precio, moneda, alcance)
- [ ] Política de cancelación definida
- [ ] Política de renovación definida
- [ ] Política de reembolso definida
- [ ] Manejo de incidencias de cobro definido

## D. Restricciones y comunicación
- [ ] Mensajes premium sin promesa de rentabilidad
- [ ] Enfoque de uso: decisión con evidencia + riesgo
- [ ] No se posiciona como app masiva de picks

## E. Evidencia y trazabilidad
- [ ] Evidencia técnica C1 disponible
- [ ] Evidencia manual C1 (cuando aplique) anexada
- [ ] Changelog actualizado
- [ ] Estado de proyecto actualizado

## Criterio de aprobación C3
C3 se considera aprobado cuando todas las secciones A–E están en conformidad y no existe flujo premium sin respaldo documental/comercial mínimo.

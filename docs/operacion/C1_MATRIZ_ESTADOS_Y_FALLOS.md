# C1 — Matriz de estados y fallos

## Matriz pago -> suscripción -> gate
| payment.status | subscription.status | feature gate |
|---|---|---|
| approved | active | enabled |
| pending | past_due | disabled |
| in_process | past_due | disabled |
| rejected | inactive | disabled |
| cancelled | inactive | disabled |
| refunded | inactive | disabled |
| charged_back | inactive | disabled |

## Fallos y manejo

### 1) Firma inválida en webhook
- Respuesta: `401 Firma inválida`.
- Efecto: no cambia intent ni suscripción.

### 2) external_reference no registrado
- Respuesta: `404 external_reference no registrado`.
- Efecto: evita huérfanos de cobro.

### 3) Webhook repetido
- Control: tabla `payment_events` con unicidad por (`external_reference`, `payment_id`, `status`).
- Efecto: idempotencia explícita (`event_idempotent=true`).

### 4) Pago no aprobado
- Efecto: suscripción queda `inactive` o `past_due` según estado.
- Gate premium permanece bloqueado.

### 5) Intent terminal ya procesado
- Control: `payment_intents` evita reescritura destructiva al repetir mismo terminal + payment_id.

## Bloqueos que pasan a C2
- SQLite sigue siendo persistencia temporal para piezas launch-critical.
- Requiere inventario y decisión formal de migración/aceptación en C2.

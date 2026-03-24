# C1 — Flujo real de pagos (operativo)

## Objetivo
Garantizar cobro confiable y trazable para habilitar funcionalidades premium con feature gating consistente.

## Flujo operativo
1. Usuario autenticado solicita `POST /api/pagos/checkout-session`.
2. Backend crea `payment_intent` en estado `pending` y retorna `checkout_url` + `external_reference`.
3. Gateway notifica `POST /api/pagos/webhook/mercadopago` con firma HMAC.
4. Backend valida firma y registra evento idempotente (`payment_events`).
5. Backend actualiza intent y sincroniza estado de suscripción según estado de pago.
6. Frontend consulta:
   - `GET /api/pagos/suscripcion/mia`
   - `GET /api/pagos/feature-gate?feature=...`

## Endpoints C1
- `POST /api/pagos/checkout-session`
- `POST /api/pagos/webhook/mercadopago`
- `GET /api/pagos/suscripcion/mia`
- `GET /api/pagos/feature-gate`
- `GET /api/pagos/matriz-estados`

## Regla de feature gating
- `subscription.status == active` => habilita feature premium.
- `past_due|inactive` => bloquea feature premium.

## Trazabilidad mínima exigida
- `payment_intents` por intento de cobro.
- `payment_events` por webhook recibido (idempotencia por `external_reference + payment_id + status`).
- `subscriptions` sincronizada con último estado de cobro relevante.

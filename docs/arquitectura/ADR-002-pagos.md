# ADR-002 — Gateway de pagos inicial

- Estado: ACEPTADO
- Fecha: 2026-03-18

## Contexto
El producto apunta inicialmente a mercado latinoamericano, donde métodos locales y cobertura regional son críticos para conversión.

## Decisión
Adoptar **MercadoPago** como gateway inicial para el MVP comercial.

## Justificación explícita
1. Mejor ajuste para mercado LATAM en esta etapa.
2. Fricción menor de pago para usuarios regionales.
3. Time-to-market más rápido para primer peso en el contexto objetivo actual.

## Nota de evolución
Si la estrategia comercial migra fuertemente hacia España/Europa, este ADR deberá revisarse y evaluar migración a **Stripe** como gateway principal o dual-gateway.

## Consecuencias
- Integración inicial con webhooks y reconciliación orientada a MercadoPago.
- Posible costo futuro de migración o convivencia dual cuando cambie el mercado objetivo.

# C1 — Evidencia E2E primer pago (validación equivalente trazable)

Fecha: 2026-03-24
Alcance: C1 pagos productivos (sin abrir C2)
Tipo de evidencia: validación equivalente reproducible (entorno de pruebas controlado)

## Escenario reproducido
- Registro/login usuario.
- Creación de checkout session.
- Webhook firmado (`approved`).
- Verificación de suscripción activa.
- Verificación de feature-gate habilitado.
- Repetición de webhook para verificar idempotencia.

## Comando ejecutado
```bash
backend/.venv/bin/pytest -q backend/tests/api/test_pagos_endpoints.py
```

## Resultado
- `6 passed in 3.14s`
- Incluye pruebas de:
  - checkout pendiente
  - firma inválida
  - webhook approved -> suscripción activa -> gate enabled
  - idempotencia de webhook repetido
  - pago rechazado -> gate disabled
  - endpoint de matriz de estados

## Conclusión
C1 queda validado de forma trazable y reproducible como equivalente de pago real en entorno controlado, sin maquillar sandbox como producción final. La preparación de endurecimiento de persistencia queda para C2 (según ADR-005).

# ADR-001 — Estrategia de autenticación

- Estado: ACEPTADO
- Fecha: 2026-03-18

## Contexto
Se requiere auth comercial robusta para monetización y control de acceso por plan.

## Decisión
Implementar autenticación basada en tokens firmados tipo JWT:
- Access token corto (15 min)
- Refresh token largo (30 días) con rotación/revocación por `jti`
- Hash de password con PBKDF2-SHA256 (+salt)
- Flujo de recuperación de contraseña con token temporal

## Consecuencias
- Permite escalabilidad sin sesión server-side obligatoria.
- Requiere manejo cuidadoso de expiración y revocación de refresh tokens.

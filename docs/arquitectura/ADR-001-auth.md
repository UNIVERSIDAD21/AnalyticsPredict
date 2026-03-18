# ADR-001 — Estrategia de autenticación

- Estado: ACEPTADO
- Fecha: 2026-03-18

## Contexto
Se requiere auth comercial robusta para monetización y control de acceso por plan.

## Decisión
Implementar autenticación basada en JWT:
- Access token corto (15 min)
- Refresh token (7 días)
- Hash de password con bcrypt
- Flujo de recuperación de contraseña con token temporal

## Consecuencias
- Permite escalabilidad sin sesión server-side obligatoria.
- Requiere manejo cuidadoso de expiración y revocación de refresh tokens.

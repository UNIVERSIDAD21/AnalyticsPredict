# ESTADO_PROYECTO.md

Estado global: EN EJECUCIÓN (pre-lanzamiento comercial)
Última actualización: 2026-03-18
Responsable operativo: UNIVERSIDAD21

## Objetivo actual
Llegar a lanzamiento comercial mínimo viable con capacidad de cobrar el primer peso y operar con trazabilidad.

## Camino crítico vigente
A1 → (A2/A3/A4/A5) → A6 → (B1/B2/B3) → (B4/B5/B6) → B7

## Estado por bloque

| Bloque | Estado | Hecho | Decisiones tomadas | Abierto |
|---|---|---|---|---|
| A1 | EN_CURSO | Plan v3 incorporado, ADRs iniciales creados, CI en GitHub Actions creado (`.github/workflows/ci.yml`), base de staging en Docker creada (`deploy/staging/*`), validación local CI realizada (backend smoke 3/3 y frontend lint/build OK) | Staging+CI/CD básico adelantado a A1 | Validar despliegue real de staging con `staging.env` y smoke operativo (pendiente: host actual sin Docker) |
| A2 | EN_CURSO | Endpoints auth base + UI completa de auth en frontend (login/registro/recuperación/reset), contexto de sesión, rutas protegidas y cierre de sesión en header; tests API auth 3/3 y frontend lint/build OK | Tokens firmados con rotación/revocación (`jti`) + guard de rutas por sesión autenticada + flujo de recuperación temporal en staging | Migrar store auth a PostgreSQL y conectar recuperación a proveedor de correo real (eliminar `reset_token_dev`) |
| A3 | PENDIENTE | — | Contrato canónico con legacy temporal medido | Retiro progresivo legacy |
| A4 | PENDIENTE | — | Legal transversal obligatorio | Persistencia de aceptación legal |
| A5 | PENDIENTE | — | Métricas mínimas operativas obligatorias | Implementación dashboard/alertas |
| A6 | PENDIENTE | — | Gate con 0 P0/P1 | Validación integral |
| B1 | PENDIENTE | — | MercadoPago como gateway inicial | Implementación checkout/webhooks |
| B2 | PENDIENTE | — | Dashboard de usuario obligatorio para retención | Implementación onboarding+dashboard |
| B3 | PENDIENTE | — | Fútbol cross-liga v1 requerido antes del GO final | Ajustes de features y calibración |
| B4 | PENDIENTE | — | Notificaciones MVP por email | Jobs y preferencias usuario |
| B5 | PENDIENTE | — | Contexto chat con ventana deslizante N | Implementación chat_contexto.py |
| B6 | PENDIENTE | — | Hardening productivo se mantiene en fase B | Infra seguridad y runbooks |
| B7 | PENDIENTE | — | Gate final de salida comercial | E2E primer peso |

## Reglas permanentes de documentación
1. Al cerrar bloque: actualizar este archivo.
2. Registrar entrada breve en `CHANGELOG.md`.
3. Actualizar estado ADR (`PROPUESTO/ACEPTADO/SUPERADO`).
4. Eliminar/archivar documentación obsoleta para evitar contexto viejo.

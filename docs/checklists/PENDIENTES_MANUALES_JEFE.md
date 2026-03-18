# Pendientes manuales del Jefe (bloques AnalyticsPredict)

Estado: ACTIVO
Última actualización: 2026-03-18 02:25 UTC

## Cómo se usa
- Aquí se registran únicamente acciones que requieren intervención manual del Jefe.
- Cada pendiente debe incluir: bloque, motivo, acción exacta y estado.

## Pendientes actuales

### [A2] SMTP proveedor externo (opcional, no bloqueante)
- **Motivo:** A2 quedó cerrado con SMTP rápido local (MailHog). Para producción real conviene proveedor externo.
- **Acción manual del Jefe:** elegir proveedor SMTP (SendGrid / Resend / SES / Zoho / Gmail Workspace) y compartir credenciales/secretos.
- **Qué haré yo al recibirlo:** configurar env segura, validar envío real, documentar y cerrar pendiente.
- **Estado:** Pendiente (opcional)

---

## Histórico de pendientes resueltos

### [A2] Permiso Docker para despliegue staging
- **Estado:** Resuelto
- **Resolución:** acceso habilitado vía `sudo docker compose` para levantar y validar E2E en staging.

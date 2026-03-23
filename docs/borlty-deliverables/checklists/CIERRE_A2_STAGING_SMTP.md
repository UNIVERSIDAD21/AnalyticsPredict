# Checklist de cierre A2 en staging (Auth + SMTP)

Estado: LISTO PARA EJECUTAR
Última actualización: 2026-03-18

## Objetivo
Validar extremo a extremo en staging:
1) registro
2) login
3) refresh
4) logout
5) forgot/reset por correo real

---

## 0) Precondiciones

- Código desplegado con commits:
  - `365bfa6` (auth store postgres)
  - `a356239` (forgot/reset SMTP)
- Staging con backend y frontend levantados.
- PostgreSQL accesible desde backend.
- Cuenta SMTP operativa.

---

## 1) Configurar variables de entorno en staging

En `deploy/staging/staging.env` (o equivalente en tu entorno):

```env
# Base
DATABASE_URL=postgresql://usuario:password@host:5432/analyticspredict
AUTH_STORE_DRIVER=postgres
AUTH_SECRET_KEY=CAMBIAR_A_UN_SECRETO_FUERTE

# Recuperación por correo
AUTH_RESET_EMAIL_MODE=smtp
AUTH_FRONTEND_URL=http://localhost:15173
# Opción rápida recomendada (local): MailHog en Docker Compose
AUTH_SMTP_HOST=mailhog
AUTH_SMTP_PORT=1025
AUTH_SMTP_USER=
AUTH_SMTP_PASSWORD=
AUTH_SMTP_FROM=no-reply@tu-dominio.com
AUTH_SMTP_STARTTLS=false
AUTH_SMTP_SSL=false
STAGING_SMTP_UI_PORT=18025

# Opción proveedor externo (si ya tienes credenciales)
# AUTH_SMTP_HOST=smtp.tu-proveedor.com
# AUTH_SMTP_PORT=587
# AUTH_SMTP_USER=usuario_smtp
# AUTH_SMTP_PASSWORD=password_smtp
# AUTH_SMTP_STARTTLS=true
# AUTH_SMTP_SSL=false
```

> Nota: usa `AUTH_SMTP_SSL=true` y puerto `465` si tu proveedor lo requiere.

---

## 2) Reiniciar servicios de staging

```bash
cd deploy/staging
docker compose --env-file staging.env up -d --build
```

Verificar salud:

```bash
curl -s http://localhost:18000/salud
```

---

## 3) Smoke técnico de Auth API (manual)

### 3.1 Registro

```bash
curl -s -X POST http://localhost:18000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"qa-auth@analyticspredict.com","password":"12345678"}'
```

Esperado: `201`, `access_token`, `refresh_token`.

### 3.2 Login

```bash
curl -s -X POST http://localhost:18000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"qa-auth@analyticspredict.com","password":"12345678"}'
```

Esperado: `200`, tokens válidos.

### 3.3 Refresh

```bash
curl -s -X POST http://localhost:18000/api/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<REFRESH_TOKEN_LOGIN>"}'
```

Esperado: `200`, nuevos tokens.

### 3.4 Logout + bloqueo de token

```bash
curl -s -X POST http://localhost:18000/api/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN_LOGIN>"
```

Luego probar `/api/auth/me` con el mismo token:

```bash
curl -s http://localhost:18000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN_LOGIN>"
```

Esperado: `401` (token revocado).

---

## 4) Forgot/Reset con correo real

### 4.1 Solicitar recuperación

```bash
curl -s -X POST http://localhost:18000/api/auth/forgot-password \
  -H 'Content-Type: application/json' \
  -d '{"email":"qa-auth@analyticspredict.com"}'
```

Esperado:
- `200`
- mensaje estándar
- **sin** `reset_token_dev` en la respuesta

### 4.2 Revisar bandeja de correo

- Validar llegada del email.
- Copiar token incluido.

### 4.3 Reset password

```bash
curl -s -X POST http://localhost:18000/api/auth/reset-password \
  -H 'Content-Type: application/json' \
  -d '{"token":"<TOKEN_DEL_CORREO>","new_password":"87654321"}'
```

Esperado: `200`, contraseña actualizada.

### 4.4 Validar login con nueva contraseña

```bash
curl -s -X POST http://localhost:18000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"qa-auth@analyticspredict.com","password":"87654321"}'
```

Esperado: `200`.

---

## 5) Smoke frontend

1. Abrir `http://localhost:15173/login`.
2. Probar login exitoso.
3. Probar registro de nuevo usuario.
4. Probar forgot/reset siguiendo correo real.
5. Verificar redirección a rutas protegidas después de login.
6. Verificar logout desde header.

---

## 6) Criterio de cierre A2

A2 se considera **CERRADO** cuando:
- [ ] Auth corre sobre PostgreSQL en staging.
- [ ] Forgot/reset usa SMTP real (sin `reset_token_dev`).
- [ ] Flujo E2E completo validado en backend y frontend.
- [ ] Sin P0/P1 abiertos en auth.

---

## 7) Trazabilidad documental obligatoria al cerrar

Actualizar:
- `docs/arquitectura/ESTADO_PROYECTO.md` → A2 = CERRADO
- `CHANGELOG.md` con evidencia de validación
- ADR relacionado si cambió decisión técnica

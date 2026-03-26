# 01 — A1 real (staging + smoke)

## Objetivo
Cerrar A1 con despliegue real de staging y smoke operativo reproducible.

## Criterio de done
- Staging desplegado con `staging.env` válido.
- Smoke end-to-end ejecutado y evidenciado.
- Registro en reporte + actualización de estado.

## Entregables
- Runbook de despliegue staging real.
- Reporte smoke con resultado y evidencias.
- Estado A1 => CERRADO en ESTADO_PROYECTO.

## Riesgos
- Falta de host con Docker/recursos.
- Variables incompletas en staging.env.

---

## Runbook operativo (ejecución real)

### 1) Preparar entorno
```bash
cd deploy/staging
cp -n staging.env.example staging.env
# editar staging.env con valores reales
```

Campos críticos:
- `DATABASE_URL`
- `AUTH_SECRET_KEY`
- `MP_ACCESS_TOKEN`
- `MP_WEBHOOK_SECRET`
- puertos `STAGING_BACKEND_PORT` / `STAGING_FRONTEND_PORT`

### 2) Levantar staging
```bash
docker compose --env-file staging.env up -d --build
```

### 3) Ejecutar smoke A1
Desde raíz del repo:
```bash
STAGING_BASE_URL="http://localhost:${STAGING_BACKEND_PORT:-18000}" ./scripts/a1_smoke_staging.sh
```

El script genera reporte automático en:
- `docs/reportes/A1_SMOKE_STAGING_<timestamp>.md`

### 4) Criterio de avance
- Si smoke pasa + servicios estables: A1 listo para cierre documental.
- Si falla, registrar causa/acción en reporte y repetir.

## Evidencia mínima esperada para cerrar A1
1. Captura de `docker compose ps` con servicios healthy.
2. Reporte `A1_SMOKE_STAGING_*.md` exitoso.
3. Entrada en `CHANGELOG.md` + actualización de `ESTADO_PROYECTO.md`.

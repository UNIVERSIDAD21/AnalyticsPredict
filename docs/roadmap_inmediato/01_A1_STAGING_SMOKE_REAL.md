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

# B6 — Runbook de hardening productivo

Estado: EN_CURSO
Fecha: 2026-03-26

## Objetivo
Asegurar base operativa para pre-go-live público (secretos, despliegue controlado, recuperación).

## Flujo operativo recomendado
1. Ejecutar preflight de hardening:
```bash
./scripts/b6_preflight_hardening.sh
```
2. Revisar reporte `docs/reportes/B6_PREFLIGHT_<ts>.md`.
3. Corregir faltantes críticos de secretos y artefactos.
4. Validar staging + smoke A1.
5. Registrar evidencia de backup/restore (C2).

## Criterios mínimos de operación segura
- Variables sensibles presentes y no vacías.
- Composición de staging versionada.
- Scripts de smoke/reportes disponibles.
- Runbooks de pagos y persistencia accesibles.

## Salida esperada
- Reporte preflight verde.
- Checklist B6 en progreso con hallazgos/resolución.

# B6 — Checklist de hardening productivo

Estado: EN_CURSO

## Secretos y configuración
- [ ] `DATABASE_URL` definido y validado
- [ ] `AUTH_SECRET_KEY` definido y robusto
- [ ] `MP_ACCESS_TOKEN` presente
- [ ] `MP_WEBHOOK_SECRET` presente

## Operación y despliegue
- [ ] `deploy/staging/docker-compose.yml` vigente
- [ ] `staging.env` auditado sin placeholders críticos
- [ ] smoke A1 ejecutado en staging real

## Continuidad y recuperación
- [ ] estrategia C2 de persistencia revisada
- [ ] runbook rollback/secretos validado
- [ ] evidencia de restore reciente

## Cierre B6
- [ ] preflight B6 sin hallazgos críticos
- [ ] reporte de cierre B6 emitido
- [ ] ESTADO_PROYECTO actualizado

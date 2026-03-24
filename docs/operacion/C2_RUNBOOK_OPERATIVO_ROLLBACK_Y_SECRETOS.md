# C2 — Runbook operativo, rollback y secretos

## 1) Runbook de operación mínima

### Arranque
1. Verificar variables críticas:
   - `AUTH_DB_PATH`
   - `PAGOS_DB_PATH`
   - `MERCADOPAGO_WEBHOOK_SECRET`
2. Validar salud mínima:
   - `GET /api/operacion/c2/health-critical`
3. Validar pagos:
   - `GET /api/pagos/matriz-estados`

### Monitoreo diario
- Revisar `overall` en `health-critical`.
- Revisar tamaño de DBs y presencia de tablas críticas.
- Revisar tasa de webhooks inválidos/404.

## 2) Backups y restore

### Backup
```bash
scripts/ops/backup_sqlite.sh
```

### Restore
```bash
scripts/ops/restore_sqlite.sh <ruta_backup>
```

### Test de restore real
```bash
scripts/ops/test_backup_restore.sh
```

## 3) Rollback operativo
1. Pausar tráfico de escritura (o modo mantenimiento).
2. Seleccionar backup válido más reciente.
3. Ejecutar restore.
4. Verificar salud (`/api/operacion/c2/health-critical`).
5. Reanudar tráfico y monitorear 15 min.

## 4) Política mínima de secretos
- No secretos en código ni repositorio.
- Solo por variables de entorno o secret manager del entorno.
- Rotación mínima trimestral para webhook secret.
- Cambio de secreto => validar firma en webhook antes de habilitar tráfico.

## 5) Criterio de incidente severo
- Corrupción/no lectura de DB crítica.
- caída de componente pagos/auth en `health-critical`.
- webhooks fallando sistemáticamente.

Acción: activar rollback + reporte de incidente.

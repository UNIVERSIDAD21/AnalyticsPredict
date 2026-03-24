# C2 — Matriz formal de persistencias temporales y decisiones

| componente | ruta/archivo | tipo de dato | criticidad | tecnología actual | riesgo | decisión propuesta | justificación | impacto en lanzamiento |
|---|---|---|---|---|---|---|---|---|
| AuthStore | `backend/servicios/auth_store.py` + `AUTH_DB_PATH` | usuarios, sesión, revocación tokens | Alta (launch-critical) | SQLite | single-node/local-disk, backup manual | Aceptar temporal con mitigación | Permite salida controlada si hay backup/restore probado + runbook + monitoreo | No bloquea C2 si mitigaciones activas |
| PagosStore | `backend/servicios/pagos_store.py` + `PAGOS_DB_PATH` | intents, suscripciones, eventos webhook | Muy alta (launch-critical) | SQLite | pérdida de estado por corrupción/disco, concurrencia limitada | Aceptar temporal con mitigación (C2) + migración planificada C2.1 | Idempotencia y trazabilidad ya implementadas; falta endurecimiento de persistencia | No bloquea primer peso con controles C2 activos |
| Evidencia/reportes | `docs/reportes/*` | evidencia operativa/auditoría | Media | Markdown + git | dispersión documental | Aceptar | No es estado transaccional de producto | Sin impacto crítico |
| Métricas operativas mínimas | endpoint nuevo `GET /api/operacion/c2/health-critical` | salud de componentes críticos | Alta | FastAPI + sqlite checks | sin endpoint => baja detectabilidad | Migrar (implementar ahora) | Necesario para observabilidad mínima de lanzamiento | Reduce MTTR y ambigüedad |
| Backups de DB críticas | `scripts/ops/backup_sqlite.sh` | snapshot auth/pagos | Muy alta | shell + copy | sin automatización => no recuperabilidad real | Migrar (implementar ahora) | obligatorio para continuidad operativa mínima | Habilita restore test y runbook |
| Restore de DB críticas | `scripts/ops/restore_sqlite.sh` | recuperación auth/pagos | Muy alta | shell + copy | no probar restore => falsa seguridad | Migrar (implementar ahora) | criterio explícito de C2 | Habilita go-live controlado |

## Nota de gobierno
Esta matriz no oculta deuda: SQLite sigue siendo tecnología temporal para piezas launch-critical, pero queda formalmente aceptada con mitigaciones activas y evidencia de restore test real.

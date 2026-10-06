# Inventario de datos para migración single-user — 2026-10-05

**Fuente:** conexión a Neon mediante `DATABASE_URL` de `backend/.env`, transacción `BEGIN READ ONLY`, `statement_timeout` y solo consultas de metadatos/conteos. No se ejecutaron escrituras, migraciones ni ingestas. No se registraron IDs, correos, hashes, tokens, importes o filas de apuestas. El timeout anterior fue transitorio: DNS, TCP y PostgreSQL respondieron en el nuevo intento.

## Cardinalidad observada

| Tabla | Filas | IDs de usuario distintos | Uso |
|---|---:|---:|---|
| `usuarios` | 4 | 4 | Tabla de aplicación |
| `auth_users` | 2 | 2 | Login legacy, ID numérico |
| `apuestas` | 182 | 3 | NBA/bitácora; `usuario_id` UUID no nulo |
| `apuestas_futbol` | 13 | 1 | Fútbol; `usuario_id` UUID no nulo |
| `apuestas_combinadas` | 7 | 1 | Combinadas; `usuario_id` UUID no nulo |
| `apuestas_analizadas` | 436 | — | Analítica; revisar relación propia y consumidores |
| `onboarding_profiles` / `onboarding_events` | 1 / 80 | 1 / 1 | Activación comercial/perfil |
| `subscriptions` | 1 | 1 | Existe registro; no borrar sin clasificar |
| `payment_intents` / `payment_events` | 0 / 0 | 0 / — | Ningún intento/evento en este corte |
| `auth_reset_tokens` / `auth_reset_tokens_v2` / `auth_revoked_tokens` | 2 / 0 / 3 | 2 / 0 / — | Datos de auth legacy |

Las vistas `vista_analisis_apuestas`, `vista_bitacora_unificada`, `vista_resumen_apuestas`, `vista_resumen_apuestas_futbol` y `vista_resumen_por_tipo_apuesta` también exponen `usuario_id`; deben revisarse antes de quitar la columna.

## Distribución seudonimizada de `usuarios`

Los alias U1–U4 corresponden al orden por UUID **solo en esta consulta**; no son identidades comerciales ni autorizan fusionar datos. Las fechas son extremos de creación, no una recertificación de resultados.

| Alias | Perfil técnico | Apuestas NBA | Fútbol | Combinadas | Primer/último registro de apuesta |
|---|---|---:|---:|---:|---|
| U1 | UUID fijo de desarrollo; rol admin; creado 2026-01-07 | 172 | 13 | 7 | 2026-01-10 / 2026-03-30 |
| U2 | Usuario activo sin apuestas en estas tres tablas; creado 2026-04-01 | 0 | 0 | 0 | — |
| U3 | Usuario activo con hash placeholder de login; creado 2026-04-01 | 1 | 0 | 0 | 2026-04-01 |
| U4 | Usuario activo con hash placeholder de login; creado 2026-04-01 | 9 | 0 | 0 | 2026-04-01 / 2026-04-03 |

El cotejo por correo entre `auth_users` y `usuarios` no produjo coincidencias en estas cuatro filas. Un correo de referencia del repositorio tampoco coincidió; ello **no identifica al propietario**, pues su correo de aplicación podría ser diferente. El único ID de `subscriptions` coincide con `auth_users` y no con `usuarios`; el de `onboarding_profiles` y los 80 eventos coincide con `usuarios` y no con `auth_users`. No se registraron esos IDs ni se asignó el perfil a un alias en este informe.

## Integridad estructural

- `apuestas.usuario_id`, `apuestas_futbol.usuario_id` y `apuestas_combinadas.usuario_id` tienen FK hacia `usuarios`; `auth_reset_tokens.user_id` referencia `auth_users`.
- Las tres tablas de apuestas tienen `usuario_id NOT NULL`, sin nulos en el corte. No se comprobó aún el contenido ni integridad de todas las vistas/triggers.
- **Conclusión:** existen varias identidades históricas. No es válido retirar `usuarios`, quitar la FK o fusionar apuestas automáticamente. Conservar procedencia y decidir qué registros serán visibles en métricas personales antes de migrar.

## Próxima verificación

Clasificar U1–U4 con el propietario; inventariar `pg_views`, triggers, índices, consumers SQL y configuración de sizing; generar snapshot aislado y comparar conteos/checksums en ensayo reversible. Mantener `subscriptions` archivada hasta determinar su naturaleza. Ningún H1–H4 se marca cerrado por este inventario.

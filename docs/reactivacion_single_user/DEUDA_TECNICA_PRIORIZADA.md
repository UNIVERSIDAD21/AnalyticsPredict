# Deuda técnica priorizada — reactivación single-user

**Corte:** 2026-10-05. Prioridades derivadas del plan del propietario y H1–H12 de la auditoría histórica; no equivalen a certificación actual.

| Prioridad | Trabajo | Criterio verificable | Estado |
|---|---|---|---|
| P0 | Perímetro privado antes de retirar auth | Backend sensible ligado a loopback | Cerrado para uso exclusivamente local confirmado; revalidar ante otra topología |
| P0 | Inventario y migración de `usuario_id`/FK | Ensayo aislado y conteos idénticos | Cerrado: backup privado verificado, todos los registros deportivos conservados |
| P0 | Retirar login/auth, pagos, MP, suscripciones y tiers sin perder análisis | OpenAPI/UI sin superficies comerciales, headers/tokens ni gates; NBA/fútbol/bitácora íntegros | Cerrado en código/API/UI/BD activos; smoke visual y HTTP |
| P1 | H6 escala `hit_rate_sin_push` | Casos 0/50/56/100%, backend/FE coherentes | Corregido; tests numéricos y build |
| P1 | H7 envelopes y estados de bitácora | Lista y tarjetas no vacías, error no convertido a cero | Corregido en clientes v2 de bitácora; pruebas FE/BE dirigidas. Falta smoke visual posterior al reinicio. |
| P1 | H9 métricas Brier/ECE/LogLoss | Medición real o `null` explícito, tests numéricos | Corregido para calibración fútbol; 24 mercados sin outcomes devuelven `null`, no proxies |
| P1 | H11 entorno reproducible y H10 CI | BD efímera, unit/contract/integration/FE/build en CI | CI ampliada a unitarias/contratos/FE; integración con BD efímera y lock Python pendientes. |
| P1 | H4 SQLite versionadas | Retirar seguimiento sin borrar evidencia; clasificar credenciales | DB comerciales retiradas del índice Git e ignoradas; copias locales preservadas. Historial Git anterior aún contiene blobs. |
| P1 analítico | H8 walk-forward real/no-leakage | `fit_end < prediction_time < outcome_time`, snapshots/model IDs | Pendiente, después de plataforma |
| P2 analítico | Recertificar NBA/fútbol, confidence, odds, calidad y KPIs | Cortes actuales, n/método/limitaciones, sin rentabilidad futura | Pendiente |
| P3 | H12 permisos/reportes vacíos y project rot | Reparación específica con evidencia, no limpieza estética | Pendiente; 30 cambios de modo preexistentes preservados |

H1–H3 no se cierran por decisión de producto sino al probar la desaparición de sus superficies. Fútbol permanece beta hasta evidencia cuantitativa actual; el análisis NBA interno mantiene política sin picks/stakes/recomendaciones.

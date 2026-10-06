# Deuda técnica priorizada — reactivación single-user

**Corte:** 2026-10-05. Prioridades derivadas del plan del propietario y H1–H12 de la auditoría histórica; no equivalen a certificación actual.

| Prioridad | Trabajo | Criterio verificable | Estado |
|---|---|---|---|
| P0 | Perímetro privado de cada entorno antes de retirar auth | Backend sensible inaccesible fuera de loopback/VPN/access proxy; topología y prueba registradas | Local observado en loopback; staging/remoto sin verificar |
| P0 | Inventario y migración de `usuario_id`/FK | Cardinalidad/propiedad, ensayo aislado y conteos idénticos | BD remota timeout; pendiente |
| P0 | Retirar login/auth, pagos, MP, suscripciones y tiers sin perder análisis | OpenAPI/UI sin superficies comerciales, headers/tokens ni gates; NBA/fútbol/bitácora íntegros | Pendiente |
| P1 | H6 escala `hit_rate_sin_push` | Casos 0/50/56/100%, backend/FE coherentes | Pendiente |
| P1 | H7 envelopes y estados de bitácora | Lista y tarjetas no vacías, error no convertido a cero | Pendiente |
| P1 | H9 métricas Brier/ECE/LogLoss | Medición real o `null` explícito, tests numéricos | Pendiente |
| P1 | H11 entorno reproducible y H10 CI | BD efímera, unit/contract/integration/FE/build en CI | Documentado inicialmente; implementación pendiente |
| P1 | H4 SQLite versionadas | Retirar seguimiento sin borrar evidencia; clasificar credenciales | Pendiente |
| P1 analítico | H8 walk-forward real/no-leakage | `fit_end < prediction_time < outcome_time`, snapshots/model IDs | Pendiente, después de plataforma |
| P2 analítico | Recertificar NBA/fútbol, confidence, odds, calidad y KPIs | Cortes actuales, n/método/limitaciones, sin rentabilidad futura | Pendiente |
| P3 | H12 permisos/reportes vacíos y project rot | Reparación específica con evidencia, no limpieza estética | Pendiente; 30 cambios de modo preexistentes preservados |

H1–H3 no se cierran por decisión de producto sino al probar la desaparición de sus superficies. Fútbol permanece beta hasta evidencia cuantitativa actual; el análisis NBA interno mantiene política sin picks/stakes/recomendaciones.

# Roadmap de reactivación AnalyticsPredict

**Directiva vigente:** plan single-user del propietario del 2026-10-05. Esta secuencia sustituye C0–C7 comerciales. `CERRADO` solo se usa con evidencia; diseño documental no equivale a implementación.

| Bloque | Objetivo | Estado al 2026-10-05 | Gate para avanzar |
|---|---|---|---|
| A0 | Snapshot, mapa de impacto, arquitectura, endpoints y migración | Documentado; rama de recuperación creada | Verificar mapa contra código al ejecutar cambios |
| A1 | Perímetro privado en todos los entornos y datos | Defaults de desarrollo/Compose ligados a loopback; inventario Neon read-only completado, despliegue no verificado | Topología comprobada + clasificación de propiedad U1–U4 |
| A2 | Retirar auth/login y headers/tokens | Pendiente | API y UI sin sesión; operaciones sensibles privadas |
| A3 | Retirar pagos, suscripciones y tiers; conservar profundidad analítica | Pendiente | Superficies comerciales ausentes, contratos analíticos pasan |
| A4 | Migrar configuración, bitácora y datos históricos | Pendiente | Ensayo aislado, conteos/checksums y rollback; aplicar real solo autorizado |
| A5 | Limpiar legacy/config/DB versionadas y reportar eliminación | Pendiente | Sin consumidores; H1–H4 con evidencia; README/estado/CI alineados |
| B | H6/H7/H9, entorno reproducible y CI | Entorno descrito inicialmente; correcciones pendientes | Pruebas numéricas/contrato y gates CI reales |
| C | NBA, fútbol, walk-forward, confidence, odds, data quality, KPIs y observabilidad | Pendiente | Evidencia actual, muestras y límites explícitos |
| D | Explicabilidad avanzada, gobierno de modelos y evolución | Fuera del bloque inmediato | Solo tras recertificación C |

## Dependencia inmediata

El timeout inicial de Neon fue transitorio. El inventario de solo lectura detectó varias identidades históricas; falta clasificar propiedad de registros y ensayar una copia aislada. También se debe verificar si existe despliegue accesible fuera del host local antes de desmontar auth. Ningún cobro, ingesta o despliegue se usa como prueba de arranque.

## Forma de cierre por bloque

Registrar objetivo, evidencia previa, archivos, decisiones, tests, resultados, riesgos, pendientes y siguiente paso. Actualizar `ESTADO_PROYECTO.md`/`CHANGELOG.md` y este roadmap sin reescribir los informes de auditoría.

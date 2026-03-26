# 00 — Índice de Ejecución Inmediata (Panel Operativo Permanente)

Estado: VIGENTE
Fecha: 2026-03-26

Este índice define el orden operativo único para evitar confusión entre sesiones.

## Orden de ejecución aprobado
1. A1 real (staging + smoke)
2. B3 cierre formal (2 ciclos semanales)
3. B4 cierre formal (24h SLO)
4. B6 hardening productivo
5. P7 backend profundo
6. Optimización extra frontend (DashboardFutbol/index)
7. Sunset legacy (A3 post-cierre)
8. B5 proveedor real (solo si chat vuelve a prioridad)

## Regla de gobierno
- Este índice manda sobre listas dispersas de prioridades.
- Si cambia el orden, se actualiza aquí primero y luego ESTADO_PROYECTO/CHANGELOG.

## Documentos de bloque
- [01_A1_STAGING_SMOKE_REAL.md](./01_A1_STAGING_SMOKE_REAL.md)
- [02_B3_CIERRE_FORMAL.md](./02_B3_CIERRE_FORMAL.md)
- [03_B4_CIERRE_24H_SLO.md](./03_B4_CIERRE_24H_SLO.md)
- [04_B6_HARDENING_PRODUCTIVO.md](./04_B6_HARDENING_PRODUCTIVO.md)
- [05_P7_BACKEND_PROFUNDO.md](./05_P7_BACKEND_PROFUNDO.md)
- [06_P9_OPTIMIZACION_FRONTEND_EXTRA.md](./06_P9_OPTIMIZACION_FRONTEND_EXTRA.md)
- [07_A3_SUNSET_LEGACY_REAL.md](./07_A3_SUNSET_LEGACY_REAL.md)
- [08_B5_PROVEEDOR_REAL_CHAT_OPCIONAL.md](./08_B5_PROVEEDOR_REAL_CHAT_OPCIONAL.md)

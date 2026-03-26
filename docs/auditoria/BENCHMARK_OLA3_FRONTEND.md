# BENCHMARK OLA 3 — FRONTEND

Fecha: 2026-03-26
Alcance: UX + rendimiento en frontend (P9) y observabilidad operativa para P7.

## Comandos ejecutados
- `npm run lint`
- `npm run build`

## Resultados de build (última corrida)
- `PaginaPrincipal`: **159.60 kB** (gzip 36.50 kB)
- `PaginaDashboardUsuario`: **13.13 kB** (gzip 3.76 kB)
- `DashboardFutbol`: **28.51 kB** (gzip 6.38 kB)
- `GraficoRoiTemporalFutbol` (lazy): **384.56 kB** (gzip 106.31 kB)
- `index`: **274.47 kB** (gzip 86.40 kB)

## Variación relevante
- `DashboardFutbol` baja de **412.41 kB** a **28.51 kB** moviendo gráfico ROI a chunk lazy dedicado.
- Carga inicial del dashboard mejora; costo pesado de charts pasa a carga bajo demanda.

## Mejoras aplicadas durante Ola 3
1. Carga diferida por rutas (`React.lazy` + `Suspense`) en `App.tsx`.
2. Carga diferida de módulos pesados de estadísticas en `PaginaPrincipal`.
3. Caché de 5 min para baseline técnico 1X2.
4. Caché de 60s para observabilidad/salud backend con refresh forzado.
5. KPIs de rendimiento cliente visibles en dashboard (DOM Ready / Load / Transfer).

## Conclusión
- El sistema quedó con instrumentación de rendimiento visible y optimizaciones de carga activas.
- Se establece baseline técnico reproducible para continuar iteraciones sin perder trazabilidad.

# BENCHMARK OLA 3 — FRONTEND

Fecha: 2026-03-26
Alcance: UX + rendimiento en frontend (P9) y observabilidad operativa para P7.

## Comandos ejecutados
- `npm run lint`
- `npm run build`

## Resultados de build (última corrida)
- `PaginaPrincipal`: **159.60 kB** (gzip 36.50 kB)
- `PaginaDashboardUsuario`: **13.13 kB** (gzip 3.76 kB)
- `DashboardFutbol`: **412.41 kB** (gzip 112.00 kB)
- `index`: **274.47 kB** (gzip 86.41 kB)

## Mejoras aplicadas durante Ola 3
1. Carga diferida por rutas (`React.lazy` + `Suspense`) en `App.tsx`.
2. Carga diferida de módulos pesados de estadísticas en `PaginaPrincipal`.
3. Caché de 5 min para baseline técnico 1X2.
4. Caché de 60s para observabilidad/salud backend con refresh forzado.
5. KPIs de rendimiento cliente visibles en dashboard (DOM Ready / Load / Transfer).

## Conclusión
- El sistema quedó con instrumentación de rendimiento visible y optimizaciones de carga activas.
- Se establece baseline técnico reproducible para continuar iteraciones sin perder trazabilidad.

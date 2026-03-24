# C6 — Inventario real de vistas NBA vs fútbol

Fecha: 2026-03-24
Estado: CERRADO

## Vistas NBA (actuales)
- `/` → `PaginaPrincipal` (análisis NBA principal)
- `/bitacora` → `PaginaBitacora`

## Vistas fútbol (actuales)
- `/futbol` → `PaginaFutbol` (partidos + filtros + acceso a análisis)
- `/futbol/partidos/:id` → `AnalisisPartidoFutbol`
- `/futbol/dashboard` → `DashboardFutbol`
- `/futbol/bitacora` → `PaginaBitacora` en contexto fútbol

## Vistas comunes transversales
- `/centro-analitico` → `PaginaCentroAnalitico` (nuevo en C6)
- `/chat` → `PaginaChat`
- `/configuracion` → `PaginaConfiguracion`
- `/dashboard` → `PaginaDashboardUsuario`

## Lectura operativa
- NBA y fútbol comparten estructura de uso (análisis/bitácora/KPIs base),
  pero mantienen semánticas analíticas distintas.
- C6 no fusiona paneles profundos: unifica shell y capa de entrada multideporte.

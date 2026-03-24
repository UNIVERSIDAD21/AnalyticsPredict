# C6 — Ejecución Centro Analítico Multideporte (2026-03-24)

## Orden interno ejecutado
1. Inventario real de vistas NBA y fútbol.
2. Definición de shell común y navegación común.
3. Definición de KPIs base compartidos.
4. Incorporación de selector/filtro por deporte.
5. Visualización explícita de madurez/estado por deporte.
6. Mantenimiento de paneles específicos por dominio.
7. Definición de contrato base de métricas comunes.
8. Actualización de documentación, estado y changelog.

## Implementación
- Nueva vista unificada: `/centro-analitico` (`PaginaCentroAnalitico`).
- Navegación común reforzada en `Encabezado` con acceso directo a Centro.
- Selector de deporte integrado en la vista unificada.
- KPIs base compartidos calculados sobre apuestas analizadas por deporte.
- Señal de madurez explícita: NBA (MADURO), Fútbol (BETA/LAB).
- Análisis profundo se mantiene en páginas específicas (no monolito).

## Conclusión
C6 habilita una base multideporte escalable sin romper camino principal de caja ni alterar estrategia comercial vigente.

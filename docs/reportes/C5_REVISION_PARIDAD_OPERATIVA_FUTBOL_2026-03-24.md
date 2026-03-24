# C5 — Revisión de paridad operativa fútbol (2026-03-24)

## Hallazgos
- Frontend `DashboardFutbol` usaba serie temporal simulada para ROI acumulado.
- Backend no exponía endpoint canónico específico para serie temporal de ROI acumulado.

## Acciones ejecutadas
1. Implementado endpoint backend real: `GET /api/futbol/metricas/roi-temporal`.
2. Actualizado frontend para consumir `obtenerRoiTemporal(30)`.
3. Eliminada generación mock del gráfico temporal en `DashboardFutbol`.
4. Documentados contrato canónico, checklist de madurez y criterios de promoción comercial.

## Resultado
- Dashboard de fútbol opera con datos reales (o vacío explícito) para ROI temporal.
- Se reduce ambigüedad operativa y se fortalece trazabilidad del módulo.

## Riesgos remanentes
- Persisten riesgos globales ya conocidos: C1 requiere validación manual final de MP y deuda estructural de persistencias fuera del alcance de C5.

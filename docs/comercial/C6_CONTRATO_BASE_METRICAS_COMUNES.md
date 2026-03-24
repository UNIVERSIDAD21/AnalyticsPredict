# C6 — Contrato base de métricas comunes multideporte

Fecha: 2026-03-24
Estado: CERRADO

## Objetivo del contrato
Definir una capa de KPIs compartidos entre deportes para el Centro Analítico, sin mezclar semánticas de análisis profundo.

## Fuente actual (v1)
`GET /api/bitacora/apuestas-analizadas?page_size=500`

## Transformación canónica C6 (frontend)
Filtrar por `deporte` en cliente y calcular:
- `apuestasTotales`
- `resueltas`
- `ganadas`
- `winRate`

## Esquema canónico KPIBase
```json
{
  "apuestasTotales": 0,
  "resueltas": 0,
  "ganadas": 0,
  "winRate": 0.0
}
```

## Reglas de uso
1. `KPIBase` es para comparabilidad transversal y navegación ejecutiva.
2. Métricas específicas (calibración por mercado, modelos por dominio, etc.) se mantienen en vistas específicas por deporte.
3. Si no hay datos de un deporte, se muestra cero explícito; no se simulan datos.

## Anti-monolito
El contrato base NO reemplaza contratos analíticos específicos de NBA/fútbol; solo los complementa para shell común.

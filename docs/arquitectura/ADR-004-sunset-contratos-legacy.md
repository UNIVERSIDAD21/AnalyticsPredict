# ADR-004 — Umbral global de sunset para contratos legacy

- Estado: ACEPTADO
- Fecha: 2026-03-18

## Contexto
Durante A3 se habilitó contrato canónico (`v2`) con compatibilidad temporal `legacy` en dominios críticos (Auth, Bitácora y Resolución de apuestas fútbol). Se requiere un criterio único y medible para retirar `legacy` sin romper clientes activos.

## Decisión
Definir un umbral global de retiro de `legacy`:

1. **Condición técnica de sunset:** ratio de uso `legacy` menor al **5%** durante **7 días corridos** en cada dominio con telemetría de contrato.
2. **Condición operativa previa:** anunciar ventana de retiro con **30 días** de anticipación.
3. **Ejecución:** al cumplirse ambas condiciones, cambiar default a contrato canónico y deshabilitar explícitamente `legacy` en la siguiente release controlada.

## Consecuencias
- Se evita mantener indefinidamente deuda de compatibilidad.
- El retiro de `legacy` queda gobernado por métricas objetivas, no por percepción.
- Requiere revisar periódicamente endpoints de `contract-usage` para cada dominio.

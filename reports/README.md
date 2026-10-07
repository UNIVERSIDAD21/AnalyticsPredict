# Reportes locales heredados

Los reportes de este directorio son capturas históricas y **no certifican** el estado actual. Tres archivos JSON de 2026-02-22 estaban versionados con cero bytes: `csv/2026-02-22_021415/calidad_mercados.json`, `ejecutivo/2026-02-22_021251/resumen_compacto.json` y `ejecutivo/2026-02-22_021509/resumen_compacto.json`. Son capturas fallidas, no conjuntos vacíos válidos.

Esos tres archivos se retiraron solo del índice Git; las copias locales se preservan y el historial anterior permanece. Ningún dato fue reconstruido ni imputado. Los consumidores deben rechazar JSON vacío o inválido y mostrar `N/D`/error de captura, nunca convertirlo en cero. Nuevos reportes operativos deben quedar fuera del repositorio salvo evidencia agregada y revisada.

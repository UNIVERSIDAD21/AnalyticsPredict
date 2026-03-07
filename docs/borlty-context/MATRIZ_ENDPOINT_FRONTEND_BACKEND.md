# MATRIZ_ENDPOINT_FRONTEND_BACKEND.md

## Alcance
Matriz mínima de rutas críticas consumidas por frontend y su estado de contrato con backend.

## Leyenda
- ✅ Alineado
- ⚠️ Alineado con legado/heterogeneidad
- ❌ Roto

## Matriz (prioridad operativa)

| Ruta frontend | Backend existe | Estado contrato | Notas |
|---|---|---|---|
| `/api/analizar` | Sí | ⚠️ | respuesta útil, convención de envelope heterogénea |
| `/api/analizar-en-vivo` | Sí | ⚠️ | idem |
| `/api/bitacora` | Sí | ✅ | usa envelopes consistentes en rutas principales |
| `/api/bitacora/resumen` | Sí | ✅ | envelope estable |
| `/api/bitacora/metricas` | Sí | ⚠️ | revisar campos opcionales/legacy |
| `/api/bitacora/apuestas-analizadas` | Sí | ⚠️ | contrato útil, naming mixto |
| `/api/bitacora/unificada` | Sí | ⚠️ | payload grande, compatibilidad necesaria |
| `/api/predicciones/historial` | Sí | ⚠️ | convención de error no homogénea |
| `/api/partidos/hoy` | Sí | ⚠️ | coexiste retorno envelope/directo según ruta |
| `/api/partidos/proximos` | Sí | ⚠️ | idem |
| `/api/partidos` | Sí | ⚠️ | idem |
| `/api/partidos/buscar` | Sí | ⚠️ | idem |
| `/api/equipos` | Sí | ⚠️ | convención varía por endpoint |
| `/api/equipos/temporadas` | Sí | ⚠️ | idem |
| `/api/estadisticas-equipos` | Sí | ⚠️ | idem |
| `/api/combinadas` | Sí | ⚠️ | mezcla respuesta `{"exito":true}` y objeto directo |
| `/api/futbol/analizar` | Sí | ⚠️ | contrato funcional, heterogeneidad de errores |
| `/api/futbol/partidos/hoy` | Sí | ⚠️ | usa schemas fútbol con `exito` |
| `/api/futbol/partidos/proximos` | Sí | ⚠️ | idem |
| `/api/futbol/partidos/recientes` | Sí | ⚠️ | idem |
| `/api/futbol/partidos/h2h` | Sí | ⚠️ | idem |
| `/api/futbol/competiciones` | Sí | ⚠️ | idem |
| `/api/futbol/equipos` | Sí | ⚠️ | idem |
| `/api/futbol/apuestas` | Sí | ✅ | ruta canónica tras corrección previa |
| `/api/futbol/apuestas/resolver` | Sí | ✅ | alineado |
| `/api/futbol/metricas/resumen` | Sí | ⚠️ | envelope + detail según error |
| `/api/futbol/metricas/rendimiento` | Sí | ⚠️ | idem |
| `/api/futbol/metricas/calibracion` | Sí | ⚠️ | idem |
| `/api/futbol/metricas/modelos` | Sí | ⚠️ | idem |
| `/api/futbol/metricas/resumen-calidad-1x2` | Sí | ⚠️ | idem |
| `/api/metricas/calibracion` | Sí | ⚠️ | contrato útil, error heterogéneo |
| `/api/interno/recalibrar` | Sí | ✅ | respuesta envelope consistente |
| `/api/interno/alertas-calibracion/resolver` | Sí | ✅ | respuesta envelope consistente |

## Caso roto histórico ya cerrado
- `/api/futbol/apuestas/estadisticas` ❌ (no existe en backend)
- Estado actual: ✅ resuelto en frontend usando `/api/futbol/apuestas` + `resumen`.

---

## Observación clave
El problema actual no es tanto rutas faltantes (salvo caso ya corregido), sino **heterogeneidad de contratos de éxito/error entre dominios**.

# Estado de fuentes e ingesta controlada — 2026-10-06

**Estado:** NBA tiene flujo diario idempotente en ESPN; fútbol Sofascore está `SOURCE_UNAVAILABLE` (HTTP 403), **no** `NO_DATA`. Ninguna fuente/resultado está certificado por comparación independiente. No se lanzó ingesta fútbol con escritura.

> **Probe posterior sin DML:** `backend/scripts/auditar_fuente_espn_soccer.py` valida contrato read-only de scoreboard mensual ESPN Soccer y de boxscore por evento. La Liga `esp.1` 2026-03 devolvió 36 finales con identidad, kickoff UTC y goles; dos boxscores muestreados tenían corners, tiros y tiros a puerta completos para ambos equipos. Octubre 2026 devolvió 36 eventos programados, cero finales al corte: los scores pregame no se imputan. El cliente no reintenta HTTP 403, distingue `NO_DATA` de `SOURCE_UNAVAILABLE` y falla ante lista/identidad incompleta. Esto prueba factibilidad parcial de una fuente alternativa, **no** adaptación a IDs Sofascore/Neon, cobertura de otras ligas, ingesta reciente ni outcome independiente de ESPN NBA. Evidencia JSON fuera del repo en `CIERRE_PENDIENTES_ANALYTICSPREDICT_2026-10-06`.

## Comprobaciones observadas

| Fuente | Comprobación | Resultado |
|---|---|---|
| ESPN NBA | `actualizar_partidos_nba.py --from-date 2026-10-01 --to-date 2026-10-06 --season 2027 --dry-run` contra Neon en lectura | 8 existentes, 0 nuevos, 0 actualizados, 0 fallos. Son pretemporada; el lote real de 8 ya se documentó en `INGESTA_NBA_CONTROLADA_2026-10-06.md`. |
| Sofascore fútbol | `sincronizar_futbol.py --liga laliga --dias 7 --dry-run --timeout 8` | HTTP 403 en `unique-tournament/8/seasons`, salida 1, `SOURCE_UNAVAILABLE`, cero escrituras. Se detiene tras **una** respuesta 403 sin impersonación, VPN ni reintentos. |
| ESPN soccer | Probe de Scoreboard público, separado de la ingesta actual | HTTP 200 y eventos en ventanas anteriores de Premier/La Liga, pero cero eventos el 2026-10-03/06 en las ligas consultadas. Es un **candidato** para evaluar contrato/mapeo; no está integrado ni autoriza imputar fútbol actual. |

Un 200 con JSON válido y lista vacía después de consulta completa significa `NO_DATA` **solo para la ventana consultada**. Un 403, 404/contrato roto o interrupción de paginación significa `SOURCE_UNAVAILABLE`; no se procesa lote parcial. El sincronizador ahora informa la última respuesta 200 y la fecha del último evento válido por separado. El `--dry-run` coloca también la transacción de BD en `READ ONLY` (NBA y fútbol), no solo omite los `INSERT`.

## Calidad de mapeo pendiente

NBA conserva clave `source=ESPN`/`source_game_id`, separa `PRE/REG/POST`, rechaza 0–0, exige cuatro cuartos y confronta líneas de OT con totales; mantiene idempotencia. La fecha del evento proviene de ISO de ESPN; requiere cotejo independiente de timezone del partido y resultado antes de usarlo como outcome científico. Football conserva ID Sofascore y estados de proveedor; el cliente ahora usa UTC y preserva marcador **cero** cuando `current=0` (antes la expresión `or` lo reemplazaba). Solo marca completos corners y disparos cuando ambos equipos aportan los campos requeridos. Estas correcciones de código no rellenan los 25 finalizados incompletos ni prueban cobertura de competiciones.

## Checklist y criterio de aceptación

- [x] NBA dry-run read-only e idempotencia observada sobre la ventana 1–6 de octubre.
- [x] Temporada NBA 2026–27 y segmentación PRE/REG/POST en el ingestor.
- [x] Sofascore 403 diagnosticado sin eludir protecciones; 403 no se etiqueta como jornada vacía.
- [x] Dry-run de fútbol sin escrituras y con falla rápida.
- [x] Marcador cero y timestamps UTC tratados explícitamente en cliente fútbol.
- [x] Pruebas dirigidas de 403, dry-run y completitud de estadísticas.
- [ ] Fuente fútbol utilizable/permitida y validada con eventos recientes.
- [ ] Calendario y finalizados recientes de fútbol ingresados con procedencia.
- [ ] Cotejo independiente de resultados NBA/fútbol y cobertura por competición/mercado.
- [ ] Última ingesta exitosa de fútbol y último dato real recientes: N/D mientras 403 persista.

**Aceptación:** NBA **operativo para ingesta**, no para certificar outcomes; fútbol **bloqueado por proveedor**. Siguiente acción: evaluar acceso/contrato legítimo de fuente alternativa y mapeo de IDs/equipos/temporadas en una restauración aislada antes de escribir en Neon; no ejecutar el sincronizador real si el dry-run reporta `SOURCE_UNAVAILABLE`.

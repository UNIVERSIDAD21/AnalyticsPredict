# Scraper WNBA robusto — 2026-10-24

Orden: revisar el scraper actual y crear uno mejorado para WNBA. Alcance implementado:
extracción independiente ESPN → archivos verificables. Sin alta de competición en
BD, incorporación al frontend, modelo, apuestas, cron ni backfill histórico.

## Revisión del flujo anterior

Inspección del checkout `88e2b1f`, limpio antes de editar:

| Componente existente | Observación | Decisión para WNBA |
|---|---|---|
| `motor/nba_scraper_espn.py` | Endpoint NBA fijo, filas centradas en equipo; conversor admite fragmentos numéricos y completa faltantes con cero; localía tiene fallback por orden | Cliente WNBA aislado, una fila por ID de evento, localía/IDs estrictos, NULL y cuarentena |
| `scripts/nba_scraper_multi_teams.py` | Combina descarga/CSV, entrenamiento y persistencia; convenciones NBA | No importar ese ejecutor ni sus efectos: la CLI WNBA no carga `.env`, BD ni modelos |
| `scripts/actualizar_partidos_nba.py` | Controles más nuevos de final/OT y stop 403; escribe NBA | Reutilizar principios, no escritor, catálogo ni mapeos NBA |
| Esquema de baloncesto | Admite competición y Q1–Q4/OT | Exportar contrato independiente preparado para un futuro mapeo explícito; no simular integración actual |

Los archivos anteriores quedan intactos. WNBA tiene identificadores, temporadas
anuales y clasificación propios. El caso real de Commissioner’s Cup final mostró
`season.type=2`, pero `competition.type={id:39, abbreviation:CC}`: se exporta COPA.
No se mezcla con REG. Formato Q1–Q4 desde 2006; temporadas anteriores fuera de alcance.

## Arquitectura

- `scrapers/wnba/contrato.py`: normalización pura, identidad, estados, periodos,
  prórrogas, fases y estadísticas comprobadas. Ausencia ≠ cero.
- `scrapers/wnba/cliente.py`: HTTP serial y acotado, reintentos selectivos,
  limitación de tasa, presupuesto y no evasión.
- `scrapers/wnba/archivo.py`: raws inmutables, hashes, caché/observaciones,
  atomicidad, permisos y bloqueo de escritor.
- `scrapers/wnba/pipeline.py`: ventanas locales/UTC/Eastern, deduplicación,
  apartar conflictos, checkpoint, cobertura y exports.
- `scripts/scraper_wnba.py`: plan predeterminado, `--fetch` explícito y replay
  `--offline`; `--estadisticas` opcional. No escritura de BD en ningún modo.

[Manual completo y comandos](../../backend/scrapers/wnba/README.md).

## Validación

- Pruebas sintéticas de contratos, OT/múltiple OT, cero real, NULL, fases,
  Commissioner’s Cup, fechas/zonas, summary incompatible y estadísticas.
- Pruebas HTTP sin red: 401/403/redirect, 429/Retry-After, 5xx/timeout, presupuesto,
  ritmo mínimo, respuesta desmesurada, JSON inválido y errores no tratados como vacío.
- Persistencia: manipulación de caché, refresh conservando versiones, reanudación
  después de agotamiento de presupuesto, offline sin solicitudes, interrupción,
  checksum, duplicados/conflictos, lock, CLI real y CSV sin fórmulas activas.
- 100 pruebas específicas WNBA y 36 regresiones de scrapers existentes: 136 passed.
  La ruta WNBA queda añadida al job de unitarias sin BD de CI y al descubrimiento
  global normal de pytest. No se modifica la política de CI.
- Sondeo técnico acotado: ocho finales únicos en las ventanas de muestra de 2019
  y 2025 con periodos/FT coherentes; tres summaries iniciales. No es cobertura
  completa de esas temporadas ni corroboración por fuente independiente.
- Piloto de CLI con día colombiano 03/07/2025: cinco partidos y 32 campos de
  estadísticas por partido presentes (16 por lado), cero cuarentena. Dos ventanas
  Eastern por límites de zona, cinco GET nuevos y dos respuestas en caché.
- Respuestas y archivos fuera del checkout, en la entrega
  `SCRAPER_WNBA_ROBUSTO_2026-10-24`. No se versionan datos de ESPN ni evidencias privadas.

## Límites explícitos

No se acredita licencia/retención masiva por obtener HTTP 200 ni se promete SLA de
ESPN. No evasión de bloqueos. Una ventana con feed vacío no prueba ausencia de
partidos reales. La cobertura anterior a las muestras no está medida. Datos
individuales de jugadoras, lesiones, cuotas y play-by-play permanecen solo si
existen en los raws, sin contrato normalizado propio. El resultado no prueba
capacidad predictiva, calibración ni rentabilidad. WNBA aún no está integrada al
catálogo productivo; NBA/Euroliga y sus artefactos se mantienen separados e intactos.

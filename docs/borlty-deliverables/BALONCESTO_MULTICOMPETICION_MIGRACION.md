# Migracion Baloncesto Multi-competicion (NBA + Euroliga)

## Objetivo
Migrar baloncesto desde modo monolitico NBA a modelo multi-competicion, manteniendo compatibilidad con NBA/ESPN y habilitando Euroliga/Sofascore.

Entregables implementados en este repo:
- `backend/scripts/sql/baloncesto_multicompeticion/01_migracion_baloncesto_multicompeticion_up.sql`
- `backend/scripts/sql/baloncesto_multicompeticion/02_migracion_baloncesto_multicompeticion_validate.sql`
- `backend/scripts/sql/baloncesto_multicompeticion/03_migracion_baloncesto_multicompeticion_rollback.sql`
- `backend/scripts/scraper_euroliga.py`

## Mapping de fuentes e IDs

| Competicion | Fuente | ID Sofascore | En BD |
|---|---|---:|---|
| NBA | ESPN | 132 | `competiciones_baloncesto.sofascore_id = NULL` |
| Euroliga | Sofascore | 138 | `competiciones_baloncesto.sofascore_id = 138` |

Regla critica:
- El scraper nuevo (`scraper_euroliga.py`) solo consulta torneo `138`.
- No consulta NBA en Sofascore.

## Flujo de migracion recomendado

1. Backup de BD antes de cambios.
2. Ejecutar migracion `up`.
3. Ejecutar validacion post-migracion.
4. Ejecutar scraper de Euroliga.
5. Re-ejecutar validacion.

### Comandos (psql)

```bash
psql "$DATABASE_URL" -f backend/scripts/sql/baloncesto_multicompeticion/01_migracion_baloncesto_multicompeticion_up.sql
psql "$DATABASE_URL" -f backend/scripts/sql/baloncesto_multicompeticion/02_migracion_baloncesto_multicompeticion_validate.sql
```

### Comandos (PowerShell + python, sin psql)

```powershell
python - <<'PY'
import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

load_dotenv('backend/.env')
url = os.getenv('DATABASE_URL')
if 'sslmode=' not in url:
    url += ('&' if '?' in url else '?') + 'sslmode=require'

sql = Path('backend/scripts/sql/baloncesto_multicompeticion/01_migracion_baloncesto_multicompeticion_up.sql').read_text(encoding='utf-8')
with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
PY
```

## Que hace la migracion `up`

- Crea/ajusta `competiciones_baloncesto`, `equipos_baloncesto`, `temporadas_baloncesto`, `partidos_baloncesto`, `ingestion_state_baloncesto`.
- Inserta/actualiza competiciones:
  - `nba` con `sofascore_id = NULL`
  - `euroleague` con `sofascore_id = 138`
- Migra catalogo NBA a `equipos_baloncesto` (30 equipos esperados).
- Asegura `competicion_id` en temporadas/partidos/predicciones/apuestas.
- Hace `conferencia` y `division` opcionales en tabla legacy `equipos` para soportar equipos no NBA.
- Conserva campos NBA/ESPN (`espn_game_id`, `source`, `source_game_id`) en partidos.

## Scraper Euroliga

Script:
- `backend/scripts/scraper_euroliga.py`

Caracteristicas:
- Cliente anti-bot (`curl_cffi`) con rate limiting.
- Sincroniza `events/last` y opcionalmente `events/next`.
- Upsert de equipos Euroliga y partidos con `sofascore_match_id`.
- Actualiza `ingestion_state_baloncesto` (`clave = euroliga_sync`).
- Valida que `competiciones_baloncesto.codigo='euroleague'` tenga `sofascore_id=138`.

Ejecucion:

```bash
python backend/scripts/scraper_euroliga.py --dias 7
python backend/scripts/scraper_euroliga.py --dias 7 --dias-futuros 7 --incluir-futuros
```

## Consultas SQL de uso comun

### 1) Proximos partidos Euroliga

```sql
SELECT
  p.id,
  p.fecha_partido,
  el.nombre_corto AS local,
  ev.nombre_corto AS visitante,
  p.source,
  p.sofascore_match_id
FROM partidos_baloncesto p
JOIN competiciones_baloncesto c ON c.id = p.competicion_id
JOIN equipos el ON el.id = p.equipo_local_id
JOIN equipos ev ON ev.id = p.equipo_visitante_id
WHERE c.codigo = 'euroleague'
  AND p.fecha_partido >= CURRENT_DATE
ORDER BY p.fecha_partido
LIMIT 50;
```

### 2) Partidos NBA por ESPN ID

```sql
SELECT id, fecha_partido, source, source_game_id, espn_game_id
FROM partidos_baloncesto
WHERE source = 'ESPN'
  AND source_game_id = '401585123';
```

### 3) Verificacion de regla NBA sin Sofascore

```sql
SELECT COUNT(*) AS nba_con_sofascore_match_id
FROM partidos_baloncesto p
JOIN competiciones_baloncesto c ON c.id = p.competicion_id
WHERE c.codigo = 'nba'
  AND p.sofascore_match_id IS NOT NULL;
```

### 4) Equipos NBA en catalogo multi

```sql
SELECT COUNT(*) AS equipos_nba
FROM equipos_baloncesto eb
JOIN competiciones_baloncesto c ON c.id = eb.competicion_principal_id
WHERE c.codigo = 'nba';
```

## Troubleshooting

### Error: `euroleague debe tener sofascore_id=138`
Causa: competencia mal configurada.
Solucion: ejecutar migracion `up` o corregir manualmente:

```sql
UPDATE competiciones_baloncesto
SET sofascore_id = 138
WHERE codigo = 'euroleague';
```

### Error de `403 Forbidden` en Sofascore
Causa: bloqueo anti-bot.
Solucion:
- Instalar `curl_cffi`.
- Subir `--intervalo` (ej: `--intervalo 3.0`).
- Reintentar mas tarde.

### Error de abreviatura duplicada en `equipos`
Causa: restriccion unica legacy.
Solucion:
- El scraper ya intenta abreviaturas alternativas.
- Si persiste, ajustar manualmente abreviatura en `equipos` y reintentar.

### El scraper NBA/ESPN no debe tocarse
Esta migracion no modifica `backend/scripts/scraper_partidos_futuros.py` ni flujo ESPN.

## Rollback

Rollback a modo NBA monolitico:

```bash
psql "$DATABASE_URL" -f backend/scripts/sql/baloncesto_multicompeticion/03_migracion_baloncesto_multicompeticion_rollback.sql
```

Efecto del rollback:
- Limpia datos no-NBA en tablas de baloncesto.
- Deja NBA como competicion activa.
- Restaura restricciones legacy en `equipos`.
- Restaura unique global de `temporadas_baloncesto.nombre`.

## Validaciones clave esperadas tras migrar

- `competiciones_baloncesto` contiene `nba` y `euroleague`.
- `euroleague.sofascore_id = 138`.
- `nba.sofascore_id IS NULL`.
- `equipos_baloncesto` contiene 30 equipos NBA migrados.
- `equipos_baloncesto.sofascore_id IS NULL` para equipos NBA.
- `partidos_baloncesto`, `temporadas_baloncesto`, `predicciones_registradas` tienen `competicion_id` no nulo.
- `scraper_euroliga.py` solo usa torneo Sofascore `138`.

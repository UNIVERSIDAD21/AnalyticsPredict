# Validación por lote de análisis de partidos NBA

Generado: 2026-05-06T01:08:13

## Resumen
- Total partidos validados: 5
- OK: 0
- WARNING: 5
- ERROR: 0

## Principales advertencias
- diferencia fuerte reciente/completa en FULL_GAME_TOTAL: 4
- línea no real en AWAY_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD: 4
- línea no real en HOME_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD: 4
- diferencia fuerte reciente/completa en AWAY_TEAM_TOTAL: 3
- diferencia fuerte reciente/completa en HOME_TEAM_TOTAL: 3
- línea no real en Q1_TOTAL: TECHNICAL_ESTIMATE: 3
- {"code": "EXCLUDED_APPEARANCES", "details": {"excluded": 17}, "message": "se excluyeron 17 apariciones antes de calcular muestras", "scope": "data_quality", "severity": "WARNING"}: 3
- {"code": "EXCLUDED_APPEARANCES", "details": {"excluded": 18}, "message": "se excluyeron 18 apariciones antes de calcular muestras", "scope": "data_quality", "severity": "WARNING"}: 1
- {"code": "EXCLUDED_APPEARANCES", "details": {"excluded": 20}, "message": "se excluyeron 20 apariciones antes de calcular muestras", "scope": "data_quality", "severity": "WARNING"}: 1

## Resultado por partido

| Estado | Partido | Fecha | Candidatas | Usadas | Excluidas | JSON | Markdown |
|---|---|---|---:|---:|---:|---|---|
| WARNING | San Antonio Spurs vs Minnesota Timberwolves | 2026-05-05 | 360 | 120 | 20 | `reports/match_analysis_input/san_antonio_spurs_vs_minnesota_timberwolves_2026-05-05.json` | `reports/match_analysis_reports/san_antonio_spurs_vs_minnesota_timberwolves_2026-05-05.md` |
| WARNING | NYK vs PHI | 2026-05-05 | 360 | 120 | 18 | `reports/match_analysis_input/new_york_knicks_vs_philadelphia_76ers_2026-05-05.json` | `reports/match_analysis_reports/new_york_knicks_vs_philadelphia_76ers_2026-05-05.md` |
| WARNING | Cleveland Cavaliers vs Toronto Raptors | 2026-05-03 | 360 | 120 | 17 | `reports/match_analysis_input/cleveland_cavaliers_vs_toronto_raptors_2026-05-03.json` | `reports/match_analysis_reports/cleveland_cavaliers_vs_toronto_raptors_2026-05-03.md` |
| WARNING | HOU vs Los Angeles Lakers | 2026-05-02 | 360 | 120 | 17 | `reports/match_analysis_input/houston_rockets_vs_los_angeles_lakers_2026-05-02.json` | `reports/match_analysis_reports/houston_rockets_vs_los_angeles_lakers_2026-05-02.md` |
| WARNING | ORL vs DET | 2026-05-01 | 360 | 120 | 17 | `reports/match_analysis_input/orlando_magic_vs_detroit_pistons_2026-05-01.json` | `reports/match_analysis_reports/orlando_magic_vs_detroit_pistons_2026-05-01.md` |

## Detalle de warnings por partido

### sas_min_2026_05_05 — WARNING
- {"code": "EXCLUDED_APPEARANCES", "severity": "WARNING", "message": "se excluyeron 20 apariciones antes de calcular muestras", "scope": "data_quality", "details": {"excluded": 20}}
- línea no real en Q1_TOTAL: TECHNICAL_ESTIMATE
- diferencia fuerte reciente/completa en FULL_GAME_TOTAL
- línea no real en HOME_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en HOME_TEAM_TOTAL
- línea no real en AWAY_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- Source types: {"TECHNICAL_ESTIMATE": 1, "REAL_MARKET": 1, "DERIVED_FROM_TOTAL_SPREAD": 2}

### nyk_phi_2026_05_05 — WARNING
- {"code": "EXCLUDED_APPEARANCES", "severity": "WARNING", "message": "se excluyeron 18 apariciones antes de calcular muestras", "scope": "data_quality", "details": {"excluded": 18}}
- línea no real en HOME_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- línea no real en AWAY_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en AWAY_TEAM_TOTAL
- Source types: {"REAL_MARKET": 1, "DERIVED_FROM_TOTAL_SPREAD": 2}

### cle_tor_2026_05_03 — WARNING
- {"code": "EXCLUDED_APPEARANCES", "severity": "WARNING", "message": "se excluyeron 17 apariciones antes de calcular muestras", "scope": "data_quality", "details": {"excluded": 17}}
- línea no real en Q1_TOTAL: TECHNICAL_ESTIMATE
- diferencia fuerte reciente/completa en FULL_GAME_TOTAL
- Source types: {"TECHNICAL_ESTIMATE": 1, "REAL_MARKET": 1}

### hou_lal_2026_05_02 — WARNING
- {"code": "EXCLUDED_APPEARANCES", "severity": "WARNING", "message": "se excluyeron 17 apariciones antes de calcular muestras", "scope": "data_quality", "details": {"excluded": 17}}
- diferencia fuerte reciente/completa en FULL_GAME_TOTAL
- línea no real en HOME_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en HOME_TEAM_TOTAL
- línea no real en AWAY_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en AWAY_TEAM_TOTAL
- Source types: {"REAL_MARKET": 1, "DERIVED_FROM_TOTAL_SPREAD": 2}

### orl_det_2026_05_01 — WARNING
- {"code": "EXCLUDED_APPEARANCES", "severity": "WARNING", "message": "se excluyeron 17 apariciones antes de calcular muestras", "scope": "data_quality", "details": {"excluded": 17}}
- línea no real en Q1_TOTAL: TECHNICAL_ESTIMATE
- diferencia fuerte reciente/completa en FULL_GAME_TOTAL
- línea no real en HOME_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en HOME_TEAM_TOTAL
- línea no real en AWAY_TEAM_TOTAL: DERIVED_FROM_TOTAL_SPREAD
- diferencia fuerte reciente/completa en AWAY_TEAM_TOTAL
- Source types: {"TECHNICAL_ESTIMATE": 1, "REAL_MARKET": 1, "DERIVED_FROM_TOTAL_SPREAD": 2}

## Resúmenes para análisis externo

### sas_min_2026_05_05
## Resumen para análisis externo
Partido: San Antonio Spurs local vs Minnesota Timberwolves visitante, fecha 2026-05-05. BD disponible hasta 2026-05-05.
Muestras recientes: SAS general 30 y local 30; MIN general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 57.93, Q2 56.65, Q3 59.05, Q4 58.88, total partido 233.35.
Líneas evaluadas técnicamente: Q1_TOTAL línea 54.5 (TECHNICAL_ESTIMATE): señal estadística débil, diff 2.62, vol 5.48; FULL_GAME_TOTAL línea 218.5 (REAL_MARKET): señal inconsistente, diff 7.53, vol 14.39; HOME_TEAM_TOTAL línea 114.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística débil, diff 1.33, vol 9.66; AWAY_TEAM_TOTAL línea 104.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.20, vol 8.01.
Usar como evidencia estadística, no como recomendación de apuesta.

### nyk_phi_2026_05_05
## Resumen para análisis externo
Partido: New York Knicks local vs Philadelphia 76ers visitante, fecha 2026-05-05. BD disponible hasta 2026-05-05.
Muestras recientes: NYK general 30 y local 30; PHI general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 58.10, Q2 58.77, Q3 57.55, Q4 53.05, total partido 229.20.
Líneas evaluadas técnicamente: FULL_GAME_TOTAL línea 212.5 (REAL_MARKET): señal inconsistente, diff 12.78, vol 16.42; HOME_TEAM_TOTAL línea 110.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.83, vol 10.71; AWAY_TEAM_TOTAL línea 102.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.95, vol 10.96.
Usar como evidencia estadística, no como recomendación de apuesta.

### cle_tor_2026_05_03
## Resumen para análisis externo
Partido: Cleveland Cavaliers local vs Toronto Raptors visitante, fecha 2026-05-03. BD disponible hasta 2026-05-05.
Muestras recientes: CLE general 30 y local 30; TOR general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 56.05, Q2 58.20, Q3 60.13, Q4 55.83, total partido 230.35.
Líneas evaluadas técnicamente: Q1_TOTAL línea 52.5 (TECHNICAL_ESTIMATE): señal estadística moderada, diff 4.28, vol 7.62; FULL_GAME_TOTAL línea 209.5 (REAL_MARKET): señal inconsistente, diff 18.40, vol 16.93.
Usar como evidencia estadística, no como recomendación de apuesta.

### hou_lal_2026_05_02
## Resumen para análisis externo
Partido: Houston Rockets local vs Los Angeles Lakers visitante, fecha 2026-05-02. BD disponible hasta 2026-05-05.
Muestras recientes: HOU general 30 y local 30; LAL general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 57.48, Q2 55.33, Q3 54.83, Q4 52.40, total partido 221.08.
Líneas evaluadas técnicamente: FULL_GAME_TOTAL línea 203.5 (REAL_MARKET): señal inconsistente, diff 18.12, vol 16.16; HOME_TEAM_TOTAL línea 104.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.50, vol 10.02; AWAY_TEAM_TOTAL línea 99.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 12.62, vol 9.61.
Usar como evidencia estadística, no como recomendación de apuesta.

### orl_det_2026_05_01
## Resumen para análisis externo
Partido: Orlando Magic local vs Detroit Pistons visitante, fecha 2026-05-01. BD disponible hasta 2026-05-05.
Muestras recientes: ORL general 30 y local 30; DET general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 56.87, Q2 57.03, Q3 57.32, Q4 52.42, total partido 224.52.
Líneas evaluadas técnicamente: Q1_TOTAL línea 52.5 (TECHNICAL_ESTIMATE): señal estadística moderada, diff 3.77, vol 6.27; FULL_GAME_TOTAL línea 210.5 (REAL_MARKET): señal inconsistente, diff 11.50, vol 18.53; HOME_TEAM_TOTAL línea 103.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.42, vol 10.76; AWAY_TEAM_TOTAL línea 107.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.08, vol 11.59.
Usar como evidencia estadística, no como recomendación de apuesta.

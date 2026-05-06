# Análisis estadístico previo NBA: New York Knicks vs Philadelphia 76ers

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: New York Knicks (NYK) local vs Philadelphia 76ers (PHI) visitante
- Fecha del partido: 2026-05-05
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T01:08:00

## Mercados soportados por el script
- Q1_TOTAL
- FULL_GAME_TOTAL
- HOME_TEAM_TOTAL
- AWAY_TEAM_TOTAL

## Reglas de clasificación de señales
- **señal estadística fuerte:** brecha promedio-línea >= 6, al menos 3 ventanas con cumplimiento direccional >=60% o <=40%, y ventanas consistentes
- **señal estadística moderada:** brecha promedio-línea >= 3 y al menos 2 ventanas con cumplimiento direccional
- **señal estadística débil:** evaluable, pero sin suficiente brecha/consenso
- **señal inconsistente:** volatilidad alta o advertencias de inconsistencia reciente vs completa
- **no evaluable por datos insuficientes:** línea inválida, mercado no soportado o muestra insuficiente

## Muestras usadas
- Local general/local: 30 / 30
- Visitante general/visitante: 30 / 30

## Calidad de datos usada en este análisis
- Apariciones candidatas: 360
- Apariciones usadas: 120
- Apariciones excluidas: 18 (5.00%)
- Razones de exclusión: Marcador 0-0 no válido para muestra histórica: 18

## Forma reciente - New York Knicks local

### General
- Últimos 5: PF total 125.00 / PA total 98.20; Q1 PF 31.20, Q2 34.60, Q3 30.60, Q4 28.60; OT 0
- Últimos 10: PF total 116.80 / PA total 104.10; Q1 PF 31.00, Q2 31.80, Q3 27.70, Q4 26.30; OT 0
- Últimos 20: PF total 116.30 / PA total 106.90; Q1 PF 29.50, Q2 30.20, Q3 28.50, Q4 28.10; OT 0
- Últimos 30: PF total 115.87 / PA total 105.17; Q1 PF 29.07, Q2 30.07, Q3 28.37, Q4 28.37; OT 0

### Split local
- Últimos 5: PF total 120.60 / PA total 104.00; Q1 PF 34.40, Q2 30.00, Q3 28.80, Q4 27.40; OT 0
- Últimos 10: PF total 120.80 / PA total 104.20; Q1 PF 30.80, Q2 29.00, Q3 32.10, Q4 28.90; OT 0
- Últimos 20: PF total 117.65 / PA total 105.40; Q1 PF 30.45, Q2 27.00, Q3 29.50, Q4 28.90; OT 2
- Últimos 30: PF total 118.47 / PA total 108.47; Q1 PF 30.30, Q2 27.17, Q3 30.47, Q4 29.33; OT 2

## Forma reciente - Philadelphia 76ers visitante

### General
- Últimos 5: PF total 104.40 / PA total 111.00; Q1 PF 23.20, Q2 27.20, Q3 31.00, Q4 23.00; OT 0
- Últimos 10: PF total 108.60 / PA total 111.10; Q1 PF 24.60, Q2 29.30, Q3 29.60, Q4 25.10; OT 0
- Últimos 20: PF total 112.80 / PA total 114.65; Q1 PF 27.95, Q2 28.00, Q3 30.45, Q4 26.40; OT 0
- Últimos 30: PF total 113.73 / PA total 115.80; Q1 PF 28.70, Q2 29.33, Q3 28.80, Q4 26.90; OT 0

### Split visitante
- Últimos 5: PF total 104.40 / PA total 110.80; Q1 PF 24.20, Q2 28.60, Q3 28.40, Q4 23.20; OT 0
- Últimos 10: PF total 116.70 / PA total 115.20; Q1 PF 29.80, Q2 29.90, Q3 31.00, Q4 26.00; OT 0
- Últimos 20: PF total 114.75 / PA total 117.35; Q1 PF 29.10, Q2 30.65, Q3 28.30, Q4 26.70; OT 0
- Últimos 30: PF total 115.63 / PA total 115.83; Q1 PF 29.53, Q2 30.97, Q3 27.87, Q4 26.63; OT 2

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 55.10 | 60.20 | 55.60 | 49.00 | 219.90 |
| 10 | 58.80 | 58.85 | 59.10 | 51.70 | 228.45 |
| 20 | 57.90 | 58.85 | 56.75 | 52.38 | 227.57 |
| 30 | 58.10 | 58.77 | 57.55 | 53.05 | 229.20 |

## Evaluación técnica de líneas

### FULL_GAME_TOTAL
- Línea: 212.5
- Tipo de fuente: REAL_MARKET (REAL)
- Fuente: ESPN pickcenter / DraftKings close
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871159
- Notas: overUnder 212.5, odds -110/-110
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 225.28
- Mediana combinada: 223.00
- Diferencia contra línea: 12.78
- Volatilidad/desv. estándar: 16.42
- Cumplimiento over 5/10/20/30: {'5': 60.0, '10': 50.0, '20': 65.0, '30': 66.67}
- Cumplimiento under 5/10/20/30: {'5': 40.0, '10': 50.0, '20': 35.0, '30': 33.33}
- Cumplimiento split local/visitante over: 83.33%
- Cumplimiento split local/visitante under: 16.67%
- Advertencias: [HIGH_VOLATILITY] desviación estándar alta: mercado volátil ({'stddev': 16.42})

### HOME_TEAM_TOTAL
- Línea: 110.0
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 212.5 and spread NY -7.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871159
- Notas: Team total implícito del local.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 115.83
- Mediana combinada: 113.25
- Diferencia contra línea: 5.83
- Volatilidad/desv. estándar: 10.71
- Cumplimiento over 5/10/20/30: {'5': 60.0, '10': 50.0, '20': 65.0, '30': 63.33}
- Cumplimiento under 5/10/20/30: {'5': 40.0, '10': 50.0, '20': 35.0, '30': 36.67}
- Cumplimiento split local/visitante over: 73.33%
- Cumplimiento split local/visitante under: 26.67%
- Advertencias: [NON_REAL_MARKET_LINE] La línea HOME_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'})

### AWAY_TEAM_TOTAL
- Línea: 102.5
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 212.5 and spread NY -7.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871159
- Notas: Team total implícito del visitante.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 109.45
- Mediana combinada: 106.00
- Diferencia contra línea: 6.95
- Volatilidad/desv. estándar: 10.96
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 60.0, '20': 70.0, '30': 66.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 30.0, '20': 25.0, '30': 30.0}
- Cumplimiento split local/visitante over: 86.67%
- Cumplimiento split local/visitante under: 13.33%
- Advertencias: [NON_REAL_MARKET_LINE] La línea AWAY_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 101.3, 'avg_30': 109.45})

## Advertencias generales
- [EXCLUDED_APPEARANCES] se excluyeron 18 apariciones antes de calcular muestras ({'excluded': 18})

## Resumen para análisis externo
Partido: New York Knicks local vs Philadelphia 76ers visitante, fecha 2026-05-05. BD disponible hasta 2026-05-05.
Muestras recientes: NYK general 30 y local 30; PHI general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 58.10, Q2 58.77, Q3 57.55, Q4 53.05, total partido 229.20.
Líneas evaluadas técnicamente: FULL_GAME_TOTAL línea 212.5 (REAL_MARKET): señal inconsistente, diff 12.78, vol 16.42; HOME_TEAM_TOTAL línea 110.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.83, vol 10.71; AWAY_TEAM_TOTAL línea 102.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.95, vol 10.96.
Usar como evidencia estadística, no como recomendación de apuesta.

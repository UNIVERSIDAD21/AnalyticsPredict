# Análisis estadístico previo NBA: Houston Rockets vs Los Angeles Lakers

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: Houston Rockets (HOU) local vs Los Angeles Lakers (LAL) visitante
- Fecha del partido: 2026-05-02
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T01:08:08

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
- Apariciones excluidas: 17 (4.72%)
- Razones de exclusión: Marcador 0-0 no válido para muestra histórica: 17

## Forma reciente - Houston Rockets local

### General
- Últimos 5: PF total 98.80 / PA total 100.00; Q1 PF 24.60, Q2 23.60, Q3 24.60, Q4 24.60; OT 1
- Últimos 10: PF total 107.50 / PA total 102.50; Q1 PF 27.70, Q2 25.30, Q3 26.50, Q4 27.30; OT 1
- Últimos 20: PF total 109.40 / PA total 109.30; Q1 PF 27.40, Q2 26.50, Q3 28.05, Q4 26.45; OT 2
- Últimos 30: PF total 110.47 / PA total 108.57; Q1 PF 27.20, Q2 27.63, Q3 28.87, Q4 25.70; OT 3

### Split local
- Últimos 5: PF total 106.20 / PA total 102.60; Q1 PF 28.00, Q2 23.20, Q3 28.20, Q4 25.40; OT 1
- Últimos 10: PF total 108.60 / PA total 105.90; Q1 PF 28.90, Q2 26.20, Q3 28.60, Q4 24.20; OT 1
- Últimos 20: PF total 108.90 / PA total 105.20; Q1 PF 28.30, Q2 27.45, Q3 27.70, Q4 24.50; OT 2
- Últimos 30: PF total 109.27 / PA total 105.83; Q1 PF 28.30, Q2 28.03, Q3 27.63, Q4 24.67; OT 2

## Forma reciente - Los Angeles Lakers visitante

### General
- Últimos 5: PF total 100.00 / PA total 98.80; Q1 PF 28.80, Q2 23.20, Q3 19.60, Q4 26.20; OT 1
- Últimos 10: PF total 106.60 / PA total 104.40; Q1 PF 29.00, Q2 26.20, Q3 23.40, Q4 26.90; OT 1
- Últimos 20: PF total 113.75 / PA total 109.15; Q1 PF 29.95, Q2 27.30, Q3 27.55, Q4 27.95; OT 2
- Últimos 30: PF total 114.67 / PA total 109.53; Q1 PF 30.70, Q2 27.20, Q3 28.03, Q4 28.07; OT 2

### Split visitante
- Últimos 5: PF total 107.80 / PA total 114.00; Q1 PF 29.80, Q2 27.20, Q3 20.60, Q4 28.00; OT 1
- Últimos 10: PF total 111.20 / PA total 112.10; Q1 PF 30.60, Q2 27.00, Q3 25.00, Q4 27.50; OT 1
- Últimos 20: PF total 113.95 / PA total 112.80; Q1 PF 31.80, Q2 27.30, Q3 26.55, Q4 27.75; OT 1
- Últimos 30: PF total 113.03 / PA total 114.03; Q1 PF 30.17, Q2 27.57, Q3 26.97, Q4 27.97; OT 1

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 56.10 | 51.30 | 49.40 | 54.90 | 215.30 |
| 10 | 58.00 | 54.55 | 52.35 | 52.20 | 218.90 |
| 20 | 57.42 | 54.12 | 55.15 | 52.17 | 220.43 |
| 30 | 57.48 | 55.33 | 54.83 | 52.40 | 221.08 |

## Evaluación técnica de líneas

### FULL_GAME_TOTAL
- Línea: 203.5
- Tipo de fuente: REAL_MARKET (REAL)
- Fuente: ESPN pickcenter / DraftKings close
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869409
- Notas: overUnder 203.5, odds -112/-108 convertidas aprox.
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 221.62
- Mediana combinada: 225.25
- Diferencia contra línea: 18.12
- Volatilidad/desv. estándar: 16.16
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 70.0, '20': 80.0, '30': 86.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 30.0, '20': 20.0, '30': 13.33}
- Cumplimiento split local/visitante over: 93.33%
- Cumplimiento split local/visitante under: 6.67%
- Advertencias: [HIGH_VOLATILITY] desviación estándar alta: mercado volátil ({'stddev': 16.158}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 198.8, 'avg_30': 221.617}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 5 apariciones recientes ({'overtime_count': 5})

### HOME_TEAM_TOTAL
- Línea: 104.5
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 203.5 and spread HOU -5.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869409
- Notas: Team total implícito del local.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 110.00
- Mediana combinada: 111.75
- Diferencia contra línea: 5.50
- Volatilidad/desv. estándar: 10.02
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 60.0, '20': 75.0, '30': 76.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 40.0, '20': 25.0, '30': 20.0}
- Cumplimiento split local/visitante over: 80.00%
- Cumplimiento split local/visitante under: 20.00%
- Advertencias: [NON_REAL_MARKET_LINE] La línea HOME_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 98.8, 'avg_30': 110.0}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 5 apariciones recientes ({'overtime_count': 5})

### AWAY_TEAM_TOTAL
- Línea: 99.0
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 203.5 and spread HOU -5.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869409
- Notas: Team total implícito del visitante.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 111.62
- Mediana combinada: 112.75
- Diferencia contra línea: 12.62
- Volatilidad/desv. estándar: 9.61
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 70.0, '20': 85.0, '30': 86.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 30.0, '20': 15.0, '30': 13.33}
- Cumplimiento split local/visitante over: 90.00%
- Cumplimiento split local/visitante under: 10.00%
- Advertencias: [NON_REAL_MARKET_LINE] La línea AWAY_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 100.0, 'avg_30': 111.617}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 5 apariciones recientes ({'overtime_count': 5})

## Advertencias generales
- [EXCLUDED_APPEARANCES] se excluyeron 17 apariciones antes de calcular muestras ({'excluded': 17})

## Resumen para análisis externo
Partido: Houston Rockets local vs Los Angeles Lakers visitante, fecha 2026-05-02. BD disponible hasta 2026-05-05.
Muestras recientes: HOU general 30 y local 30; LAL general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 57.48, Q2 55.33, Q3 54.83, Q4 52.40, total partido 221.08.
Líneas evaluadas técnicamente: FULL_GAME_TOTAL línea 203.5 (REAL_MARKET): señal inconsistente, diff 18.12, vol 16.16; HOME_TEAM_TOTAL línea 104.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.50, vol 10.02; AWAY_TEAM_TOTAL línea 99.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 12.62, vol 9.61.
Usar como evidencia estadística, no como recomendación de apuesta.

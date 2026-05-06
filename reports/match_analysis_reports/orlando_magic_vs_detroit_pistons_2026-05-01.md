# Análisis estadístico previo NBA: Orlando Magic vs Detroit Pistons

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: Orlando Magic (ORL) local vs Detroit Pistons (DET) visitante
- Fecha del partido: 2026-05-01
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T01:08:12

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

## Forma reciente - Orlando Magic local

### General
- Últimos 5: PF total 97.80 / PA total 103.60; Q1 PF 25.00, Q2 31.80, Q3 18.40, Q4 22.60; OT 0
- Últimos 10: PF total 100.30 / PA total 104.60; Q1 PF 27.10, Q2 29.10, Q3 20.90, Q4 23.20; OT 0
- Últimos 20: PF total 106.95 / PA total 113.30; Q1 PF 28.35, Q2 29.70, Q3 24.05, Q4 24.85; OT 0
- Últimos 30: PF total 110.47 / PA total 112.07; Q1 PF 28.50, Q2 29.83, Q3 26.13, Q4 25.57; OT 1

### Split local
- Últimos 5: PF total 101.60 / PA total 101.20; Q1 PF 28.60, Q2 30.80, Q3 22.80, Q4 19.40; OT 0
- Últimos 10: PF total 108.20 / PA total 108.00; Q1 PF 28.60, Q2 32.50, Q3 24.80, Q4 22.30; OT 0
- Últimos 20: PF total 112.55 / PA total 110.25; Q1 PF 28.95, Q2 29.80, Q3 28.20, Q4 24.95; OT 1
- Últimos 30: PF total 113.57 / PA total 113.50; Q1 PF 28.10, Q2 29.00, Q3 28.77, Q4 27.27; OT 1

## Forma reciente - Detroit Pistons visitante

### General
- Últimos 5: PF total 103.60 / PA total 97.80; Q1 PF 27.40, Q2 26.60, Q3 22.40, Q4 27.20; OT 0
- Últimos 10: PF total 106.70 / PA total 102.20; Q1 PF 26.90, Q2 25.40, Q3 27.00, Q4 26.50; OT 1
- Últimos 20: PF total 113.70 / PA total 105.40; Q1 PF 28.90, Q2 28.00, Q3 28.15, Q4 27.80; OT 2
- Últimos 30: PF total 114.10 / PA total 107.37; Q1 PF 28.03, Q2 28.30, Q3 29.23, Q4 27.70; OT 3

### Split visitante
- Últimos 5: PF total 101.00 / PA total 97.40; Q1 PF 27.20, Q2 20.00, Q3 24.40, Q4 27.60; OT 1
- Últimos 10: PF total 110.80 / PA total 103.90; Q1 PF 28.90, Q2 25.50, Q3 26.80, Q4 28.70; OT 1
- Últimos 20: PF total 112.00 / PA total 106.50; Q1 PF 29.15, Q2 26.90, Q3 28.85, Q4 26.65; OT 1
- Últimos 30: PF total 113.43 / PA total 108.53; Q1 PF 29.33, Q2 28.43, Q3 28.93, Q4 26.30; OT 2

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 53.10 | 52.70 | 46.60 | 46.00 | 200.60 |
| 10 | 55.75 | 56.35 | 53.40 | 48.85 | 215.45 |
| 20 | 56.08 | 56.23 | 55.80 | 51.48 | 220.65 |
| 30 | 56.87 | 57.03 | 57.32 | 52.42 | 224.52 |

## Evaluación técnica de líneas

### Q1_TOTAL
- Línea: 52.5
- Tipo de fuente: TECHNICAL_ESTIMATE (TÉCNICA)
- Fuente: manual/technical
- URL fuente: N/D
- Notas: Línea técnica para validar Q1; no mercado real observado.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico.
- Promedio combinado: 56.27
- Mediana combinada: 55.75
- Diferencia contra línea: 3.77
- Volatilidad/desv. estándar: 6.27
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 50.0, '20': 70.0, '30': 73.33}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 50.0, '20': 25.0, '30': 23.33}
- Cumplimiento split local/visitante over: 73.33%
- Cumplimiento split local/visitante under: 26.67%
- Advertencias: [NON_REAL_MARKET_LINE] La línea Q1_TOTAL no proviene de mercado real ({'source_type': 'TECHNICAL_ESTIMATE'}); [TECHNICAL_ESTIMATE_ONLY] Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico. ({'source_type': 'TECHNICAL_ESTIMATE'}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 4 apariciones recientes ({'overtime_count': 4})

### FULL_GAME_TOTAL
- Línea: 210.5
- Tipo de fuente: REAL_MARKET (REAL)
- Fuente: ESPN pickcenter / DraftKings close
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869417
- Notas: overUnder 210.5, odds -115/-105 convertidas aprox.
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 222.00
- Mediana combinada: 224.25
- Diferencia contra línea: 11.50
- Volatilidad/desv. estándar: 18.53
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 60.0, '20': 75.0, '30': 83.33}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 40.0, '20': 20.0, '30': 13.33}
- Cumplimiento split local/visitante over: 93.33%
- Cumplimiento split local/visitante under: 6.67%
- Advertencias: [HIGH_VOLATILITY] desviación estándar alta: mercado volátil ({'stddev': 18.534}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 201.4, 'avg_30': 222.0}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 4 apariciones recientes ({'overtime_count': 4})

### HOME_TEAM_TOTAL
- Línea: 103.5
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 210.5 and spread DET -3.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869417
- Notas: Team total implícito del local underdog.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 108.92
- Mediana combinada: 112.00
- Diferencia contra línea: 5.42
- Volatilidad/desv. estándar: 10.76
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 60.0, '20': 65.0, '30': 76.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 40.0, '20': 35.0, '30': 23.33}
- Cumplimiento split local/visitante over: 73.33%
- Cumplimiento split local/visitante under: 23.33%
- Advertencias: [NON_REAL_MARKET_LINE] La línea HOME_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 97.8, 'avg_30': 108.917}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 4 apariciones recientes ({'overtime_count': 4})

### AWAY_TEAM_TOTAL
- Línea: 107.0
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 210.5 and spread DET -3.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869417
- Notas: Team total implícito del visitante favorito.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 113.08
- Mediana combinada: 115.00
- Diferencia contra línea: 6.08
- Volatilidad/desv. estándar: 11.59
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 40.0, '20': 70.0, '30': 70.0}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 60.0, '20': 30.0, '30': 30.0}
- Cumplimiento split local/visitante over: 76.67%
- Cumplimiento split local/visitante under: 23.33%
- Advertencias: [NON_REAL_MARKET_LINE] La línea AWAY_TEAM_TOTAL no proviene de mercado real ({'source_type': 'DERIVED_FROM_TOTAL_SPREAD'}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 103.6, 'avg_30': 113.083}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 4 apariciones recientes ({'overtime_count': 4})

## Advertencias generales
- [EXCLUDED_APPEARANCES] se excluyeron 17 apariciones antes de calcular muestras ({'excluded': 17})

## Resumen para análisis externo
Partido: Orlando Magic local vs Detroit Pistons visitante, fecha 2026-05-01. BD disponible hasta 2026-05-05.
Muestras recientes: ORL general 30 y local 30; DET general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 56.87, Q2 57.03, Q3 57.32, Q4 52.42, total partido 224.52.
Líneas evaluadas técnicamente: Q1_TOTAL línea 52.5 (TECHNICAL_ESTIMATE): señal estadística moderada, diff 3.77, vol 6.27; FULL_GAME_TOTAL línea 210.5 (REAL_MARKET): señal inconsistente, diff 11.50, vol 18.53; HOME_TEAM_TOTAL línea 103.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 5.42, vol 10.76; AWAY_TEAM_TOTAL línea 107.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.08, vol 11.59.
Usar como evidencia estadística, no como recomendación de apuesta.

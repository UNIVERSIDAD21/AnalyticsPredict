# Análisis estadístico previo NBA: San Antonio Spurs vs Minnesota Timberwolves

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: San Antonio Spurs (SAS) local vs Minnesota Timberwolves (MIN) visitante
- Fecha del partido: 2026-05-05
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T00:51:47

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
- Apariciones excluidas: 20 (5.56%)
- Razones de exclusión: marcador 0-0: 20

## Forma reciente - San Antonio Spurs local

### General
- Últimos 5: PF total 110.60 / PA total 101.20; Q1 PF 27.40, Q2 26.00, Q3 26.60, Q4 30.60; OT 0
- Últimos 10: PF total 116.50 / PA total 102.50; Q1 PF 30.10, Q2 29.40, Q3 27.90, Q4 29.10; OT 0
- Últimos 20: PF total 121.30 / PA total 107.30; Q1 PF 32.00, Q2 30.25, Q3 30.80, Q4 28.25; OT 0
- Últimos 30: PF total 120.63 / PA total 107.27; Q1 PF 31.40, Q2 30.70, Q3 30.53, Q4 28.00; OT 0

### Split local
- Últimos 5: PF total 111.80 / PA total 103.40; Q1 PF 29.20, Q2 28.80, Q3 27.40, Q4 26.40; OT 0
- Últimos 10: PF total 116.50 / PA total 109.00; Q1 PF 30.90, Q2 28.50, Q3 30.00, Q4 27.10; OT 0
- Últimos 20: PF total 119.55 / PA total 109.60; Q1 PF 32.30, Q2 29.50, Q3 30.20, Q4 27.55; OT 0
- Últimos 30: PF total 119.23 / PA total 110.57; Q1 PF 31.70, Q2 29.17, Q3 30.27, Q4 28.10; OT 0

## Forma reciente - Minnesota Timberwolves visitante

### General
- Últimos 5: PF total 110.40 / PA total 103.40; Q1 PF 25.80, Q2 27.00, Q3 26.40, Q4 31.20; OT 0
- Últimos 10: PF total 109.50 / PA total 106.30; Q1 PF 27.70, Q2 26.70, Q3 25.50, Q4 29.60; OT 0
- Últimos 20: PF total 111.50 / PA total 110.55; Q1 PF 27.60, Q2 28.00, Q3 27.05, Q4 28.10; OT 1
- Últimos 30: PF total 113.13 / PA total 111.03; Q1 PF 28.27, Q2 28.37, Q3 27.23, Q4 28.77; OT 1

### Split visitante
- Últimos 5: PF total 109.80 / PA total 114.00; Q1 PF 28.40, Q2 26.80, Q3 23.40, Q4 31.20; OT 0
- Últimos 10: PF total 113.30 / PA total 114.20; Q1 PF 27.10, Q2 29.50, Q3 27.10, Q4 29.60; OT 0
- Últimos 20: PF total 116.20 / PA total 115.70; Q1 PF 27.70, Q2 27.80, Q3 29.65, Q4 31.05; OT 0
- Últimos 30: PF total 119.87 / PA total 117.03; Q1 PF 28.77, Q2 28.47, Q3 29.50, Q4 32.37; OT 1

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 56.10 | 53.30 | 52.50 | 57.60 | 219.50 |
| 10 | 56.15 | 54.65 | 58.45 | 57.25 | 226.50 |
| 20 | 57.23 | 56.48 | 59.15 | 57.67 | 230.53 |
| 30 | 57.93 | 56.65 | 59.05 | 58.88 | 233.35 |

## Evaluación técnica de líneas

### Q1_TOTAL
- Línea: 54.5
- Tipo de fuente: TECHNICAL_ESTIMATE (TÉCNICA)
- Fuente: manual/technical
- URL fuente: N/D
- Notas: Línea técnica para validar Q1; no proviene de mercado real observado.
- Clasificación técnica: **señal estadística débil**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico.
- Promedio combinado: 57.12
- Mediana combinada: 57.50
- Diferencia contra línea: 2.62
- Volatilidad/desv. estándar: 5.48
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 70.0, '20': 70.0, '30': 76.67}
- Cumplimiento under 5/10/20/30: {'5': 60.0, '10': 30.0, '20': 30.0, '30': 23.33}
- Cumplimiento split local/visitante over: 76.67%
- Cumplimiento split local/visitante under: 23.33%
- Advertencias: línea no REAL_MARKET: TECHNICAL_ESTIMATE; Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico.; datos afectados por overtime en 1 apariciones recientes

### FULL_GAME_TOTAL
- Línea: 218.5
- Tipo de fuente: REAL_MARKET (REAL)
- Fuente: ESPN pickcenter / DraftKings close
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871152
- Notas: overUnder 218.5, odds -110/-110
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 226.03
- Mediana combinada: 225.75
- Diferencia contra línea: 7.53
- Volatilidad/desv. estándar: 14.39
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 50.0, '20': 75.0, '30': 80.0}
- Cumplimiento under 5/10/20/30: {'5': 80.0, '10': 50.0, '20': 25.0, '30': 20.0}
- Cumplimiento split local/visitante over: 83.33%
- Cumplimiento split local/visitante under: 16.67%
- Advertencias: desviación estándar alta: mercado volátil; diferencia fuerte entre forma reciente (5) y muestra completa (30); datos afectados por overtime en 1 apariciones recientes

### HOME_TEAM_TOTAL
- Línea: 114.5
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 218.5 and spread SA -10.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871152
- Notas: Team total implícito del local.
- Clasificación técnica: **señal estadística débil**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 115.83
- Mediana combinada: 117.25
- Diferencia contra línea: 1.33
- Volatilidad/desv. estándar: 9.66
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 40.0, '20': 60.0, '30': 63.33}
- Cumplimiento under 5/10/20/30: {'5': 80.0, '10': 60.0, '20': 40.0, '30': 36.67}
- Cumplimiento split local/visitante over: 56.67%
- Cumplimiento split local/visitante under: 43.33%
- Advertencias: línea no REAL_MARKET: DERIVED_FROM_TOTAL_SPREAD; diferencia fuerte entre forma reciente (5) y muestra completa (30); datos afectados por overtime en 1 apariciones recientes

### AWAY_TEAM_TOTAL
- Línea: 104.0
- Tipo de fuente: DERIVED_FROM_TOTAL_SPREAD (DERIVADA/IMPLÍCITA)
- Fuente: derived from total 218.5 and spread SA -10.5
- URL fuente: https://www.espn.com/nba/game/_/gameId/401871152
- Notas: Team total implícito del visitante.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Promedio combinado: 110.20
- Mediana combinada: 109.75
- Diferencia contra línea: 6.20
- Volatilidad/desv. estándar: 8.01
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 50.0, '20': 70.0, '30': 73.33}
- Cumplimiento under 5/10/20/30: {'5': 40.0, '10': 40.0, '20': 20.0, '30': 13.33}
- Cumplimiento split local/visitante over: 80.00%
- Cumplimiento split local/visitante under: 13.33%
- Advertencias: línea no REAL_MARKET: DERIVED_FROM_TOTAL_SPREAD; datos afectados por overtime en 1 apariciones recientes

## Advertencias generales
- se excluyeron 20 apariciones con marcador 0 o incompleto antes de calcular muestras

## Resumen para análisis externo
Partido: San Antonio Spurs local vs Minnesota Timberwolves visitante, fecha 2026-05-05. BD disponible hasta 2026-05-05.
Muestras recientes: SAS general 30 y local 30; MIN general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 57.93, Q2 56.65, Q3 59.05, Q4 58.88, total partido 233.35.
Líneas evaluadas técnicamente: Q1_TOTAL línea 54.5 (TECHNICAL_ESTIMATE): señal estadística débil, diff 2.62, vol 5.48; FULL_GAME_TOTAL línea 218.5 (REAL_MARKET): señal inconsistente, diff 7.53, vol 14.39; HOME_TEAM_TOTAL línea 114.5 (DERIVED_FROM_TOTAL_SPREAD): señal estadística débil, diff 1.33, vol 9.66; AWAY_TEAM_TOTAL línea 104.0 (DERIVED_FROM_TOTAL_SPREAD): señal estadística moderada, diff 6.20, vol 8.01.
Usar como evidencia estadística, no como recomendación de apuesta.

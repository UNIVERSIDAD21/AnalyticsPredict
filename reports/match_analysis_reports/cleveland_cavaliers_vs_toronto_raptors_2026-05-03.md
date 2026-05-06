# Análisis estadístico previo NBA: Cleveland Cavaliers vs Toronto Raptors

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: Cleveland Cavaliers (CLE) local vs Toronto Raptors (TOR) visitante
- Fecha del partido: 2026-05-03
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T00:59:51

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

## Forma reciente - Cleveland Cavaliers local

### General
- Últimos 5: PF total 108.40 / PA total 110.60; Q1 PF 27.20, Q2 24.20, Q3 30.00, Q4 25.80; OT 1
- Últimos 10: PF total 113.60 / PA total 112.20; Q1 PF 29.20, Q2 25.00, Q3 30.70, Q4 28.10; OT 1
- Últimos 20: PF total 118.40 / PA total 114.85; Q1 PF 30.80, Q2 27.00, Q3 30.70, Q4 29.60; OT 1
- Últimos 30: PF total 117.00 / PA total 112.73; Q1 PF 30.93, Q2 26.70, Q3 30.67, Q4 28.33; OT 2

### Split local
- Últimos 5: PF total 125.80 / PA total 113.60; Q1 PF 32.60, Q2 29.80, Q3 33.00, Q4 30.40; OT 0
- Últimos 10: PF total 120.10 / PA total 115.90; Q1 PF 29.70, Q2 28.40, Q3 32.60, Q4 29.40; OT 0
- Últimos 20: PF total 120.05 / PA total 113.35; Q1 PF 29.50, Q2 30.65, Q3 32.10, Q4 27.80; OT 0
- Últimos 30: PF total 120.10 / PA total 114.83; Q1 PF 29.67, Q2 29.90, Q3 32.37, Q4 28.17; OT 1

## Forma reciente - Toronto Raptors visitante

### General
- Últimos 5: PF total 110.60 / PA total 108.40; Q1 PF 27.40, Q2 27.80, Q3 26.00, Q4 27.80; OT 1
- Últimos 10: PF total 114.10 / PA total 112.00; Q1 PF 26.70, Q2 29.10, Q3 27.60, Q4 29.90; OT 1
- Últimos 20: PF total 115.00 / PA total 114.00; Q1 PF 27.65, Q2 28.75, Q3 30.05, Q4 28.15; OT 1
- Últimos 30: PF total 114.03 / PA total 112.03; Q1 PF 27.33, Q2 28.63, Q3 30.23, Q4 27.57; OT 1

### Split visitante
- Últimos 5: PF total 111.20 / PA total 121.40; Q1 PF 26.00, Q2 29.80, Q3 25.20, Q4 30.20; OT 0
- Últimos 10: PF total 114.50 / PA total 120.30; Q1 PF 26.50, Q2 30.00, Q3 30.00, Q4 28.00; OT 0
- Últimos 20: PF total 114.15 / PA total 115.55; Q1 PF 26.05, Q2 29.60, Q3 31.00, Q4 27.50; OT 0
- Últimos 30: PF total 112.57 / PA total 113.20; Q1 PF 27.03, Q2 28.43, Q3 30.23, Q4 26.87; OT 0

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 57.90 | 57.30 | 60.90 | 59.90 | 236.00 |
| 10 | 57.20 | 56.95 | 61.85 | 59.40 | 235.40 |
| 20 | 56.33 | 57.88 | 60.42 | 56.92 | 231.55 |
| 30 | 56.05 | 58.20 | 60.13 | 55.83 | 230.35 |

## Evaluación técnica de líneas

### Q1_TOTAL
- Línea: 52.5
- Tipo de fuente: TECHNICAL_ESTIMATE (TÉCNICA)
- Fuente: manual/technical
- URL fuente: N/D
- Notas: Línea técnica para validar mercado Q1 sin fuente real observada.
- Clasificación técnica: **señal estadística moderada**
- Advertencia de trazabilidad: esta línea no está marcada como mercado real; interpretar con menor peso analítico.
- Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico.
- Promedio combinado: 56.78
- Mediana combinada: 57.50
- Diferencia contra línea: 4.28
- Volatilidad/desv. estándar: 7.62
- Cumplimiento over 5/10/20/30: {'5': 60.0, '10': 60.0, '20': 70.0, '30': 70.0}
- Cumplimiento under 5/10/20/30: {'5': 40.0, '10': 30.0, '20': 20.0, '30': 20.0}
- Cumplimiento split local/visitante over: 66.67%
- Cumplimiento split local/visitante under: 26.67%
- Advertencias: [NON_REAL_MARKET_LINE] La línea Q1_TOTAL no proviene de mercado real ({'source_type': 'TECHNICAL_ESTIMATE'}); [TECHNICAL_ESTIMATE_ONLY] Esta línea no proviene de mercado real; se usa solo para simulación/análisis técnico. ({'source_type': 'TECHNICAL_ESTIMATE'}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 3 apariciones recientes ({'overtime_count': 3})

### FULL_GAME_TOTAL
- Línea: 209.5
- Tipo de fuente: REAL_MARKET (REAL)
- Fuente: ESPN pickcenter / DraftKings close
- URL fuente: https://www.espn.com/nba/game/_/gameId/401869384
- Notas: overUnder 209.5, odds -105/-115 convertidas aprox.
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 227.90
- Mediana combinada: 227.75
- Diferencia contra línea: 18.40
- Volatilidad/desv. estándar: 16.93
- Cumplimiento over 5/10/20/30: {'5': 80.0, '10': 90.0, '20': 95.0, '30': 90.0}
- Cumplimiento under 5/10/20/30: {'5': 20.0, '10': 10.0, '20': 5.0, '30': 10.0}
- Cumplimiento split local/visitante over: 90.00%
- Cumplimiento split local/visitante under: 10.00%
- Advertencias: [HIGH_VOLATILITY] desviación estándar alta: mercado volátil ({'stddev': 16.925}); [RECENT_FULL_SAMPLE_DIVERGENCE] diferencia fuerte entre forma reciente (5) y muestra completa (30) ({'recent_avg': 219.0, 'avg_30': 227.9}); [OVERTIME_IN_SAMPLE] datos afectados por overtime en 3 apariciones recientes ({'overtime_count': 3})

## Advertencias generales
- [EXCLUDED_APPEARANCES] se excluyeron 17 apariciones antes de calcular muestras ({'excluded': 17})

## Resumen para análisis externo
Partido: Cleveland Cavaliers local vs Toronto Raptors visitante, fecha 2026-05-03. BD disponible hasta 2026-05-05.
Muestras recientes: CLE general 30 y local 30; TOR general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 56.05, Q2 58.20, Q3 60.13, Q4 55.83, total partido 230.35.
Líneas evaluadas técnicamente: Q1_TOTAL línea 52.5 (TECHNICAL_ESTIMATE): señal estadística moderada, diff 4.28, vol 7.62; FULL_GAME_TOTAL línea 209.5 (REAL_MARKET): señal inconsistente, diff 18.40, vol 16.93.
Usar como evidencia estadística, no como recomendación de apuesta.

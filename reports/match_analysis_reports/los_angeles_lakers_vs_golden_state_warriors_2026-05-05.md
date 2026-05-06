# Análisis estadístico previo NBA: Los Angeles Lakers vs Golden State Warriors

> Insumo técnico. No es recomendación de apuesta, no calcula stake y no expresa certezas.

## Metadata
- Partido: Los Angeles Lakers (LAL) local vs Golden State Warriors (GSW) visitante
- Fecha del partido: 2026-05-05
- Fecha máxima disponible en BD: 2026-05-05
- Generado: 2026-05-06T00:30:49

## Reglas de clasificación de señales
- **señal estadística fuerte:** brecha promedio-línea >= 6, al menos 3 ventanas con cumplimiento direccional >=60% o <=40%, y ventanas consistentes
- **señal estadística moderada:** brecha promedio-línea >= 3 y al menos 2 ventanas con cumplimiento direccional
- **señal estadística débil:** evaluable, pero sin suficiente brecha/consenso
- **señal inconsistente:** volatilidad alta o advertencias de inconsistencia reciente vs completa
- **no evaluable por datos insuficientes:** línea inválida, mercado no soportado o muestra insuficiente

## Muestras usadas
- Local general/local: 30 / 30
- Visitante general/visitante: 30 / 30

## Forma reciente - Los Angeles Lakers local

### General
- Últimos 5: PF total 100.00 / PA total 98.80; Q1 PF 28.80, Q2 23.20, Q3 19.60, Q4 26.20; OT 1
- Últimos 10: PF total 106.60 / PA total 104.40; Q1 PF 29.00, Q2 26.20, Q3 23.40, Q4 26.90; OT 1
- Últimos 20: PF total 113.75 / PA total 109.15; Q1 PF 29.95, Q2 27.30, Q3 27.55, Q4 27.95; OT 2
- Últimos 30: PF total 114.67 / PA total 109.53; Q1 PF 30.70, Q2 27.20, Q3 28.03, Q4 28.07; OT 2

### Split local
- Últimos 5: PF total 109.60 / PA total 101.00; Q1 PF 30.20, Q2 26.00, Q3 27.40, Q4 26.00; OT 0
- Últimos 10: PF total 116.30 / PA total 106.20; Q1 PF 29.30, Q2 27.60, Q3 30.10, Q4 28.40; OT 1
- Últimos 20: PF total 114.95 / PA total 109.25; Q1 PF 30.65, Q2 26.70, Q3 29.55, Q4 27.60; OT 1
- Últimos 30: PF total 115.40 / PA total 111.07; Q1 PF 30.27, Q2 27.97, Q3 29.17, Q4 27.70; OT 1

## Forma reciente - Golden State Warriors visitante

### General
- Últimos 5: PF total 107.80 / PA total 118.60; Q1 PF 23.40, Q2 26.00, Q3 28.40, Q4 30.00; OT 0
- Últimos 10: PF total 112.70 / PA total 119.70; Q1 PF 27.60, Q2 26.70, Q3 26.70, Q4 30.60; OT 1
- Últimos 20: PF total 111.45 / PA total 119.00; Q1 PF 28.10, Q2 25.55, Q3 27.85, Q4 28.40; OT 3
- Últimos 30: PF total 111.80 / PA total 117.60; Q1 PF 29.03, Q2 26.20, Q3 26.70, Q4 28.83; OT 3

### Split visitante
- Últimos 5: PF total 112.40 / PA total 121.00; Q1 PF 27.00, Q2 28.00, Q3 26.00, Q4 29.20; OT 1
- Últimos 10: PF total 111.00 / PA total 118.60; Q1 PF 28.00, Q2 26.80, Q3 26.50, Q4 28.60; OT 1
- Últimos 20: PF total 110.65 / PA total 113.50; Q1 PF 27.10, Q2 26.40, Q3 27.70, Q4 28.20; OT 2
- Últimos 30: PF total 111.30 / PA total 112.50; Q1 PF 26.27, Q2 27.47, Q3 27.73, Q4 28.83; OT 3

## Métricas combinadas esperadas

| Ventana | Q1 total | Q2 total | Q3 total | Q4 total | Partido completo |
|---:|---:|---:|---:|---:|---:|
| 5 | 57.50 | 52.10 | 55.00 | 55.80 | 222.00 |
| 10 | 55.90 | 54.25 | 57.25 | 57.05 | 226.05 |
| 20 | 56.10 | 54.05 | 56.77 | 55.80 | 224.18 |
| 30 | 56.23 | 55.30 | 56.60 | 55.63 | 225.13 |

## Evaluación técnica de líneas

### Q1_TOTAL
- Línea: 56.5
- Clasificación técnica: **señal estadística débil**
- Promedio combinado: 58.27
- Mediana combinada: 59.25
- Diferencia contra línea: 1.77
- Volatilidad/desv. estándar: 6.94
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 50.0, '20': 50.0, '30': 53.33}
- Cumplimiento under 5/10/20/30: {'5': 80.0, '10': 50.0, '20': 45.0, '30': 40.0}
- Cumplimiento split local/visitante over: 43.33%
- Cumplimiento split local/visitante under: 50.00%
- Advertencias: datos afectados por overtime en 5 apariciones recientes

### FULL_GAME_TOTAL
- Línea: 228.5
- Clasificación técnica: **señal inconsistente**
- Promedio combinado: 226.80
- Mediana combinada: 227.25
- Diferencia contra línea: -1.70
- Volatilidad/desv. estándar: 15.12
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 30.0, '20': 40.0, '30': 40.0}
- Cumplimiento under 5/10/20/30: {'5': 80.0, '10': 60.0, '20': 55.0, '30': 56.67}
- Cumplimiento split local/visitante over: 33.33%
- Cumplimiento split local/visitante under: 63.33%
- Advertencias: desviación estándar alta: mercado volátil; diferencia fuerte entre forma reciente (5) y muestra completa (30); datos afectados por overtime en 5 apariciones recientes

### HOME_TEAM_TOTAL
- Línea: 112.5
- Clasificación técnica: **señal estadística moderada**
- Promedio combinado: 116.13
- Mediana combinada: 116.00
- Diferencia contra línea: 3.63
- Volatilidad/desv. estándar: 9.25
- Cumplimiento over 5/10/20/30: {'5': 20.0, '10': 50.0, '20': 65.0, '30': 66.67}
- Cumplimiento under 5/10/20/30: {'5': 80.0, '10': 50.0, '20': 35.0, '30': 33.33}
- Cumplimiento split local/visitante over: 46.67%
- Cumplimiento split local/visitante under: 53.33%
- Advertencias: datos afectados por overtime en 5 apariciones recientes

### AWAY_TEAM_TOTAL
- Línea: 110.5
- Clasificación técnica: **señal estadística débil**
- Promedio combinado: 110.67
- Mediana combinada: 111.75
- Diferencia contra línea: 0.17
- Volatilidad/desv. estándar: 9.01
- Cumplimiento over 5/10/20/30: {'5': 40.0, '10': 50.0, '20': 55.0, '30': 53.33}
- Cumplimiento under 5/10/20/30: {'5': 40.0, '10': 40.0, '20': 40.0, '30': 43.33}
- Cumplimiento split local/visitante over: 43.33%
- Cumplimiento split local/visitante under: 56.67%
- Advertencias: datos afectados por overtime en 5 apariciones recientes

## Advertencias generales
- se excluyeron 19 apariciones con marcador 0 o incompleto antes de calcular muestras

## Resumen para análisis externo
Partido: Los Angeles Lakers local vs Golden State Warriors visitante, fecha 2026-05-05. BD disponible hasta 2026-05-05.
Muestras recientes: LAL general 30 y local 30; GSW general 30 y visitante 30.
Combinado split local/visitante últimos 30: Q1 56.23, Q2 55.30, Q3 56.60, Q4 55.63, total partido 225.13.
Líneas evaluadas técnicamente: Q1_TOTAL línea 56.5: señal estadística débil, diff 1.77, vol 6.94; FULL_GAME_TOTAL línea 228.5: señal inconsistente, diff -1.70, vol 15.12; HOME_TEAM_TOTAL línea 112.5: señal estadística moderada, diff 3.63, vol 9.25; AWAY_TEAM_TOTAL línea 110.5: señal estadística débil, diff 0.17, vol 9.01.
Usar como evidencia estadística, no como recomendación de apuesta.

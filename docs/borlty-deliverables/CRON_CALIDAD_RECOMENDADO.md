# Cron recomendado (calidad profesional)

## Objetivo
Automatizar ciclo de calidad + reporte ejecutivo sin intervención manual.

## Jobs sugeridos (UTC)

### 1) Resolución + snapshot diario
- Hora: `06:10 UTC`
- Comando:

```bash
cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo
```

### 2) Reporte ejecutivo diario
- Hora: `06:20 UTC`
- Comando:

```bash
cd /home/borlty/repos/AnalyticsPredict && bash scripts/reporte_ejecutivo_calidad.sh
```

### 3) Revisión extra intradía (opcional)
- Hora: `14:00 UTC`
- Comando:

```bash
cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo-fast
```

### 4) Reporte semanal automático
- Día/hora: `Lunes 06:30 UTC`
- Comando:

```bash
cd /home/borlty/repos/AnalyticsPredict && make reporte-semanal-auto
```

## Ejemplo crontab

```cron
10 6 * * * cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo >> /tmp/analyticspredict_calidad.log 2>&1
20 6 * * * cd /home/borlty/repos/AnalyticsPredict && bash scripts/reporte_ejecutivo_calidad.sh >> /tmp/analyticspredict_reporte.log 2>&1
0 14 * * * cd /home/borlty/repos/AnalyticsPredict && make calidad-ciclo-fast >> /tmp/analyticspredict_calidad_fast.log 2>&1
30 6 * * 1 cd /home/borlty/repos/AnalyticsPredict && make reporte-semanal-auto >> /tmp/analyticspredict_reporte_semanal.log 2>&1
```

## Política de alertas
- score_global < 70 => crítico
- cualquier mercado con Brier > 0.26 y n>=100 => recalibración prioritaria
- deporte con n_resueltas=0 y n_total>0 => bloquear decisiones automáticas

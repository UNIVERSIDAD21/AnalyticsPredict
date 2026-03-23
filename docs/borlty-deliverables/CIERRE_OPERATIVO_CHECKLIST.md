# Cierre Operativo - Checklist

## Al final del día
1. Ejecutar:
   ```bash
   cd /home/borlty/repos/AnalyticsPredict && make cierre-operativo
   ```
2. Revisar `reports/cierre/<timestamp>/CIERRE_OPERATIVO.md`.
3. Confirmar GO/NO-GO para siguiente ventana.
4. Si NO-GO, dejar nota en bitácora y no publicar recomendaciones automáticas.

## Criterios de salida saludable
- score_global >= 85
- semáforo en verde o amarillo controlado
- sin alertas críticas de ingestión
- sin motivos de bloqueo en modo estricto

# CRITERIOS_DE_PROMOCION_Y_ROLLBACK

Versión: 1.0  
Fecha: 2026-03-09

## 1. Matriz de decisión

| Métrica | Umbral | Bloqueante |
|---|---|---|
| MAE promedio Q1..Q4 (NBA) | mejora >3% | Sí |
| Brier | mejora >2% | Sí |
| ECE | <0.05 | Sí |
| LogLoss | degradación <=3% | Sí |
| Smoke API/DB | sin 500 en endpoints críticos | Sí |
| Coherencia A+warning crítico | 422 controlado | Sí |

## 2. Pasos de promoción

1. Validar candidate en staging.
2. Comparar contra baseline vigente.
3. Verificar umbrales de matriz.
4. Activar con feature flag/control de versión.
5. Monitorear 30 días en producción.

## 3. Pasos de rollback

1. Detectar trigger (regresión métrica o incidente crítico).
2. Diagnóstico rápido (data/modelo/contrato).
3. Revertir versión activa (serving/flag).
4. Notificar stakeholders.
5. Documentar postmortem y acción correctiva.

## 4. Gobernanza de deuda

`confidence_parcial` no puede pasar a RESUELTA sin 30+ días de estabilidad en producción con los criterios anteriores.

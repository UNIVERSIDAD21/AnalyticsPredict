# Alertas de calidad locales — single-user

Por decisión del propietario **no se envían notificaciones externas**. El scorecard produce `alertas_locales` en JSON; no hay Telegram, email, webhook ni cron de mensajes. Los documentos de alertas comerciales anteriores son históricos.

## Política

- `CRITICO`: impide declarar certificada la métrica o modelo afectado. Ejemplos: P&L inconsistente, cutoff posterior a generación, predicción huérfana, probabilidad fuera de rango. Requiere diagnóstico antes de reportar rendimiento.
- `OBSERVAR`: necesita clasificación/contexto; no provoca borrado, reescritura ni promoción. Ejemplos: 0 observaciones recientes, 0–0, cobertura insuficiente.
- `NO_EVALUABLE`: falta dato/probe. No entra en `alertas_locales` porque un cero ficticio sería engañoso; sí aparece en `reglas` para que el operador lo vea.
- `OK`: cumple la regla calculable, no equivale a certificación global.

El evaluador no tiene side effects. Es apto para CI con un fixture sintético y para Neon solo mediante el corte read-only previo. Los 11 avisos locales del corte 2026-10-06 incluyen tres críticos principales: P&L NBA (102), cutoff NBA (2.136) y versión de modelo fútbol ausente (567); un cuarto control crítico detecta 25 finalizados fútbol sin goles. Otras alertas son observaciones, no evidencias de caída de feed.

Tras la ingesta NBA, el control de frescura NBA pasó a OK. El probe separado de fuentes dejó ESPN en OK y Sofascore en CRITICO (HTTP 403), con 11 alertas locales en el scorecard combinado. Un 403 es bloqueo de acceso al feed consultado, no prueba que no se hayan jugado partidos. No se envía ningún aviso fuera de los archivos JSON locales.

## Runbook mínimo

1. Ejecutar corte read-only, guardar JSON fuera del repositorio y generar scorecard (comandos en `DATA_QUALITY_RULES.md`).
2. Revisar `estado`, `alertas_locales`, `reglas` y denominadores; comparar con corte anterior y calendario.
3. Para P&L, revisar semántica y evidencia primaria antes de corregir cualquier fila. Para cutoff, invalidar trazas no verificables antes de backtesting. Para finalizados sin goles, distinguir fuente incompleta de estado incorrecto.
4. Reejecutar tests/scorecard después de una reparación; no cerrar la alerta solo por ejecutar el script.

Prueba automatizada: `python -m pytest -q backend/tests/calidad/test_reglas_single_user.py` desde la raíz con `PYTHONPATH=backend`, o desde `backend` sin variable adicional.

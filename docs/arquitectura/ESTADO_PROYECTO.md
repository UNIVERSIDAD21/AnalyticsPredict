# Estado vigente — AnalyticsPredict

Última actualización: **2026-10-16**. Herramienta personal single-user, local y
ligada a loopback. Sin login, pagos, suscripciones, tiers ni lanzamiento comercial.
Responsable operativo: UNIVERSIDAD21. Dictamen analítico: **NO CERTIFICADO**.

## Fuentes y continuidad

- [Fuente de verdad](../FUENTE_DE_VERDAD_ACTUAL.md).
- [Roadmap vigente](../reactivacion_single_user/ROADMAP_REACTIVACION_ANALYTICSPREDICT.md).
- [Deuda priorizada](../reactivacion_single_user/DEUDA_TECNICA_PRIORIZADA.md).
- [Checklist de uso](../reactivacion_single_user/CHECKLIST_PREPARACION_USO_2026-10-15.md).
- [Siete frentes, fuentes por mitades y validación](../reactivacion_single_user/SIETE_FRENTES_2026-10-16.md).
- [KPI/P&L y auditoría GET](../reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md).
- [KPI de calibración](../reactivacion_single_user/KPI_CALIBRACION_2026-10-16.md).
- [Evaluación temporal fútbol](../reactivacion_single_user/EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md).

## Hechos comprobados y límites

| Frente | Cierre acreditado | Pendiente real |
|---|---|---|
| Single-user | Migración con backup, historial deportivo conservado; auth/pagos/tiers retirados de API/UI/BD activos | Revalidar perímetro si cambia topología; visual completo aún no acreditado |
| Entorno y CI | Python3.12 persistente, lock, pruebas PostgreSQL sintéticas, frontend y Compose en CI | Estado de procesos se comprueba al operar; un HTTP200 anterior no demuestra que sigan activos |
| NBA canónico/serving | Selector NBA válido, modelo2123 con30equipos, 73partidos añadidos; reload sin entrenar | No es validación de eficacia; PRE separado de regular |
| Fútbol canónico | 337eventos ESPN vinculados, 200finales, 136programados, 1suspendido; 23.919históricos/apuestas/predicciones conservados, reimportación0/0 | 200finales completados con goles/córners1T/2T explícitos y evidencia separada, rollback/idempotencia/postflight. No imputar desdeFT |
| ML fútbol técnico | Artefacto completo verificable, activación atómica y loader read-only, API/UI sin modelos/MAE/fechas ficticios;771backend/24frontend en ese corte | No hay modelo fútbol activo registrado en el último corte real |
| ML fútbol temporal | Reevaluación tras completar tiempos:618EVAL por familia, política original; frescura reciente recuperada | Ninguna familia apta: cobertura79,13% en las tres y target corners peor. CensoCAL97finales<100mínimo; sin modelos/activación enNeon |
| P&L histórico | Guardas y N/D;114/181binarias NBA no evaluables,67solo aritméticas,8discrepancias deportivas | Propietario confirma que NO existen soportes: no pedirlos ni inventarlos. Exclusión controlada; ROI no certificado |
| Temporalidad histórica NBA | 2.934trazas auditadas:2.136inválidas,476ambiguas,322indeterminadas | 0certificables en ese corte; no convertir histórico en prospectiva |
| Prospectiva NBA | 12capturas Q1raw PRE congeladas antes de inicio, hashes/horas/políticas verificados;0outcomes al último corte | Partidos16/10 23:00Z–17/10 02:30Z, resolución posterior porUUID y fuente independiente; CBScoincide12/12calendarios pero upstream sin acreditar. No repetir capturas |
| KPI/observabilidad | [M04/M05 técnico](../reactivacion_single_user/KPI_PNL_Y_GET_2026-10-16.md): P&L común cross-sport/N/D, grano/cohortes, calibración con serie/n/modelo, sinTTL;78GET revisados y guardas READONLY/errores sanitizados | M12 evaluado:1.303cohortesraw de2–4pares, cero calibradasID/elegibles temporales; confianza/cuotas descriptivas y P&LN/D. Certificación y visual pendientes |
| Mantenimiento | H6/H7 técnico y reproducibilidad/CI cerrados en sus alcances | H12parcial:10→5altasdev/0prod, residuobraces sin parche;0discrepanciasmodo yfavicon reparado. H4ensayo357/357refs y4blobs fuera; remoto aún alcanzable por12heads/13refsPR y cachés, sin purga parcial |

Las cifras de datos/DB corresponden a cortes identificados en sus informes, no a
una consulta permanente. La evaluación temporal usa cinco ligas y desde2023-07;
no se confunde su dataset acotado con el diagnóstico global de persistencia.

## Decisiones del propietario ya resueltas

No hay soportes originales P&L ni tarea humana para recuperarlos. Revisión visual
y diagnóstico del navegador corresponden al agente, con control autorizado.
No existe necesidad concreta pendiente de login/2FA, contratación o gestión
personal GitHub. Un fallo de herramienta no se atribuye a falta de permiso humano.
No hay acciones futuras automáticas ni notificaciones externas configuradas por
estos bloques. El análisis NBA interno mantiene no_picks/no_stake/no_recommendations.

## Histórico preservado, no órdenes vigentes

Los cortes superados y C0–C7/A1–B7/P1–P9 se conservan íntegros en
[estado anterior a la consolidación](../archive/ESTADO_PROYECTO_ANTES_CONSOLIDACION_2026-10-16.md).
Sus cobros, MP, login, premium, dominios y tareas de lanzamiento **no** son requisitos
actuales. Ver ADR-005 histórico y ADR-006 aceptado para artefactos fútbol.

## Regla de cierre

Actualizar estado, changelog, roadmap y evidencia al cerrar cada bloque. No declarar
terminado el conjunto por un cierre técnico ni usar backtesting como promesa futura.

# Estado vigente — AnalyticsPredict

Última actualización: **2026-10-20**. Herramienta personal single-user, local y
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

## Recuperación multi-fuente de nulos — 2026-10-20

[Estado, cobertura y límites](../reactivacion_single_user/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md).
Recuperación parcial ya persistida: 234 vínculos proveedor-partido y 1.374
actualizaciones NULL-only, con 1.386 observaciones de procedencia. Censo READ ONLY:
24.593 finales FT, 4.605 partidos con algún NULL de corners/disparos/tiros al arco
(26.426 campos); gaps en ENG_FACUP, ESP_COPA, UEFA Champions/Europa/Conference,
FRA_COUPE e ITA_COPPA. ESPN aportó tandas verificadas; DataHub PDDL amplió top-5 y
un crosswalk exacto de LaLiga (dos partidos/12 valores) pasó backup, rollback y doble
postflight. Una excepción limitada completó corners local 0 de Verona–Roma tras
conciliación ESPN/HF/DataHub y corroboración Kaggle; el FT canónico 3–0 se conservó
y no se infirió la causa del desacuerdo de score. Kaggle/HF aportaron subconjuntos
conservadores. Se identificó importador histórico SofaScore con hora local ingenua;
la única excepción ESPN/SofaScore permite +5 h exactas en el mismo día UTC y conserva
la fecha canónica. Otros datasets se excluyen por métricas, upstream/licencias/robots
o procedencia insuficiente. El censo no afirma que todos los NULL sean recuperables;
PitchAPI sigue sin clave ni cobertura autenticada. Sin ML fútbol activo, apuestas
alteradas ni ingestas programadas.

## Corte vigente de datos — 2026-10-18

[Actualización integral enero–octubre](../reactivacion_single_user/ACTUALIZACION_INTEGRAL_DATOS_2026-10-18.md):
2.928 finales de fuentes contrastados, sin faltantes en esa cohorte. Fútbol +273
partidos/108 actualizaciones (82 estados programados cerrados y 26 conciliaciones);
NBA +18/6 fases; Euroliga +183. Totales 25.118 fútbol/24.593 finales FT,
10.379 NBA y 2.672 Euro. Un desglose de periodos inválido del proveedor se conserva
NULL, no imputado. Backups, rollback, idempotencia y once huellas protegidas intactas;
875 backend y 36 frontend aprobadas, lint/build/audit producción 0.
Fútbol sin ML activo, NBA 2123 sin reentrenar, prospectiva 15/9/0 independientes
sin modificar. Servicios no arrancados por esta tarea; no cron ni certificación.
Las cifras y límites analíticos del 16/10 siguientes son antecedentes de sus
cohortes; no se han recalculado ni trasladado a esta nueva base.

## Flujo inicial de uso — 2026-10-19

`/futbol` permite seleccionar un partido y consultar los datos/análisis
disponibles; “Guardar para revisar” lo agrega a una lista separada dentro de
`/bitacora`, desde donde se vuelve a abrir por su UUID. Guardar/reabrir no crea
una apuesta, mercado, pick ni probabilidad. El estado neutral queda fuera de
conteos, métricas, evaluaciones y backfill de apuestas. La implementación no
requiere DDL; solo escribe cuando el propietario pulsa guardar o quitar. Modelo
ML fútbol continúa sin activo; la certificación global permanece **NO CERTIFICADO**.
Detalle y pruebas dirigidas en la entrega externa
`PARTIDOS_GUARDADOS_BITACORA_2026-10-19`.

## Desarrollo ML fútbol V4 — 2026-10-19

[Protocolo, resultados y límites](../reactivacion_single_user/ML_FUTBOL_FORMA_V4_2026-10-19.md).
Nuevos candidatos Ridge con forma causal/contexto de liga y refit final anterior
a eventos futuros, separados de V1/V2/V3. Desarrollo retrospectivo:1.157/1.193
pares goles/disparos,96,98%cobertura, mejora frente a baseline de liga y sin targets
nominalmente peores; esto NO certifica el refit final ni reescribe los gatesV1.
Córners619/1.193,51,89%, no apto por cobertura. Cohorte futura20oct–1dicUTC:
251partidos,251predicciones goles/251disparos/223córners+28abstenciones, techo
córners88,84%<90. Estado inicial0pares/N/D, sin calibrador ni activación.
JSONcoeficientes/features/estado/hash completo y CLI de evaluación posterior,
archivos externos no sobrescribibles.887backend/0fallos/0skips, dos deprecaciones;
CI y publicación delSHA final en acta externa. Neon soloREADONLY,0MLfútbol activos,
serving/NBA/apuestas/bitácora intactos. No cron, ingesta ni arranque de servicios.

## Corte de uso local y visual — 2026-10-16

[Arranque, correcciones y límites](../reactivacion_single_user/ARRANQUE_VISUAL_Y_USO_LOCAL_2026-10-16.md).
Backend/frontend loopback,2123/30equipos sin reentrenar; flujos visibles y formulario
fútbol sintético verificados. H12Tailwind4/audit0,854backend/36frontend/lint/build;
publicación/CI final acreditadas en acta externa. Estado15capturas/9outcomesPRE/
0independientes;6pendientes, sin repetir congelamientos. H4ticket#4868445cerrado
por proveedor con autoservicio, sin coordinación de purga. Fútbol0MLactivos y
P&LN/D; eficaciaNO_CERTIFICADA. Este corte reemplaza bloqueos visual/H12 y conteos
outcomes anteriores, no los cierres científicos aún pendientes.

## Última pasada integral anterior — 2026-10-16

[Detalle y límites](../reactivacion_single_user/VALIDACION_ESTACIONAL_Y_FASES_NBA_2026-10-16.md):
426finales recuperados con goles por mitades/FT/tiros,38colisiones retenidas,
163programados de noviembre sin marcadores, total24.845fútbol. No se incorporan
nuevos córners por mitades;358rechazos de conciliación conservados. Postflight
reconciliado con trigger genéricoFT sin corregir datos. V1sigue no apta.
V2futura199partidos:163predicciones/36abstenciones por familia, techo81,91%;
V3CAL100:88/78efectivos<100, sin candidato. Ninguna activaciónMLfútbol.
NBA+2PRE(50),15snapshots(12PRE intactos+3REG20oct)/0outcomes,2123 sin reentrenar;
fases visibles API/UI/reportes. H12laboratorio0alertas/npm10ci/29tests/lint/build,
no publicado por visual bloqueado; producto conserva5altasdev/0prod. SolicitudH4
preparada, no enviada. Propuestas concretas de alcance al cierre, no tareas
manuales de programación ni soportes inexistentes para el propietario.

La tabla siguiente conserva los alcances y cortes anteriores; el corte de uso
local al inicio prevalece para visual/H12/outcomes/H4 actuales.

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

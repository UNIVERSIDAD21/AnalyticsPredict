# Deuda técnica priorizada — AnalyticsPredict single-user

**Corte consolidado:2026-10-16.** No sustituye gates científicos ni reactiva planes
comerciales. [Estado vigente](../arquitectura/ESTADO_PROYECTO.md) y
[roadmap](ROADMAP_REACTIVACION_ANALYTICSPREDICT.md) gobiernan el trabajo nuevo.

| Prioridad | Trabajo | Criterio de cierre | Estado real |
|---|---|---|---|
| P1 | KPI/caches coherentes | Grano/ventana/n/excluidos y N/D iguales en SQL/API/UI; raw/calibrado separados; frescura verificable | Cierre técnico16/10: políticaP&Lcross-sport/N/D y cohortes/API/UI, calibración sinTTL. M12 científico separado; no crear vistas propuestas sin consumidor |
| P1 | Auditoría GET y observabilidad | Llamadas transitivas sin escritura implícita, errores sanitizados, jobs/datos/modelos observables | Cierre técnico16/10:78GET revisados, protecciónGET/HEAD/errores sanitizados y pruebas. Nuevos endpoints requieren mantener los controles |
| P1 | H4 historiaGit | Purga integral recuperable y ausencia acreditada en todas las refs relevantes | Ensayo357/357refs y4blobs fuera con árboles restantes idénticos; backup privado. Remoto12heads/13refsPR contaminadas+cachésGitHub; no purga parcial |
| P2 | H12 dev/permisos/rot | Versiones compatibles, lock/pruebas/lint/build/CI; permisos reparados solo con evidencia | 16/10:5altasdev porbraces sin parche,0prod;10→5tras Vite/overrides probados.0discrepanciasmodo/sin chmod, respaldo histórico preservado |
| P2 | Visual/E2E | Flujo visible completo con evidencia, no solo HTTP200 | Herramienta rechazó navegación local; diagnóstico del agente, no falta de permiso del propietario |
| P2 analítico | Actualización y activación fútbol | Gates predeclarados por familia; fuente por tiempos/cobertura; versión/calibrador vinculados | 200complementos1T/2T aplicados;618EVAL/familia, ninguna apta:79,13%cobertura y targetcorners. CensoCAL97<100; no fallo de persistencia ni falta de permiso |
| P2 analítico | H8/H9 científico y prospectiva | fit_end<prediction_time<outcome_time, datos disponibles, independencia y muestra suficiente | 0históricasNBAcertificables;12snapshotsPRE/0outcomes al último corte, eventos aún futuros |
| P2 analítico | Confidence/odds/calibración | Cortes por deporte/mercado/versión, n/IC/baseline y elegibilidad temporal | Evaluación realizada:1.303cohortesraw n2–4,0calibradasID/pares temporales; confianza/cuotas descriptivas. Certificación abierta, sinprobabilidades/ROI certificados |
| Control permanente | P&L sin soportes | Preservar filas, exclusiones y ROI N/D; propagar motivos | Ausencia definitiva confirmada por propietario;114/181binarias no evaluables,67solo aritméticas. Nada que pedirle |

## Cierres que no se reabren por leer históricos

H1–H3 single-user, H6 escalas, H7 técnico/envelopes, H10/H11 reproducibilidad/CI,
H9 técnico de vistas, catálogo NBA/selector/modelo2123, fútbol canónico337/200,
artefactos/loaderMLfútbol y12congelamientosNBA ya están acreditados en sus alcances.
M04/M05 técnico se cerraron16/10; H9/M12 científico siguen abiertos. Fútbol sigue beta.
Análisis NBA interno: no picks, stakes ni recomendaciones de apuestas.

[Deuda previa íntegra](../archive/DEUDA_ANTES_CONSOLIDACION_2026-10-16.md), con sus
cortes y adendas, se preserva para trazabilidad; sus cifras antiguas no son nuevas
mediciones ni órdenes de pedir comprobantes, logins, pagos o dominios.

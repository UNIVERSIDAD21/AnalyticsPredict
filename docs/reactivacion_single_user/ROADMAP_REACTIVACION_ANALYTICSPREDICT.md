# Roadmap vigente de reactivación AnalyticsPredict

**Corte consolidado:2026-10-20.** Directiva single-user del propietario del2026-10-05
y órdenes posteriores. Sustituye C0–C7 comercial; no abre evolución avanzada D.
La ejecución detallada se registra en el `PLAN_MAESTRO.md` externo solicitado por
el propietario, sin copiar memoria/configuración del agente al producto.

## Predictor Euroliga integrado — 2026-10-21

[Uso, método y límites](PREDICTOR_EUROLIGA_2026-10-21.md). Pantalla `/euroliga`, API,
Ridge y artefacto propios; probabilidades RAW de cuartos/total de 40 min sin OT,
condicionamiento a Q1–Q3 completos y journal separado. 2.591 finales hasta21oct tras
una alta oficial 90–81 Hapoel–Virtus con rollback/postflight. NBA 2123 intacto.
Euroliga `euro-f9cc361e255b91196acc`, 29 entidades históricas,69 fixtures reconocibles.
EVAL 327/463: MAE total 15,9832 vs media 15,6727; sin superioridad acreditada ni calibración
del refit final. Cohorte 69/0 abstenciones, 63 anteriores por fecha, 0 outcomes; 6 del 22oct
sin hora de kickoff no acreditan prospectiva. 994 backend/42 frontend/lint/build y
visual desktop/móvil aprobados. Sin apuestas/registros NBA ni cron. Funcionalidad
integrada; eficacia NO_CERTIFICADA y no demostrada equivalente a NBA.


## Aplicación puntual de lote WEB — 2026-10-21

El Jefe suministró una matriz de estadísticas y ordenó aplicarla bajo categoría
`WEB`, dejando sin completar los pendientes posteriores. Se registraron
**11.991 valores** en **2.185 partidos**, mediante **2.435 vínculos** y **11.991
observaciones** con autoridad/URL original campo a campo. La matriz indicó cifras
de UEFA.com (7.522), Flashscore (3.624), ESPN (410), APWin (399) y FotMob (36).
Los controles validaron estructura e identidad canónica, no cada cifra contra la
página. Sin solicitudes a esos sitios durante la escritura. Backup privado,
rollback comprobado y postflight READ ONLY: 24.593 finales FT, ahora 2.497 partidos
y 14.153 celdas NULL en las seis métricas; 2.062 completados. El Jefe pidió dejar
el residual tal cual. No se modificaron marcadores, apuestas o modelos; cero modelos
activos. Esta persistencia es una instrucción puntual con datos del propietario, no
certifica las licencias de los proveedores ni autoriza otras recolecciones. Evidencia
privada `Carpeta de Entregas de Borlty/APLICACION_STATS_FUTBOL_WEB_2026-10-21/`.

## Recuperación multi-fuente autorizada20/10

[Resolver y fuentes revisadas](RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20.md):
cliente PitchAPI y resolución campo-a-campo con origen/hash, identidad mapeada,
conflictos en cuarentena y actualización `NULL`-only explícita. Ya se aplicaron
1.374 valores en 234 vínculos fuente-partido, conservando 1.386 observaciones de
procedencia. Censo READ ONLY: 24.593 finales FT, 4.605 con al menos un NULL entre
las seis métricas (26.426 campos), principalmente en copas nacionales y torneos
UEFA. DataHub PDDL completó 2 LaLiga/12 campos; Verona–Roma añadió 1 corner local
0 corroborado por tres fuentes, con backup privado, ensayo rollback y postflight.
El FT canónico 3–0 se preservó; el 0–0 reportado para el partido jugado no se usa
para modificar el marcador y la causa del desacuerdo no se adjudicó. El desfase +5h del
importador SofaScore solo se admite en la excepción ESPN/SofaScore exacta, mismo día
UTC y con equipos/FT/competición concordantes; fechas no se corrigen. Se usaron
cohortes verificadas ESPN, DataHub, Kaggle y HF; no se mezclan definiciones ni se
sobrescriben valores. StatsBomb no halló NULLs objetivo en su muestra. Un mirror HF
es duplicado exacto del ya auditado; otros datasets no aportan métricas o quedan
excluidos por licencia, upstream/robots, bloqueo o procedencia no acreditada. PitchAPI
mantiene cobertura sin probar por falta de clave protegida. Continuar el censo/búsqueda
para los gaps restantes, sin prometer completitud y sin ingestas programadas; cualquier
nuevo lote requiere identidad por partido/campo, NULL-only, backup y postflight. El
cotejo READ ONLY UEFA 2025/26 confirmó gaps solo en clasificatorias de julio/agosto
(55 Champions, 58 Europa, 181 Conference); ESPN Scoreboard no lista eventos UCL en
las fechas de muestra y los 55 candidatos no tienen ID ESPN vinculado. TotalCorner se
excluye por términos contra extracción automatizada y FCStats por su robots.txt
específico para crawlers de IA.

## Nuevo desarrollo ML autorizado19/10

[V4 forma temporal](ML_FUTBOL_FORMA_V4_2026-10-19.md): selección CAL de diseño/alpha,
refit final explícito y nueva cohorte futura, sin alterar V1/V2/V3. Goles/disparos
superan controles exploratorios retrospectivos con96,98%cobertura; NO es eficacia
del modelo final.251capturas futuras por familia,20oct–1dicUTC,0outcomes iniciales.
Córners223/251, techo88,84%<90: bloqueado aun antes de outcomes. No cambiar esta
cohorte tras ver resultados. El siguiente paso es evaluar sus finales reales,
separar calibración probabilística y nueva evaluación antes de promoción/serving.
Sin calendario automático ni activación por CI o MAE;0MLfútbol activos.

## Recuperación de datos enero–octubre cerrada 18/10

[Alcance y controles](ACTUALIZACION_INTEGRAL_DATOS_2026-10-18.md): 2.928 finales
fuente conciliados, 474 altas y 114 actualizaciones de registros/fases. Estados
PROGRAMADO corregidos únicamente con final acreditado; sin duplicar históricos.
La recuperación es puntual para 12 competiciones fútbol, NBA y Euro; no programar
ingestas futuras ni repetir las cohortes aplicadas. Modelos/capturas/outcomes y
apuestas intactos. M03/M12 científicos permanecen abiertos; si se solicita una
nueva evaluación deberá declarar otra cohorte sin alterar V1/V2/V3 congeladas.

## Corte de uso local posterior16oct

[Visual y H12](ARRANQUE_VISUAL_Y_USO_LOCAL_2026-10-16.md): navegación/datos reales,
envío fútbol aislado y NBA interno con corte/fase verificados; audit0/854backend/
36frontend/lint/build. Cierre técnico visual/H12 sujeto a publicación/CI del acta.
15capturas/9outcomesPRE/0independientes; faltan6outcomes en este corte, independencia,
muestra y calibración. H4ticketcerrado por proveedor: bloqueado, sin purga parcial.
Los estados antiguos siguientes se conservan como antecedentes, no bloqueos
actuales del navegador ni permiso para repetir ingestas/capturas/entrenamiento.

## Base cerrada (no repetir)

| Alcance | Evidencia |
|---|---|
| A1–A4: local, retirada comercial, migración/historial | Backup/ensayo/Neon, API/UI sin auth/pagos/tiers; todos los registros deportivos visibles |
| H6/H7 técnico/H10/H11 | Escalas/envelopes corregidos, Python3.12/PG sintético/frontend/Compose en CI |
| NBA dominio/calidad/serving | Selector común válido, artefacto2123 con30NBA,73partidos nuevos; reload no entrena |
| Fútbol datos canónicos | Capturas337/200FT y vínculo explícito a catálogo, idempotencia0/0; histórico conservado |
| Fútbol ciclo ML técnico | Persistencia/activación/loader reparados, JSON verificable, sin modelos/métricas ficticias |
| Fútbol evaluación retrospectiva | Política previa inalterada,618EVAL por familia tras200complementos por mitades; ninguna apta por cobertura/targetcorners |
| KPI/P&L y GET técnicos | [Cierre16/10](KPI_PNL_Y_GET_2026-10-16.md): política monetaria cross-sport/N/D, cohortes/grano, sinTTL,78GET y protección read-only/observabilidad |
| Prospectiva técnica NBA | 12snapshotsPRE inmutables anteriores al inicio; no equivalen a12outcomes ni a certificación |

## Pasada integral posterior del16oct

[Estado de ejecución y continuidad](VALIDACION_ESTACIONAL_Y_FASES_NBA_2026-10-16.md).
Recuperación426finales y calendario163programados aplicados con controles;38casos
retenidos por identidad/horario, no duplicados ni corrección automática. V1noapta;
V2futura163/199porfamilia y36abstenciones, techo81,91%;V3CAL100noalcanza100efectivos.
No tratar el nuevo protocolo ni sus candidatos como permiso de activación.
NBA2finalesPRE añadidos y3congelamientosREG reales, preservando12PRE;0outcomes.
Visual y H4 requieren decisiones de alcance concretas al cierre. H12migración
completa preparada externamente/audit0, pero sigue sin publicar y sin cierrevisual.
No hay acciones futuras programadas ni nuevos bloques de evolución avanzada.

## Pendientes ejecutables del agente

1. **Validación analítica M12:** evaluación descriptiva ejecutada por1.303cohortesraw de2–4pares; cero elegibilidad temporal histórica/calibradasID. Certificación y calibración requieren nuevas cadenas/muestra válidas, no agrupar versiones ni fabricar calibrador.
3. **H12 y visual:** cierre técnico posterior de uso local; ver informe y acta
   final para publicación/CI. No repetir diagnóstico del navegador ya recuperado.
5. **Fuentes:** complemento200finales1T/2T aplicado/verificado; proveedor NBA independiente permitido aún sin acreditar. CBS12/12calendarios y finalprobe no demuestran upstream independiente. No evadir403 ni llamar independientes a dos endpoints ESPN.
6. **Calibración/confidence/odds:** evaluar por versión/deporte/mercado con muestras
   válidas, intervalos y disponibilidad histórica explícita; no fabricar calibrador.
7. **H4 integral:** preflight/backup/ensayo357/357refs realizado,4blobs fuera del ensayo y árboles restantes iguales. Remoto aún con13refsPR/cachés administrados porGitHub; no purga parcial ni contacto no autorizado.

## Dependencias medidas, no tareas humanas genéricas

| Frente | Estado | Condición de reanudación |
|---|---|---|
| Activación fútbol | Sin activo; V4 en evaluación futura, V1/V2/V3 conservadas | V4 goles/disparos96,98%retrospectivo,251predicciones futuras sin outcomes; falta prueba propia/calibración/promoción. Córners techo88,84%<90. No bajar gates ni heredar métricas de desarrollo al refit |
| OutcomesNBA | 9PRE resueltos,6outcomes pendientes en15capturas | Resolver porUUID existente tras evento/final; independencia y muestra siguen sin acreditar; no retrofechar |
| IndependenciaNBA | No acreditada | Proveedor permitido con identidad/instantes/resultados trazables; CDN403 no se sortea |
| P&L sin soportes | No recuperable controlado | Mantener exclusiones/ROI N/D; propietario confirma ausencia, no pedir pruebas inexistentes |
| H4 | Purga integral no acreditada | Alcance completo de refs y verificación de inaccesibilidad, no solo ramas |

**NO CERTIFICADO** permanece vigente. No hace falta recuperar cada apuesta ni
cerrar toda esta deuda para consulta exploratoria local. No hay login/2FA, compra
ni gestión personal GitHub identificada como requisito actual del propietario.

## Evidencias y antecedentes

- [Siete frentes y dependencias](SIETE_FRENTES_2026-10-16.md).
- [Evaluación temporal](EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md).
- [Persistencia ML](PERSISTENCIA_ML_FUTBOL_2026-10-15.md).
- [Operación/prospectiva](OPERACION_Y_PROSPECTIVA_2026-10-15.md).
- [Checklist de uso](CHECKLIST_PREPARACION_USO_2026-10-15.md).
- [Recertificación histórica](RECERTIFICACION_ANALITICA_2026-10-06.md).
- [Roadmap anterior íntegro](../archive/ROADMAP_ANTES_CONSOLIDACION_2026-10-16.md).

Cierre por bloque: objetivo, evidencia, pruebas proporcionales, diff/secretos,
estado/changelog y commit/push sin fuerza. Nunca marcar certificado por CI verde.

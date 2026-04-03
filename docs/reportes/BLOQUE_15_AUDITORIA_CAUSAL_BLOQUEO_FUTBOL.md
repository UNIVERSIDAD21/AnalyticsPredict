# BLOQUE 15 — Auditoría de causa raíz de bloqueo total por mercado (fútbol)

## Resumen ejecutivo
- Snapshot: {'bloqueado': ['CORNERS_1T', 'CORNERS_2T', 'CORNERS_FT', 'CORNERS_LOCAL_1T', 'CORNERS_LOCAL_2T', 'CORNERS_LOCAL_FT', 'CORNERS_VISITANTE_1T', 'CORNERS_VISITANTE_2T', 'CORNERS_VISITANTE_FT', 'DISPAROS_ARCO_FT', 'DISPAROS_FT', 'DISPAROS_LOCAL_ARCO_FT', 'DISPAROS_LOCAL_FT', 'DISPAROS_VISITANTE_ARCO_FT', 'DISPAROS_VISITANTE_FT', 'GOLES_1T', 'GOLES_2T', 'GOLES_FT', 'GOLES_LOCAL_1T', 'GOLES_LOCAL_2T', 'GOLES_LOCAL_FT', 'GOLES_VISITANTE_1T', 'GOLES_VISITANTE_2T', 'GOLES_VISITANTE_FT'], 'laboratorio': [], 'validacion': [], 'promocionable': []}
- Diagnóstico causal: el bloqueo 24/24 se explica principalmente por **volumen resuelto insuficiente** + **tasa de resolución operativa baja** + **demotions automáticos activos**.

## Agrupación de causas raíz
- **resolucion/outcomes**: {'volumen_resuelto_insuficiente': 24, 'tasa_resolucion_operativa_baja': 24}
- **datos/ETL**: {'fallback_alto': 24}
- **monitoreo/gates**: {'datos_incompletos_o_estado_mercado': 24, 'auto_demotion_activo': 24}
- **modelo/features**: {'features_modelado_insuficiente': 24}
- **calibracion**: {'calibracion_fuera_tolerancia': 9}

## Ranking de rescate (más rescatable -> menos)
1. CORNERS_1T (score=0.428)
2. CORNERS_LOCAL_1T (score=0.428)
3. CORNERS_LOCAL_2T (score=0.428)
4. CORNERS_LOCAL_FT (score=0.428)
5. CORNERS_VISITANTE_1T (score=0.428)
6. CORNERS_VISITANTE_2T (score=0.428)
7. CORNERS_VISITANTE_FT (score=0.428)
8. CORNERS_2T (score=0.4244)
9. GOLES_LOCAL_1T (score=0.3563)
10. DISPAROS_LOCAL_ARCO_FT (score=0.3532)
11. DISPAROS_VISITANTE_ARCO_FT (score=0.3532)
12. DISPAROS_ARCO_FT (score=0.353)
13. DISPAROS_VISITANTE_FT (score=0.3499)
14. DISPAROS_LOCAL_FT (score=0.3371)
15. GOLES_VISITANTE_2T (score=0.3205)
16. CORNERS_FT (score=0.2535)
17. GOLES_VISITANTE_FT (score=0.2304)
18. DISPAROS_FT (score=0.217)
19. GOLES_FT (score=0.16)
20. GOLES_1T (score=0.1212)
21. GOLES_2T (score=0.1212)
22. GOLES_LOCAL_2T (score=0.1212)
23. GOLES_LOCAL_FT (score=0.1212)
24. GOLES_VISITANTE_1T (score=0.1212)

## Recomendación de foco (siguiente fase, máximo 2-3 mercados)
- Prioritarios: CORNERS_1T, CORNERS_LOCAL_1T, CORNERS_LOCAL_2T
- Estrategia: concentrar ingesta/resolución/outcomes y cobertura de líneas solo en estos mercados durante 2 ventanas de monitoreo antes de expandir.

## Tabla causal por mercado
| Mercado | Estado | Causas principales |
|---|---|---|
| CORNERS_1T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_2T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_FT | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_LOCAL_1T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_LOCAL_2T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_LOCAL_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_VISITANTE_1T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_VISITANTE_2T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| CORNERS_VISITANTE_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_ARCO_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_FT | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_LOCAL_ARCO_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_LOCAL_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_VISITANTE_ARCO_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| DISPAROS_VISITANTE_FT | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_1T | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_2T | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_FT | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_LOCAL_1T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_LOCAL_2T | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_LOCAL_FT | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_VISITANTE_1T | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_VISITANTE_2T | BLOQUEADO | auto_demotion_activo, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |
| GOLES_VISITANTE_FT | BLOQUEADO | auto_demotion_activo, calibracion_fuera_tolerancia, datos_incompletos_o_estado_mercado, fallback_alto, features_modelado_insuficiente, tasa_resolucion_operativa_baja, volumen_resuelto_insuficiente |

## Riesgos residuales
- Con volumen actual, cualquier mejora de métricas puntuales puede ser estadísticamente frágil.
- Sin fortalecer resolución de outcomes y cobertura de líneas, el gate seguirá bloqueando mercados aunque UI/contrato estén limpios.

## Siguiente frente técnico con foco
1) Resolver pipeline de outcomes/resolución para elevar tasa resuelta por mercado.
2) Aumentar coverage de líneas en mercados priorizados.
3) Re-correr walk-forward + monitoreo en 2 ventanas consecutivas y reauditar.
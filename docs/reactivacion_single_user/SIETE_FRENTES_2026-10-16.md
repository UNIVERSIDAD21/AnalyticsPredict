# Ejecución de los siete frentes — 2026-10-16

Orden del propietario: «Bien hazlos todos». Se trabajaron los siete frentes;
**no están todos cerrados**, por las dependencias medidas abajo. No se equipara
un diagnóstico, una CI verde o una evaluación retrospectiva con certificación.

## Datos y aptitud fútbol (M09/M03)

Se recuperaron goles y córners 1T/2T en **200/200 finales ESPN ya vinculados**.
Goles: dos linescores explícitos; córners: jugadas tipadas de cronología completa,
IDs/periodos/equipos exactos, límitesUTC y reconciliación conFT. No se imputa
un reparto desdeFT ni se interpreta texto libre para asignar periodos.

Aplicación respaldada tras CI verde y ensayo real con rollback: una transacción
DDL+DML añade evidencia separada y completa ocho campos por partido. Segunda
aplicación 0/0; postflight independiente200/200. FT/tiros/identidades, capturas y
vínculos originales, apuestas, predicciones, modelos y12 snapshots inmutables
permanecen íntegros según huellas. No se toca datos_completos para forzar aptitud.
El trigger canónico deriva `datos_corners_completos`:200 false→true. El primer
postflight detuvo la evaluación por no contemplar ese flag; se reconcilió contra
backup, regla del trigger y huella global sin escritura adicional. Se conserva
el fallo original y se añadió la prueba SQL con trigger. No se ocultó la incidencia.
No se repiten ingestas históricas ni congelamientos NBA.

La nueva evaluación conserva política SHA256
`cf466ed77a57181a9596956fbcb2085c074d07315ee4a7704ee25a63a2afa11a`. CAL es selección de alpha, no calibrador probabilístico.
La disponibilidad histórica del dataset sigue sin acreditarse. Los 200 partidos
actualizados cambian cohortes: no atribuir mejora comparando MAE de cohortes distintas.

| Familia | Partidos EVAL | MAE / baseline | IC95 deltaMAE | Cobertura | Gate pendiente |
|---|---:|---:|---|---:|---|
| corners | 618 | 1.3960 / 1.4228 | [-0.04710; -0.00643] | 79.13% | COBERTURA_INSUFICIENTE, TARGET_PEOR_QUE_BASELINE |
| goles | 618 | 0.6671 / 0.6889 | [-0.03001; -0.01347] | 79.13% | COBERTURA_INSUFICIENTE |
| disparos | 618 | 2.6791 / 2.9067 | [-0.30501; -0.15369] | 79.13% | COBERTURA_INSUFICIENTE |

Se censaron también las cinco ligas en junio/julio/agosto:15 lotes válidos,
**97 finales en agosto y cero en junio/julio** en esta fuente. Incluso antes de
excluir equipos/targets,97 < 100 CAL mínimo para septiembre. 96 de los 97 finales pasan el contrato completo de mitades; uno se rechaza porque
sus córners no concilian. Esa captura adicional
se conserva fuera de Neon, sin DML: no puede resolver el gate y no se baja el
mínimo ni se elimina la ventana tras medir. Ver M09_FUENTES/HUECO_CAL/RESUMEN.json.

La decisión depende de TODOS los gates, no solo del MAE. Ventanas sin CAL y equipos
fuera de TRAIN se excluyen y cuentan. No se rebajan umbrales tras medir; no se
activa una familia no apta. Ver actaM03 y reporte por ventana, no solo el agregado.

## Ciencia y prospectiva (M12/M11)

Evaluación ejecutada:1.303 cohortes raw separadas por deporte/mercado/modelo/origen,
1.279 NBA + 24 fútbol, **2–4 pares por cohorte**. Brier/logloss/ECE e ICbootstrap por
partido son descriptivos; baseline p=0,5 de igual cohorte. Ninguna cohorte calibrada
con ID válido, cero pares básicos temporales fútbol y cero cadenas históricas NBA
certificables (2.136 inválidas, 476 ambiguas, 322 indeterminadas). No se fabrica un
calibrador ni se mezclan versiones para aparentar muestra. Confianza/cuotas de
bitácora no acreditan eficacia; P&L permanece N/D sin soportes.

12 snapshots PRE / 0 outcomes; hashes y orden fit<freeze<inicio intactos. Inicios16/10
23:00 UTC→17/10 02:30 UTC (16/10 18:00–21:30 Bogotá); no son horas de finalización.
Esperar resultados reales es una dependencia temporal, no una prueba omitida.
CBS coincide12/12 en calendario y permite extraer cuartos reconciliados de un
FINAL de prueba del día 15; publicación distinta, **upstream no acreditado**.
No se insertó ese partido de prueba como outcome de la cohorte.

## Mantenimiento, visual e historial (M06/M08/M10)

| Frente | Trabajo realizado | Límite y condición de cierre |
|---|---|---|
| H12 | Auditoría fresca: 5 altas dev / 0 prod; braces 3.0.3 sin parche publicado | Tailwind 4 major exige migración y revisión visual hoy bloqueada; no ocultar auditoría ni publicar control omitido |
| Visual | Browser gestionado/CDP/doctor sanos, apertura local reproduce rechazo | `browser navigation blocked by policy`; sin cambios globales, evasión ni smoke visual acreditado |
| H4 | Backup privado/bundle verificado; ensayo357/357 refs, 4 blobs fuera, árboles restantes iguales | Remoto conserva12 heads + 13 refs PR contaminadas; refsPR/cachés requieren vía GitHub soportada. Sin purga parcial ni contacto a terceros |

## Estado de cierre

- M09 fútbol: complemento por tiempos aplicado y verificado; no equivale a cerrar
  independencia NBA ni acreditar disponibilidad histórica.
- M03: decisión según gates medidos en tabla; ninguna activación por intuición.
- M12: evaluación descriptiva terminada; certificación/calibración pendientes de
  nuevas cadenas/muestra elegibles. No rentabilidad ni rendimiento futuro prometidos.
- M11: espera de eventos; no se programaron acciones futuras ni notificaciones.
- M06/M08/M10: controles/ensayo realizados, cierres globales aún bloqueados como se
  documenta arriba. No son tareas genéricas del Jefe ni falta de autorización humana.

Evidencia externa: `CIERRE_SIETE_FRENTES_2026-10-16`, actas por frente, raw de fuentes,
hash de backup/rollback/postflight/huellas, política/snapshot/reporte, auditoría yCI.
Dictamen global: **NO CERTIFICADO**. Producto mantiene política NBA interna sin
picks, stakes ni recomendaciones. P&L sin soportes conserva exclusión/N/D y filas.

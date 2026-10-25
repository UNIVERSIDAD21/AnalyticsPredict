# WNBA: recorrido NBA compartido y calendario de tres meses

## Uso y alcance

URL local: <http://127.0.0.1:5173/baloncesto?liga=wnba>.
La configuración utiliza `FormularioAnalisis`, la cabecera NBA extraída sin
reducirla y `ResultadoAnalisis`. Se elimina el resultado alternativo WNBA.
No se utiliza `SeccionesAnalisisIntegral` como sustituto: no es el recorrido NBA
normal. El selector conserva la liga al recargar y desmonta el estado incompatible;
peticiones abortadas/tardías no reemplazan el análisis de otra liga.

Equipos, estadísticas, temporadas anuales, calendario, contextos y journals WNBA
tienen contratos propios. Temporadas seleccionadas, fases y corte exclusivo
afectan medias, dispersión, OT y descriptivos; las cachés incluyen todo el alcance.
Un fixture POST incorpora REG/POST sin añadir una segunda configuración visible.
No se utilizan pesos, calibradores ni políticas de score/sizing NBA o Euroliga.

## Matriz de producto y aceptación

| Recorrido NBA / orden | WNBA / origen | Verificación |
|---|---|---|
| Marco de uso, Análisis y Estadísticas | Cabecera común; identidad WNBA | Navegación/recarga y DOM |
| Partido, Actualizar, seleccionar/cambiar | Selector común; fixtures WNBA con revisión | Ventana móvil, API y PostgreSQL sintético |
| Local, visitante y estadísticas rápidas | UUID/catálogo y finales WNBA | Sin llamadas de catálogo/temporadas NBA |
| Mercado, línea, lado, resumen | Mismos componentes y orden | Paridad de controles/clases por modo |
| PRE/cierre Q1/Q2/Q3; marcadores por cuarto | Mismos controles; condicional WNBA | Contradicciones/mercados resueltos rechazados |
| Temporadas, todas/limpiar | Chips comunes; anuales WNBA | Selección efectiva, caché y límites temporales |
| Cuotas Over/Under y margen | Misma visibilidad PRE; sin cuotas en cortes | Sin/una/dual; margen N/D sin opuesta |
| Analizar, limpiar, vacío/carga/error | Mismos componentes | Invalidación y respuesta tardía |
| Advertencias, estado, encuentro y selección | Renderer común; RAW y traza WNBA | Sin pantalla de diagnóstico adicional |
| Ganador, probabilidades, proyecciones | Distribución WNBA por mercado | Observados fijos; suma de masas y ganador |
| Impacto/ajustes | Intercepto Ridge frente a identidad/localía | Descomposición, no segundo ajuste |
| Valor, de-vig, score, sizing/calibración | Campos comunes; EV/push; políticas no validadas N/D | Conserva desglose, sin confianza/stake inventados |
| H2H, forma, descanso y razones | Finales propios del alcance | Métrica/periodo coincidentes; descanso N/D sin fecha |
| Historial detallado, filtros y sede | Endpoint WNBA con análisis/snapshot original | No cambia al llegar resultados nuevos |
| Guardar y combinadas | Misma UI; validadores y conjunta WNBA propios | Escritura solo en PG sintético; revisión obsoleta bloqueada |
| Escritorio/móvil | Mismos layouts/clases | Capturas auténticas 1440/390 y medición de overflow |

La igualdad es de campos, componentes, orden y reglas según disponibilidad, no
de cifras ni de afirmaciones estadísticas. RAW reemplaza la etiqueta calibrada;
score/stake/confianza sin política WNBA validada conservan sus campos con N/D.
Una media línea no añade tarjeta push vacía (masa exactamente cero); la línea
entera conserva la masa push calculada. Las diferencias de duración/OT, muestras,
estado de calendario y procedencia se informan en los espacios comunes.

## Convenciones y motor ampliado

`NBA_EQUIVALENTE_V2` ofrece PRE y cierres de Q1–Q3. PRE Juego completo incluye OT;
los cuartos son de diez minutos y no incluyen OT. El total de regulación de 40
minutos permanece separado. Los cortes Juego completo son regulación sin OT,
como el recorrido NBA; no se anuncian como estimación con reloj/posesiones.

Los puntos recibidos son de cada cuarto terminado, no acumulados. La normal
multivariada WNBA se condiciona mediante Schur, fija observados y reduce la
covarianza a lo pendiente. Se integra con Sobol determinista (32.768 muestras),
redondeo entero y censura en cero. Solo los empates a 40 minutos reciben un
incremento OT remuestreado de empates WNBA reconciliados del mismo alcance;
requiere diez casos. Sin muestra suficiente se abstiene, sin fallback ni 50%.
Ganador corresponde al periodo y admite empate donde el contrato lo permite.

La publicación de datos/Ridge v1 `wnba-v1-912782c821ae18d8895a723a` se conserva.
Cada cálculo ampliado tiene ID `wnba-v2-<hash>` independiente. El contrato v1
continúa disponible por API; sus métricas no se atribuyen a v2.

### Evaluación nueva

Protocolo previo: [protocolo](PROTOCOLO_WNBA_PARIDAD_2026-10-25.md).
Candidato `wnba-v2-candidato-f0ab74e63033bb3e67bea950`: TRAIN REG 2019–2023,
984 partidos; CAL dispersión 98 en 2024; 43 OT TRAIN. EVAL REG 2025–2026,
616 elegibles, 450 evaluables y 166 abstenciones por modo (73,05% de cobertura).
Son 1.800 proyecciones sobre los mismos 450 partidos, no 1.800 partidos distintos.

| Total / modo | MAE candidato | MAE referencia |
|---|---:|---:|
| PRE (con OT) | 15,7171 | 15,7745 |
| Cierre Q1 | 12,5035 | 12,6653 |
| Cierre Q2 | 10,5566 | 10,1866 |
| Cierre Q3 | 7,2017 | 7,1461 |

3.600 comparaciones reproducidas (modelo y referencia), fitting prohibido y
diferencia máxima cero. Cohortes, Brier/log-loss/cobertura por mercado y bundle
fuera del producto. No hay superioridad general, calibración ni prospectiva
acreditada; retrospectiva exploratoria sobre datos ya observados. Las métricas
no validan el refit solicitado por temporadas ni su dispersión transferida.

## Calendario comprobado

Ventana inclusiva 25/10/2026–25/01/2027: 93 días locales; 95 consultas de días
ESPN incluyendo las dos guardas UTC/COT. Tres eventos corroborados con páginas
oficiales: 401918309/310/311, juegos WNBA 1042600305/306/307.

| Fecha COT, 19:00 | Local | Visitante | Condición publicada |
|---|---|---|---|
| 26/10/2026 | Golden State Valkyries | Atlanta Dream | Publicado |
| 29/10/2026 | Atlanta Dream | Golden State Valkyries | Publicado |
| 31/10/2026 | Golden State Valkyries | Atlanta Dream | Si es necesario |

La consulta directa de calendario oficial devolvió 403 y se conservó como fallo,
no como lista vacía. Se corroboraron páginas oficiales de juegos, fechas clave
y cuadro. No se acredita publicación íntegra del calendario oficial 2027 ni se
infiere que una lista vacía demuestre que no habrá partidos. La comprobación
fechada/procedencia/límites se muestra en el selector.

Migración propia: fixtures sin puntos, revisiones inmutables y comprobaciones;
`apuestas.fixture_wnba_id` mantiene el vínculo antes de existir el resultado
canónico. La importación final validada enlaza el mismo fixture y sus selecciones.
Reprogramación/aplazamiento/cancelación son revisiones; no se sobrescribe un final
válido sin revisión expresa. Respaldo restaurado, ensayo rollback y aplicación
previos a la reanudación: tres altas. Repetición con guardas: cero altas/revisiones.

## Actualizaciones: tres operaciones separadas

1. **Calendario:** cargar pantalla consulta BD. **Actualizar** ejecuta sincronización
   explícita con fuente, ventana móvil de tres meses y evidencia privada,
   respaldo/ensayo/aplicación/postflight. No trae resultados ni ajusta modelos.
   Alternativa CLI, desde raíz del repositorio:

   ```bash
   backend/.venv/bin/python backend/scripts/sincronizar_calendario_wnba.py \
     --salida /ruta/externa/nueva-consulta
   ```

   Sin `--aplicar`, solo plan. Tras revisión, reutilizar `--reporte consulta.json`
   con `--aplicar` y otra salida NUEVA. No repetir operaciones aplicadas.
2. **Resultados:** scraper WNBA independiente genera un lote local nuevo;
   `backend/scripts/importar_wnba.py` valida hashes, ensayo/rollback y respaldo
   antes de `--aplicar`. `--help` documenta argumentos exactos. Los FT válidos
   enlazan fixture/resultado; no se inventan finales desde el calendario.
3. **Modelo WNBA:** después de la ingesta verificada, ejecutar expresamente
   `backend/scripts/gestionar_predictor_wnba.py --corte FECHA --salida RUTA_NUEVA
   --publicar` con el Python del backend. Publica solo WNBA; crea artefactos
   distintos y no convierte la retrospectiva v2 en evidencia prospectiva.

No hay cron, refresco live automático, lesiones/viajes/sedes neutrales modelados,
ni nuevas apuestas reales. Cuotas son manuales. Cortes son solo consulta; pruebas,
manuales e históricos no permiten guardado oficial. El guardado PRE exige fixture
futuro vigente, snapshot exacto, probabilidad intacta y revisión actual bajo lock.
Combinadas WNBA usan conjunta propia dentro de fixture, pushes y supuesto de
independencia entre fixtures; no aceptan mezcla de ligas ni factores NBA.

## Evidencias

Entrega externa `PARIDAD_EXACTA_WNBA_2026-10-25`: matriz detallada, bundle v2,
cohortes/reproducción, calendario/raws, backup/rollback/postflight, pruebas,
capturas y manifiesto. Formularios NBA/WNBA son de aplicación real sin submit.
Resultados comparativos: banco externo rotulado; NBA con pesos y contexto de UI
sintéticos, WNBA con respuestas reales archivadas de prueba. No constituyen
una ejecución productiva NBA. Las capturas no se editan ni se generan por IA.
El acta externa registra los controles finales y el SHA/CI exactos de publicación.

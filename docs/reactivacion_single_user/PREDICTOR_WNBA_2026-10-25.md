# WNBA integrada en Baloncesto — 2026-10-25

## Uso local

URL: http://127.0.0.1:5173/baloncesto?liga=wnba . API propia `/api/wnba`.

1. En Baloncesto elige **WNBA**. La URL conserva la liga al recargar/compartir.
2. Selecciona temporadas anuales y corte exclusivo en hora Colombia. REG es base;
   puedes incluir POST. El selector histórico permite reconstruir un análisis previo
   al encuentro; si no hay calendario próximo, usa dos equipos manualmente.
3. Elige equipos, Q1–Q4 o total de regulación y línea. Cuotas opcionales, nunca
   stake sugerido. Pulsa **Analizar Partido**.
4. Revisa probabilidades RAW, muestra, puntos, dispersión, advertencias y
   Trazabilidad. Historial WNBA reabre la misma salida sin repetir el cálculo/POST.
5. Estadísticas y validación muestra el candidato evaluado, su referencia y bins.

No se inventaron próximos partidos. Se observaron cero fixtures próximos utilizables
al cierre. Simulaciones y reconstrucciones históricas son consultables, pero no se
registran como pronósticos oficiales de encuentros inexistentes. La bandera
`es_prueba` conserva los ensayos separados de cualquier futura evaluación prospectiva.
Cambiar de liga desmonta el módulo, aborta solicitudes e ignora respuestas tardías.

## Datos observados y elegibilidad

Se verificó mediante SQL READ ONLY el lote existente, no se volvió a consultar ESPN:
2.098 filas fuente, 2.088 finales canónicos, 21 participantes de ingesta, 8 temporadas.
El catálogo analítico contiene **15 equipos de liga**, no invitados de PRE.
Diez no finales permanecen en fuente; 8 cuarentenados nunca pasan al modelo.
Finales elegibles: **1.840 REG + 157 POST = 1.997**. Se excluyen 85 PRE y 6 COPA.
La copa final no duplica REG. No se acredita calendario histórico completo por el
solo hecho de terminar un barrido ESPN. Tampoco hay contraste independiente añadido.

| Temporada anual | REG | POST optativo |
|---|---:|---:|
| 2019 | 204 | 16 |
| 2020 | 132 | 15 |
| 2021 | 192 | 17 |
| 2022 | 216 | 23 |
| 2023 | 240 | 20 |
| 2024 | 240 | 22 |
| 2025 | 286 | 24 |
| 2026 | 330 | 20 |

Elegible exige fuente WNBA/ESPN, final completo, canónico válido y fase coincidente,
8 cuartos enteros no negativos, reconciliación exacta con original/OT/FT, IDs propios,
fecha UTC con zona y temporada anual. NULL nunca se convierte en cero. Faltantes
estadísticos de boxscore no se imputan: esta versión usa puntos por cuarto, no esas
métricas opcionales. Regulación y OT permanecen separadas en historial y fuente.

El corte es un **día COT exclusivo**: se excluye entero el día del encuentro porque
no se dispone de timestamp histórico de publicación del FT. Fechas/horas oficiales
se conservan UTC y se muestran en Colombia. Para histórico se rechaza un corte
posterior al inicio; no entran el propio partido ni los siguientes en ajuste,
recencia, dispersión o descriptivos. Este es histórico reconstruido con la BD
actual, no prueba de que cada dato/corrección estuviera publicado en su día.

## Modelo y contrato numérico

Ridge WNBA multisalida, alpha 5 fijo, intercepto no penalizado, ataque y defensa
por equipo y localía nominal del fixture. No carga pesos/escalas NBA o Euroliga.
No modela sedes neutrales, viajes, burbuja 2020, lesiones o posesiones; 2020 es
seleccionable y esa limitación importa al interpretar la localía nominal.

Ocho objetivos de regulación (4 por lado). Mínimos: 120 encuentros por alcance,
60 TRAIN iniciales, selección temporal y >=40 residuos de dispersión; cada equipo
requiere >=8 partidos y >=6 efectivos Kish. Equipos nuevos sin soporte se abstienen
con motivo, no reciben 50 %. Recencia uniforme/semivida365/730 se elige por MAE
solo en la partición de selección pasada, misma cohorte entre variantes. En el
serving completo REG se seleccionó semivida365 días; no se fija para otras ventanas.

Cada petición vuelve a ajustar **solo** sus temporadas/fases/corte sobre snapshot
WNBA publicado. La selección afecta coeficientes, muestras, recencia y dispersión.
Caché LRU16 incluye publicación, huella, temporadas, fases, corte y filas exactas.
No muta el artefacto ni otra petición. Se rechazan IDs de temporadas/equipos ajenos.

La matriz 8×8 de errores temporales usa segundo momento (incluido sesgo), shrinkage
0,1 hacia diagonal y regularización1e-6. Varianza de total es `aᵀΣa`, con covarianzas
entre equipos/cuarto; no suma ingenua de sigmas. Tras estimarla en pasado se hace
refit final: transferir esa dispersión no demuestra calibración del refit.

Probabilidades por normal redondeada/discreta censurada en cero. Over/Under/push
suman1 con tolerancia1e-12; media línea no tiene push, entera sí tiene masa exacta
(que puede redondear visualmente a0). Línea0 no asigna Under a puntos negativos.
Se validan valores finitos/rangos. Ganador de regulación tiene local/empate/visitante,
no moneyline con OT. EV opcional respeta devolución push y no produce recomendaciones.

**Disponibles:** Q1–Q4 y total40min, manual/histórico/prepartido oficial cuando
haya fixture elegible. Ganador3vías como salida complementaria. **No disponibles:**
OT incluido, posesiones/reloj/en vivo/cortes observados. La API rechaza modo live,
la UI no lo ofrece. N/D/abstención no se sustituye por modelo ajeno.

## Publicación y evaluación temporal

- Publicación local: `wnba-v1-912782c821ae18d8895a723a`.
- Snapshot: `ab3ed6fe0efd600c6ace9f8222f2d03d1d7ea65bc9a2acaa5b3153af6f951176`.
- Candidato evaluado: `wnba-candidato-dc88ccc690ba65e6841e`.
- Artefacto propio `~/.local/share/analyticspredict/wnba/activo.json`, versiones
  inmutables en `versiones/`, journal propio `analisis/`.
- El bundle conserva datos normalizados, pesos exactos del candidato y refit,
  matriz de dispersión, cohortes evaluadas/rechazadas, métricas y protocolo.
- Se reprodujeron las450 proyecciones del candidato recargado con fitting prohibido:
  diferencia máxima0. No se atribuyen esas métricas a los ajustes finales/por temporadas.

Protocolo fijado antes de medir: TRAIN2019–2023 (984REG), CAL selección142REG
2024-01-01–2024-07-15, CAL dispersión98REG 2024-07-15–2025-01-01; EVAL2025–2026.
El candidato seleccionado usa semivida730 y conserva pesos TRAIN, no refit EVAL.
Referencia media por objetivo del mismo TRAIN y dispersión de sus errores en el
mismo CAL. No se probó una lista abierta de variantes ni se escogió con EVAL.

EVAL616 partidos 2025-05-16–2026-09-24:450 analizados y166 abstenciones (equipos
nuevos/muestra insuficiente), cobertura73,05 %. Referencia y modelo comparten esos
450 casos. Retrospectiva exploratoria, cero resultados prospectivos acreditados.

| Mercado | N | MAE WNBA | MAE referencia | Brier WNBA | Brier referencia |
|---|---:|---:|---:|---:|---:|
| Q1 | 450 | 6.4722 | 6.4462 | 0.5023 | 0.4960 |
| Q2 | 450 | 5.7888 | 5.9181 | 0.4818 | 0.4987 |
| Q3 | 450 | 6.5221 | 6.5044 | 0.5076 | 0.5044 |
| Q4 | 450 | 6.9862 | 6.9210 | 0.5122 | 0.5038 |
| COMPLETO | 450 | 15.2951 | 15.3209 | 0.4881 | 0.4928 |

Total: log loss0,6809; Brier con push en línea162=0,5288,15 pushes observados.
Brier multiclase es suma de errores cuadrados en Over/Under/push (no Brier binario
re-escalado). La media línea161,5 y entera162 se fijan desde media TRAIN, no desde
cuotas reales ni optimizando EVAL. El informe guarda cada mercado/línea/bins.
Intervalo nominal80 % cubrió76,67 % del total. Bins muestran desajustes (por ejemplo
probabilidades medias45,1 % frente a frecuencia61,5 %, n143). **No hay superioridad
general acreditada**: la diferencia MAE total es pequeña y Q1/Q3/Q4 no superan la
referencia en MAE. Todos los porcentajes, ganador e intervalos siguen **SIN CALIBRAR**.
Un70 % estimado no equivale a70 % de precisión demostrada. POST, alcances distintos,
ganador3vías y el refit final no tienen evaluación prospectiva específica certificada.

## Persistencia, aislamiento y recuperación

No se requieren migraciones nuevas ni DML para esta integración: el esquema de la
ingesta ya basta. Lecturas de catálogo/análisis usan transacciones READ ONLY. La
única persistencia de análisis es journal local WNBA exclusivo, no tablas NBA ni
operaciones financieras. Fallo del modelo WNBA responde503 recuperable, sin fallback.

La bitácora admite código WNBA y resuelve total en regulación. Guardado solo por
acción explícita sobre análisis oficial previo vigente con ID canónico, trazabilidad
exacta y probabilidad RAW coincidente. Manual/histórico/prueba no habilitan guardado.
Actualmente no hay fixture futuro canónico: el control queda deshabilitado, sin
fabricar partidos ni exigir puntos para convertir programados en finales.

Los modelos/journals ajenos y archivos de scrapers WNBA/MLS se preservan mediante
huellas. No se entrenó, activó ni calibró NBA/Euroliga/fútbol. La identidad de equipos,
versiones, temporadas y caché permanece separada. El helper SQL compartido de Euro
es exclusivamente infraestructura de conexión READ ONLY, nunca sus parámetros.

## Actualizar únicamente WNBA

1. Incorporar resultados nuevos mediante el contrato local documentado en
   [Ingesta WNBA](INGESTA_WNBA_2026-10-25.md), con validación de hashes, backup,
   recuperación y ensayo antes de cualquier DML. No hay ingesta remota implícita.
2. Ejecutar desde la raíz del repo, con la configuración habitual `backend/.env`;
   usar un directorio de entrega **nuevo** y sustituir fecha/corte por los deseados:

```bash
backend/.venv/bin/python backend/scripts/gestionar_predictor_wnba.py \
  --corte 2026-10-25 \
  --salida "/home/erik-fuentes/AnalyticsPredict/Carpeta de Entregas de Borlty/REFIT_WNBA_2026-10-25/ejecucion_nueva" \
  --publicar
```

Sin `--publicar` produce bundle/informe fuera del producto sin cambiar el activo.
La salida es exclusiva (no sobreescribe reportes); la publicación es atómica y
conserva versión anterior. Reversión: restaurar **solo** la copia WNBA previa del
activo/versiones, no modelos ajenos. La versión actual no requiere reinicio: cada
análisis lee el puntero WNBA. Revisar hash BD, alcances y evaluación antes de usar.
No hay cron ni reajustes de otras ligas. Si cambia el contrato matemático hay que
versionar FORMATO y repetir validación; no reciclar métricas del candidato anterior.

Si la BD cambia (incluso corrección antigua sin nueva fecha máxima), el catálogo y
los análisis avisan que difiere del snapshot. Se muestra último final BD y último
dato **utilizado** por separado; >30d sin dato utilizado también advierte.

## Evidencia y pruebas

Entrega privada externa `INTEGRACION_WNBA_BALONCESTO_2026-10-25`: snapshot READ ONLY,
protocolo previo, bundle/evaluación, reproducción exacta, logs unitarios/globales,
frontend/lint/build, tres análisis reales marcados de prueba, capturas auténticas
1440/390, hashes ajenos y postflight. No reemplazar este material por mocks.

La comprobación local incluye selecciónWNBA → equipos/temporadas → análisis real →
resultado/traza → historial sin nuevoPOST → cambiar NBA/Euro → volverWNBA sin estado
arrastrado. La suite sintética verifica aislamiento SQL/READ ONLY, NULL≠0, corte,
seasons efectivas, incertidumbre correlacionada, push, abstenciones, modelo ausente,
historial, guardado explícito y respuestas tardías. Métricas/pruebas de la ejecución
final y commit exacto constan en el acta externa; no certificar el rendimiento futuro.

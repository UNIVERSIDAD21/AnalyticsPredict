# Misma distribución, línea y origen — 2026-10-30

Revisión L05 sobre código vigente. No nuevos porcentajes para partidos reales,
entrenamiento, calibrador, publicación de modelos o escrituras deportivas.

## Hallazgo de presentación y corrección

La tarjeta compartida podía priorizar `probabilidad_over` base y al mismo tiempo
`prediccion_ajustada.media_ajustada` o media de un candidato. Esos parámetros no
describen necesariamente el mismo porcentaje. Se corrigió la selección **NBA**:

- Mercado/línea principales proceden de la selección de consulta, no de un
  candidato alternativo. Los parámetros, Over y Under provienen juntos de la
  `prediccion` del mercado original. No se complementa un lado ausente.
- La tarjeta identifica **Base NBA RAW** o **corte heurístico RAW** sin reloj.
  El escenario contextual y la evaluación de candidatos continúan separados,
  identificados con sus propias medias/probabilidades; no se mezclan sus cifras.
- Si el usuario selecciona otra línea sin una nueva respuesta, los porcentajes
  quedan N/D. El comparador separado no cambia el resultado/selección originales.
- La serialización añade `metadata.contrato_probabilidad`: familia continua,
  mercado/línea, RAW, origen,48min sinOT, masa de push y motivo de ausencia. Se
  copia metadata: ni el objeto en memoria ni valores legacy se reescriben.
  PRE, corte e histórico conservan su cálculo y efectos originales.

## Líneas, push y origen por dominio

- NBA continuo: las líneas .5 separan eventos enteros sin push. En enteras u
  otras fracciones no se acredita una distribución discreta: porcentaje del
  evento/push N/D en la presentación, conservando media y desviación. Los campos
  legacy numéricos API permanecen por compatibilidad, **no representan una masa
  discreta certificada**. No se transforma la CDF continua en una PMF inventada.
- Fútbol legacy: si una línea entera no conserva push, la tarjeta principal y el
  comparador indican liquidación N/D. No se presenta el Under complementario
  como probabilidad estricta de quedar por debajo con push separado. El snapshot
  conserva sus valores originales para auditoría; no se reescriben journals.
- Euroliga conserva su normal discretizada y push real del contrato; WNBA su
  integración discreta conOT cuando el mercado/alcance lo soportan. No heredan
  la normal continua NBA ni una convenciónOT ajena.
- RAW, escenario heurístico y calibrador identificado no equivalen a fiabilidad
  certificada. La eficacia del refit sigue sin evaluación independiente propia.

La interfaz no habilita guardar una apuesta desde la selección incompatible.
Esto no elimina ni altera endpoints/registros legacy: los consumidores API deben
usar el contrato explícito y no inferir liquidación de campos históricos ambiguos.
No se modifica política de activación ni se promete rendimiento.

## Pruebas

399 backend aprobadas conPG18 sintético/0omitidas. La serialización conserva
exactamente media/probabilidad y no muta metadata; el corte mantiene su origen.
Frontend verifica desacuerdo deliberado entre base/contexto/candidato, selección
de otra línea, lado ausente y entero sin push. La tarjeta recibe valores del mismo
origen; enteras incompatibles no muestran una liquidación ni acción de guardado.
Conteo definitivo, lint/build, integración y CI constan en recibo externo
`CONTRATO_PROBABILIDAD_NBA_2026-10-30`.

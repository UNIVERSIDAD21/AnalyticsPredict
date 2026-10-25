# Protocolo previo: paridad WNBA, cortes y prórroga

Declarado antes de medir la ampliación. El candidato regulación v1 y sus cohortes
no se reemplazan. No se emplean parámetros NBA/Euroliga.

## Referencia de producto

`PaginaPrincipal`, `FormularioAnalisis`, `ResultadoAnalisis`, `SelectorPartido` y
sus componentes importados constituyen la referencia, inspeccionada en código y
navegador el 25/10. Se reutilizan estructura, orden, filtros y reglas de visibilidad.
No se usa `SeccionesAnalisisIntegral` como resultado alternativo: NBA no lo utiliza
en su recorrido normal. Los contratos WNBA se adaptan al renderer NBA.

## Ampliación matemática RAW

Ridge y covarianza WNBA v1 se preservan. Para Q1–Q3 terminados se condiciona la
normal multivariada mediante el complemento de Schur. Se fijan ambos puntos de
cada cuarto observado; solo lo pendiente conserva varianza. No se usan FT reales,
reloj, posesiones ni calibradores. Se abstiene ante medias condicionales negativas.

El prepartido COMPLETO incluye OT, como el mercado NBA; el corte COMPLETO ofrece
regulación, como el corte NBA. La regulación de 40 minutos se conserva por separado.
Se integra la distribución conjunta con Sobol determinista (2^15 muestras, seed
WNBA fija), redondeo a puntos enteros y censura en cero. Solo las simulaciones con
empate de regulación reciben OT. Su incremento conjunto se remuestrea del historial
WNBA empatado a 40 minutos, con al menos 10 partidos y OT final reconciliado.
No se añaden puntos OT a partidos sin empate. Se conservan ganador y push por mercado.
La aproximación numérica no es calibración ni evidencia prospectiva.

## Evaluación nueva, independiente de las métricas anteriores

TRAIN REG 2019–2023; CAL selección y dispersión 2024, con la misma separación
temporal explícita de v1. OT se estima exclusivamente en TRAIN. EVAL REG 2025–2026
con todos los elegibles en denominador y abstenciones identificadas. Por prepartido
y cierre Q1/Q2/Q3 se comparan los mismos encuentros contra referencia media TRAIN,
condicionada con su propia covarianza CAL y el mismo contrato OT. MAE, Brier,
log-loss y cobertura nominal80 por mercado pendiente. Línea media/entera fijada
desde TRAIN, no elegida con EVAL. No se seleccionan diseños con EVAL. Estos datos
ya fueron observados: retrospectiva exploratoria, no test virgen. El refit por
alcance no hereda sus métricas ni las del candidato anterior. Todo SIN_CALIBRAR.

## Calendario

Ventana de tres meses calendario, ambos extremos locales incluidos. Fuentes
oficiales y proveedor deben conservar fecha, alcance y resultado de consulta.
Una respuesta vacía aislada no acredita ausencia oficial. Fixtures sin puntos,
identidad estable y revisiones inmutables; final canónico solo con FT validado.
Sincronizar calendario no incorpora resultados ni publica modelos implícitamente.

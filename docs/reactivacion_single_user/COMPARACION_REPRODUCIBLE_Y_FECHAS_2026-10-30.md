# Comparación reproducible y precisión temporal — 2026-10-30

Continuación del catálogo autorizado. No activa modelos, cambia predicciones
originales, retira gates ni utiliza datos productivos como prueba.

## Contrato de comparación, por dominio

| Dominio | Evidencia retenida | Comparación permitida | Límite |
|---|---|---|---|
| NBA base local | Media/sigma normal continua original | Líneas .5, CDF aproximada | No OT, contexto ni calibración; enteras N/D |
| Euroliga | Parámetros originales de la misma corrida | Normal discretizada, enteras/.5, push | RAW, mismo escenario/condicionamiento; CDF aproximada |
| WNBA v2 | Histograma de los mismos32768 puntos Sobol | Enteras/.5, sumas exactas de frecuencias/push | Misma muestra, no una normal inferida; no calibración |
| Fútbol | Probabilidades por línea ya calculada del mercado objetivo | Solo líneas presentes, sin interpolación | Fuente RAW/calibrador identificado preservada; push entero ausente N/D |

El histograma WNBA se construye **una vez** desde `objetivos` de la ejecución ya
realizada, después del condicionamiento y OT correspondientes. No ajusta ni integra
de nuevo. Cuartos nunca heredan OT del total; si el total no tiene muestra OT,
conserva `distribucion_comparable=null` y sus probabilidades N/D. Valor/frecuencia,
simulaciones, mercado y convención OT tienen hash canónico. No guarda32768 filas
individuales ni toca artefactos activos. Se añade a la respuesta/journal de nuevas
consultas; archivos anteriores no se reescriben ni enriquecen con masas nuevas.

Las pruebas comparan todas las probabilidades sobre cinco líneas contra las mismas
muestras originales en PRE conOT, corte sinOT y cuarto. Igualdad exacta, no solo
medias parecidas. Un0%/100% de integración finita no acredita certeza real.

Fútbol conserva cada par disponible y su fuente. No complementa un porcentaje
ausente ni inventa un calibrador. No infiere una familia Poisson/NB/ensemble a
partir de media/sigma. Un ID de calibrador no acredita evaluación independiente.

Comparar es lectura del snapshot del navegador, sin POST, fit, registro ni cambio
de la selección original. La nueva línea del comparador no se usa para guardar
una apuesta: eso requeriría otra selección/consulta explícita. Copias antiguas sin
contrato compatible muestran N/D; no se sustituyen por una distribución actual.
La UI valida soportes ordenados, frecuencias enteras/suma y probabilidades antes
de presentar una comparación. Corrupción no se normaliza silenciosamente.

## Precisión de la fecha en fútbol

La agenda devuelve `fecha_fuente` nominal, separada de `fecha_partido` canónica,
sin migración/escritura de BD. La tabla ya existente de horarios es opcional:
si no existe, el nuevo campo esnull. Con `precision_fecha=DIA`, la ficha muestra
únicamente ese día y **Hora por confirmar**. Sin día nominal conservado, N/D;
no deriva un kickoff ni un día COT de un timestamp técnico anterior. Con hora
acreditada mantiene la conversión UTC→Colombia. Elegibilidad/reconstrucción y
timestamp de cálculo no se cambian para resolver un problema de presentación.

Prueba PostgreSQL sintética: el día nominal de fuente se conserva en la API aunque
la fecha canónica del catálogo sea distinta; el catálogo no se reescribe.

## Validación y límites

388 pruebas backend aprobadas con PostgreSQL18 sintético exclusivo,0 omitidas.
El primer ensayo tuvo un fallo en el nuevo test por desempaquetar incorrectamente
su fixture; corregido sin alterar producto y conservado en evidencia diagnóstica.
Frontend: pruebas funcionales de masa/tabla, ausencia, corrupción, fecha nominal,
adaptador y selector de líneas; lint/TypeScript/build. Recibo final externo.
CI incluye ahora expresamente el experimento WNBA offline también en Windows.

No acredita calibración de distribuciones, eficacia futura, precisión de relojes
live, lesiones/alineaciones o xG. No nuevos modelos ni ingestas. La migración y
los originales V4 siguen pendientes. Conservar la entrega externa
`COMPARACION_REPRODUCIBLE_Y_FECHAS_2026-10-30` junto a los dos recibos anteriores.

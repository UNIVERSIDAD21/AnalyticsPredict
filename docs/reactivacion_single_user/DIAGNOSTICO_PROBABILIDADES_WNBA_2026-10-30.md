# Diagnóstico probabilístico WNBA — 2026-10-30

## Evidencia existente, no nuevo calibrador

La publicación íntegra ya conserva candidato, cohorte, abstenciones, líneas y bins.
Laboratorio los presenta por mercado, identificando candidato, ventana, denominador
y límites. Es una retrospectiva de desarrollo ya observada. No es evaluación del
refit final, de todas las temporadas del formulario, del pipeline conOT ni evidencia
prospectiva. No se inventan muestras o frecuencias para bins vacíos.

Brier conservado es suma de tres clases Over/Under/Push, rango0–2; en .5 equivale
al doble del Brier binario. Línea fija del desarrollo, no precio de mercado. Se
muestran Brier/referencia, logloss, push observado en línea entera y cobertura del
intervalo nominal80 RAW. La tabla no convierte un porcentaje en fiabilidad futura.
Bins pequeños y dependencia entre partidos limitan conclusiones. No se selecciona
un calibrador mirando esta evaluación.

## Auditoría independiente de serialización, sin refit

`backend/scripts/auditar_probabilidades_wnba.py --publicacion RUTA --salida NUEVA`
verifica hash canónico, dataset, IDs, fechas y outcomes del snapshot. La cohorte y
los rechazados deben cubrir exactamente todos los REG EVAL originales desde2025,
sin duplicados/intersección ni cambiar denominador. Reproduce medias del candidato
guardado y MAE/Brier/logloss/push/bins/cobertura80 desde proyecciones conservadas.
No llama ajustar/elegir_recencia. La referencia se presenta tal como fue guardada;
esta auditoría no reajusta su dispersión ni acredita su eficacia independiente.

La salida debe ser externa al repositorio **y al directorio de publicación**; se
rechaza sobrescritura. Nunca modifica coeficientes, journals, cohortes o rutas
activas. El recibo identifica hashes de archivo/dataset/cohorte y publicación/candidato.
El guard externo bloqueó fit, escrituras ajenas, red y subprocesos;0intentos.
Es un hook Python, no aislamiento del sistema operativo.

## Resultado observado

Publicación `wnba-v1-912782c821ae18d8895a723a`:616finales elegibles;450proyecciones
originales,166abstenciones conservadas. Delta máximo de medias0. Diferencia máxima
en métricas1.1102230246251565e-16 por coma flotante; todas<=1e-10.

| Objetivo REG | n | Brier suma de clases | Log loss | Cobertura nominal80 RAW |
|---|---:|---:|---:|---:|
| Q1 |450|0.502337|0.695685|76.44%|
| Q2 |450|0.481752|0.674779|83.33%|
| Q3 |450|0.507564|0.701235|73.56%|
| Q4 |450|0.512154|0.705440|74.89%|
| Total |450|0.488099|0.680861|76.67%|

No es una mejora medida del modelo: es trazabilidad de evidencia existente. La
cobertura observada no coincide necesariamente con80 y no justifica promocionar
intervalos/calibradores. L09 queda **parcial**: falta CAL/TEST independiente por
objetivo y cohorte futura; no se reparte de nuevo esta cohorte para aparentarla.
NBA/Euro/fútbol no heredan esta evaluación o calibración.

405backend aprobadas conPG18 sintético/0omitidas; fórmulas conocidas, bins vacíos,
integridad y ausencia conservada probadas. Frontend verifica definición, muestras,
N/D y cambio de mercado sin mutar origen. Lint/build, integración, capturas, guard y
CI se guardan fuera de producto en `DIAGNOSTICO_PROBABILIDADES_WNBA_2026-10-30`.

# WNBA: soporte de muestra por mercado

## Corrección

El requisito de diez empates WNBA con OT se aplicaba a toda solicitud PRE,
incluidos Q1–Q4. Se separa del ajuste/covarianza de regulación: la falta de OT
no invalida los cuartos calculables ni cambia sus mínimos de muestra.

Si falta soporte OT:

- Q1–Q4 conservan medias, dispersión, ganador y probabilidades propias.
- `predicciones` conserva solo mercados calculables; `mercados_no_disponibles`
  identifica COMPLETO y su causa. La tabla muestra su fila con N/D, no la omite.
- Si se solicita COMPLETO, devuelve resultado parcial HTTP200 con probabilidades,
  ganador y EV del objetivo NULL/N/D. No sustituye el total por regulación ni
  inventa cero, 50% o prórrogas. `regulacion` sigue siendo una salida separada.
- El total no disponible no permite guardado ni selección de combinada. Una
  combinada de cuartos calculables no depende de las muestras de COMPLETO.
- Los cortes Q1–Q3 conservan su contrato de regulación sin OT y no requieren
  muestra OT. No se cambian el mínimo120 del alcance ni8/6 por equipo.

Trazabilidad: política `wnba-soporte-por-mercado-v1` incorporada a la identidad
del cálculo. Publicación v1, cohortes y análisis anteriores no se reescriben.
Las distribuciones antes soportadas no cambian; no es calibración ni modelo nuevo.

## Verificación individual del snapshot 2019–2026

Corte exclusivo25oct2026, REG, pareja Atlanta Dream–Chicago Sky. Cada temporada
se ajustó por separado, en memoria y sin registrar análisis. No prueba todas las
parejas posibles ni acredita eficacia.

| Temporada | Partidos REG | OT | Q1–Q4 | Total con OT |
|---|---:|---:|---|---|
| 2019 | 204 | 5 | Calculables | N/D |
| 2020 | 132 | 4 | Calculables | N/D |
| 2021 | 192 | 13 | Calculables | Calculable |
| 2022 | 216 | 11 | Calculables | Calculable |
| 2023 | 240 | 10 | Calculables | Calculable |
| 2024 | 240 | 8 | Calculables | N/D |
| 2025 | 286 | 5 | Calculables | N/D |
| 2026 | 330 | 12 | Calculables | Calculable |

40 solicitudes de cálculo verificadas;20 antes soportadas comparadas con el
motor publicado previo, con igualdad exacta de predicciones/probabilidades,
ganador, regulación y OT. Snapshot activo y journals permanecen intactos.

Regresiones: API Q1/PRE solo2020 y objetivo COMPLETO parcial; Q1–Q4 independientes
de OT; umbral9/10; cortes; conjunta de cuartos; UI con total N/D y sin falsos
porcentajes/NaN/guardado. No se realizaron POST productivos, DML, sincronizaciones
ni publicación/reentrenamiento persistente de artefactos. Probabilidades RAW.

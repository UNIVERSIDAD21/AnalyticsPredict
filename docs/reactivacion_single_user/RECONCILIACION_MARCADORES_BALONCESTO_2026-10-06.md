# Reconciliación de marcadores 0–0 NBA y Euroliga — 2026-10-06

## Alcance y fuentes

El propietario autorizó reconciliar Neon con fuentes verificables. La auditoría consultó **148 eventos NBA** directamente mediante `site.api.espn.com` (summary por `espn_game_id`) y **83 registros Euroliga** contra `api-live.euroleague.net/v1/results` de sus seis temporadas. Para el único final Euroliga ausente en la BD se usó el boxscore de `live.euroleague.net/api/Boxscore?gamecode=134&seasoncode=E2025`, con cuartos 23–25–26–30 y 29–17–21–20, total 104–87. Las respuestas oficiales, hashes, cruce individual y scripts de respaldo/ensayo/rollback se guardaron **fuera del repositorio** en `RECONCILIACION_BALONCESTO_OFICIAL_2026-10-06` dentro de la Carpeta de Entregas de Borlty; no contienen credenciales.

El cotejo exige temporada, competición, pareja local/visitante, ID o fixture único y fecha; ESPN confirma 81 finales con puntos/cuartos consistentes y 67 `STATUS_POSTPONED`. En Euroliga, 48 filas 0–0 reprogramadas apuntan a **44 finales únicos** positivos ya existentes en Neon; 34 (E2021, equipos rusos) no tienen final en los resultados oficiales consultados; una fila OLY–FBB de la jornada 14, originalmente 2025-12-04, corresponde al final oficial E2025_134 del 2026-03-17. «Sin final oficial» no equivale por sí solo a afirmar que se jugó o canceló.

## Cambio controlado

- Un respaldo privado captura las **231 filas 0–0**, cinco apuestas vinculadas y 66 vínculos de predicción, con SHA-256. El procedimiento comprueba que no cambiaron desde el respaldo, bloquea solo esas 231 filas, exige conteos exactos y confirma o revierte **una sola transacción**. El ensayo con rollback proyectó 81 NBA con marcador final, 67 NBA pospuestos inválidos, 82 Euroliga sin resultado acreditable inválidos y un final Euroliga reprogramado; no modifica apuestas, predicciones ni los 44 finales duplicados ya existentes.
- Se conservan los 0–0 históricos pospuestos o sin final acreditado, ahora marcados `valido=false`, con razón y fuente. Los 81 finales NBA reciben cuartos/totales oficiales sin alterar la fecha local histórica. El final Euroliga recibe fecha y boxscore oficiales, conservando el identificador Sofascore original como procedencia de la fila.
- El gate P&L de bitácora y auditor excluye importes si el resultado registrado contradice marcador, línea y lado. Se detectaron **seis** discrepancias sobre marcadores ya positivos y **dos** más entre las cuatro apuestas ligadas a los 81 finales NBA. No se reescribe ni presupone el settlement financiero; el ROI continúa **NO CERTIFICADO**.

## Estado y límites

**Pendiente de confirmación de CI, aplicación y postflight en Neon.** La corrección retrospectiva de marcador no certifica el histórico P&L, la validez temporal de las predicciones, la frescura de fútbol ni un rendimiento prospectivo. Los 24 outcomes NBA excluidos pertenecen a tres partidos pospuestos; no se convierten en pares calibrables por esta reconciliación. La fuente Euroliga es primaria/oficial, mientras Sofascore seguía devolviendo 403 en el cotejo; los 34 sin final no reciben un score inferido.

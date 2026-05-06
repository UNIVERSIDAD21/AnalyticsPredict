# Reporte de calidad de datos NBA

Generado: 2026-05-06T00:19:04

## Estado general
- Total partidos NBA: 10278
- Última fecha cargada: 2026-05-05
- Partidos sin source/source_game_id: 219
- Partidos con overtime: 531
- Inconsistencias total local: 0
- Inconsistencias total visitante: 0
- Inconsistencias flag overtime: 0
- Duplicados por source/source_game_id: 0

## Partidos por temporada NBA

| Temporada | Activa | Partidos | Primera fecha | Última fecha |
|---|---:|---:|---|---|
| 2025-2026 | True | 1291 | 2025-10-21 | 2026-05-05 |
| 2024-2025 | False | 1320 | 2024-10-22 | 2025-06-23 |
| 2023-2024 | False | 1315 | 2023-10-24 | 2024-06-18 |
| 2022-2023 | False | 1315 | 2022-10-18 | 2023-06-13 |
| 2021-2022 | False | 1350 | 2021-05-23 | 2022-06-17 |
| 2020-2021 | False | 1174 | 2020-12-23 | 2021-07-21 |
| 2019-2020 | False | 1154 | 2019-10-23 | 2020-10-11 |
| 2018-2019 | False | 1359 | 2018-04-14 | 2019-06-14 |

## Cobertura reciente por equipo

| Equipo | General | Local | Visitante | Fecha reciente | Advertencias |
|---|---:|---:|---:|---|---|
| ATL - Atlanta Hawks | 669 | 333 | 336 | 2026-04-30 | OK |
| BKN - Brooklyn Nets | 668 | 335 | 333 | 2026-04-12 | OK |
| BOS - Boston Celtics | 759 | 382 | 377 | 2026-05-02 | OK |
| CHA - Charlotte Hornets | 634 | 315 | 319 | 2026-04-17 | OK |
| CHI - Chicago Bulls | 641 | 322 | 319 | 2026-04-12 | OK |
| CLE - Cleveland Cavaliers | 688 | 348 | 340 | 2026-05-03 | OK |
| DAL - Dallas Mavericks | 697 | 345 | 352 | 2026-04-12 | OK |
| DEN - Denver Nuggets | 742 | 373 | 369 | 2026-05-01 | OK |
| DET - Detroit Pistons | 653 | 326 | 327 | 2026-05-03 | OK |
| GSW - Golden State Warriors | 714 | 356 | 358 | 2026-04-18 | OK |
| HOU - Houston Rockets | 683 | 344 | 339 | 2026-05-02 | OK |
| IND - Indiana Pacers | 696 | 345 | 351 | 2026-04-12 | OK |
| LAC - Los Angeles Clippers | 696 | 348 | 348 | 2026-04-16 | OK |
| LAL - Los Angeles Lakers | 700 | 354 | 346 | 2026-05-02 | OK |
| MEM - Memphis Grizzlies | 671 | 336 | 335 | 2026-04-12 | OK |
| MIA - Miami Heat | 721 | 356 | 365 | 2026-04-14 | OK |
| MIL - Milwaukee Bucks | 719 | 361 | 358 | 2026-04-12 | OK |
| MIN - Minnesota Timberwolves | 684 | 341 | 343 | 2026-05-05 | OK |
| NOP - New Orleans Pelicans | 660 | 328 | 332 | 2026-04-12 | OK |
| NYK - New York Knicks | 686 | 344 | 342 | 2026-05-05 | OK |
| OKC - Oklahoma City Thunder | 691 | 350 | 341 | 2026-04-28 | OK |
| ORL - Orlando Magic | 672 | 332 | 340 | 2026-05-03 | OK |
| PHI - Philadelphia 76ers | 710 | 354 | 356 | 2026-05-05 | OK |
| PHX - Phoenix Suns | 696 | 354 | 342 | 2026-04-28 | OK |
| POR - Portland Trail Blazers | 680 | 339 | 341 | 2026-04-29 | OK |
| SAC - Sacramento Kings | 646 | 322 | 324 | 2026-04-12 | OK |
| SAS - San Antonio Spurs | 656 | 323 | 333 | 2026-05-05 | OK |
| TOR - Toronto Raptors | 700 | 353 | 347 | 2026-05-03 | OK |
| UTA - Utah Jazz | 669 | 333 | 336 | 2026-04-12 | OK |
| WAS - Washington Wizards | 655 | 326 | 329 | 2026-04-12 | OK |

## Archivos
- JSON por equipo: `reports/team_recent_form/nba_team_recent_form.json`
- SQL base: `backend/scripts/sql/ultimos_30_partidos_nba_por_equipo.sql`

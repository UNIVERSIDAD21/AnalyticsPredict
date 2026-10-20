# Recuperación multi-fuente de estadísticas nulas — 2026-10-20

## Estado

**Infraestructura de resolución preparada; cobertura real y recuperación de datos no cerradas.** No se cambió ninguna fila de Neon ni se aplicó la migración de procedencia. No se declara recuperado ningún campo en este bloque.

El trabajo responde a las estadísticas nulas de partidos finalizados. `NULL` significa desconocido/no publicado, nunca cero. Los campos de partidos futuros siguen siendo nulos por diseño. Los valores canónicos no nulos no se sobrescriben; una fuente no enlazada, un partido ambiguo, un desacuerdo o una estadística ausente queda fuera del plan de aplicación.

## Corte observado en Neon (solo lectura)

- Catálogo canónico: 12 competiciones de fútbol en este corte; los otros 13 torneos de la auditoría de octubre son un conjunto separado, no se deben atribuir al catálogo activo.
- Finales con marcador FT: 24.593 según el corte de datos del 18/10.
- 4.739 finales con fuente declarada SofaScore conservan ID SofaScore y tienen al menos un campo objetivo FT nulo en corners/tiros; ninguno de esos registros tiene vínculo ESPN. No hay IDs API-Football ni Flashscore para enlazarlos directamente.
- 97 gaps adicionales pertenecen a vínculos ESPN de copas (59 FA Cup, 25 Copa del Rey, 7 Coupe de France, 6 Coppa Italia). Se consultaron los97 resúmenes públicos a ritmo secuencial de1,2s. Los97 pasaron crosswalk de competición/temporada/equipos, ID de evento, fecha±2min, estado final y FT; los97 tenían `statistics=[]` y cero elementos estadísticos, incluso con claves sin mapear. No hubo bloqueo ni error de red. Resultado: 0 campos nuevos disponibles por ESPN para esta cohorte.
- Una observación de diciembre de 2025 (Tenerife–Granada) mostró un desfase de inicio de cinco horas entre el registro canónico y ESPN; el resultado y nombres coincidían, pero no pasa la tolerancia de identidad y no se usa.

Un segundo censo READONLY sobre los 24.593 finales FT midió nulos por columna (no equivale a faltantes recuperables): goles 1T local/visitante42/37; goles 2T6.182/6.181; goles ET671/671; marcador de tanda de penales24.563/24.563; corners 1T6.089 por lado,2T6.093 por lado y FT4.323 por lado; disparos totales4.814 por lado y a puerta4.763 por lado; disparos fuera/bloqueados24.593 por lado; posesión5.866 por lado; faltas, tarjetas amarillas/rojas y fueras de juego24.593 por lado; xG16.166 por lado y xG 1T24.593 por lado. Penales/ET son condicionales al tipo de partido; un `NULL` puede ser no aplicable, y no se debe reemplazar automáticamente por cero.

Las cifras anteriores son consultas identificadas de ese corte, no garantías de exhaustividad global ni un backfill.

## Fuentes públicas examinadas

| Fuente | Evidencia observada | Resultado para completar nulos |
|---|---|---|
| ESPN Soccer | 97/97 summaries de los gaps, todos con ID/equipos/fecha±2min/estado/FT concordantes y `statistics=[]`; se contaron también las claves sin mapear dentro del boxscore. | 0 valores estadísticos disponibles para recuperar en esta cohorte. Payloads y manifiesto externos íntegros. |
| StatsBomb Open Data | 1.819 partidos listados de seis competiciones/temporadas; 155 coincidencias candidatas únicas por competición, equipos ordenados, fecha±1 día y FT; 0 de esos candidatos tenía nulos en los 10 campos corners/disparos inicialmente examinados. | Ningún nulo objetivo observado en esa muestra. El kickoff StatsBomb no trae zona horaria y no se reconcilió con el timestamp canónico; esos155 son candidatos exploratorios, no enlaces de identidad aptos para aplicación. Otros campos no se auditaron. 1.026 no produjeron vínculo por fecha/equipos/FT; 638 no tuvieron cruce de alias de equipo unívoco. |
| PitchAPI | Documentación oficial pública consultada el20/10 declara77ligas, todas las rutas del plan gratis, histórico desde2021 y sin cuota de requests; tiene un fair-use burst guard. En `/matches/{id}/stats` publica `shots`, `shots_on_target`, `BallPossesion` y `expected_goals`/xG por mitades. | El mapeo canónico solo habilita `shots` y posesión; el endpoint todavía requiere `X-API-KEY` y cobertura de liga/temporada/partido no comprobada en vivo. Se retienen tiros a puerta porque la definición puede incluir bloqueos y xG porque el proveedor exige no mezclar modelos. `is_on_target` tampoco se usa: explícitamente incluye bloqueos dirigidos al arco. Fuente: [documentación PitchAPI](https://pitchapi.dev/). |
| football-data.org | Cobertura anunciada para scores/calendarios; corners y tiros están en el complemento publicado de €15/mes. | No comprado. Profundidad histórica por liga/partido desde 2018 no acreditada. |
| football-data.co.uk | GET directo a un CSV público de muestra terminó por timeout de conexión antes de obtener respuesta HTTP. | Sin datos descargados ni usados; no se sorteó el bloqueo de red. |
| FBref | La página pública de estadísticas de Premier League respondió HTTP 403 con desafío del sitio. | No se consultaron endpoints alternos ni se intentó evadir el bloqueo. |
| TheSportsDB / otras APIs comerciales | TheSportsDB respondió HTTP 403 en la pasada previa; TheStatsAPI/Sportmonks requieren plan comercial y no acreditan campos/seasons completos en evidencia actual. | No se eluden bloqueos ni se contratan planes. |

## Código añadido

- `backend/servicios/proveedor_pitchapi.py`: cliente GET de host fijo, ritmo conservador, sin redirecciones ni reintentos de 401/403, errores sanitizados y parser de partido.
- `backend/servicios/resolucion_multifuente_futbol.py`: validación de identidad por IDs mapeados, vínculo único, parser ESPN campo-a-campo, mapeo PitchAPI solo para métricas de semántica compatible y parser genérico con mapa explícito; hash de payload, merge que conserva valores no nulos y controles de consistencia. La allowlist comprende36 columnas canónicas; el mapeo PitchAPI actual cubre disparos totales y posesión, no las36.
- `backend/migrations/2026-10-20_observaciones_multifuente_futbol.sql`: tabla de evidencia por campo/evento/proveedor. **Solo archivo de migración; no aplicada.**
- `backend/scripts/auditar_catalogo_pitchapi.py`: auditor autenticado de catálogo y partidos en modo exclusivamente GET; no lee `.env`, no conecta a PostgreSQL, guarda fuera del repositorio con modo privado y no sobrescribe evidencia.
- `backend/scripts/auditar_gaps_espn_multifuente.py`: lector PostgreSQL READ ONLY que consulta los97 gaps enlazados y resúmenes ESPN con GET secuencial; sin reintentos/redirecciones, valida crosswalks y guarda JSON sin sobrescribir fuera del repo.
- Pruebas dirigidas de resolución, parser y controles de red. La integración PostgreSQL se ejecuta solo si `DATABASE_URL` apunta a una BD sintética `ap_suite_test_*`.

La escritura requiere llamada explícita a `aplicar_plan_resolucion(..., dry_run=False)`, bloque `connection.transaction()` activo, migración aplicada y revalidación del estado/FT bajo bloqueo. La sentencia incluye guardas `IS NULL`; ET/tanda exigen ambos marcadores laterales y actualizan sus flags canónicos dentro de la misma transacción. El usuario operativo debe realizar backup, ensayo/rollback y postflight antes de autorizar un lote productivo. Ninguna de esas operaciones se ejecutó en este bloque.

## Próximo trabajo sin pausa artificial

1. Continuar sin pausa artificial buscando fuentes públicas accesibles con contrato/licencia y campos demostrables; conservar el ritmo y detener solo la fuente ante bloqueos, rate limit o fallos.
2. Cuando la clave PitchAPI esté disponible por el almacén protegido, ejecutar el auditor de catálogo/temporadas y una muestra real del endpoint de estadísticas; no pegar claves en chat, `.env` o archivos.
3. Construir crosswalk explícito de competiciones/equipos, conciliar identidad, fecha y FT y medir cobertura por temporada/campo. No elevar los155 candidatos StatsBomb con hora local sin zona a identidad validada.
4. Solo con identidad y métricas acreditadas, generar un dry-run y preparar lote de aplicación con backup, rollback, idempotencia y postflight independientes. La migración sigue sin aplicar y no se habilita DML por tener código listo.
5. Mantener `NULL` para cualquier temporada/campo sin fuente verificable. No se promete completar todos los nulos.

ETA medida a partir de una credencial funcional: 1–3 horas para una primera evaluación autenticada y contrato por muestra; después, la duración de un backfill depende de cobertura real y volumen. El alcance completo de los 4.739 gaps no tiene ETA garantizable y podría permanecer incompleto si las fuentes no publican el dato.

## Verificación de código de este corte

- `pytest -q backend/tests/test_resolucion_multifuente_futbol.py backend/tests/test_proveedor_pitchapi.py`: **39 aprobadas, 1 omitida**. La omitida requiere PostgreSQL sintético local; el host no tiene `initdb`, `pg_ctl`, `pg_config` ni `docker` disponibles y no se usó Neon para probar DML.
- `compileall` de los módulos y script: aprobado.
- `git diff --check`: aprobado.
- Sin migración, DDL/DML, ingesta, activación de modelos, serving, cron ni compra.

Evidencia cruda externa y manifiesto: `Carpeta de Entregas de Borlty/RECUPERACION_MULTIFUENTE_DATOS_NULOS_2026-10-20`.

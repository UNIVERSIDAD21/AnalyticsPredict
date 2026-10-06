# Inventario legacy y project rot — 2026-10-06

## Capa comercial y consumidores

Se contrastaron importaciones y referencias de clases/módulos bajo `backend/esquemas` y rutas/servicios del frontend en el worktree single-user. Los esquemas `auth.py`, `pagos.py`, `onboarding.py`, `chat.py` y `notificaciones.py` no tenían consumidores activos ni tests propios vigentes y se retiraron. `backend/esquemas/__init__.py` queda para el paquete. `frontend/src/pages/ConfiguracionUsuario.tsx` y `PaginaDashboardUsuario.tsx` **sí** tienen rutas activas: su nombre no justifica eliminación. `frontend/src/contextos/Toasts.tsx` maneja avisos locales de UI, no notificaciones externas.

Barrido estático adicional: 290 módulos Python backend y 167 archivos TS/TSX frontend. En `backend/servicios`, los tres servicios (`apuestas_analizadas`, `b3_estabilizacion_futbol`, `servicio_combinadas`) tienen importadores activos. En `backend/esquemas`, `combinadas.py` tiene consumidor; `analisis_contextual.py` no tenía referencias a sus clases y se retiró. En frontend, 8 archivos sin importación directa fuera de `main.tsx`/tests: tres barrels (`dashboard/index.ts`, `paginas/index.ts`, `constantes/index.ts`), `ExplicacionDemo.tsx`, `GraficoRoiTemporalFutbol.tsx`, `observabilidad.ts`, `performance.ts` y `visitante.ts`. Solo `visitante.ts` era telemetría comercial de landing sin consumidor y se retiró. Los demás se conservan por posible uso manual/futuro; no se confunde ausencia de importación estática con prueba de inutilidad. Tests de flujos eliminados: ninguno activo hallado; las pruebas de contrato single-user se mantienen.

Los directorios `docs/borlty-deliverables/`, arquitectura C0–C7 y ADR-005 son evidencia histórica del producto comercial. No se borran ni se reinterpretan como política single-user vigente. El reporte de eliminación y los nuevos documentos de `docs/reactivacion_single_user/` indican el estado operativo.

## Dependencias y compatibilidad

`frontend/package.json` usa React 18, React Router 7, Vite 5, Vitest 4 y TypeScript 5; el lock reproducible backend apunta a Python 3.12. El primer `npm audit --omit=dev --json` detectó **7 vulnerabilidades en dependencias de producción** (3 high: axios, form-data, lodash; 4 moderate: @remix-run/router, follow-redirects, react-router, react-router-dom). Se actualizó el lock dentro de las restricciones y React Router al release 7.18.4; `npm audit --omit=dev` posterior reportó **0 vulnerabilidades de producción**. Lint, 11 tests y build pasaron. El árbol completo aún presenta 10 alertas en herramientas de desarrollo (7 high, 3 moderate), varias solo reparables con saltos mayores de Tailwind/Vite; no se confunden con cero deuda. CI incorpora gate de auditoría de producción.

`pip-audit -r backend/requirements.lock` en entorno temporal informó **0 vulnerabilidades conocidas** para el lock Python; ello no prueba ausencia de fallos no publicados ni sustituye actualización periódica.

CI fija Node 20 y Python 3.12. `backend/.env.example` ya no pide auth/pagos; el Compose privado usa loopback y la configuración comercial C0–C7 queda histórica. El salto a React Router 7 se verificó además en preview headless de `/`, `/dashboard`, `/app`, `/bitacora`, `/futbol` y `/configuracion`: HTTP 200, raíz no vacía, redirección de `/` a `/dashboard` y cero errores JavaScript de página. No se probó cada interacción profunda.

## APIs, scripts y artefactos

- ESPN Scoreboard respondió HTTP 200 con JSON y cinco eventos el 2026-10-05. El primer intento de dry-run quedó bloqueado porque faltaba la temporada NBA 2026–27; posteriormente se creó con respaldo y control de temporada activa, se corrigió la consulta por día y se ingresaron 8 partidos de pretemporada con segundo dry-run idempotente. Ver `INGESTA_NBA_CONTROLADA_2026-10-06.md`. Esto acredita el tramo de ingesta, no outcomes independientes ni modelos.
- Sofascore `unique-tournament/8` respondió HTTP 403 con `requests` y `curl_cffi` (perfil Chrome). No se informa como calendario vacío ni se promueve fútbol.
- El inventario de scripts sin uso y de cambios de modo H12 continúa abierto: el checkout `main` conserva 30 cambios de modo preexistentes, que no se tocaron desde este worktree. No se borran scripts por mera falta de referencias estáticas, porque varios son CLI/cron manuales.
- Cuatro SQLite comerciales y `backend/data/bitacora_contract_usage.json` ya no están en HEAD, pero siguen alcanzables en commits anteriores. El preflight `PREFLIGHT_REESCRITURA_HISTORIAL_2026-10-06.md` explica por qué los 168 refs y 2 PR abiertos impiden llamar «purga» a un force push de esta sola rama; existe bundle privado de recuperación.

## Criterio de cierre

Este inventario cierra la revisión de esquemas huérfanos y el primer barrido de vulnerabilidades conocidas, **no** cierra todavía la fase completa de project rot ni el saneamiento de dev dependencies/historia. No se cambian secrets, endpoints de terceros, datos analíticos ni políticas de mercados para satisfacer un checklist.

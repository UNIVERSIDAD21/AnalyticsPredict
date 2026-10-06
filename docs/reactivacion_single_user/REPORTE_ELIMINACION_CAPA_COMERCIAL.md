# Reporte de eliminación de capa comercial — 2026-10-05

## Objetivo y corte

Convertir AnalyticsPredict en herramienta privada single-user sin login, cuentas, pagos, suscripciones ni tiers. Rama `reactivacion/implementacion-single-user`, sobre snapshot `reactivacion/snapshot-2026-10-05` (`0d75afa`). Este reporte cubre el código activo y el corte local/Neon registrado durante la reactivación; no recertifica modelos ni rendimiento deportivo.

## Retirado y conservado

| Elemento | Resultado y evidencia |
|---|---|
| Auth, pagos, tiers, onboarding comercial, notificaciones por cuenta y chat no prioritario | Routers/servicios/páginas activos retirados en `3b47761`. OpenAPI actual: **94 paths, 101 operaciones**, cero bajo `/api/auth`, `/api/pagos`, `/api/premium`, `/api/access`, `/api/onboarding`, `/api/notificaciones` y `/api/chat`; test `test_single_user_contract.py`. |
| Identidad por cliente | OpenAPI sin security schemes ni parámetros `Authorization`, `X-Usuario-Id` o `usuario_id`; bitácora, combinadas y análisis ya no filtran por cuenta. Perímetro de uso confirmado: solo local con configuración de loopback. |
| Backend/FE comercial | Dependencias de auth, MercadoPago, gates, pricing y sesión retiradas. `/` lleva al dashboard personal; NBA, fútbol y bitácora permanecen. |
| SQLite comercial | `auth.db`, `pagos.db`, `onboarding.db`, `product_analytics.db` y telemetría de contrato runtime retiradas **solo del índice Git** e ignoradas. Los archivos físicos locales no se borraron. Se retiraron los tres scripts exclusivos de backup/restore SQLite comercial y variables comerciales de `backend/.env.example`. Los blobs de commits anteriores persisten en la historia Git: el cambio no la reescribe. |
| Contenedor local opcional | Compose heredado de staging ya no incluye MailHog, SMTP ni secretos de auth/pagos; publica solo en loopback y configura la URL backend del frontend en build. Smoke HTTP legado ya no consulta endpoints comerciales. Script B6 de preflight comercial y cron de notificaciones retirados. Docker no estaba disponible en este host: se verificaron YAML y sintaxis, no se desplegó. |
| Datos analíticos | Neon conservó 182 apuestas NBA/base, 13 fútbol, 7 combinadas y 16 selecciones según cotejo antes/después registrado en el corte de migración. Predicciones, partidos y `apuestas_analizadas` también se conservaron según validaciones SQL de la migración. Las vistas analíticas se recrearon sin identidad de cuenta. |
| Configuración | Preferencias y parámetros de la cuenta con mayor actividad migraron a la fila única de `configuracion_sistema`. La procedencia multiidentidad anterior se conserva únicamente en backups privados; no se presenta como una identidad activa. |

## Migración y respaldo

El propietario confirmó uso exclusivamente local y que todos los registros deportivos históricos serían visibles. Se ensayó `backend/migrations/2026-10-05_single_user.sql` en restauración aislada y se aplicó a Neon después de un segundo respaldo verificado con escritura pausada. El SQL valida ganador único de configuración, conteos antes/después, ausencia de columnas de identidad y existencia de una sola configuración. La migración elimina `usuarios`, `auth_users`, tablas de reset/revocación, pagos, suscripciones y onboarding. No repetirla sobre una base ya migrada. Los respaldos están fuera del repositorio.

## Contratos y métricas

- Bitácora FE solicita `version=v2` explícito, valida `ok/data` y estructura esencial, y muestra error si llega una respuesta desconocida. El endpoint de analizadas informa total global, no tamaño de página; su estado canónico es `FINALIZADA`.
- `hit_rate_sin_push` de fútbol 1X2 usa porcentaje `0–100` y `null` cuando no hay ganadas/perdidas. El frontend no vuelve a multiplicarlo por cien.
- Calibración fútbol calcula Brier, ECE y Log Loss desde pares probabilidad/outcome binario válidos; sin pares publica `null`. No se usan los proxies `Brier × 0,5/1,5`. Esto no recertifica otros consumidores de métricas ni los calibradores históricos.

## Validación de este corte

- Backend: 16 pruebas dirigidas aprobadas (unitarias analíticas, contratos bitácora/fútbol, OpenAPI y smoke), en venv temporal Python 3.14. Una advertencia de deprecación Starlette/httpx; CI usará Python 3.12.
- Frontend: 11 pruebas en 4 archivos, lint y build aprobados. Las pruebas de bitácora cubren datos v2, error/contrato desconocido, estado y total.
- OpenAPI inspeccionada sin arrancar lifespan/entrenamiento. `git diff --check` sin incidencias. No se ejecutó ingesta ni cobro.
- Después del commit, se reanudó el entorno local en loopback. El startup del backend entrenó su modelo habitual desde BD; no se tomó ese hecho como recertificación analítica. `/salud`, OpenAPI y raíz frontend respondieron HTTP 200 y ambos sockets escucharon solo en `127.0.0.1`.

## Límites y siguientes pasos

Actualización 2026-10-06: la integración PostgreSQL efímera, el lock Python 3.12 y el smoke real de Compose en runner alojado pasaron CI (run 37481234870); Docker local sigue ausente pero ya no bloquea esa verificación. La suite global no se declara verde. Falta smoke visual e inventario final de archivos legacy sin consumidores; README ya se actualizó. H1–H3 se eliminan del **producto activo** por cambio de alcance; H4 queda mitigado en tracking, con historia Git aún conservada. H8 y la recertificación NBA/fútbol, confidence, odds y calidad siguen abiertas: el corte de solo lectura del 2026-10-06 resultó **NO CERTIFICADO** (ver reporte específico).

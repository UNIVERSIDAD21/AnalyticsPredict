# Impacto de eliminar auth, pagos y usuarios comerciales

**Corte:** 2026-10-05, `0d75afaf4d4c70cb348ebb99ba742505dfffd323`. **Estado:** inventario estático previo a cambios funcionales. El plan del propietario en `/home/erik-fuentes/AnalyticsPredict/PLAN_REACTIVACION_SINGLE_USER_ANALYTICSPREDICT/` sustituye la dirección SaaS; los informes de auditoría H1–H12 quedan intactos como evidencia histórica.

## Snapshot y alcance

- Rama de recuperación `reactivacion/snapshot-2026-10-05` en el commit anterior; rama de trabajo `reactivacion/single-user` creada desde el mismo commit.
- El árbol ya tenía **30 cambios exclusivos de modo** `100755 → 100644`, 0 líneas de contenido. No forman parte de esta reactivación y no se incluirán en sus commits.
- Inventario por inspección de código, rutas, stores, ejemplos de entorno y tests. La conexión de solo lectura a la BD remota configurada terminó en **timeout**, sin ejecutar consultas; no se verificó despliegue remoto. La auditoría previa solo contó filas y leyó esquemas de SQLite local en modo inmutable.
- Las etiquetas describen **destino propuesto**, no una eliminación ya ejecutada. `MIGRAR` exige copia/verificación de datos; `REVISAR` exige prueba de consumidores o datos.

## Backend: rutas y servicios

| Elemento | Clasificación | Dependencia / decisión |
|---|---|---|
| `api/rutas_auth.py`, `esquemas/auth.py`, `servicios/auth_seguridad.py`, `servicios/auth_mailer.py` | ELIMINAR | Registro, login, refresh, logout, recuperación, token, aceptación legal de cuenta y métricas del contrato auth no tienen función single-user. Retirar registro de router en `app.py` solo junto con consumidores. |
| `servicios/auth_store.py` | MIGRAR | Gestiona `auth_users`, tokens y `usuarios`, además de suministrar driver/path por defecto a pagos y onboarding. Desacoplar stores primero; conservar datos históricos hasta inventario de BD. |
| `api/dependencias.py` | REEMPLAZAR | `obtener_usuario_id`, opcional y `obtener_usuario_actual` aceptan `X-Usuario-Id`, Bearer y fallback de desarrollo. Eliminar autoridad de cliente; sustituir por operaciones globales sin identidad tras migrar FKs. |
| `api/rutas_pagos.py`, `esquemas/pagos.py`, `servicios/pagos_store.py` | ELIMINAR | Checkout, webhook MP, suscripción, matriz y gate; no deben permanecer montados. Archivar datos contables antes de retirar tablas. |
| `api/rutas_access.py`, `servicios/access_policy.py`, `servicios/access_tiers.py` | ELIMINAR | Capability-check y policy por tier; separar capacidades analíticas de monetización donde tengan consumidores. |
| `api/rutas_premium.py` | REEMPLAZAR | `/capas-depth` entrega contenido analítico valioso; quitar tier/gate y ofrecerlo como módulo normal. `/estado-tier` desaparece. |
| `api/rutas_onboarding.py`, `esquemas/onboarding.py`, `servicios/onboarding_store.py` | REVISAR | Conversión/activación comercial desaparece; preferencias útiles podrían pasar a configuración global. `onboarding_store` hereda driver/path de auth: desacoplar antes de retirar auth. |
| `api/rutas_notificaciones.py`, `servicios/notificaciones_store.py` | MIGRAR | Preferencias/envíos pueden servir al dueño, pero están indexados por `user_id`, comparten SMTP con auth y contienen alertas de suscripción. Quitar solo eventos comerciales y migrar configuración si se conserva el módulo. |
| `api/rutas_product_analytics.py` | REVISAR | Eventos de funnel comercial deben retirarse; eventos de uso técnico solo si aportan diagnóstico personal. |
| `api/rutas_chat.py`, `servicios/chat_contexto.py` | CONSERVAR | Hoy no está montado por defecto (`CHAT_ENABLED=false`). No reactivar ni introducir chatbot durante la simplificación; revisar almacenamiento `user_id` antes de cualquier reactivación. |
| `api/rutas_match_analysis_nba.py` | REEMPLAZAR | Conserva análisis NBA y política `no_picks/no_stake/no_betting_recommendations`; quitar `Depends(obtener_usuario_actual)` solo cuando el ingreso sea privado. |
| `api/rutas_bitacora.py`, `api/rutas_apuestas_futbol.py`, `api/rutas_combinadas.py` | MIGRAR | Lecturas/escrituras y filtros `usuario_id`; FK en `apuestas`, `apuestas_futbol`, `apuestas_combinadas`. Preservar registros y resolver propiedad histórica antes de quitar filtros/FKs. |
| `api/rutas_analisis.py`, `api/rutas_metricas_futbol.py`, `motor/resolucion_apuestas.py`, `motor/resolucion_combinadas.py` | MIGRAR | Configuración de sizing, métricas y resolución condicionadas por usuario. Convertir configuración a global y probar recuentos antes/después. No cambiar fórmulas de modelos en este bloque. |
| Rutas de partidos, equipos, predicción, calidad y explicabilidad sin dependencia de cuenta | NO RELACIONADO | Conservar cálculos/ingesta; comprobar contratos después de retirar wrappers de acceso. |
| `app.py` | REEMPLAZAR | Monta auth, pagos, onboarding, notificaciones, premium, access y resto de routers; además inicia modelo/BD en lifespan. Endurecer ingreso privado y desmontar rutas comerciales de manera coordinada. |

## Frontend

| Elemento | Clasificación | Dependencia / decisión |
|---|---|---|
| `App.tsx`, `main.tsx` | REEMPLAZAR | Wrappers `RutaProtegida`, `RutaConOnboarding`, `RutaConCapacidad`, proveedores de auth/access/gate; `/` redirige a dashboard protegido. Entrar directo a herramienta personal tras cerrar perímetro. |
| `componentes/paginas/PaginaLogin.tsx`, `PaginaOnboarding.tsx` | ELIMINAR | Cuenta y activación comercial; rescatar preferencias útiles antes de retirar onboarding. |
| `contextos/AuthContext.tsx`, `servicios/auth.ts`, `tipos/auth.ts` | ELIMINAR | Sesión/tokens y usuario comercial. |
| `contextos/AccessPolicyContext.tsx`, `GatePromptContext.tsx`, `hooks/useGateNavigation.ts`, `servicios/accessPolicy.ts`, `freemium.ts`, `pagos.ts`, `premium.ts`, `onboarding.ts` | REEMPLAZAR | Hay gates, checkout y tiers mezclados con navegación, KPI de dashboard y contenido analítico premium. Desacoplar contenido y navegación antes de borrar los servicios. |
| `servicios/api.ts` | REEMPLAZAR | Inyecta Bearer, refresh y `X-Usuario-Id`; incluso fabrica UUID de desarrollo y almacena IDs/tokens. Cliente HTTP final sin identidad de usuario. |
| `componentes/organismos/Encabezado.tsx`, `PaginaCentroAnalitico.tsx`, `PaginaPublicaProducto.tsx` | REEMPLAZAR | Copy de visitante/planes y acciones gateadas; navegación personal directa. |
| `PaginaDashboardUsuario.tsx`, `PaginaPrincipal.tsx`, `PaginaFutbol.tsx`, `PaginaConfiguracion.tsx`, `PanelDepthPremium.tsx` | REEMPLAZAR | Conservar análisis, bitácora y preferencias; eliminar badges/paywalls/gates y habilitar profundidad analítica sin tier. |
| `contextos/ConfiguracionUsuario.tsx` | CONSERVAR | Bankroll, riesgo y stake locales son configuración personal, no cuenta de login. Revisar persistencia y nombre al integrar configuración global. |
| `PaginaBitacora.tsx`, `PaginaAnalisisNbaAdmin.tsx`, `AnalisisPartidoFutbol.tsx` | CONSERVAR | Función analítica; retirar wrappers y dependencias indirectas de identidad. |

## Datos y relaciones

| Tabla / campo observado | Clasificación | Restricción |
|---|---|---|
| SQLite/Postgres `auth_users`, `auth_reset_tokens`, `auth_reset_tokens_v2`, `auth_revoked_tokens` | REVISAR | Exclusivos de login; archivar y verificar relaciones antes de retirar. `auth_reset_tokens` referencia `auth_users` en DDL del store. |
| `usuarios` | MIGRAR | Tabla comercial y también FK/lookup para bitácora y configuración. No `DROP` hasta sustituir todas las referencias. |
| `payment_intents`, `payment_events`, `subscriptions` | REVISAR | Solo monetización; conservar archivo auditable de pagos históricos si existen. |
| `onboarding_profiles`, `onboarding_events` | REVISAR | `user_id` en ambos; preferencias potencialmente útiles, eventos de conversión no. |
| `notificaciones_preferencias`, `notificaciones_envios`, `notificaciones_cola` | MIGRAR | `user_id`; preferencias/cola requieren definición de configuración single-user. |
| `apuestas`, `apuestas_futbol`, `apuestas_combinadas` | MIGRAR | `usuario_id` es filtro y relación histórica; preservar filas, origen y resoluciones. |
| `apuestas_analizadas`, `product_events`, `chat_contexto` | REVISAR | Las dos primeras requieren verificar retención/consumidores; chat está fuera de alcance y contiene `user_id`. |
| `backend/data/{auth,onboarding,pagos,product_analytics}.db` | REVISAR | Las cuatro SQLite están versionadas. H4 sigue abierto: no borrar ni reescribir historial. La auditoría reportó 1 usuario auth local, 1 perfil, 0 pagos y 4 eventos; **no describe la BD operativa**. |

## Tests, configuración y documentación

- **ELIMINAR/REEMPLAZAR tests:** `backend/tests/api/test_auth_endpoints.py`, `test_pagos_endpoints.py`, `test_onboarding_endpoints.py`, `test_access_policy_tiers.py`; reescribir tests de bitácora, fútbol y `test_match_analysis_nba_endpoint.py` para rutas sin sesión. `test_notificaciones_endpoints.py` depende de la decisión de conservar notificaciones.
- **CONSERVAR tests analíticos:** pruebas de cálculos/modelos/contratos no comerciales, especialmente las de NBA/fútbol, con fixtures aisladas. No declarar suite global verde por el smoke de CI.
- **ELIMINAR tras desacoplar:** `AUTH_*`, `MP_*`, `MERCADOPAGO_*`, `PAGOS_*`, `ONBOARDING_*`, `VITE_USUARIO_ID`, `NOTIF_MAX_INTENTOS_ALERTAS_SUSCRIPCION`. **REVISAR:** `LEGAL_CURRENT_VERSION`, variables SMTP usadas también por notificaciones y `PRODUCT_ANALYTICS_DB_PATH`; **CONSERVAR:** `DATABASE_URL` para datos analíticos. Nombres observados en `.env.example`, `deploy/staging/staging.env.example` y código; no se leyeron valores secretos.
- **REVISAR despliegue:** `deploy/staging/*`, cron de notificaciones, CORS y bind host antes de retirar auth. No asumir que Internet ya está protegido.
- **REEMPLAZAR documentación vigente:** `docs/FUENTE_DE_VERDAD_ACTUAL.md`, `docs/arquitectura/ESTADO_PROYECTO.md`, plan C0–C7, work orders, roadmap, README y copy comercial. Mantener auditoría y reportes históricos intactos, marcados como históricos; no reescribir H1–H12.

## Bloqueos de verificación antes de eliminación física

1. Inventariar en la BD operativa, **solo lectura**, número de IDs distintos, FKs, conteos por tabla, nulos y propiedad de registros. La SQLite versionada no prueba unicidad real.
2. Definir y comprobar perímetro privado en cada entorno activo. Sin esta evidencia, desmontar auth abriría escrituras sensibles públicamente.
3. Ensayar migración sobre copia aislada, comparar conteos/checksums y referencias; no borrar tablas/archivos históricos en esta fase.
4. Ejecutar contratos FE/BE y pruebas de NBA, fútbol y bitácora con dependencias reproducibles antes de publicar retirada de rutas.

# Arquitectura objetivo single-user

**Estado:** implementada en entorno local y Neon el 2026-10-05; el inventario y mapa de impacto documentan la situación anterior.

## Invariantes

1. Un propietario, sin cuenta de producto, login, registro, token de usuario, `X-Usuario-Id`, selección de cuenta ni tier.
2. Privacidad de infraestructura **antes** de quitar auth: uso local con backend ligado a `127.0.0.1` y frontend local; si se usa otro host, exigir VPN/access proxy o red privada verificada. No exponer `/api/*` de escritura en IP pública. El control de red no se confunde con auth comercial.
3. NBA, fútbol, bitácora, dashboard, configuración y capas analíticas quedan disponibles directamente. El módulo NBA interno mantiene `no_picks`, `no_stake`, `no_betting_recommendations`.
4. Todos los datos deportivos y la bitácora histórica se muestran como historial personal por decisión explícita posterior del propietario. La procedencia previa se conserva en el backup privado; `usuario_id` salió del esquema activo tras migración comprobada.
5. Preferencias de bankroll/riesgo/stake/fuentes, si se conservan, pertenecen a una configuración global única (`configuracion_sistema`) y no a `usuarios`.
6. Ningún cambio de modelos, features, umbrales, ROI o confidence forma parte de esta simplificación.

## Transición controlada

| Etapa | Estado deseado | Gate de salida |
|---|---|---|
| 0 | Mapa completo y snapshot recuperable | Este inventario, mapa de rutas y plan de datos revisados. |
| 1 | Ingreso privado verificable | Bind/firewall/proxy comprobados por entorno; prueba de denegación desde fuera. |
| 2 | Datos globales de propietario | Copia aislada, clasificación de IDs, mapping de FKs y conteos iguales antes/después. |
| 3 | Rutas analíticas sin identidad | API sin header/Bearer de usuario; tests NBA/fútbol/bitácora y autorización de red. |
| 4 | UI sin sesión/tier | `/` útil sin login; peticiones sin UUID/tokens; análisis conservados. |
| 5 | Retiro comercial | Routers, servicios, componentes y variables sin consumidores; archivo de datos histórico preservado. |

## Decisiones de componentes

- Backend sigue FastAPI con PostgreSQL para analítica. Rutas de auth/pagos/tiers/onboarding comercial no se montan en el estado final; notificaciones se resuelven por configuración global o se retiran si solo eran comerciales.
- Frontend React/Vite navega directo a `/dashboard` desde `/`; `/app`, `/futbol`, `/bitacora` y `/admin/nba-analysis` quedan sin guard de usuario. El nombre `/admin/nba-analysis` es histórico; revisar ruta/copy sin degradar el contrato NBA.
- El cliente HTTP no almacena ni transmite tokens, IDs o headers de identidad. Errores de API no se muestran como ceros, en preparación de H7.
- Profundidad antes llamada `premium` se conserva como funcionalidad analítica normal si aporta valor; se elimina solo el control de pago/acceso.
- Scripts, cron y configuración comercial se retiran tras demostrar ausencia de consumidores. El motor y métricas no cambian en este bloque.

## Riesgo abierto

El propietario confirmó uso solo local. Backend y frontend están configurados para escuchar en `127.0.0.1:8000` y `:5173`; los procesos estaban detenidos en la comprobación posterior. Cualquier exposición futura requiere control de red privado independiente; no habilitar acceso público sin él.

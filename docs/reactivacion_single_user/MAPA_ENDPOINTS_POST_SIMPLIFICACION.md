# Mapa de endpoints para transición single-user

**Estado:** objetivo propuesto, no inventario de rutas ya eliminadas. Derivado de decoradores `@router` y montaje en `backend/app.py` al corte `0d75afa`. La API sigue en estado anterior hasta implementar y probar cada grupo.

| Prefijo / ruta actual | Métodos / cantidad | Destino | Motivo / dependencia |
|---|---|---|---|
| `/api/auth/register`, `/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password`, `/accept-legal`, `/contract-usage`, `/me` | POST × 7, GET × 2 | ELIMINAR | Cuenta, sesión y contrato comercial. |
| `/api/pagos/checkout-session`, `/webhook/mercadopago`, `/suscripcion/mia`, `/feature-gate`, `/matriz-estados` | POST × 2, GET × 3 | ELIMINAR | Pago y suscripción; webhook debe quedar desmontado, no responder 200 ficticio. |
| `/api/access/capability-check`, `/policy` | GET × 2 | ELIMINAR | Gate/tier sin sentido single-user. |
| `/api/premium/capas-depth`, `/estado-tier` | GET × 2 | REEMPLAZAR / ELIMINAR | Conservar datos de profundidad sin gate; eliminar estado de tier. |
| `/api/onboarding/estado`, `/perfil`, `/kpis`, `/evento` | GET × 2, POST × 2 | REVISAR | Conversión comercial fuera de alcance; rescatar preferencias como configuración global si aportan valor. |
| `/api/product-analytics/events` | POST × 1 | REVISAR | Retirar funnel de conversión; decidir si quedan eventos diagnósticos. |
| `/api/notificaciones/*` | GET/PUT/POST × 8 | MIGRAR / REVISAR | Preferencias y cola por usuario; alerta de suscripción se elimina. Conservar avisos personales solo si se desacoplan de auth. |
| `/api/nba/match-analysis` | POST × 1 | CONSERVAR / REEMPLAZAR | Misma política analítica; quitar dependencia de usuario una vez cerrado perímetro. |
| `/api/bitacora/*` | GET/POST/PATCH/DELETE | MIGRAR | Preservar operaciones y datos; quitar filtros `usuario_id`, guard admin de tabla `usuarios`, auto-resolución por usuario y header. |
| `/api/futbol/apuestas/*` | GET/POST/PATCH/DELETE | MIGRAR | Preservar resultados y bitácora de fútbol; quitar aislamiento por usuario tras migración. |
| `/api/combinadas/*` | GET/POST/PATCH/DELETE × 5 | MIGRAR | Mantener función; quitar `Depends(obtener_usuario_id)` y FK/filtros de usuario tras cotejo. |
| `/api/analisis/*` y rutas de métricas fútbol con `usuario_id` | Varios | MIGRAR | Configuración/filtrado por usuario pasa a global. No modificar matemáticas en Bloque A. |
| Rutas de partidos, equipos, calidad, predicción, explicación, backtest e internas | Varios | CONSERVAR / REVISAR | Verificar que no tengan dependencias indirectas de identidad antes de dar por cerrado H1. Endpoints de operación interna requieren perímetro privado. |
| `/api/chat/*` | Fuera del montaje por defecto | CONSERVAR DESACTIVADO | Chat no entra en la reactivación; no reexponer. |

## Frontend objetivo

- `/` → herramienta útil (dashboard personal sin sesión), `/app` NBA, `/futbol` y detalle, `/bitacora`, `/configuracion`, análisis NBA interno: **conservar sin wrappers de auth/tier/onboarding**.
- `/login` y `/onboarding`: **eliminar**; `/centro-analitico`, `/futbol/bitacora`, `/futbol/dashboard` pueden mantener redirecciones de compatibilidad no comerciales.
- `/legal/*`: **revisar** como documentación personal/legal; ya no para aceptación de cuenta. `/chat` permanece desactivado.
- No añadir endpoints de “usuario singleton”: la configuración se resuelve internamente sin identidad del cliente.

## Pruebas de contrato necesarias

1. Inventariar OpenAPI real en proceso de prueba aislado, sin lifespan de entrenamiento/productivo; comparar exactamente rutas esperadas/retiradas.
2. Aserciones de que `/api/auth/*`, `/api/pagos/*`, `/api/access/*` y `/api/premium/estado-tier` no existen; header `X-Usuario-Id` y Bearer no alteran rutas conservadas.
3. FE: `/` y módulos analíticos funcionan sin sesión; ninguna solicitud envía token ni UUID; contenido de depth queda disponible.
4. Bitácora: conservar filas y operaciones de lectura/escritura/resolución con conteos íntegros; no confundir error de contrato con lista vacía.

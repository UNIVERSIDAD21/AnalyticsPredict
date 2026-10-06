# Plan de migración de datos single-user

**Estado:** diseño; ninguna migración aplicada a BD. La cifra local de usuarios de la auditoría no prueba que la BD operativa sea single-user.

**Inventario 2026-10-05:** el primer intento a `DATABASE_URL` remota dio timeout; el segundo conectó en transacción de solo lectura. Se observaron 4 usuarios, 3 IDs con apuestas y 3 FKs de bitácora hacia `usuarios`; detalle seudonimizado en `INVENTARIO_DATOS_SINGLE_USER_2026-10-05.md`. No se imprimió ni guardó la URL o valores de filas. La propiedad de U1–U4 sigue sin determinarse.

## Descubrimiento de solo lectura

1. En una conexión protegida y de solo lectura, inventariar tablas/columnas `user_id`, `usuario_id`, `auth_user_id`; FKs, índices, triggers, vistas y consumidores. Registrar solo conteos y hashes agregados, nunca correos, passwords, tokens o datos de apuestas en Markdown.
2. Medir `COUNT(*)`, `COUNT(DISTINCT usuario_id)`, nulos, huérfanos y recuentos por ID seudonimizado para `usuarios`, `apuestas`, `apuestas_futbol`, `apuestas_combinadas`, configuración, notificaciones y onboarding. Comparar identidad auth (`auth_users`) con `usuarios`; no asumir igualdad de IDs.
3. Separar datos exclusivos de comercio (`payment_*`, `subscriptions`, conversion events) de datos analíticos. Archivar los primeros si tienen historia; nunca borrarlos solo porque el producto ya no cobra.

## Decisión según cardinalidad

- **Un único propietario probado:** copiar BD a entorno aislado, crear configuración global, reasignar preferencias y eliminar filtros por usuario de las consultas. Mantener columnas/FKs durante transición; quitar solo tras verificar todas las rutas y scripts.
- **Varios IDs o propiedad incierta:** no fusionar. Crear mapping privado de procedencia y seleccionar datos del propietario con evidencia. Conservar archivo separado de otros registros. Pedir decisión concreta sobre filas ambiguas después de presentar conteos, sin mostrar datos sensibles.
- **Nulos/huérfanos:** conservar filas en cuarentena lógica con identificador original; no inventar propiedad.

## Ensayo y validación

1. Snapshot/backup consistente y prueba de restauración en BD efímera. Registrar esquema y conteos pre-migración.
2. Migración reversible y transaccional en copia: configuración global, referencias analíticas, queries y escrituras. Evitar `DROP TABLE` y `DROP COLUMN` en primer pase.
3. Verificar igualdad de conteos de eventos/partidos/apuestas/resultados, unicidad de IDs y checksums de columnas no identificatorias; `EXPLAIN` de consultas críticas.
4. Probar lectura/escritura NBA, fútbol, bitácora y dashboard sin identidad de cliente; probar que header `X-Usuario-Id` no altera resultados.
5. Solo después de prueba aislada y autorización de cambio en el entorno real, aplicar migración allí con rollback documentado y cotejo antes/después. No ejecutar una migración real como prueba de arranque.

## Dependencias observadas

`api/rutas_bitacora.py` crea/consulta `usuarios` para FK; `rutas_apuestas_futbol.py` y `rutas_combinadas.py` filtran por `usuario_id`; `rutas_analisis.py` consulta configuración de usuario para sizing; `rutas_metricas_futbol.py` y motores de resolución también filtran. `auth_store.py` crea `usuarios` y los stores de pagos/onboarding heredan su driver/path. Estas referencias se desacoplan antes de retirar tablas o stores.

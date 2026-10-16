# Checklist de preparación para uso — 2026-10-15

**Orden del propietario:** implementar el diagnóstico y actualizar completados y
pendientes con evidencia. Base `ebf128c`, rama `reactivacion/implementacion-single-user`.
`[x]` significa resultado comprobado, no certificación predictiva. `[ ]` conserva
el motivo de bloqueo/en curso. Evidencias sin secretos fuera del repo:
`Carpeta de Entregas de Borlty/PREPARACION_USO_INTEGRAL_2026-10-15`.

## A. Entorno y flujo local

- [x] Crear `backend/.venv` persistente con Python 3.12 y `requirements.lock`.
- [x] Verificar dependencias frontend y compatibilidad de Node local/CI. Node24 local: lint, 19 tests y build verdes; CI usa Node20.
- [x] Arranque reproducible en loopback, sin parar procesos ajenos ni autoentrenar. `scripts/dev.sh`, 8000/5173 HTTP200; salud con30 equipos.
- [ ] Smoke HTTP y visual de Dashboard, NBA, fútbol y bitácora; ausencia de login.

## B. NBA: dominio, calidad y actualización

- [x] Filtrar NBA explícitamente y excluir invalidados/0–0/cuarto inválido en entrenamiento, backtest y consultas dependientes. Selector/conteos/temporadas comunes; lookups de registro delimitados a NBA.
- [x] Probar con PostgreSQL sintético mezcla NBA/Euroliga, inválidos y cutoffs. Regresión real del selector y rollback completo del ingestor.
- [x] Rechazar en serving artefactos sin dominio/calidad acreditados; no seguir sirviendo el mixto de 58 entidades como NBA. Formato2 con dominio/política explícitos.
- [x] Actualizar NBA con dry-run, backup, ingesta controlada y postflight/idempotencia. 73 filas nuevas (33 playoffs+40 PRE), una exhibición fuera de dominio excluida por ID; cero filas históricas sobrescritas.
- [x] Entrenamiento explícito NBA con 30 equipos, dataset/versiones identificados y backup del artefacto previo; recarga sin nueva escritura. Modelo2123 publicado con30 equipos y último dato de entrenamiento2026-06-14; servicio recargó2123 sin crear otra versión.

## C. Fútbol canónico

- [x] Acreditar correspondencias ESPN↔competición/temporada/clubes, incluidos ascendidos; no usar similitud automática. Manifiesto externo de96 clubes revisados contra catálogo/variantes/alias y rosters2026; dos altas (Hull/Coventry), cinco temporadas2026–27 con evidencia de scoreboard.
- [ ] Implementar vínculo/ingesta canónica con procedencia, NULL, anti-duplicados y preservación del histórico; ensayar rollback. Código y regresiones sintéticas terminados (suite740); falta ensayo de contrato/datos reales y CI.
- [ ] Aplicar con backup/postflight y conectar calendario/estadísticas al flujo API/UI.
- [ ] Verificar modelos/calibradores de fútbol por dominio/fecha y actualizar solo con dataset apto, sin atribuir validación inexistente.

## D. Operación y evidencia

- [ ] Rutina manual explícita/idempotente de actualización y estado read-only de fuentes, frescura, modelos y jobs, sin notificaciones externas.
- [ ] Cadena prospectiva congelada: evento, mercado, hora UTC, features/dataset/modelo/calibrador y predicción anteriores al inicio; outcome posterior acreditado y resolución idempotente.
- [ ] Prueba E2E aislada y captura real prospectiva sin picks/stakes/recomendaciones en el módulo NBA interno.
- [ ] Unificar gates de métricas SQL/API/UI, conservar N/D y motivos de exclusión; no reescribir apuestas dudosas.
- [ ] Acumular outcomes futuros y validar walk-forward/calibración/confidence con n e intervalos. **Pendiente temporal: requiere que ocurran partidos después del congelamiento.**
- [ ] Acreditar unidad/fuente/instante de stake/cuota/ganancia históricos. **Bloqueo de procedencia: no se inventa información irrecuperable; se mantiene excluida.**
- [ ] Verificar fuente permitida independiente para resultados/inicio. **Sin sortear 403; no confundir dos consultas ESPN con independencia.**

## E. Publicación y cierre

- [ ] Tests proporcionales, diff/secretos, CI, commit/push de cada lote validado; estado/changelog/checklist actualizados.
- [ ] Cierre HTTP/UI y reporte de lo terminado, pendiente y bloqueado; checkout limpio y memoria propia actualizada.

H4 integral y H12 restantes conservan su plan previo; no iniciar purga parcial de
historia ni cambios globales. El bloque D de evolución avanzada sigue fuera de alcance.

## Registro

- 2026-10-15: checklist creado y entorno backend persistente instalado con lock.
  No se inició entrenamiento ni se alteró Neon para probar el entorno.
- 2026-10-15: CI337288d 4/4; detectado contrato hashvarchar32 al entrenar, corregido en852f4ba con CI38837332780 4/4, sin repetir73 filas deportivas ni publicar artefacto fallido. Modelo2123 ya activo,30 equipos. Datos ajenos/apuestas/predicciones intactos. Browser visual bloqueado por política de navegación local; HTTP comprobado, sin sortear la política.

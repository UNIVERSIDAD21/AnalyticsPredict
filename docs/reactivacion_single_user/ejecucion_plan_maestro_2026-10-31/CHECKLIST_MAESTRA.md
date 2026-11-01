# Checklist maestra — AnalyticsPredict

Revisión del control: 289

Control canónico, derivado resumido en ESTADO_ACTUAL.json e historia append-only en BITACORA_EJECUCION.md.
Única raíz editable: C:/Users/ING-ERIK/.openclaw/workspace/repos/AnalyticsPredict/docs/reactivacion_single_user/ejecucion_plan_maestro_2026-10-31. Las copias empaquetadas son snapshots históricos; no retomarlas como un tablero rival.
Agente activo: Borlty-Predict. Relevo secuencial: verificar operaciones y registrar la transferencia antes de editar.
Fuente del encargo: prompt maestro de Codex del 31-oct-2026. Los HECHO requieren evidencia; NO_APLICA permanece sin marcar.
Usar el helper externo control.py o conservar el mismo protocolo de revisión. El JSON no sustituye esta checklist.

## B00 — HECHO

- [x] **B00.01** — Leer instrucciones y fuentes vigentes; localizar o crear el control compartido y registrar el punto inicial real.
  - Estado: HECHO
  - Depende de: Ninguna
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:15:51.655463-05:00 / 2026-11-01T04:15:51.655463+00:00
  - Criterio de aceptación: Leer instrucciones y fuentes vigentes; localizar o crear el control compartido y registrar el punto inicial real.
  - Resultado observado: Control compartido y fuentes enlazados; 75 checks pendientes reales, sin atribuir ejecución al prompt.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_01_CONTROL_INICIAL.json #sha256=9abcea21a3b387cbb0da0fdbcb3f9f4296beb2ae164faf7adc0e3f0b2dd8407d
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 2

- [x] **B00.02** — Preservar HEAD/rama/status/diffs/índice y fuentes pertinentes, incluyendo no versionados; distinguir contenido, modos históricos y trabajo ajeno.
  - Estado: HECHO
  - Depende de: B00.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:15:53.093387-05:00 / 2026-11-01T04:15:53.093387+00:00
  - Criterio de aceptación: Preservar HEAD/rama/status/diffs/índice y fuentes pertinentes, incluyendo no versionados; distinguir contenido, modos históricos y trabajo ajeno.
  - Resultado observado: Línea base de tres árboles y recibos preservada; previos ajenos y el índice de R intactos. No reset/clean/stage.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_02_PRESERVACION.json #sha256=6d23f675245e5df14b46f4b897f423a809cae20217de3d62ccbe33a0ffc82d5e
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 4

- [x] **B00.03** — Identificar la instalación/artefactos vigentes y medir recursos disponibles, puertos y destinos propios; estimar el espacio de exportación/restauración/ensayo con información actual.
  - Estado: HECHO
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:17:04.198226-05:00 / 2026-11-01T04:17:04.198226+00:00
  - Criterio de aceptación: Identificar la instalación/artefactos vigentes y medir recursos disponibles, puertos y destinos propios; estimar el espacio de exportación/restauración/ensayo con información actual.
  - Resultado observado: CPU/RAM/NTFS/puertos medidos y 10557 archivos del paquete04 verificados; tamaño de BD todavía N/D, guard de espacio antes de export/restore.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_03_RECURSOS.json #sha256=93daf4a8584d07bd7c976dd775304c5de6d39fb58497f7c50ce18c7c00c07753
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 6

- [x] **B00.04** — Preparar un staging nuevo e identificado con producto integrado y runtime apropiado; conservar intactos paquetes anteriores y manifiestos de I.
  - Estado: HECHO
  - Depende de: B00.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:19:53.659747-05:00 / 2026-11-01T04:19:53.659747+00:00
  - Criterio de aceptación: Preparar un staging nuevo e identificado con producto integrado y runtime apropiado; conservar intactos paquetes anteriores y manifiestos de I.
  - Resultado observado: Staging privado nuevo con producto integrado/runtime autónomo manifestados; paquete04 conservado intacto.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_04_STAGING.json #sha256=bc7b3171e992775bd550c515ff4489b49259716c5ea67513b6f39c5bb628e922
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 9

- [x] **B00.05** — Revisar y, si hace falta, corregir el continuador: tiempos de espera, registro inmediato de procesos, fallos parciales, limpieza propia y reanudación segura. Verificar los cambios con pruebas proporcionadas en entornos aislados.
  - Estado: HECHO
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:32:56.293486-05:00 / 2026-11-01T04:32:56.293486+00:00
  - Criterio de aceptación: Revisar y, si hace falta, corregir el continuador: tiempos de espera, registro inmediato de procesos, fallos parciales, limpieza propia y reanudación segura. Verificar los cambios con pruebas proporcionadas en entornos aislados.
  - Resultado observado: Orquestación corregida: 27 regresiones, sintaxis y preflight nativo aprobados. Solo delta propio integrado; dump/recibo original intactos. Publicación en lote B03 pendiente.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_05_ORQUESTACION_VERIFICADA.json #sha256=4f5714386de0a39a66542e488ceaf06d5c581c906786244489c10f27e50183ef
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 27

- [x] **B00.06** — Acreditar identidad del clúster propio 55433, rutas, herramientas y configuración protegida; emitir el preflight con límites explícitos y distinguirlo de una migración realizada.
  - Estado: HECHO
  - Depende de: B00.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:33:37.957355-05:00 / 2026-11-01T04:33:37.957355+00:00
  - Criterio de aceptación: Acreditar identidad del clúster propio 55433, rutas, herramientas y configuración protegida; emitir el preflight con límites explícitos y distinguirlo de una migración realizada.
  - Resultado observado: Dos ciclos SQL autenticado/reinicio/parada del clúster propio55433 aprobados; identidad de ruta/rol/extensiones confirmada, detenido y sin BD restaurada aún.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B00_06_CLUSTER_EXCLUSIVO.json #sha256=8135e54032bb615e96bed620a3bcba7e0b04d5fd840d123557a5a1667834b933
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 35

## B01 — HECHO

- [x] **B01.01** — Confirmar acceso e identidad del origen por los mecanismos existentes, con alcance de solo lectura y recibo sin secretos.
  - Estado: HECHO
  - Depende de: B00.02, B00.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:20:34.430880-05:00 / 2026-11-01T04:20:34.430880+00:00
  - Criterio de aceptación: Confirmar acceso e identidad del origen por los mecanismos existentes, con alcance de solo lectura y recibo sin secretos.
  - Resultado observado: Origen READ ONLY identificado y accesible; tamaño real 187015168 bytes y espacio de resguardo/restauración suficiente.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_01_ORIGEN.json #sha256=bbfdfedce07dd7690fa509cb379b23f5bb69e7b55a268a273af41892a225971d
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 12

- [x] **B01.02** — Inventariar escritores del origen, fijar el corte final y documentar pausa propia o reconciliación; establecer cómo detectar escrituras posteriores que impedirían activar el destino.
  - Estado: HECHO
  - Depende de: B01.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:20:44.711448-05:00 / 2026-11-01T04:20:44.711448+00:00
  - Criterio de aceptación: Inventariar escritores del origen, fijar el corte final y documentar pausa propia o reconciliación; establecer cómo detectar escrituras posteriores que impedirían activar el destino.
  - Resultado observado: Inventario propio y política de corte/detección registrados; ausencia universal de escritores externos NO supuesta. B01.07 exige igualdad final antes de activar.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_02_ESCRITORES_Y_CORTE.json #sha256=305081a9bad043466ef5ed5654b97bc1ed0cb4bb3df81872d908bde5d01614a3
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 14

- [x] **B01.03** — Obtener y preservar el dump consistente del corte identificado, usando snapshot mantenido mientras lo consume pg_dump; registrar versiones, SHA-256 y legibilidad.
  - Estado: HECHO
  - Depende de: B00.04, B01.01, B01.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:23:47.256551-05:00 / 2026-11-01T04:23:47.256551+00:00
  - Criterio de aceptación: Obtener y preservar el dump consistente del corte identificado, usando snapshot mantenido mientras lo consume pg_dump; registrar versiones, SHA-256 y legibilidad.
  - Resultado observado: Dump consistente privado verificado: 53 tablas/108190 filas, SHA y legibilidad correctos. Corte final de activación pendiente B01.07.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_03_EXPORTACION.json #sha256=15f55e39d59f897b7ee0711c65a1bfca7c9a8c07057193eef92f447ed7f30a42
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 22

- [x] **B01.04** — Restaurar en una BD nueva única del clúster propio, con rol local propio e identidad de destino comprobada.
  - Estado: HECHO
  - Depende de: B01.03, B00.05, B00.06
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:47:47.607609-05:00 / 2026-11-01T04:47:47.607609+00:00
  - Criterio de aceptación: Restaurar en una BD nueva única del clúster propio, con rol local propio e identidad de destino comprobada.
  - Resultado observado: Nueva restauración ap_unicode_20261101_044650, 53tablas/108190filas verificadas, builtin C.UTF-8; primer destino y configuración preservados. Reconciliar B01.05/B01.06.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_04_RESTAURACION_UNICODE.json #sha256=e628cf82a7cf5d9737150375567cc1eb1768eda4b62e90ff502058b90e8a1cb1
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 59

- [x] **B01.05** — Conciliar datos, tablas/columnas, huellas y conteos; verificar secuencias sin colisiones, objetos grandes, extensiones y cobertura de índices/constraints/funciones/vistas/triggers necesarios.
  - Estado: HECHO
  - Depende de: B01.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:50:10.692881-05:00 / 2026-11-01T04:50:10.692881+00:00
  - Criterio de aceptación: Conciliar datos, tablas/columnas, huellas y conteos; verificar secuencias sin colisiones, objetos grandes, extensiones y cobertura de índices/constraints/funciones/vistas/triggers necesarios.
  - Resultado observado: Datos53tablas/108190filas, secuencias, objetos grandes/extensiones y nueve categorías DDL lógicas coinciden; diferencias físicas/deparse explícitas, locale pendiente B01.06.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_05_CONCILIACION_V2_20261101T045010Z_29366f.json #sha256=08bd949a9ccb9283cbf110b38072959c02efda352c9bdc45f04392becaec117b
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 62

- [x] **B01.06** — Revisar adecuaciones locales realmente necesarias y sus diferencias antes/después; explicar cualquier divergencia legítima. No activar con discrepancias inexplicadas.
  - Estado: HECHO
  - Depende de: B01.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:51:27.421364-05:00 / 2026-11-01T04:51:27.421364+00:00
  - Criterio de aceptación: Revisar adecuaciones locales realmente necesarias y sus diferencias antes/después; explicar cualquier divergencia legítima. No activar con discrepancias inexplicadas.
  - Resultado observado: Unicode acreditado en 4434 textos de catálogos y constantes, secuencias seguras y TimeZone/DateStyle iguales. Diferencia de ordenación default documentada; datos intactos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_06_ADECUACIONES_VERIFICADAS.json #sha256=22e06a22bfeb3295dd41fa3029e611051dfb8582c677bf502b738966c47561e5
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 65

- [x] **B01.07** — Verificar el corte final de origen y la ausencia de pérdida de escrituras al traspaso; cerrar H1 con evidencia o conservar el bloqueo preciso.
  - Estado: HECHO
  - Depende de: B01.06
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:56:06.749534-05:00 / 2026-11-01T04:56:06.749534+00:00
  - Criterio de aceptación: Verificar el corte final de origen y la ausencia de pérdida de escrituras al traspaso; cerrar H1 con evidencia o conservar el bloqueo preciso.
  - Resultado observado: H1 acreditado: origen sin cambios de datos/esquema al cotejo final, 53tablas/108190filas iguales en destino Unicode; sin escritor activo observado. H2/API/UI aún pendientes.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B01_07_CORTE_FINAL.json #sha256=1b75d12de0dc2b06b26a9fb95b9c367a19106ae432b454f432b2fe3aecfd2323
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 74

## B02 — HECHO

- [x] **B02.01** — Configurar el backend del staging para la BD local protegida; demostrar por sus conexiones que no utiliza una URL remota heredada.
  - Estado: HECHO
  - Depende de: B01.07
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:57:35.204324-05:00 / 2026-11-01T04:57:35.204324+00:00
  - Criterio de aceptación: Configurar el backend del staging para la BD local protegida; demostrar por sus conexiones que no utiliza una URL remota heredada.
  - Resultado observado: API/web disponibles y conexiones del backend verificadas en la BD local, con cliente loopback y modo con BD. Acceso habitual aún intacto.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_01_BACKEND_LOCAL.json #sha256=f271fa8ca0a780c80c58c24ec0fbaba5866f13a540a42dc05c4260d60321954d
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 77

- [x] **B02.02** — Verificar API y contenido contra la BD restaurada, con conteos/cortes coherentes; conservar el modo base como alternativa identificada.
  - Estado: HECHO
  - Depende de: B02.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-10-31T23:59:51.591670-05:00 / 2026-11-01T04:59:51.591670+00:00
  - Criterio de aceptación: Verificar API y contenido contra la BD restaurada, con conteos/cortes coherentes; conservar el modo base como alternativa identificada.
  - Resultado observado: Nueve GET reales, sesiones del backend y huella53tablas/108190filas acreditados sin escrituras. Modo base sigue separado; UI/reinicio/backup pendientes.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_02_API_VERIFICADA.json #sha256=b09eeca59f762dba012b0ec6af721f33a8b535d7a026e289327aaf052656aeda
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 80

- [x] **B02.03** — Completar el recorrido real de Hoy, deportes, historia, Mis análisis, Seguimiento, métricas y Estado, preservando notas y aliases; distinguir estados con datos, vacíos y errores.
  - Estado: HECHO
  - Depende de: B02.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:11:40.900219-05:00 / 2026-11-01T05:11:40.900219+00:00
  - Criterio de aceptación: Completar el recorrido real de Hoy, deportes, historia, Mis análisis, Seguimiento, métricas y Estado, preservando notas y aliases; distinguir estados con datos, vacíos y errores.
  - Resultado observado: 26 vistas DOM reales desktop/móvil, 4 capturas revisadas visualmente, historial original y aliases/notas técnicas íntegros; 0JS/HTTP/overflow/POST. BD y38estado intactos; capturas privadas.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_03_UI_VERIFICADA.json #sha256=f73decb2f0692bdf1c4e13c0e3eef3fd67dab4364bc61600899720a01ef01391
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 84

- [x] **B02.04** — Probar escrituras y ausencia de duplicados exclusivamente en un clon desechable con datos técnicos; evitar POST repetidos en la BD personal para obtener capturas.
  - Estado: HECHO
  - Depende de: B02.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:15:45.859614-05:00 / 2026-11-01T05:15:45.859614+00:00
  - Criterio de aceptación: Probar escrituras y ausencia de duplicados exclusivamente en un clon desechable con datos técnicos; evitar POST repetidos en la BD personal para obtener capturas.
  - Resultado observado: API real en clon: guardado neutral idempotente, NULL analíticos, listado/archivo/reapertura y404 verificados; clon/rol propios eliminados. BD personal intacta, sin apuestas ni fit.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_04_ESCRITURAS_CLON.json #sha256=1468a8732dd698fce02b547d67b08db8e45096fdcfe65d70774c6926402c7bc3
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 89

- [x] **B02.05** — Reiniciar procesos propios y clúster; comprobar reconexión y arranque sin entrenar, sincronizar o resolver resultados de forma implícita.
  - Estado: HECHO
  - Depende de: B02.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:18:54.214012-05:00 / 2026-11-01T05:18:54.214012+00:00
  - Criterio de aceptación: Reiniciar procesos propios y clúster; comprobar reconexión y arranque sin entrenar, sincronizar o resolver resultados de forma implícita.
  - Resultado observado: API/web y clúster propio reiniciados: reconexión/GET local aprobados, datos y38estado iguales; sin entrenamiento, sincronización ni resolución implícitos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_05_REINICIO_VERIFICADO.json #sha256=0416cca03bb885777425444897b85c60b4f83eeb21a8a9f2d516c06a4bdeff44
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 95

- [x] **B02.06** — Crear un respaldo local y restaurarlo realmente en otra BD nueva de ensayo; repetir conciliación y lecturas relevantes.
  - Estado: HECHO
  - Depende de: B02.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:24:48.952081-05:00 / 2026-11-01T05:24:48.952081+00:00
  - Criterio de aceptación: Crear un respaldo local y restaurarlo realmente en otra BD nueva de ensayo; repetir conciliación y lecturas relevantes.
  - Resultado observado: Backup local nuevo restaurado en BD exclusiva: datos/esquema/API iguales,38estado/config protegida preservados y modelo cargado desde backup; red externa denegada en prueba. Clon/rol eliminados, BD personal intacta.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_06_RECUPERACION_BACKUP.json #sha256=ad412db5b3111d0a7b421bcf9b666a0ae009f88427f28cbd3fc20c30327f8be1
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 101

- [x] **B02.07** — Actualizar el acceso habitual tras verificar todo, respaldar su versión anterior y documentar retorno antes/después de nuevas escrituras locales, así como el límite de protección frente a pérdida física del disco.
  - Estado: HECHO
  - Depende de: B02.06
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:30:42.704755-05:00 / 2026-11-01T05:30:42.704755+00:00
  - Criterio de aceptación: Actualizar el acceso habitual tras verificar todo, respaldar su versión anterior y documentar retorno antes/después de nuevas escrituras locales, así como el límite de protección frente a pérdida física del disco.
  - Resultado observado: Acceso habitual actualizado tras backup recuperado: reutilización/cierre/arranque frío/reapertura sin duplicados y CMD real aprobados; retorno y límite SSD documentados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_07_ACCESO_HABITUAL.json #sha256=8e202aa5f14c28e2a029e3d1f202bca21d7d289efb37ba56051d45d6fd8e2793
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 106

- [x] **B02.08** — Cerrar H2 como `MIGRADO_LOCAL_VERIFICADO` solo con evidencia completa; dejar cualquier criterio faltante explícito.
  - Estado: HECHO
  - Depende de: B02.07
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:31:31.065622-05:00 / 2026-11-01T05:31:31.065622+00:00
  - Criterio de aceptación: Cerrar H2 como `MIGRADO_LOCAL_VERIFICADO` solo con evidencia completa; dejar cualquier criterio faltante explícito.
  - Resultado observado: H2 MIGRADO_LOCAL_VERIFICADO: API/UI, clon de escritura, reinicio, recuperación real y acceso habitual acreditados. B10/ciencia y copia física externa siguen pendientes.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B02_08_H2_VERIFICADO.json #sha256=8ac13ae0b8a2c720fd68cb23e9c7090120b882d14206fe5aa557f3b03bff6821
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 111

## B03 — PARCIAL

- [x] **B03.01** — Comparar R/A/P y clasificar deltas por objetivo/procedencia; no confundir archivos modificados con funcionalidades nuevas ni con deltas ya publicados.
  - Estado: HECHO
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:32:35.545877-05:00 / 2026-11-01T05:32:35.545877+00:00
  - Criterio de aceptación: Comparar R/A/P y clasificar deltas por objetivo/procedencia; no confundir archivos modificados con funcionalidades nuevas ni con deltas ya publicados.
  - Resultado observado: 92 deltas R/A clasificados por objetivo/procedencia; A incluye P y la continuación Codex. Diferencias de modo separadas, fuente anterior no reatribuida a esta ejecución.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_01_CLASIFICACION.json #sha256=e14e95ceecc760da746a9c920eb2eee50f893e678c58764926c4e644691e8304
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 113

- [x] **B03.02** — Consolidar lotes coherentes en ramas/worktrees apropiados, conservando R y su índice; incorporar solo diferencias examinadas.
  - Estado: HECHO
  - Depende de: B03.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:32:36.988715-05:00 / 2026-11-01T05:32:36.988715+00:00
  - Criterio de aceptación: Consolidar lotes coherentes en ramas/worktrees apropiados, conservando R y su índice; incorporar solo diferencias examinadas.
  - Resultado observado: Fuentes atribuidas consolidadas en W sobre fba0ee44; R y su índice preservados. Sin publicar todavía; revisar diff/secretos y validar el lote.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_02_CONSOLIDACION.json #sha256=8f93049594dca9796c7ac2cd11efcf05024cdb31f4b3e96152a0ef8b7acb79c8
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 115

- [x] **B03.03** — Revisar diff, exclusiones y secretos antes de publicar; tratar la deuda de historia H4 por su alcance propio, sin purga o reescritura de historia por arrastre.
  - Estado: HECHO
  - Depende de: B03.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T00:36:45.534792-05:00 / 2026-11-01T05:36:45.534792+00:00
  - Criterio de aceptación: Revisar diff, exclusiones y secretos antes de publicar; tratar la deuda de historia H4 por su alcance propio, sin purga o reescritura de historia por arrastre.
  - Resultado observado: 104 fuentes revisadas; cero secretos literales. Único patrón era plantilla f-string de URI protegida, inspeccionada. H4 histórico no se purga por arrastre;229 regresiones de fuentes Windows aprobadas.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_03_HALLAZGO_REVISADO.json #sha256=7cca80d37150fb723ec9cb12f735ac3eae8ca97f5e0f9e88f05a112c03b81bc8
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 118

- [x] **B03.04** — Validar el lote, usar identidad Git acordada `UNIVERSIDAD21 <efuentes1@udi.edu.co>`, publicar sin force y comprobar CI del SHA exacto conforme a las autorizaciones existentes.
  - Estado: HECHO
  - Depende de: B03.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T09:54:29.398792-05:00 / 2026-11-01T14:54:29.398792+00:00
  - Criterio de aceptación: Validar el lote, usar identidad Git acordada `UNIVERSIDAD21 <efuentes1@udi.edu.co>`, publicar sin force y comprobar CI del SHA exacto conforme a las autorizaciones existentes.
  - Resultado observado: Lote publicado sin force con identidad exacta; SHA remoto coincidente y cinco jobs CI aprobados.1865 backend/0omitidas;225 frontend previas,13 focales de aislamiento y servicios/build/audit finales acreditados. Primer fallo CI preservado y corregido.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_CI_41318153861_20261101T145429Z_41ed15.json #sha256=fac0befd6da8f1568f6032fbb4f7bd1d7e2acd244c5d5badd3999676c13bbb44
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 140

- [x] **B03.05** — Emitir una release/paquete identificado y la matriz delta → commit → CI → paquete; actualizar documentación vigente sin borrar recibos históricos.
  - Estado: HECHO
  - Depende de: B03.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T10:05:57.044768-05:00 / 2026-11-01T15:05:57.044768+00:00
  - Criterio de aceptación: Emitir una release/paquete identificado y la matriz delta → commit → CI → paquete; actualizar documentación vigente sin borrar recibos históricos.
  - Resultado observado: Paquete nuevo atribuible a60af3ce/CI5success: integridad, Python aislado y modo base real aprobados,38archivos de estado intactos. Acceso diario/BD local privados y paquetes previos conservados; matriz delta→commit→CI→paquete emitida.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_05_PAQUETE.json #sha256=d6b52ca04be8e57dac5a1677e956a6a918dd4bae9ca5e8bafe4d38a764bebf40
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 155

- [ ] **B03.06** — Conciliar evidencias y estado final; publicar documentación atribuible y entregar el informe acumulado con bloqueos honestos.
  - Estado: EN_CURSO
  - Depende de: B03.05, B12.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:45:13.204871-05:00 / 2026-11-01T16:45:13.204871+00:00
  - Criterio de aceptación: Conciliar evidencias y estado final; publicar documentación atribuible y entregar el informe acumulado con bloqueos honestos.
  - Resultado observado: Matriz L01–L30 conciliada con B04–B12: los ensayos/censos ya ejecutados no figuran pendientes, manteniendo los límites y la clasificación heredada conservadora19/4/7.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\CIERRE_PLAN_MAESTRO_2026-11-01\ACTUALIZACION_MATRIZ_L.json #sha256=783aa1de8529fa6b87aca7c04149601714a8d86c154aa18e0cbeeda0eb4da287
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Publicar el cierre documental con evidencia verificada y conservar los ocho bloqueos reales.
  - Revisión de última transición: 289

## B04 — HECHO

- [x] **B04.01** — Medir censo local por deporte/competición/temporada/fase: identidades, estados, fechas, fuentes, nulos, duplicados y conflictos.
  - Estado: HECHO
  - Depende de: B02.08
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T09:58:27.980068-05:00 / 2026-11-01T14:58:27.980068+00:00
  - Criterio de aceptación: Medir censo local por deporte/competición/temporada/fase: identidades, estados, fechas, fuentes, nulos, duplicados y conflictos.
  - Resultado observado: Censo local por competición/temporada/fase y cada columna, identidades/estados/fuentes/NULL/ceros/duplicados medidos en snapshot READ ONLY. Denominador oficial y disponibilidad histórica no se inventan.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B04_01_CENSO.json #sha256=4d5c55d3800145581f3c0f5d19f1e0919d22477346f9c8cb2462d28c1bec7a69
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 142

- [x] **B04.02** — Verificar periodos, OT, conciliación de totales y targets por familia, manteniendo NULL/ceros y fechas sin hora correctamente diferenciados.
  - Estado: HECHO
  - Depende de: B04.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T09:58:34.265604-05:00 / 2026-11-01T14:58:34.265604+00:00
  - Criterio de aceptación: Verificar periodos, OT, conciliación de totales y targets por familia, manteniendo NULL/ceros y fechas sin hora correctamente diferenciados.
  - Resultado observado: Q1–Q4/FT/OT y targets fútbol conciliados por política; mitades de tiros siguen ESTIMADO, no observaciones. NULL/ceros y ET/penales separados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B04_02_PERIODOS.json #sha256=f33521e3e3abf81396d2851369f62f8149bba4dd98484ddaaa4236b96cc4ce31
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 144

- [x] **B04.03** — Construir la matriz objetivo × campos necesarios × elegibles × abstenciones × disponibilidad temporal; no inflar muestras con filas espejadas.
  - Estado: HECHO
  - Depende de: B04.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T09:58:43.617674-05:00 / 2026-11-01T14:58:43.617674+00:00
  - Criterio de aceptación: Construir la matriz objetivo × campos necesarios × elegibles × abstenciones × disponibilidad temporal; no inflar muestras con filas espejadas.
  - Resultado observado: Matriz por liga/objetivo con elegibles y exclusiones sin inflar filas espejadas. Disponibilidad histórica preevento no acreditada; solo aptitud estructural retrospectiva.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B04_03_APTITUD.json #sha256=59fb8b140692c6a51e937783d7c59d0f27cb2ce80a1e0b2f8461e94b24d8bf18
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 146

- [x] **B04.04** — Conciliar artefactos, calibradores realmente aplicados, versiones y políticas; inventariar originales y cohortes presentes/ausentes.
  - Estado: HECHO
  - Depende de: B04.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T10:03:15.449759-05:00 / 2026-11-01T15:03:15.449759+00:00
  - Criterio de aceptación: Conciliar artefactos, calibradores realmente aplicados, versiones y políticas; inventariar originales y cohortes presentes/ausentes.
  - Resultado observado: 38 archivos de estado y tres publicaciones conciliados con políticas por ruta;5/24 calibradores activos de BD no se transfieren a otros modelos. OriginalesV4 no presentes en estado instalado; B06 conserva recuperación específica.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B04_04_ARTEFACTOS.json #sha256=e188c788e9a55a63ef0c7be076de29fdc9541f678ec114086df66d3d936986d7
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 148

- [x] **B04.05** — Congelar datasets aptos con consultas/filtros/manifiestos/hashes y emitir backlog medido; mantener N/D cuando no exista denominador oficial de cobertura.
  - Estado: HECHO
  - Depende de: B04.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T10:03:15.922448-05:00 / 2026-11-01T15:03:15.922448+00:00
  - Criterio de aceptación: Congelar datasets aptos con consultas/filtros/manifiestos/hashes y emitir backlog medido; mantener N/D cuando no exista denominador oficial de cobertura.
  - Resultado observado: Snapshots privados con consultas/política/hashes y backlog medido verificados. NBA9564/Euro2578/WNBA1840REG aptos estructurales; fútbol por objetivo. Sin eficacia, disponibilidad causal o calendario íntegro inventados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B04_05_CONGELADO.json #sha256=5bbfc3b522ef0031d96f998aa4de4cf9738132d84d80a112f0ae1e97160219da
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 150

## B05 — HECHO

- [x] **B05.01** — Priorizar faltantes acreditados a partir de B04; permitir concluir sin cambios cuando no haya un lote elegible.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:10:48.555566-05:00 / 2026-11-01T16:10:48.555566+00:00
  - Criterio de aceptación: Priorizar faltantes acreditados a partir de B04; permitir concluir sin cambios cuando no haya un lote elegible.
  - Resultado observado: Captura acotada NBA: 52eventos/52finales fuente; accesoEuro registrado sin evadir bloqueos. Próximo conciliar IDs y diferencias, no inferir inserciones de los finales.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B05_01_PRIORIZACION.json #sha256=26114c07a1cb59dca897225ead01777416c5d4635fed115178a47a7a6b6cff5b
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B05.02: conciliar captura contra ambas claves y equipos/fecha; backup antes de cualquier lote.
  - Revisión de última transición: 189

- [x] **B05.02** — Preparar captura fuente fechada, identidad, diff/dry-run y respaldo recuperable de cada lote autorizado; reutilizar pipelines existentes.
  - Estado: HECHO
  - Depende de: B05.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:13:37.077673-05:00 / 2026-11-01T16:13:37.077673+00:00
  - Criterio de aceptación: Preparar captura fuente fechada, identidad, diff/dry-run y respaldo recuperable de cada lote autorizado; reutilizar pipelines existentes.
  - Resultado observado: Alias LAC acreditado por regla vigente+ID12+abreviatura: 45pendientes/7coincidentes/0cuarentena. PlanV1 intacto; backup previo reutilizado porhash sin repetir export.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B05_02_PLAN_ALIAS_CONCILIADO.json #sha256=d4d1699ac7ac08aee1e617eabc1061fd8f498952801eefe2a29761a6c286e887
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B05.03 restaurar y ensayar planV2 exacto.
  - Revisión de última transición: 195

- [x] **B05.03** — Ensayar el lote en clon y comprobar que no degrada valores presentes, identidades, periodos, horarios o targets.
  - Estado: HECHO
  - Depende de: B05.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:15:59.118996-05:00 / 2026-11-01T16:15:59.118996+00:00
  - Criterio de aceptación: Ensayar el lote en clon y comprobar que no degrada valores presentes, identidades, periodos, horarios o targets.
  - Resultado observado: Backup restaurado53tablas exactas; fallo tras3 y rollback completo sin diferencias.45resultados aplicados en clon,0cambios ajenos/identidad/fechas y segunda diferencia0; clon propio retirado.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B05_03_ENSAYO.json #sha256=562d04ca9ff5191e79434dbe5092c30db183db01a455ca715982f42d5d310ce4
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B05.04: rollback real y aplicación atómica local bajo comparación del antes.
  - Revisión de última transición: 199

- [x] **B05.04** — Aplicar únicamente el lote local permitido; verificar postflight independiente e idempotencia al repetirlo.
  - Estado: HECHO
  - Depende de: B05.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:16:49.733584-05:00 / 2026-11-01T16:16:49.733584+00:00
  - Criterio de aceptación: Aplicar únicamente el lote local permitido; verificar postflight independiente e idempotencia al repetirlo.
  - Resultado observado: 45placeholders NBAREG actualizados localmente de forma atómica;7finales previos intactos. Postflight independiente exacto y segunda diferencia0 sin reescribir timestamps. Euro403 y residualWEB sin cambios.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B05_04_APLICADO.json #sha256=0c21be920a514ff87b8b6c25cff75e95d3fe2a49354a5db6ae2192b968107a5a
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B05.05: resultado y alcance, después originales/modelos en experimentos separados.
  - Revisión de última transición: 203

- [x] **B05.05** — Publicar el resultado/alcance de la actualización sin modificar modelos y conservar el residual WEB que el propietario indicó dejar pendiente.
  - Estado: HECHO
  - Depende de: B05.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:17.458232-05:00 / 2026-11-01T16:19:17.458232+00:00
  - Criterio de aceptación: Publicar el resultado/alcance de la actualización sin modificar modelos y conservar el residual WEB que el propietario indicó dejar pendiente.
  - Resultado observado: Lote local NBA45 finalizado y agenda200;38artefactos intactos. Euro403 y residualWEB expresamente sin actualizar. Informe externo distingue snapshotB04 y datos posteriores.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B05_05_RESULTADO.json #sha256=1de59a66c6bb621c3c517deb3c62b6a7b777d88417b95b5d8d5aae1bd020277a
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B06 inventariar/reproducir originales disponibles, luego B07 experimentos aislados.
  - Revisión de última transición: 206

## B06 — PARCIAL

- [x] **B06.01** — Inventariar originales con pistas nuevas verificables, sin repetir búsquedas agotadas ni usar memoria privada como evidencia.
  - Estado: HECHO
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:18.182193-05:00 / 2026-11-01T16:19:18.182193+00:00
  - Criterio de aceptación: Inventariar originales con pistas nuevas verificables, sin repetir búsquedas agotadas ni usar memoria privada como evidencia.
  - Resultado observado: 38archivos inventariados; WNBA conserva datos/candidato/cohorte originales. V4 corregidos no instalados, sin pista nueva que justifique repetir búsquedas agotadas. Euro conserva métricas pero no cohorte de predicciones completa.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B06_01_INVENTARIO.json #sha256=79a08bdaa86639ab8209ae9d062ae537d41c420f54d312e9f4c32aa321459a7a
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 208

- [ ] **B06.02** — Resolver la presencia/ausencia de `DESARROLLO_V4_CORREGIDO.json` y `COHORTE_FUTURA_V4_CORREGIDA.json`, sus fuentes, política y hashes; si faltan, mantener L10 bloqueada.
  - Estado: BLOQUEADO
  - Depende de: B06.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:19.188396-05:00 / 2026-11-01T16:19:19.188396+00:00
  - Criterio de aceptación: Resolver la presencia/ausencia de `DESARROLLO_V4_CORREGIDO.json` y `COHORTE_FUTURA_V4_CORREGIDA.json`, sus fuentes, política y hashes; si faltan, mantener L10 bloqueada.
  - Resultado observado: Faltan originales corregidos V4 en las ubicaciones ya revisadas; ninguna pista nueva. No puede reproducirse ni evaluarse L10 desde textos o loaderlegacy.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B06_02_V4_ORIGINALES_FALTANTES.json #sha256=517e167ee50338e4fa7da009f12918a1cae0ed6d4972c5a120116564a008f574
  - Bloqueo o incidencia: Faltan originales corregidos V4 en las ubicaciones ya revisadas; ninguna pista nueva. No puede reproducirse ni evaluarse L10 desde textos o loaderlegacy.
  - Siguiente acción exacta: Propietario: recuperar originales/hash/política de la copia que los conserva; no recrear cohorte.
  - Revisión de última transición: 209

- [x] **B06.03** — Para originales disponibles, recargar con fit bloqueado y reproducir features, predicciones y abstenciones sin alterar sus archivos.
  - Estado: HECHO
  - Depende de: B06.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:21.307046-05:00 / 2026-11-01T16:19:21.307046+00:00
  - Criterio de aceptación: Para originales disponibles, recargar con fit bloqueado y reproducir features, predicciones y abstenciones sin alterar sus archivos.
  - Resultado observado: WNBA450proyecciones/166abstenciones conciliadas sinfit, delta0.0;38originales intactos. V4 y cohorteEuro no se sustituyeron.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B06_03_REPRODUCCION.json #sha256=3d233e4e28893a585b834f3daedaca4bcd83588dd94a1aa36ccc147e3c01302b
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 211

- [x] **B06.04** — Cotejar outcomes realmente posteriores por identidad/tiempo/target; conservar la ventana original y distinguir evaluación parcial, retrospectiva y prospectiva.
  - Estado: HECHO
  - Depende de: B06.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:21.907515-05:00 / 2026-11-01T16:19:21.907515+00:00
  - Criterio de aceptación: Cotejar outcomes realmente posteriores por identidad/tiempo/target; conservar la ventana original y distinguir evaluación parcial, retrospectiva y prospectiva.
  - Resultado observado: WNBA0finalesREG posteriores al día de publicación;0pares prospectivos acreditados. Los450originales son retrospectivos. V4 no evaluable sin originales/ventana completa.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B06_04_OUTCOMES.json #sha256=a5ec9b6dc92cc346d308df877c8d98344560ddfddb803c6677682eeab8983f22
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 213

- [x] **B06.05** — Emitir evaluación o bloqueo por cohorte, sin regenerar V4 bajo el mismo nombre ni activar modelos por acumular resultados. Continuar otros frentes si falta una cohorte.
  - Estado: HECHO
  - Depende de: B06.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:19:22.445799-05:00 / 2026-11-01T16:19:22.445799+00:00
  - Criterio de aceptación: Emitir evaluación o bloqueo por cohorte, sin regenerar V4 bajo el mismo nombre ni activar modelos por acumular resultados. Continuar otros frentes si falta una cohorte.
  - Resultado observado: Dictamen emitido: WNBA reproducible retrospectiva, Euro sin cohorte completa, V4/L10 bloqueada por originales. Ningún modelo/cohorte reemplazado ni activado.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B06_05_DECISION.json #sha256=e01d8ffa54371254832a494c1bf75f57c7e7da8601b6c89751eca00f28193a7b
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar B07 NBA y B08 por dominios independientes.
  - Revisión de última transición: 215

## B07 — HECHO

- [x] **B07.01** — Fijar snapshot, población, cortes, baseline, hipótesis/variantes y funciones de cada partición antes de comparar resultados.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:22.377061-05:00 / 2026-11-01T16:21:22.377061+00:00
  - Criterio de aceptación: Fijar snapshot, población, cortes, baseline, hipótesis/variantes y funciones de cada partición antes de comparar resultados.
  - Resultado observado: Protocolo previoNBA congelado: TRAIN/SELECT/DISP/EVAL separados, baselineTRAIN y alpha5vigente frente alpha1/5/20, sin usar EVAL para seleccionar.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_01_PROTOCOLO.json #sha256=12a733ae05e74b6bcb3a6217af5fc17344e67574e4b890ab3d4f9993141d78c1
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 217

- [x] **B07.02** — Preparar evaluación temporal reutilizando runners; verificar causalidad, simultáneos, transformaciones y tratamiento de fases.
  - Estado: HECHO
  - Depende de: B07.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:22.919210-05:00 / 2026-11-01T16:21:22.919210+00:00
  - Criterio de aceptación: Preparar evaluación temporal reutilizando runners; verificar causalidad, simultáneos, transformaciones y tratamiento de fases.
  - Resultado observado: Particiones no solapadas porfecha,1fila porencuentro/2perspectivas solo diseño; targetsREG coherentes y fuentes de transformación guardadas. No confundir adquisición actual con disponibilidad histórica.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_02_TEMPORALIDAD.json #sha256=31efd96b83ebcdfb0290606053f453d8a57664a085a8eae201273ae554a7234d
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 219

- [x] **B07.03** — Ejecutar el benchmark emparejado de referencia/diseño vigente/candidatos con una carga pesada a la vez, preservando el modelo activo.
  - Estado: HECHO
  - Depende de: B07.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:36.784364-05:00 / 2026-11-01T16:21:36.784364+00:00
  - Criterio de aceptación: Ejecutar el benchmark emparejado de referencia/diseño vigente/candidatos con una carga pesada a la vez, preservando el modelo activo.
  - Resultado observado: Comparación ajustada soloTRAIN y selección soloSELECT: elegidoalpha20.0; pesos experimentales externos, referencia vigentealpha5 y baselineTRAIN conservados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_03_BENCHMARK.json #sha256=a997e93ae3c129b55097c22c913330aaac31a3ff0e6a7859a69fa7986c73e770
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 221

- [x] **B07.04** — Estimar dispersión y covarianza con residuos fuera de muestra; medir intervalos y sus anchuras por Q1–Q4 y total de regulación.
  - Estado: HECHO
  - Depende de: B07.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:37.522860-05:00 / 2026-11-01T16:21:37.522860+00:00
  - Criterio de aceptación: Estimar dispersión y covarianza con residuos fuera de muestra; medir intervalos y sus anchuras por Q1–Q4 y total de regulación.
  - Resultado observado: Covarianza8x8 de residuosDISP fuera de muestra; intervalos80/90 y anchurasQ1–Q4/TOTAL_REG medidosEVAL. ProbabilidadesRAW, no calibrador ni refitfinal.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_04_DISPERSION.json #sha256=10af0bd943a937cdeb2bea2f11372f9bd2b2890ebccfe326c296626d98c50322
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 223

- [x] **B07.05** — Reportar errores, sesgos, probabilidades definidas, coberturas, soporte y abstenciones con denominador completo; impedir selección sobre TEST/EVAL.
  - Estado: HECHO
  - Depende de: B07.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:38.408700-05:00 / 2026-11-01T16:21:38.408700+00:00
  - Criterio de aceptación: Reportar errores, sesgos, probabilidades definidas, coberturas, soporte y abstenciones con denominador completo; impedir selección sobre TEST/EVAL.
  - Resultado observado: EVAL1274/1274partidos, cobertura1.0000, métricas/ICpareados/abstenciones completos; líneasTRAIN y RAW sin resultados económicos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_05_RESULTADOS.json #sha256=9dff4b885e4d577c06031d1057ab9e30038c98b6a470739ed48576a48c6902c8
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 225

- [x] **B07.06** — Registrar decisión mejora/no mejora/evidencia insuficiente, artefacto experimental y límites; actualizar L06/L07/L08 solo en lo acreditado.
  - Estado: HECHO
  - Depende de: B07.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:38.902435-05:00 / 2026-11-01T16:21:38.902435+00:00
  - Criterio de aceptación: Registrar decisión mejora/no mejora/evidencia insuficiente, artefacto experimental y límites; actualizar L06/L07/L08 solo en lo acreditado.
  - Resultado observado: DecisiónNBA: no_mejora_acreditada; experimento aislado y reproducible, sin activación ni sustitución2123. El resultado no certifica rendimiento/calibración futura.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B07_06_DECISION.json #sha256=fa49cb253877910b92e67a724f0980d4653fc65c9dfeab950c3f7671be6d0aec
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 227

## B08 — PARCIAL

- [x] **B08.01** — Fijar protocolo y población apta propios de Euroliga, con baseline y contrato de 40 minutos/push.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:49.358155-05:00 / 2026-11-01T16:21:49.358155+00:00
  - Criterio de aceptación: Fijar protocolo y población apta propios de Euroliga, con baseline y contrato de 40 minutos/push.
  - Resultado observado: Euro: población/cortes/grid propios congelados,40minutos y masa push explícita. Equipos nuevos siguen como abstención; ningún fallback activado.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_01_PROTOCOLO.json #sha256=18c5ab45ea0251a0ef3e995b0a4cfff397cf468f3d6de47161fb8591ea830653
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 229

- [x] **B08.02** — Ejecutar y decidir el benchmark Euro, soporte de equipos nuevos y contracción si los datos lo permiten; separar candidato de refit.
  - Estado: HECHO
  - Depende de: B08.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:21:50.199595-05:00 / 2026-11-01T16:21:50.199595+00:00
  - Criterio de aceptación: Ejecutar y decidir el benchmark Euro, soporte de equipos nuevos y contracción si los datos lo permiten; separar candidato de refit.
  - Resultado observado: Eurobenchmark independiente: evidencia_insuficiente; EVAL315/450, cobertura0.7000. Contracción/alpha elegidossoloSELECT; nuevos equipos sin soporte abstienen, no refit/activación.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_02_RESULTADOS.json #sha256=03a8bd62edf8b6eb14685125ec8188af24eada8846c6236da84266d0043ba97e
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 231

- [x] **B08.03** — Identificar una hipótesis WNBA nueva y justificada, o documentar que no procede repetir el ensayo anterior que eligió k0.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:22:47.445081-05:00 / 2026-11-01T16:22:47.445081+00:00
  - Criterio de aceptación: Identificar una hipótesis WNBA nueva y justificada, o documentar que no procede repetir el ensayo anterior que eligió k0.
  - Resultado observado: No hay hipótesisWNBA nueva sustentada ni nuevosREG; repetir gridk0 consumiría otra vezEVAL sin evidencia distinta. Se conserva decisión y reproducción original.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_03_WNBA_SIN_NUEVA_HIPOTESIS.json #sha256=90e5b99d75c6e2742a9fb71dfa0793c42d15f121e9651c6ba967808da77f78e3
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 233

- [ ] **B08.04** — Evaluar la hipótesis WNBA admisible con sus propios datos/denominadores, regulación y OT separados; mantener gates y fallback no activado mientras no haya evidencia suficiente.
  - Estado: NO_APLICA
  - Depende de: B08.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:22:47.700761-05:00 / 2026-11-01T16:22:47.700761+00:00
  - Criterio de aceptación: Evaluar la hipótesis WNBA admisible con sus propios datos/denominadores, regulación y OT separados; mantener gates y fallback no activado mientras no haya evidencia suficiente.
  - Resultado observado: No aplica nuevo ensayo: B08.03 documenta ausencia de hipótesis admisible. No retira gates ni activafallback; calidad/prospectiva siguen pendientes.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_03_WNBA_SIN_NUEVA_HIPOTESIS.json #sha256=90e5b99d75c6e2742a9fb71dfa0793c42d15f121e9651c6ba967808da77f78e3
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar fútbol, no repetir gridWNBA.
  - Revisión de última transición: 234

- [x] **B08.05** — Definir el alcance de conteos fútbol por competición/familia y sus datos causales, reutilizando métodos y contratos existentes.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:22:49.206385-05:00 / 2026-11-01T16:22:49.206385+00:00
  - Criterio de aceptación: Definir el alcance de conteos fútbol por competición/familia y sus datos causales, reutilizando métodos y contratos existentes.
  - Resultado observado: Protocolo fútbol porfamilia/cortes vigentes predeclarado;CALselecciona alpha, EVAL no selecciona. NULLexcluidos sin imputar, denominadorglobal adicional, V4separada.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_05_PROTOCOLO_FUTBOL.json #sha256=bb8053f60dfc9dc80384d993370c9669542ac85ec2f5e918bcd25451d50e8b1f
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 236

- [x] **B08.06** — Ejecutar el ensayo fútbol apto y documentar decisión/abstenciones; mantener V4 separada del loader legacy.
  - Estado: HECHO
  - Depende de: B08.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:23:08.484244-05:00 / 2026-11-01T16:23:08.484244+00:00
  - Criterio de aceptación: Ejecutar el ensayo fútbol apto y documentar decisión/abstenciones; mantener V4 separada del loader legacy.
  - Resultado observado: Runner fútbol por3familias ejecutado; errores/IC/abstenciones y cobertura sobre todos los finales reportados además de la condicional. Retrospectiva exploratoria, no probabilidades ni V4/activación.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_06_RESULTADOS_FUTBOL.json #sha256=e332a34543d2136df9df705fd0a2c4576d29f5a657a53347c5fb9cc34c8af2a2
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 240

- [x] **B08.07** — Entregar resultados independientes por dominio y actualizar L11/L12/L13 conforme a evidencia; un deporte bloqueado no cierra ni paraliza los demás.
  - Estado: HECHO
  - Depende de: B08.06
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:25:59.129523-05:00 / 2026-11-01T16:25:59.129523+00:00
  - Criterio de aceptación: Entregar resultados independientes por dominio y actualizar L11/L12/L13 conforme a evidencia; un deporte bloqueado no cierra ni paraliza los demás.
  - Resultado observado: Dictamen porliga/familia emitido: Euro70%cobertura, WNBAk0no repetido, fútbol3familias con cobertura/gates propios; ninguna activación ni mezcla V4legacy.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B08_07_DICTAMEN_POR_DOMINIO.json #sha256=12fa5b335ed273b143e7ab9912e51d5b74d5d87084303709a72b6f643f68b5d5
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 242

## B09 — PARCIAL

- [x] **B09.01** — Fijar la política aplicable y separar selección, estimación de dispersión, ajuste de calibrador y evaluación posterior.
  - Estado: HECHO
  - Depende de: B04.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:25:59.652509-05:00 / 2026-11-01T16:25:59.652509+00:00
  - Criterio de aceptación: Fijar la política aplicable y separar selección, estimación de dispersión, ajuste de calibrador y evaluación posterior.
  - Resultado observado: Políticas separadas porversión/objetivo: CALselección/DISP no sonCALcalibrador; protocolos26oct y fútbolbeta identificados porhash. Umbrales no extrapolados universalmente.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B09_01_POLITICAS.json #sha256=a19a90f4f14fe7f0a36f90c5f82e8f3d9bedbe68ad32ff622c5d3fbefbbf1196
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 244

- [ ] **B09.02** — Ajustar/evaluar solo cuando haya muestras aptas; conservar RAW, calibrada, hashes, versión, mercado, línea y fechas sin etiquetas ficticias.
  - Estado: BLOQUEADO
  - Depende de: B09.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:25:59.927849-05:00 / 2026-11-01T16:25:59.927849+00:00
  - Criterio de aceptación: Ajustar/evaluar solo cuando haya muestras aptas; conservar RAW, calibrada, hashes, versión, mercado, línea y fechas sin etiquetas ficticias.
  - Resultado observado: No hay CALprob/TEST independientes aptos para estas versiones; no se recicla EVAL observado ni calibradoreslegacy. Probabilidades nuevas siguenRAW.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B09_02_CALIBRACION_NO_APTA.json #sha256=5fcf111d0bd84b6123be5046ea28aebf74b44d65eb5903a1033fd42b5fa5fb6f
  - Bloqueo o incidencia: No hay CALprob/TEST independientes aptos para estas versiones; no se recicla EVAL observado ni calibradoreslegacy. Probabilidades nuevas siguenRAW.
  - Siguiente acción exacta: Recoger muestra separada segúnpolítica, sin cambiar modelos ni rebajar gates.
  - Revisión de última transición: 245

- [x] **B09.03** — Congelar emisiones nuevas antes de los eventos con denominador/abstenciones completos y sin picks/stakes/recomendaciones NBA.
  - Estado: HECHO
  - Depende de: B09.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:27:09.598315-05:00 / 2026-11-01T16:27:09.598315+00:00
  - Criterio de aceptación: Congelar emisiones nuevas antes de los eventos con denominador/abstenciones completos y sin picks/stakes/recomendaciones NBA.
  - Resultado observado: 4/4eventosNBAREG1nov congeladosQ1RAW55.5 antesdelinicio; incidencia de transacción del comprobador conciliada. Rollbackcorregido exacto y reimportación0;19predicciones totales/9outcomes previos. Sinfit/picks/stakes.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B09_03_CONGELADO.json #sha256=c63d664de915cf7bc2fff933cdabc2a2c8198ff5654108f90c7e5cb71ca863da
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B09.04 solooutcomesposteriores exactos; futuros esperaneventos sinautomatismos.
  - Revisión de última transición: 247

- [ ] **B09.04** — Incorporar y evaluar outcomes posteriores disponibles sin fit; registrar espera externa cuando todavía falten eventos o muestra, sin bloquear otras entregas.
  - Estado: BLOQUEADO
  - Depende de: B09.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:27:42.874614-05:00 / 2026-11-01T16:27:42.874614+00:00
  - Criterio de aceptación: Incorporar y evaluar outcomes posteriores disponibles sin fit; registrar espera externa cuando todavía falten eventos o muestra, sin bloquear otras entregas.
  - Resultado observado: 3outcomes posteriores exactos incorporados sinfit; PRE/REGseparados, fuenteESPNnoindependiente. Cohorte1nov aúnfutura/muestra insuficiente: evaluación finalpendiente.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B09_04_OUTCOMES_PARCIALES_20261101T162742Z_ca7441.json #sha256=bf37467ad098ac9d76ce445c9e47a85c58c40ab428d8250421a0e99b493f0db0
  - Bloqueo o incidencia: 3outcomes posteriores exactos incorporados sinfit; PRE/REGseparados, fuenteESPNnoindependiente. Cohorte1nov aúnfutura/muestra insuficiente: evaluación finalpendiente.
  - Siguiente acción exacta: Tras finalizar eventos1nov, resolver porID/hora sinfit; acumular evidencia independiente de la misma versión segúnpolítica, sincron.
  - Revisión de última transición: 254

- [ ] **B09.05** — Determinar el estado de cada versión/objetivo según su política. Activar únicamente si cumple los criterios y existe la autorización aplicable; conservar rollback y decisión registrada.
  - Estado: BLOQUEADO
  - Depende de: B09.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:27:43.116938-05:00 / 2026-11-01T16:27:43.116938+00:00
  - Criterio de aceptación: Determinar el estado de cada versión/objetivo según su política. Activar únicamente si cumple los criterios y existe la autorización aplicable; conservar rollback y decisión registrada.
  - Resultado observado: No promover: calibración/evidencia futura independiente insuficientes; RAWno certificado. Se conservan modelos/calibradores y rollback actual, ningunaactivación.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B09_04_OUTCOMES_PARCIALES_20261101T162742Z_ca7441.json #sha256=bf37467ad098ac9d76ce445c9e47a85c58c40ab428d8250421a0e99b493f0db0
  - Bloqueo o incidencia: No promover: calibración/evidencia futura independiente insuficientes; RAWno certificado. Se conservan modelos/calibradores y rollback actual, ningunaactivación.
  - Siguiente acción exacta: Solo revisar promoción cuando B09.02/B09.04 cumplan la política de cada versión/objetivo y autorización aplicable.
  - Revisión de última transición: 255

## B10 — PARCIAL

- [x] **B10.01** — Definir contrato y ubicación estable fuera de releases para el almacén personal. Preferencia: SQLite de la biblioteca estándar, manteniendo PostgreSQL deportivo y el modo base independientes. Cambiar esa elección solo por una razón técnica concreta documentada.
  - Estado: HECHO
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T10:11:10.407627-05:00 / 2026-11-01T15:11:10.407627+00:00
  - Criterio de aceptación: Definir contrato y ubicación estable fuera de releases para el almacén personal. Preferencia: SQLite de la biblioteca estándar, manteniendo PostgreSQL deportivo y el modo base independientes. Cambiar esa elección solo por una razón técnica concreta documentada.
  - Resultado observado: Contrato fijado: SQLite estándar en directorio privado estable, CAS/idempotencia, GET sin escrituras,100/4M y200favoritos preservados; originales navegador y PostgreSQL separados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_01_CONTRATO.json #sha256=5b0ecfb2e53459bd16ea1293d4ab82da7e73e0c7ea8d2ee2c2f93ccba833ec91
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 157

- [x] **B10.02** — Implementar persistencia explícita de snapshots, IDs, notas, etiquetas, favoritos y revisiones; validación, conflictos y confirmación real de guardado.
  - Estado: HECHO
  - Depende de: B10.01, B03.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:09:47.217855-05:00 / 2026-11-01T16:09:47.217855+00:00
  - Criterio de aceptación: Implementar persistencia explícita de snapshots, IDs, notas, etiquetas, favoritos y revisiones; validación, conflictos y confirmación real de guardado.
  - Resultado observado: Persistencia PC completa, publicada y activa; CI5/5,1887backend/232frontend sin omisiones, guardado releído/CAS/idempotencia. Incidencia del comprobador recuperada; datos deportivos/modelos sin cambios.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_02_IMPLEMENTACION.json #sha256=10caf3bab3f14a9bfedb7b80437e057858598c7223c00003638c3d8902d3d17e
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B10.03: registrar acción visible pendiente del propietario; continuar compatibilidad y recuperación independientes.
  - Revisión de última transición: 179

- [ ] **B10.03** — Importar el contenido actual del navegador mediante acción visible, vista previa y respaldo anterior; conservar el original hasta verificar la migración y su reversión.
  - Estado: BLOQUEADO
  - Depende de: B10.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:09:47.738600-05:00 / 2026-11-01T16:09:47.738600+00:00
  - Criterio de aceptación: Importar el contenido actual del navegador mediante acción visible, vista previa y respaldo anterior; conservar el original hasta verificar la migración y su reversión.
  - Resultado observado: Falta acción visible del propietario en su perfil habitual; se conserva íntegro y no se accede automáticamente. La importación aislada probada no acredita sus datos reales.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_03_IMPORTACION_PENDIENTE.json #sha256=d47601f13ec920be7ded6e5ff67f0360a8c7441d91ae833ae677af1243e17bec
  - Bloqueo o incidencia: Falta acción visible del propietario en su perfil habitual; se conserva íntegro y no se accede automáticamente. La importación aislada probada no acredita sus datos reales.
  - Siguiente acción exacta: Jefe: revisar/importar desde Mis análisis; agente continúa checks independientes.
  - Revisión de última transición: 181

- [x] **B10.04** — Mantener import/export JSON y compatibilidad declarada con respaldos anteriores; fijar capacidad medida sin truncar datos ni quitar límites sin verificar consecuencias.
  - Estado: HECHO
  - Depende de: B10.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:09:48.270659-05:00 / 2026-11-01T16:09:48.270659+00:00
  - Criterio de aceptación: Mantener import/export JSON y compatibilidad declarada con respaldos anteriores; fijar capacidad medida sin truncar datos ni quitar límites sin verificar consecuencias.
  - Resultado observado: JSON anterior compatible con vista previa;100consultas/4MUTF16 y200favoritos conservados. Ensayo100consultas/3769845UTF16;101rechazada422 sin truncar.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_04_COMPATIBILIDAD.json #sha256=9ad159304a1f7b9dd2941805af30395b3cc52b98f8d0f3d0ba9dfd393bc23284
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar B05 y los demás checks autorizados.
  - Revisión de última transición: 183

- [x] **B10.05** — Probar navegadores/pestañas independientes, conflictos, almacenamiento lleno, cierre abrupto y conservación exacta de resultados/timestamps.
  - Estado: HECHO
  - Depende de: B10.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:09:48.808749-05:00 / 2026-11-01T16:09:48.808749+00:00
  - Criterio de aceptación: Probar navegadores/pestañas independientes, conflictos, almacenamiento lleno, cierre abrupto y conservación exacta de resultados/timestamps.
  - Resultado observado: Dos contextos independientes, conflicto sin pisar/borrador intacto, navegador sin espacio, disco lleno/rollback/cierre abrupto y reinicio con IDs/snapshots/fechas exactos; datos sintéticos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_05_CONFLICTOS.json #sha256=b9d3bea0b9306ee8a2c332d3f2e32642a650b0433d61a0128e0f38d4d8a3f716
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar B05 y los demás checks autorizados.
  - Revisión de última transición: 185

- [x] **B10.06** — Respaldar SQLite de forma consistente y restaurar en un destino nuevo; incluir este almacén en el procedimiento de recuperación junto a PostgreSQL, artefactos y configuración protegida, indicando los cortes de cada uno.
  - Estado: HECHO
  - Depende de: B10.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:09:49.286692-05:00 / 2026-11-01T16:09:49.286692+00:00
  - Criterio de aceptación: Respaldar SQLite de forma consistente y restaurar en un destino nuevo; incluir este almacén en el procedimiento de recuperación junto a PostgreSQL, artefactos y configuración protegida, indicando los cortes de cada uno.
  - Resultado observado: Backup SQLite transaccional revisión5/2consultas sintéticas restaurado exacto en destino nuevo. Guía integra cortes independientes SQLite/PG/artefactos/config privada. Perfil real no importado y mismoSSD explícitos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B10_06_RECUPERACION.json #sha256=af05396d43a899343146eff124c1f1eaba308c65a219f7095786abcf1e8785a6
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar B05 y los demás checks autorizados.
  - Revisión de última transición: 187

## B11 — HECHO

- [x] **B11.01** — Identificar fricciones reales en Hoy → encuentro → análisis → Mis análisis/Seguimiento → reapertura, conservando la navegación ya agrupada.
  - Estado: HECHO
  - Depende de: B02.08
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:30:59.137388-05:00 / 2026-11-01T16:30:59.137388+00:00
  - Criterio de aceptación: Identificar fricciones reales en Hoy → encuentro → análisis → Mis análisis/Seguimiento → reapertura, conservando la navegación ya agrupada.
  - Resultado observado: Recorrido realHoy→ficha identificada→Mi espacio/Seguimiento correcto sinPOST niJS. Guardado/reapertura conresultadoexacto acreditadosenB10aislado, no simulados en datos delJefe.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B11_01_RECORRIDO.json #sha256=a48c2b2cd077660af9d8cc8f3c498eb58712911d16cc508cd9adda784db9fff3
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 257

- [x] **B11.02** — Medir arranque frío/caliente, lecturas/análisis, CPU/RAM y varias pestañas con escenarios y repeticiones declarados.
  - Estado: HECHO
  - Depende de: B11.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:32:01.505560-05:00 / 2026-11-01T16:32:01.505560+00:00
  - Criterio de aceptación: Medir arranque frío/caliente, lecturas/análisis, CPU/RAM y varias pestañas con escenarios y repeticiones declarados.
  - Resultado observado: 3arranques de proceso conGETBDreal medidos (no cachéSOfría),35/35y100/100GET200,7pestañas auténticas y recursoCPU/RAM puntual. Límites delescenario/SLA explícitos.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B11_02_MEDICIONES.json #sha256=66039e0c50064709e2076e5c82e875df3fd3ea271f07bc77067306f6c17119b2
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 263

- [x] **B11.03** — Corregir únicamente cuellos observados y verificar inclusión/comportamiento de las reparaciones de concurrencia previas, sin venderlas de nuevo como funcionalidad nueva.
  - Estado: HECHO
  - Depende de: B11.02
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:34:26.299734-05:00 / 2026-11-01T16:34:26.299734+00:00
  - Criterio de aceptación: Corregir únicamente cuellos observados y verificar inclusión/comportamiento de las reparaciones de concurrencia previas, sin venderlas de nuevo como funcionalidad nueva.
  - Resultado observado: 22regresiones dirigidas aprobadas: trabajolento no bloqueasalud, singleton/clavecompleta/READONLY/SQLagregado. No cuello nuevo reproducido; no reparacionesficticias niTTL/timeouts mayores.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B11_03_CONCURRENCIA.json #sha256=4b991f9281d8ec0683c7530bd419b18d54e00d820a7d455a80936812a0ef0608
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 269

- [x] **B11.04** — Comparar resultados antes/después sin modificar matemática, repetir POST, compartir contexto entre ligas u ocultar datos con TTL o timeouts mayores.
  - Estado: HECHO
  - Depende de: B11.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:34:27.490040-05:00 / 2026-11-01T16:34:27.490040+00:00
  - Criterio de aceptación: Comparar resultados antes/después sin modificar matemática, repetir POST, compartir contexto entre ligas u ocultar datos con TTL o timeouts mayores.
  - Resultado observado: 5respuestas completas equivalentes salvo3claves de reloj declaradas y38artefactos idénticos antes/después. No cambio decódigo/matemática niPOST; no inventar mejora contra versiónprevia.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B11_04_EQUIVALENCIA.json #sha256=23302969fd350a653b6f9be99baeac61650c34fa1e28d707bb650a6c6d36857c
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 271

- [x] **B11.05** — Verificar teclado, foco, temas y estados con datos/vacío/error en escritorio y pantalla estrecha con dimensiones efectivamente aplicadas; documentar cualquier entorno no probado.
  - Estado: HECHO
  - Depende de: B11.04
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:34:37.401831-05:00 / 2026-11-01T16:34:37.401831+00:00
  - Criterio de aceptación: Verificar teclado, foco, temas y estados con datos/vacío/error en escritorio y pantalla estrecha con dimensiones efectivamente aplicadas; documentar cualquier entorno no probado.
  - Resultado observado: Teclado/skiplink y foco,temas claro/oscuro,datos/vacío/error503 y1366/390 reales aprobados; capturasprivadas,0POST. Sin lectorespantalla/Safari/Firefox ni certificaciónWCAGtotal.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B11_05_UI_ACCESIBILIDAD.json #sha256=3a81aa3a753dea02586bdecd6f248540f100b38ed1080eaee6e0d9af55507cda
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: B12 viabilidad de fuentes; después publicación documental y cierre completo con límites.
  - Revisión de última transición: 273

## B12 — PARCIAL

- [x] **B12.01** — Acotar viabilidad, fuentes, contratos y criterio de posponer/abandonar para reloj/posesiones y nuevas variables.
  - Estado: HECHO
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:35:10.178461-05:00 / 2026-11-01T16:35:10.178461+00:00
  - Criterio de aceptación: Acotar viabilidad, fuentes, contratos y criterio de posponer/abandonar para reloj/posesiones y nuevas variables.
  - Resultado observado: Contrato de insumos y criterio de posponer fijados; móduloactual entrecuartos no acredita reloj/posesión. No autoriza comprar, configurar proveedor nuevo ni ampliar el residualWEB.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B12_01_CONTRATO_VIABILIDAD.json #sha256=0f568c0c46136a6d39789730b4c59e0bee6b224ac01538782cf499e65c59a51e
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 275

- [ ] **B12.02** — Acreditar reloj/marcador/posesión/revisiones/orden de llegada antes de desarrollar un módulo live; no equiparar cierre de cuarto con tiempo real.
  - Estado: BLOQUEADO
  - Depende de: B12.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:35:11.562293-05:00 / 2026-11-01T16:35:11.562293+00:00
  - Criterio de aceptación: Acreditar reloj/marcador/posesión/revisiones/orden de llegada antes de desarrollar un módulo live; no equiparar cierre de cuarto con tiempo real.
  - Resultado observado: Dosobservacionesfuente no acreditan archivo causal de reloj/posesión/revisiones/ordenllegada ni contrato dereutilización. El predictoractual sigue entrecuartos, no tiempo real.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B12_02_LIVE_INSUFICIENTE.json #sha256=648cfb8cc759251060655c16ed591ee06474cdb35d3a353c92bc6011a27f57ad
  - Bloqueo o incidencia: Dosobservacionesfuente no acreditan archivo causal de reloj/posesión/revisiones/ordenllegada ni contrato dereutilización. El predictoractual sigue entrecuartos, no tiempo real.
  - Siguiente acción exacta: Obtener fuente/contrato permitidos y archivo causal verificable antes de implementar live.
  - Revisión de última transición: 278

- [ ] **B12.03** — Acreditar cobertura, definiciones y disponibilidad temporal de lesiones, alineaciones y xG, respetando permisos y el residual WEB pendiente.
  - Estado: BLOQUEADO
  - Depende de: B12.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:35:12.332893-05:00 / 2026-11-01T16:35:12.332893+00:00
  - Criterio de aceptación: Acreditar cobertura, definiciones y disponibilidad temporal de lesiones, alineaciones y xG, respetando permisos y el residual WEB pendiente.
  - Resultado observado: La presencia puntual de lesiones/boxscore o columnas no acredita cobertura/definición/asof histórico; xG específico y fuera delmergevigente. Faltan insumoscausales y permiso de reutilización verificados.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B12_03_VARIABLES_NO_ACREDITADAS.json #sha256=75b36ccbc73075c26445d8c8301c622173d9638663eb2c7e7901de0a62aa5e98
  - Bloqueo o incidencia: La presencia puntual de lesiones/boxscore o columnas no acredita cobertura/definición/asof histórico; xG específico y fuera delmergevigente. Faltan insumoscausales y permiso de reutilización verificados.
  - Siguiente acción exacta: Proveer fuente gratuita permitida y cohortecausal/semántica antes de añadir variables; residualWEB queda pendiente.
  - Revisión de última transición: 280

- [ ] **B12.04** — Solo con insumos suficientes, construir candidato aislado y evaluar su aporte con ablaciones y protocolo propio.
  - Estado: BLOQUEADO
  - Depende de: B12.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:35:12.574768-05:00 / 2026-11-01T16:35:12.574768+00:00
  - Criterio de aceptación: Solo con insumos suficientes, construir candidato aislado y evaluar su aporte con ablaciones y protocolo propio.
  - Resultado observado: No construir candidato ni ablación: no se cumplen insumos reales B12.02/B12.03. Falta de archivo causal no se suple con simulación o datos futuros.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B12_04_CANDIDATO_CONDICIONADO.json #sha256=85de51093af09c2ff4ad7f6f702c8d8fe596249d8ac047c1f3f42e5b28908570
  - Bloqueo o incidencia: No construir candidato ni ablación: no se cumplen insumos reales B12.02/B12.03. Falta de archivo causal no se suple con simulación o datos futuros.
  - Siguiente acción exacta: Retomar solo tras inputs suficientes y protocoloaislado predeclarado.
  - Revisión de última transición: 281

- [x] **B12.05** — Emitir decisión de viabilidad o límites por capacidad; actualizar L29/L30 solo si sus criterios reales se acreditan. No bloquea los hitos operativos.
  - Estado: HECHO
  - Depende de: B12.01
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T11:35:13.048917-05:00 / 2026-11-01T16:35:13.048917+00:00
  - Criterio de aceptación: Emitir decisión de viabilidad o límites por capacidad; actualizar L29/L30 solo si sus criterios reales se acreditan. No bloquea los hitos operativos.
  - Resultado observado: Dictamen porcapacidad: live y nuevasvariables pospuestos por insumos noacreditados; L29/L30no cerrados. No candidato/compra/cron/activación; migraciónoperativa y mejoras deuso permanecen válidas.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B12_05_DICTAMEN.json #sha256=b396f8702183e6ad9b30a9350514cbd2083a8c2a8e681a44b301618209c97aa8
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Revisión final delcontrol, publicaciones y evidencias; entregar cierre conbloqueosreales y condiciones.
  - Revisión de última transición: 283

## Matriz L01–L30

19 implementadas en alcance / 4 parciales / 7 pendientes-bloqueadas, heredadas al30oct. Fuente verificable: `E/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json`. B01/B02 cierran operación, no eficacia. Clasificación conservadora heredada: los límites y evidencias sí se actualizan con los ensayos de este plan. No reclasificar un ensayo negativo como mejora implantada. El revisor puede reclasificar el alcance estrecho de un objetivo si su aceptación lo permite.

| ID | Estado | Objetivo | Bloques vinculados | Evidencia y corte | Criterio pendiente / límite vigente | Última revisión |
|---|---|---|---|---|---|---|
| L01 | Implementada | Locks/ejecución/permisos compatibles con Windows | B02.08, B03.04 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B03_CI_41318153861_20261101T145429Z_41ed15.json); antecedente30oct conservado | Windows/ACL/arranque y suite nativa acreditados; no todas las sincronizaciones remotas se ejecutaron. | 2026-11-01 / B03.06 |
| L02 | Implementada | UTF-8 explícito y recarga íntegra de artefactos/journals | UTF-8 e integridad | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | UTF-8 de artefactos/journals/CLIs intervenidos; no conversión de archivos originales | 2026-11-01 / B03.03 |
| L03 | Implementada | Separar consulta NBA y ajuste/registro de versiones | Consulta NBA separada del fit | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | PRE no ajusta/crea versiones; entrenamiento solo explícito | 2026-11-01 / B03.03 |
| L04 | Implementada | Confianza y explicaciones sin muestras/factores ficticios | Explicaciones sin factores ficticios | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Sin factores/muestras/intervalos inventados; completar con evidencia real, no defaults | 2026-11-01 / B03.03 |
| L05 | Implementada | Total/regulación/OT/push y origen de probabilidad inequívocos | Regulación/OT/push y probabilidad | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Mismo origen de media/p NBA; contrato RAW/regulación/OT por liga. Enteras legacy sin push: evento N/D, campos originales preservados | 2026-11-01 / B03.03 |
| L06 | Parcial | Benchmark local actual vs referencia vs candidato | B07.01–B07.06 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B07_06_DECISION.json); antecedente30oct conservado | Benchmark temporal emparejado ejecutado en1274 EVAL; decisión no_mejora_acreditada. No constituye eficacia del refit ni validación futura. | 2026-11-01 / B03.06 |
| L07 | Pendiente de datos | NBA con recencia y forma causal aprendidas | B07.02, B07.03, B07.06 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B07_06_DECISION.json); antecedente30oct conservado | Candidato regularizado evaluado sin activar; recencia/forma causal completa y disponibilidad histórica as-of no acreditadas. No se declara mejora. | 2026-11-01 / B03.06 |
| L08 | Pendiente de datos | NBA: dispersión temporal/covarianza/intervalos | B07.04, B07.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B07_05_RESULTADOS.json); antecedente30oct conservado | Covarianza8x8 estimada en DISP fuera de muestra e intervalos80/90 medidos en EVAL. Sin despliegue ni certificación prospectiva. | 2026-11-01 / B03.06 |
| L09 | Parcial | Calibración y fiabilidad por versión/objetivo | B09.01–B09.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B09_04_OUTCOMES_PARCIALES_20261101T162742Z_ca7441.json); antecedente30oct conservado | RAW separado de calibrado; CAL/TEST independientes insuficientes. PRE12/REG2 outcomes observados en corteB09; cuatro nuevas emisiones siguen futuras. No promoción. | 2026-11-01 / B03.06 |
| L10 | Bloqueada por originales | Retomar evaluación de V4, no regenerarla | B06.01–B06.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B06_05_DECISION.json); antecedente30oct conservado | Faltan originales DESARROLLO_V4_CORREGIDO.json y COHORTE_FUTURA_V4_CORREGIDA.json; no regenerarlos ni usar loader legacy como sustituto. | 2026-11-01 / B03.06 |
| L11 | Pendiente de benchmark | Euro: recencia/regularización y mejora frente a media de liga | B08.01, B08.02 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B08_02_RESULTADOS.json); antecedente30oct conservado | Benchmark Euro ejecutado:315/450 EVAL,70% cobertura frente mínimo90%; evidencia insuficiente. No mejora/promoción acreditadas. | 2026-11-01 / B03.06 |
| L12 | Parcial | WNBA/Euro: equipos nuevos y contracción hacia liga | B06.03, B08.02–B08.04 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B08_03_WNBA_SIN_NUEVA_HIPOTESIS.json); antecedente30oct conservado | WNBA450 reproducidas sinfit/delta0; k0 conservado, sin nueva hipótesis. Euro evaluada con abstención de equipos nuevos; fallback no activado. | 2026-11-01 / B03.06 |
| L13 | Pendiente de datos | Fútbol: parámetros de conteo/ataque/defensa por competición | B08.05–B08.07 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B08_07_DICTAMEN_POR_DOMINIO.json); antecedente30oct conservado | Ensayos corners/goles/disparos ejecutados; cobertura global79,03–79,16% y gates no aptos. Sin promoción; V4 y variables causales pendientes por separado. | 2026-11-01 / B03.06 |
| L14 | Parcial | Priorización de cobertura por usos habituales | B04.01–B04.05, B05.01–B05.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B05_05_RESULTADO.json); antecedente30oct conservado | Censo vigente y aptitud medidos;45 placeholders NBA actualizados. Euro403/residualWEB intactos. Sin denominador oficial completo ni inferencia de frecuencia real. | 2026-11-01 / B03.06 |
| L15 | Implementada | Cortes, fuente y calidad visibles en cada resultado | B02.03, B10.04, B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Versiones/cortes/fuentes visibles en superficies verificadas; no se inventan trazas ausentes. | 2026-11-01 / B03.06 |
| L16 | Implementada | Portada Hoy y acceso directo a la ficha | B02.03, B05.05, B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Agenda con BD local real verificada; paginación y estados parciales conservados. Euro403 no equivale a calendario completo. | 2026-11-01 / B03.06 |
| L17 | Implementada | Sistema visual sobrio, temas y fuentes locales | B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Temas claro/oscuro y1366/390px verificados en estados recorridos; no todos los componentes legados se rediseñaron. | 2026-11-01 / B03.06 |
| L18 | Implementada | Ficha única con detalle progresivo y menos controles repetidos | Fichas y detalle progresivo | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Fichas baloncesto/fútbol progresivas; agenda y seguimiento separados de configuración | 2026-11-01 / B03.03 |
| L19 | Implementada | Favoritos, notas y etiquetas cross-liga | B10.01–B10.06 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B10_06_RECUPERACION.json); antecedente30oct conservado | SQLite durable/IDs/notas/etiquetas/favoritos probados e instalado. Importación real del navegador pendiente de acción visible; originales intactos. | 2026-11-01 / B03.06 |
| L20 | Implementada | Comparador de líneas sin recalcular modelo | B10.04, B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Comparadores/reapertura conservan la misma corrida sin repetir análisis; distribución no conservada permanece N/D. | 2026-11-01 / B03.06 |
| L21 | Implementada | Reapertura/exportación reproducible de análisis | B10.02, B10.04–B10.06 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B10_06_RECUPERACION.json); antecedente30oct conservado | JSON compatible y SQLite durable; recuperación/reinicio/conflictos probados con datos sintéticos. B10.03 real aún bloqueado. | 2026-11-01 / B03.06 |
| L22 | Implementada | Modo base local sin BD con límites visibles | B03.05, B10.04 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B10_04_COMPATIBILIDAD.json); antecedente30oct conservado | Paquete autónomo NBA/Euro/WNBA sin BD/fit; integración y guardado probados con copia sintética, no con datos del perfil del Jefe. | 2026-11-01 / B03.06 |
| L23 | Implementada | Error/vacío/N/D consistentes, sin falsos conteos cero | B10.05, B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Vacío/error/N/D y rechazo sin pérdida verificados en flujos recorridos; no se atribuye cobertura universal. | 2026-11-01 / B03.06 |
| L24 | Implementada | Teclado, legibilidad y movimiento reducido | B11.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_05_UI_ACCESIBILIDAD.json); antecedente30oct conservado | Teclado/foco/temas/tamaños y error/vacío verificados; revisión orientativa, no certificación WCAG. | 2026-11-01 / B03.06 |
| L25 | Implementada | Pruebas Windows y reloj determinista en fixtures | B03.04, B10.02, B10.04, B11.03 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_03_CONCURRENCIA.json); antecedente30oct conservado | 1887 backend sintéticos/232 frontend sin omisiones en suite finalB10;19 pruebas de guía posteriores y CI final236cb99 cincojobs. No sumar repeticiones. | 2026-11-01 / B03.06 |
| L26 | Implementada | Invalidación de caché por revisión de datos/alcance | B05.04, B10.05, B11.04 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B11_04_EQUIVALENCIA.json); antecedente30oct conservado | Idempotencia local, CAS/conflictos y equivalencia de lecturas concurrentes probados; sin revisión de caché inventada. | 2026-11-01 / B03.06 |
| L27 | Implementada | Extraer cálculo/acceso a datos de rutas monolíticas | Extracciones acotadas de lógica/acceso | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Cálculo NBA base y matemática/lecturas fútbol separados de HTTP; equivalencia; no reescritura total | 2026-11-01 / B03.03 |
| L28 | Implementada | Acceso de inicio local claro y no destructivo | B02.08, B10.02 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B10_02_IMPLEMENTACION.json); antecedente30oct conservado | Acceso habitual AP_Personal_20261101 a PG55433 local; Python embebido propio. No implica portabilidad del clúster a otro PC. | 2026-11-01 / B03.06 |
| L29 | Pendiente de diseño/datos | Live con reloj/posesiones real, como módulo nuevo | B12.01, B12.02, B12.04, B12.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B12_05_DICTAMEN.json); antecedente30oct conservado | Sin archivo causal/contrato acreditado de reloj/posesiones y revisiones. Sigue entrecuartos, no tiempo real; no candidato. | 2026-11-01 / B03.06 |
| L30 | Pendiente de fuentes | Lesiones/alineaciones/xG como features acreditadas | B12.01, B12.03–B12.05 | [Recibo](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/EJECUCION_PLAN_MAESTRO_2026-10-31/B12_05_DICTAMEN.json); antecedente30oct conservado | Lesiones/alineaciones/xG sin cobertura/asof/reutilización suficientes; fuente puntual o columna presente no basta. ResidualWEB pendiente. | 2026-11-01 / B03.06 |

## Invariantes por lote

Conservar previos/modos/paquetes y secretos. Loopback; no tocar5432/servicios ajenos. GET sin escrituras/fit. Escrituras de prueba solo en clones identificados. Una carga numérica pesada. Sin cron/pagos/activaciones implícitas. NBA neutral; residual WEB preservado. H4 histórico Git no se purga parcialmente: proveedor cerró ticket sin coordinación; no force ni reescritura por arrastre.

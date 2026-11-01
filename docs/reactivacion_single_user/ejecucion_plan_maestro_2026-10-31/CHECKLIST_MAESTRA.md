# Checklist maestra — AnalyticsPredict

Revisión del control: 134

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

- [ ] **B03.04** — Validar el lote, usar identidad Git acordada `UNIVERSIDAD21 <efuentes1@udi.edu.co>`, publicar sin force y comprobar CI del SHA exacto conforme a las autorizaciones existentes.
  - Estado: EN_CURSO
  - Depende de: B03.03
  - Agente y actualización COT / UTC: Borlty-Predict / 2026-11-01T09:43:35.497014-05:00 / 2026-11-01T14:43:35.497014+00:00
  - Criterio de aceptación: Validar el lote, usar identidad Git acordada `UNIVERSIDAD21 <efuentes1@udi.edu.co>`, publicar sin force y comprobar CI del SHA exacto conforme a las autorizaciones existentes.
  - Resultado observado: Validación frontend final registrada; revisar todos los controles antes de commit/push.
  - Evidencia y versión/corte: C:\Users\ING-ERIK\AnalyticsPredict\Carpeta de Entregas de Borlty\EJECUCION_PLAN_MAESTRO_2026-10-31\B03_FRONTEND_FINAL.json #sha256=0b09318e4bec2fddab903c5aa73c9f1d596767d294545d89a32be8bc833347ec
  - Bloqueo o incidencia: Ninguno pendiente observado en este check.
  - Siguiente acción exacta: Continuar con el siguiente check ejecutable tras verificar dependencias.
  - Revisión de última transición: 134

- [ ] **B03.05** — Emitir una release/paquete identificado y la matriz delta → commit → CI → paquete; actualizar documentación vigente sin borrar recibos históricos.
  - Estado: PENDIENTE
  - Depende de: B03.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Emitir una release/paquete identificado y la matriz delta → commit → CI → paquete; actualizar documentación vigente sin borrar recibos históricos.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Emitir una release/paquete identificado y la matriz delta → commit → CI → paquete; actualizar documentación vigente sin borrar recibos históricos.
  - Revisión de última transición: 0

## B04 — PENDIENTE

- [ ] **B04.01** — Medir censo local por deporte/competición/temporada/fase: identidades, estados, fechas, fuentes, nulos, duplicados y conflictos.
  - Estado: PENDIENTE
  - Depende de: B02.08
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Medir censo local por deporte/competición/temporada/fase: identidades, estados, fechas, fuentes, nulos, duplicados y conflictos.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Medir censo local por deporte/competición/temporada/fase: identidades, estados, fechas, fuentes, nulos, duplicados y conflictos.
  - Revisión de última transición: 0

- [ ] **B04.02** — Verificar periodos, OT, conciliación de totales y targets por familia, manteniendo NULL/ceros y fechas sin hora correctamente diferenciados.
  - Estado: PENDIENTE
  - Depende de: B04.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Verificar periodos, OT, conciliación de totales y targets por familia, manteniendo NULL/ceros y fechas sin hora correctamente diferenciados.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Verificar periodos, OT, conciliación de totales y targets por familia, manteniendo NULL/ceros y fechas sin hora correctamente diferenciados.
  - Revisión de última transición: 0

- [ ] **B04.03** — Construir la matriz objetivo × campos necesarios × elegibles × abstenciones × disponibilidad temporal; no inflar muestras con filas espejadas.
  - Estado: PENDIENTE
  - Depende de: B04.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Construir la matriz objetivo × campos necesarios × elegibles × abstenciones × disponibilidad temporal; no inflar muestras con filas espejadas.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Construir la matriz objetivo × campos necesarios × elegibles × abstenciones × disponibilidad temporal; no inflar muestras con filas espejadas.
  - Revisión de última transición: 0

- [ ] **B04.04** — Conciliar artefactos, calibradores realmente aplicados, versiones y políticas; inventariar originales y cohortes presentes/ausentes.
  - Estado: PENDIENTE
  - Depende de: B04.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Conciliar artefactos, calibradores realmente aplicados, versiones y políticas; inventariar originales y cohortes presentes/ausentes.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Conciliar artefactos, calibradores realmente aplicados, versiones y políticas; inventariar originales y cohortes presentes/ausentes.
  - Revisión de última transición: 0

- [ ] **B04.05** — Congelar datasets aptos con consultas/filtros/manifiestos/hashes y emitir backlog medido; mantener N/D cuando no exista denominador oficial de cobertura.
  - Estado: PENDIENTE
  - Depende de: B04.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Congelar datasets aptos con consultas/filtros/manifiestos/hashes y emitir backlog medido; mantener N/D cuando no exista denominador oficial de cobertura.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Congelar datasets aptos con consultas/filtros/manifiestos/hashes y emitir backlog medido; mantener N/D cuando no exista denominador oficial de cobertura.
  - Revisión de última transición: 0

## B05 — PENDIENTE

- [ ] **B05.01** — Priorizar faltantes acreditados a partir de B04; permitir concluir sin cambios cuando no haya un lote elegible.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Priorizar faltantes acreditados a partir de B04; permitir concluir sin cambios cuando no haya un lote elegible.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Priorizar faltantes acreditados a partir de B04; permitir concluir sin cambios cuando no haya un lote elegible.
  - Revisión de última transición: 0

- [ ] **B05.02** — Preparar captura fuente fechada, identidad, diff/dry-run y respaldo recuperable de cada lote autorizado; reutilizar pipelines existentes.
  - Estado: PENDIENTE
  - Depende de: B05.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Preparar captura fuente fechada, identidad, diff/dry-run y respaldo recuperable de cada lote autorizado; reutilizar pipelines existentes.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Preparar captura fuente fechada, identidad, diff/dry-run y respaldo recuperable de cada lote autorizado; reutilizar pipelines existentes.
  - Revisión de última transición: 0

- [ ] **B05.03** — Ensayar el lote en clon y comprobar que no degrada valores presentes, identidades, periodos, horarios o targets.
  - Estado: PENDIENTE
  - Depende de: B05.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Ensayar el lote en clon y comprobar que no degrada valores presentes, identidades, periodos, horarios o targets.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Ensayar el lote en clon y comprobar que no degrada valores presentes, identidades, periodos, horarios o targets.
  - Revisión de última transición: 0

- [ ] **B05.04** — Aplicar únicamente el lote local permitido; verificar postflight independiente e idempotencia al repetirlo.
  - Estado: PENDIENTE
  - Depende de: B05.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Aplicar únicamente el lote local permitido; verificar postflight independiente e idempotencia al repetirlo.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Aplicar únicamente el lote local permitido; verificar postflight independiente e idempotencia al repetirlo.
  - Revisión de última transición: 0

- [ ] **B05.05** — Publicar el resultado/alcance de la actualización sin modificar modelos y conservar el residual WEB que el propietario indicó dejar pendiente.
  - Estado: PENDIENTE
  - Depende de: B05.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Publicar el resultado/alcance de la actualización sin modificar modelos y conservar el residual WEB que el propietario indicó dejar pendiente.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Publicar el resultado/alcance de la actualización sin modificar modelos y conservar el residual WEB que el propietario indicó dejar pendiente.
  - Revisión de última transición: 0

## B06 — PENDIENTE

- [ ] **B06.01** — Inventariar originales con pistas nuevas verificables, sin repetir búsquedas agotadas ni usar memoria privada como evidencia.
  - Estado: PENDIENTE
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Inventariar originales con pistas nuevas verificables, sin repetir búsquedas agotadas ni usar memoria privada como evidencia.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Inventariar originales con pistas nuevas verificables, sin repetir búsquedas agotadas ni usar memoria privada como evidencia.
  - Revisión de última transición: 0

- [ ] **B06.02** — Resolver la presencia/ausencia de `DESARROLLO_V4_CORREGIDO.json` y `COHORTE_FUTURA_V4_CORREGIDA.json`, sus fuentes, política y hashes; si faltan, mantener L10 bloqueada.
  - Estado: PENDIENTE
  - Depende de: B06.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Resolver la presencia/ausencia de `DESARROLLO_V4_CORREGIDO.json` y `COHORTE_FUTURA_V4_CORREGIDA.json`, sus fuentes, política y hashes; si faltan, mantener L10 bloqueada.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Resolver la presencia/ausencia de `DESARROLLO_V4_CORREGIDO.json` y `COHORTE_FUTURA_V4_CORREGIDA.json`, sus fuentes, política y hashes; si faltan, mantener L10 bloqueada.
  - Revisión de última transición: 0

- [ ] **B06.03** — Para originales disponibles, recargar con fit bloqueado y reproducir features, predicciones y abstenciones sin alterar sus archivos.
  - Estado: PENDIENTE
  - Depende de: B06.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Para originales disponibles, recargar con fit bloqueado y reproducir features, predicciones y abstenciones sin alterar sus archivos.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Para originales disponibles, recargar con fit bloqueado y reproducir features, predicciones y abstenciones sin alterar sus archivos.
  - Revisión de última transición: 0

- [ ] **B06.04** — Cotejar outcomes realmente posteriores por identidad/tiempo/target; conservar la ventana original y distinguir evaluación parcial, retrospectiva y prospectiva.
  - Estado: PENDIENTE
  - Depende de: B06.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Cotejar outcomes realmente posteriores por identidad/tiempo/target; conservar la ventana original y distinguir evaluación parcial, retrospectiva y prospectiva.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Cotejar outcomes realmente posteriores por identidad/tiempo/target; conservar la ventana original y distinguir evaluación parcial, retrospectiva y prospectiva.
  - Revisión de última transición: 0

- [ ] **B06.05** — Emitir evaluación o bloqueo por cohorte, sin regenerar V4 bajo el mismo nombre ni activar modelos por acumular resultados. Continuar otros frentes si falta una cohorte.
  - Estado: PENDIENTE
  - Depende de: B06.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Emitir evaluación o bloqueo por cohorte, sin regenerar V4 bajo el mismo nombre ni activar modelos por acumular resultados. Continuar otros frentes si falta una cohorte.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Emitir evaluación o bloqueo por cohorte, sin regenerar V4 bajo el mismo nombre ni activar modelos por acumular resultados. Continuar otros frentes si falta una cohorte.
  - Revisión de última transición: 0

## B07 — PENDIENTE

- [ ] **B07.01** — Fijar snapshot, población, cortes, baseline, hipótesis/variantes y funciones de cada partición antes de comparar resultados.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Fijar snapshot, población, cortes, baseline, hipótesis/variantes y funciones de cada partición antes de comparar resultados.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Fijar snapshot, población, cortes, baseline, hipótesis/variantes y funciones de cada partición antes de comparar resultados.
  - Revisión de última transición: 0

- [ ] **B07.02** — Preparar evaluación temporal reutilizando runners; verificar causalidad, simultáneos, transformaciones y tratamiento de fases.
  - Estado: PENDIENTE
  - Depende de: B07.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Preparar evaluación temporal reutilizando runners; verificar causalidad, simultáneos, transformaciones y tratamiento de fases.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Preparar evaluación temporal reutilizando runners; verificar causalidad, simultáneos, transformaciones y tratamiento de fases.
  - Revisión de última transición: 0

- [ ] **B07.03** — Ejecutar el benchmark emparejado de referencia/diseño vigente/candidatos con una carga pesada a la vez, preservando el modelo activo.
  - Estado: PENDIENTE
  - Depende de: B07.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Ejecutar el benchmark emparejado de referencia/diseño vigente/candidatos con una carga pesada a la vez, preservando el modelo activo.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Ejecutar el benchmark emparejado de referencia/diseño vigente/candidatos con una carga pesada a la vez, preservando el modelo activo.
  - Revisión de última transición: 0

- [ ] **B07.04** — Estimar dispersión y covarianza con residuos fuera de muestra; medir intervalos y sus anchuras por Q1–Q4 y total de regulación.
  - Estado: PENDIENTE
  - Depende de: B07.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Estimar dispersión y covarianza con residuos fuera de muestra; medir intervalos y sus anchuras por Q1–Q4 y total de regulación.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Estimar dispersión y covarianza con residuos fuera de muestra; medir intervalos y sus anchuras por Q1–Q4 y total de regulación.
  - Revisión de última transición: 0

- [ ] **B07.05** — Reportar errores, sesgos, probabilidades definidas, coberturas, soporte y abstenciones con denominador completo; impedir selección sobre TEST/EVAL.
  - Estado: PENDIENTE
  - Depende de: B07.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Reportar errores, sesgos, probabilidades definidas, coberturas, soporte y abstenciones con denominador completo; impedir selección sobre TEST/EVAL.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Reportar errores, sesgos, probabilidades definidas, coberturas, soporte y abstenciones con denominador completo; impedir selección sobre TEST/EVAL.
  - Revisión de última transición: 0

- [ ] **B07.06** — Registrar decisión mejora/no mejora/evidencia insuficiente, artefacto experimental y límites; actualizar L06/L07/L08 solo en lo acreditado.
  - Estado: PENDIENTE
  - Depende de: B07.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Registrar decisión mejora/no mejora/evidencia insuficiente, artefacto experimental y límites; actualizar L06/L07/L08 solo en lo acreditado.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Registrar decisión mejora/no mejora/evidencia insuficiente, artefacto experimental y límites; actualizar L06/L07/L08 solo en lo acreditado.
  - Revisión de última transición: 0

## B08 — PENDIENTE

- [ ] **B08.01** — Fijar protocolo y población apta propios de Euroliga, con baseline y contrato de 40 minutos/push.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Fijar protocolo y población apta propios de Euroliga, con baseline y contrato de 40 minutos/push.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Fijar protocolo y población apta propios de Euroliga, con baseline y contrato de 40 minutos/push.
  - Revisión de última transición: 0

- [ ] **B08.02** — Ejecutar y decidir el benchmark Euro, soporte de equipos nuevos y contracción si los datos lo permiten; separar candidato de refit.
  - Estado: PENDIENTE
  - Depende de: B08.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Ejecutar y decidir el benchmark Euro, soporte de equipos nuevos y contracción si los datos lo permiten; separar candidato de refit.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Ejecutar y decidir el benchmark Euro, soporte de equipos nuevos y contracción si los datos lo permiten; separar candidato de refit.
  - Revisión de última transición: 0

- [ ] **B08.03** — Identificar una hipótesis WNBA nueva y justificada, o documentar que no procede repetir el ensayo anterior que eligió k0.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Identificar una hipótesis WNBA nueva y justificada, o documentar que no procede repetir el ensayo anterior que eligió k0.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Identificar una hipótesis WNBA nueva y justificada, o documentar que no procede repetir el ensayo anterior que eligió k0.
  - Revisión de última transición: 0

- [ ] **B08.04** — Evaluar la hipótesis WNBA admisible con sus propios datos/denominadores, regulación y OT separados; mantener gates y fallback no activado mientras no haya evidencia suficiente.
  - Estado: PENDIENTE
  - Depende de: B08.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Evaluar la hipótesis WNBA admisible con sus propios datos/denominadores, regulación y OT separados; mantener gates y fallback no activado mientras no haya evidencia suficiente.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Evaluar la hipótesis WNBA admisible con sus propios datos/denominadores, regulación y OT separados; mantener gates y fallback no activado mientras no haya evidencia suficiente.
  - Revisión de última transición: 0

- [ ] **B08.05** — Definir el alcance de conteos fútbol por competición/familia y sus datos causales, reutilizando métodos y contratos existentes.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Definir el alcance de conteos fútbol por competición/familia y sus datos causales, reutilizando métodos y contratos existentes.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Definir el alcance de conteos fútbol por competición/familia y sus datos causales, reutilizando métodos y contratos existentes.
  - Revisión de última transición: 0

- [ ] **B08.06** — Ejecutar el ensayo fútbol apto y documentar decisión/abstenciones; mantener V4 separada del loader legacy.
  - Estado: PENDIENTE
  - Depende de: B08.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Ejecutar el ensayo fútbol apto y documentar decisión/abstenciones; mantener V4 separada del loader legacy.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Ejecutar el ensayo fútbol apto y documentar decisión/abstenciones; mantener V4 separada del loader legacy.
  - Revisión de última transición: 0

- [ ] **B08.07** — Entregar resultados independientes por dominio y actualizar L11/L12/L13 conforme a evidencia; un deporte bloqueado no cierra ni paraliza los demás.
  - Estado: PENDIENTE
  - Depende de: B08.06
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Entregar resultados independientes por dominio y actualizar L11/L12/L13 conforme a evidencia; un deporte bloqueado no cierra ni paraliza los demás.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Entregar resultados independientes por dominio y actualizar L11/L12/L13 conforme a evidencia; un deporte bloqueado no cierra ni paraliza los demás.
  - Revisión de última transición: 0

## B09 — PENDIENTE

- [ ] **B09.01** — Fijar la política aplicable y separar selección, estimación de dispersión, ajuste de calibrador y evaluación posterior.
  - Estado: PENDIENTE
  - Depende de: B04.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Fijar la política aplicable y separar selección, estimación de dispersión, ajuste de calibrador y evaluación posterior.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Fijar la política aplicable y separar selección, estimación de dispersión, ajuste de calibrador y evaluación posterior.
  - Revisión de última transición: 0

- [ ] **B09.02** — Ajustar/evaluar solo cuando haya muestras aptas; conservar RAW, calibrada, hashes, versión, mercado, línea y fechas sin etiquetas ficticias.
  - Estado: PENDIENTE
  - Depende de: B09.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Ajustar/evaluar solo cuando haya muestras aptas; conservar RAW, calibrada, hashes, versión, mercado, línea y fechas sin etiquetas ficticias.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Ajustar/evaluar solo cuando haya muestras aptas; conservar RAW, calibrada, hashes, versión, mercado, línea y fechas sin etiquetas ficticias.
  - Revisión de última transición: 0

- [ ] **B09.03** — Congelar emisiones nuevas antes de los eventos con denominador/abstenciones completos y sin picks/stakes/recomendaciones NBA.
  - Estado: PENDIENTE
  - Depende de: B09.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Congelar emisiones nuevas antes de los eventos con denominador/abstenciones completos y sin picks/stakes/recomendaciones NBA.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Congelar emisiones nuevas antes de los eventos con denominador/abstenciones completos y sin picks/stakes/recomendaciones NBA.
  - Revisión de última transición: 0

- [ ] **B09.04** — Incorporar y evaluar outcomes posteriores disponibles sin fit; registrar espera externa cuando todavía falten eventos o muestra, sin bloquear otras entregas.
  - Estado: PENDIENTE
  - Depende de: B09.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Incorporar y evaluar outcomes posteriores disponibles sin fit; registrar espera externa cuando todavía falten eventos o muestra, sin bloquear otras entregas.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Incorporar y evaluar outcomes posteriores disponibles sin fit; registrar espera externa cuando todavía falten eventos o muestra, sin bloquear otras entregas.
  - Revisión de última transición: 0

- [ ] **B09.05** — Determinar el estado de cada versión/objetivo según su política. Activar únicamente si cumple los criterios y existe la autorización aplicable; conservar rollback y decisión registrada.
  - Estado: PENDIENTE
  - Depende de: B09.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Determinar el estado de cada versión/objetivo según su política. Activar únicamente si cumple los criterios y existe la autorización aplicable; conservar rollback y decisión registrada.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Determinar el estado de cada versión/objetivo según su política. Activar únicamente si cumple los criterios y existe la autorización aplicable; conservar rollback y decisión registrada.
  - Revisión de última transición: 0

## B10 — PENDIENTE

- [ ] **B10.01** — Definir contrato y ubicación estable fuera de releases para el almacén personal. Preferencia: SQLite de la biblioteca estándar, manteniendo PostgreSQL deportivo y el modo base independientes. Cambiar esa elección solo por una razón técnica concreta documentada.
  - Estado: PENDIENTE
  - Depende de: B00.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Definir contrato y ubicación estable fuera de releases para el almacén personal. Preferencia: SQLite de la biblioteca estándar, manteniendo PostgreSQL deportivo y el modo base independientes. Cambiar esa elección solo por una razón técnica concreta documentada.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Definir contrato y ubicación estable fuera de releases para el almacén personal. Preferencia: SQLite de la biblioteca estándar, manteniendo PostgreSQL deportivo y el modo base independientes. Cambiar esa elección solo por una razón técnica concreta documentada.
  - Revisión de última transición: 0

- [ ] **B10.02** — Implementar persistencia explícita de snapshots, IDs, notas, etiquetas, favoritos y revisiones; validación, conflictos y confirmación real de guardado.
  - Estado: PENDIENTE
  - Depende de: B10.01, B03.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Implementar persistencia explícita de snapshots, IDs, notas, etiquetas, favoritos y revisiones; validación, conflictos y confirmación real de guardado.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Implementar persistencia explícita de snapshots, IDs, notas, etiquetas, favoritos y revisiones; validación, conflictos y confirmación real de guardado.
  - Revisión de última transición: 0

- [ ] **B10.03** — Importar el contenido actual del navegador mediante acción visible, vista previa y respaldo anterior; conservar el original hasta verificar la migración y su reversión.
  - Estado: PENDIENTE
  - Depende de: B10.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Importar el contenido actual del navegador mediante acción visible, vista previa y respaldo anterior; conservar el original hasta verificar la migración y su reversión.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Importar el contenido actual del navegador mediante acción visible, vista previa y respaldo anterior; conservar el original hasta verificar la migración y su reversión.
  - Revisión de última transición: 0

- [ ] **B10.04** — Mantener import/export JSON y compatibilidad declarada con respaldos anteriores; fijar capacidad medida sin truncar datos ni quitar límites sin verificar consecuencias.
  - Estado: PENDIENTE
  - Depende de: B10.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Mantener import/export JSON y compatibilidad declarada con respaldos anteriores; fijar capacidad medida sin truncar datos ni quitar límites sin verificar consecuencias.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Mantener import/export JSON y compatibilidad declarada con respaldos anteriores; fijar capacidad medida sin truncar datos ni quitar límites sin verificar consecuencias.
  - Revisión de última transición: 0

- [ ] **B10.05** — Probar navegadores/pestañas independientes, conflictos, almacenamiento lleno, cierre abrupto y conservación exacta de resultados/timestamps.
  - Estado: PENDIENTE
  - Depende de: B10.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Probar navegadores/pestañas independientes, conflictos, almacenamiento lleno, cierre abrupto y conservación exacta de resultados/timestamps.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Probar navegadores/pestañas independientes, conflictos, almacenamiento lleno, cierre abrupto y conservación exacta de resultados/timestamps.
  - Revisión de última transición: 0

- [ ] **B10.06** — Respaldar SQLite de forma consistente y restaurar en un destino nuevo; incluir este almacén en el procedimiento de recuperación junto a PostgreSQL, artefactos y configuración protegida, indicando los cortes de cada uno.
  - Estado: PENDIENTE
  - Depende de: B10.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Respaldar SQLite de forma consistente y restaurar en un destino nuevo; incluir este almacén en el procedimiento de recuperación junto a PostgreSQL, artefactos y configuración protegida, indicando los cortes de cada uno.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Respaldar SQLite de forma consistente y restaurar en un destino nuevo; incluir este almacén en el procedimiento de recuperación junto a PostgreSQL, artefactos y configuración protegida, indicando los cortes de cada uno.
  - Revisión de última transición: 0

## B11 — PENDIENTE

- [ ] **B11.01** — Identificar fricciones reales en Hoy → encuentro → análisis → Mis análisis/Seguimiento → reapertura, conservando la navegación ya agrupada.
  - Estado: PENDIENTE
  - Depende de: B02.08
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Identificar fricciones reales en Hoy → encuentro → análisis → Mis análisis/Seguimiento → reapertura, conservando la navegación ya agrupada.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Identificar fricciones reales en Hoy → encuentro → análisis → Mis análisis/Seguimiento → reapertura, conservando la navegación ya agrupada.
  - Revisión de última transición: 0

- [ ] **B11.02** — Medir arranque frío/caliente, lecturas/análisis, CPU/RAM y varias pestañas con escenarios y repeticiones declarados.
  - Estado: PENDIENTE
  - Depende de: B11.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Medir arranque frío/caliente, lecturas/análisis, CPU/RAM y varias pestañas con escenarios y repeticiones declarados.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Medir arranque frío/caliente, lecturas/análisis, CPU/RAM y varias pestañas con escenarios y repeticiones declarados.
  - Revisión de última transición: 0

- [ ] **B11.03** — Corregir únicamente cuellos observados y verificar inclusión/comportamiento de las reparaciones de concurrencia previas, sin venderlas de nuevo como funcionalidad nueva.
  - Estado: PENDIENTE
  - Depende de: B11.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Corregir únicamente cuellos observados y verificar inclusión/comportamiento de las reparaciones de concurrencia previas, sin venderlas de nuevo como funcionalidad nueva.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Corregir únicamente cuellos observados y verificar inclusión/comportamiento de las reparaciones de concurrencia previas, sin venderlas de nuevo como funcionalidad nueva.
  - Revisión de última transición: 0

- [ ] **B11.04** — Comparar resultados antes/después sin modificar matemática, repetir POST, compartir contexto entre ligas u ocultar datos con TTL o timeouts mayores.
  - Estado: PENDIENTE
  - Depende de: B11.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Comparar resultados antes/después sin modificar matemática, repetir POST, compartir contexto entre ligas u ocultar datos con TTL o timeouts mayores.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Comparar resultados antes/después sin modificar matemática, repetir POST, compartir contexto entre ligas u ocultar datos con TTL o timeouts mayores.
  - Revisión de última transición: 0

- [ ] **B11.05** — Verificar teclado, foco, temas y estados con datos/vacío/error en escritorio y pantalla estrecha con dimensiones efectivamente aplicadas; documentar cualquier entorno no probado.
  - Estado: PENDIENTE
  - Depende de: B11.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Verificar teclado, foco, temas y estados con datos/vacío/error en escritorio y pantalla estrecha con dimensiones efectivamente aplicadas; documentar cualquier entorno no probado.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Verificar teclado, foco, temas y estados con datos/vacío/error en escritorio y pantalla estrecha con dimensiones efectivamente aplicadas; documentar cualquier entorno no probado.
  - Revisión de última transición: 0

## B12 — PENDIENTE

- [ ] **B12.01** — Acotar viabilidad, fuentes, contratos y criterio de posponer/abandonar para reloj/posesiones y nuevas variables.
  - Estado: PENDIENTE
  - Depende de: B04.05
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Acotar viabilidad, fuentes, contratos y criterio de posponer/abandonar para reloj/posesiones y nuevas variables.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Acotar viabilidad, fuentes, contratos y criterio de posponer/abandonar para reloj/posesiones y nuevas variables.
  - Revisión de última transición: 0

- [ ] **B12.02** — Acreditar reloj/marcador/posesión/revisiones/orden de llegada antes de desarrollar un módulo live; no equiparar cierre de cuarto con tiempo real.
  - Estado: PENDIENTE
  - Depende de: B12.01
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Acreditar reloj/marcador/posesión/revisiones/orden de llegada antes de desarrollar un módulo live; no equiparar cierre de cuarto con tiempo real.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Acreditar reloj/marcador/posesión/revisiones/orden de llegada antes de desarrollar un módulo live; no equiparar cierre de cuarto con tiempo real.
  - Revisión de última transición: 0

- [ ] **B12.03** — Acreditar cobertura, definiciones y disponibilidad temporal de lesiones, alineaciones y xG, respetando permisos y el residual WEB pendiente.
  - Estado: PENDIENTE
  - Depende de: B12.02
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Acreditar cobertura, definiciones y disponibilidad temporal de lesiones, alineaciones y xG, respetando permisos y el residual WEB pendiente.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Acreditar cobertura, definiciones y disponibilidad temporal de lesiones, alineaciones y xG, respetando permisos y el residual WEB pendiente.
  - Revisión de última transición: 0

- [ ] **B12.04** — Solo con insumos suficientes, construir candidato aislado y evaluar su aporte con ablaciones y protocolo propio.
  - Estado: PENDIENTE
  - Depende de: B12.03
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Solo con insumos suficientes, construir candidato aislado y evaluar su aporte con ablaciones y protocolo propio.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Solo con insumos suficientes, construir candidato aislado y evaluar su aporte con ablaciones y protocolo propio.
  - Revisión de última transición: 0

- [ ] **B12.05** — Emitir decisión de viabilidad o límites por capacidad; actualizar L29/L30 solo si sus criterios reales se acreditan. No bloquea los hitos operativos.
  - Estado: PENDIENTE
  - Depende de: B12.04
  - Agente y actualización COT / UTC: Sin ejecutar
  - Criterio de aceptación: Emitir decisión de viabilidad o límites por capacidad; actualizar L29/L30 solo si sus criterios reales se acreditan. No bloquea los hitos operativos.
  - Resultado observado: No ejecutado.
  - Evidencia y versión/corte: Sin evidencia de cierre.
  - Bloqueo o incidencia: Ninguno observado.
  - Siguiente acción exacta: Emitir decisión de viabilidad o límites por capacidad; actualizar L29/L30 solo si sus criterios reales se acreditan. No bloquea los hitos operativos.
  - Revisión de última transición: 0

## Matriz L01–L30

19 implementadas en alcance / 4 parciales / 7 pendientes-bloqueadas, heredadas al30oct. Fuente verificable: `E/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json`. B01/B02 cierran operación, no eficacia. Revisión científica pendiente por los checks enlazados.

| ID | Estado | Objetivo | Bloques vinculados | Evidencia y corte | Criterio pendiente / límite vigente | Última revisión |
|---|---|---|---|---|---|---|
| L01 | Implementada | Locks/ejecución/permisos compatibles con Windows | Compatibilidad Windows | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Compatibilidad de rutas intervenidas; operación real de sincronización no ejecutada | 2026-11-01 / B03.03 |
| L02 | Implementada | UTF-8 explícito y recarga íntegra de artefactos/journals | UTF-8 e integridad | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | UTF-8 de artefactos/journals/CLIs intervenidos; no conversión de archivos originales | 2026-11-01 / B03.03 |
| L03 | Implementada | Separar consulta NBA y ajuste/registro de versiones | Consulta NBA separada del fit | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | PRE no ajusta/crea versiones; entrenamiento solo explícito | 2026-11-01 / B03.03 |
| L04 | Implementada | Confianza y explicaciones sin muestras/factores ficticios | Explicaciones sin factores ficticios | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Sin factores/muestras/intervalos inventados; completar con evidencia real, no defaults | 2026-11-01 / B03.03 |
| L05 | Implementada | Total/regulación/OT/push y origen de probabilidad inequívocos | Regulación/OT/push y probabilidad | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Mismo origen de media/p NBA; contrato RAW/regulación/OT por liga. Enteras legacy sin push: evento N/D, campos originales preservados | 2026-11-01 / B03.03 |
| L06 | Parcial | Benchmark local actual vs referencia vs candidato | Benchmark NBA | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Laboratorio expone comparaciones originales; falta nuevo benchmark NBA emparejado | 2026-11-01 / B03.03 |
| L07 | Pendiente de datos | NBA con recencia y forma causal aprendidas | Recencia/forma causal NBA | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Recencia/forma causal NBA: snapshot elegible y protocolo antes de medir | 2026-11-01 / B03.03 |
| L08 | Pendiente de datos | NBA: dispersión temporal/covarianza/intervalos | Dispersión/covarianza fuera de muestra | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Errores fuera de muestra y covarianza por candidato/objetivo | 2026-11-01 / B03.03 |
| L09 | Parcial | Calibración y fiabilidad por versión/objetivo | Calibración y fiabilidad por versión | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Diagnóstico RAW WNBA original visible y métricas reproducidas sin fit; falta evaluación/calibración independiente del refit y cohorte futura. Ningún calibrador activado | 2026-11-01 / B03.03 |
| L10 | Bloqueada por originales | Retomar evaluación de V4, no regenerarla | Originales V4 corregidos | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Recuperar desarrollo/cohorte V4 corregidos y outcomes; no sustituirlos | 2026-11-01 / B03.03 |
| L11 | Pendiente de benchmark | Euro: recencia/regularización y mejora frente a media de liga | Benchmark temporal Euro | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Euro: comparación temporal nueva, no heredar evaluación del refit | 2026-11-01 / B03.03 |
| L12 | Parcial | WNBA/Euro: equipos nuevos y contracción hacia liga | Contracción y equipos nuevos | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | WNBA evaluada: CAL eligió k0, sin mejora; fallback no activado. Euro aún sin snapshot | 2026-11-01 / B03.03 |
| L13 | Pendiente de datos | Fútbol: parámetros de conteo/ataque/defensa por competición | Conteos fútbol por familia/competición | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Conteos fútbol por competición/familia y disponibilidad causal | 2026-11-01 / B03.03 |
| L14 | Parcial | Priorización de cobertura por usos habituales | Cobertura prioritaria medida | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Prioridad por favoritos/copias e inventario BD explícito de solo lectura implementados; medición vigente bloqueada por cuota. Sin denominador oficial ni llenado de gaps | 2026-11-01 / B03.03 |
| L15 | Implementada | Cortes, fuente y calidad visibles en cada resultado | Trazabilidad de resultados | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Trazabilidad común NBA/Euro/WNBA/fútbol y base local; datos no conservados N/D | 2026-11-01 / B03.03 |
| L16 | Implementada | Portada Hoy y acceso directo a la ficha | Hoy, agendas y paginación | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Hoy reutiliza agendas, enlace a ficha y estados parciales; BD real pendiente | 2026-11-01 / B03.03 |
| L17 | Implementada | Sistema visual sobrio, temas y fuentes locales | Sistema visual y temas | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Base visual sobria y preferencias; quedan componentes legados con colores propios | 2026-11-01 / B03.03 |
| L18 | Implementada | Ficha única con detalle progresivo y menos controles repetidos | Fichas y detalle progresivo | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Fichas baloncesto/fútbol progresivas; agenda y seguimiento separados de configuración | 2026-11-01 / B03.03 |
| L19 | Implementada | Favoritos, notas y etiquetas cross-liga | Notas, etiquetas y favoritos | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Favoritos de consultas, equipos, ligas/competiciones; notas/etiquetas y almacenamiento aislado | 2026-11-01 / B03.03 |
| L20 | Implementada | Comparador de líneas sin recalcular modelo | Comparador de la misma corrida | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | NBA base/Euro y PMF WNBA de la misma corrida; fútbol solo líneas ya calculadas. Copias sin contrato N/D | 2026-11-01 / B03.03 |
| L21 | Implementada | Reapertura/exportación reproducible de análisis | Copias, reapertura y respaldo/importador existentes | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Importador JSON con preview ya existe y se conserva; B10 amplía a almacén personal durable, no rehace el respaldo. | 2026-11-01 / B03.03 |
| L22 | Implementada | Modo base local sin BD con límites visibles | Modo base NBA/Euro/WNBA | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Modo base congelado NBA/Euro/WNBA ya existe; no requiere BD ni fit. B10 preserva los resultados originales. | 2026-11-01 / B03.03 |
| L23 | Implementada | Error/vacío/N/D consistentes, sin falsos conteos cero | Error/vacío/N/D diferenciados | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Error no equivale a cero; fuentes ausentes N/D en superficies intervenidas | 2026-11-01 / B03.03 |
| L24 | Implementada | Teclado, legibilidad y movimiento reducido | Accesibilidad inicial | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Etiquetas/errores y salto de foco verificados en36estados; no certificación WCAG de todos los estados | 2026-11-01 / B03.03 |
| L25 | Implementada | Pruebas Windows y reloj determinista en fixtures | Windows, CI y fixtures | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | CI Windows, UTF-8 real y fixture futura sin fecha de caducidad fija | 2026-11-01 / B03.03 |
| L26 | Implementada | Invalidación de caché por revisión de datos/alcance | Invalidación y aislamiento de contexto | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Relectura conservadora sin LRU; no clave de revisión inventada | 2026-11-01 / B03.03 |
| L27 | Implementada | Extraer cálculo/acceso a datos de rutas monolíticas | Extracciones acotadas de lógica/acceso | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Cálculo NBA base y matemática/lecturas fútbol separados de HTTP; equivalencia; no reescritura total | 2026-11-01 / B03.03 |
| L28 | Implementada | Acceso de inicio local claro y no destructivo | Inicio local autónomo | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Runtime propio y arranque base ya acreditados. B02 añade destino deportivo local verificado; no promete portabilidad PG entre PCs. | 2026-11-01 / B03.03 |
| L29 | Pendiente de diseño/datos | Live con reloj/posesiones real, como módulo nuevo | Live con reloj/posesiones | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Live por reloj/posesiones exige fuente temporal y evaluación nuevas | 2026-11-01 / B03.03 |
| L30 | Pendiente de fuentes | Lesiones/alineaciones/xG como features acreditadas | Lesiones/alineaciones/xG causales | [Antecedente](C:/Users/ING-ERIK/AnalyticsPredict/Carpeta%20de%20Entregas%20de%20Borlty/RESUMEN_IMPLEMENTACION_LOCAL_2026-10-30/BACKLOG_ACTUAL.json); B02.08 operativo | Lesiones/alineaciones/xG con cobertura y disponibilidad acreditadas | 2026-11-01 / B03.03 |

## Invariantes por lote

Conservar previos/modos/paquetes y secretos. Loopback; no tocar5432/servicios ajenos. GET sin escrituras/fit. Escrituras de prueba solo en clones identificados. Una carga numérica pesada. Sin cron/pagos/activaciones implícitas. NBA neutral; residual WEB preservado. H4 histórico Git no se purga parcialmente: proveedor cerró ticket sin coordinación; no force ni reescritura por arrastre.

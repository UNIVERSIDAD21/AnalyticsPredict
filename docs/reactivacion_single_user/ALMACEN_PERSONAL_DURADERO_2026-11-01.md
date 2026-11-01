# Mis análisis duradero — contrato del 1-nov-2026

## Elección y alcance

SQLite de la biblioteca estándar, separado de PostgreSQL deportivo. Ubicación
predeterminada estable: `~/AnalyticsPredict/Datos privados locales/personal/`.
El backend admite un directorio configurado por el operador para pruebas o
recuperación; ningún cliente HTTP elige una ruta. No va dentro de releases/Git.
JSON atómico no aporta control de concurrencia/backup transaccional equivalente
sin reimplementar esas funciones. Usar PostgreSQL impediría Mis análisis cuando
se usa el modo base sin BD deportiva. No se añade un servidor o dependencia.

## Contrato

- Documento personal versionado: consultas con ID, snapshot original, timestamp,
  notas/etiquetas/favorito; favoritos de equipos/ligas/competiciones y apariencia
  opcional. No se mezcla con Seguimiento ni se recalcula un análisis al abrirlo.
- GET no crea archivos, esquema, migraciones, backups ni registros. Un almacén
  inexistente se identifica como tal, no como una migración de navegador hecha.
- Escritura JSON explícita con revisión esperada y UUID de operación. CAS
  transaccional: conflicto409 sin sobrescritura; repetir la misma operación
  devuelve el recibo previo, reutilizarla con otro contenido es conflicto.
- Una consulta existente mantiene snapshot, ID, fecha, liga y tipo inmutables;
  solo cambian organización/notas o una eliminación explícita. Validación de
  profundidad, tipos estrictos, duplicados y capacidad antes de transaccionar.
- Se conservan100 consultas/4.000.000unidadesUTF-16,200 favoritos y compatibilidad
  con JSON personalv1/cuaderno anterior. No se amplía capacidad por comodidad.
- Acceso loopback con Host/Origin explícitos y cabecera de escritura propia;
  no se expone un explorador de archivos o API de rutas arbitrarias.
- SQLite DELETE/FULL evita escrituras auxiliares de una lectura normal. Un
  cierre abrupto con journal caliente puede requerir recuperación explícita;
  GET informa indisponibilidad, no escribe para ocultar el incidente. La
  recuperación usa SQLite, no borra journals manualmente.

## Navegador, conflictos y compatibilidad

Las copias anteriores permanecen en sus claves originales. La nueva superficie
identifica el almacén del PC y permite importar las copias del navegador mediante
vista previa y descarga de respaldo anterior. Un ID ya presente conserva la
versión del PC; los conflictos se cuentan, no se pisan. El original no se elimina.
La prueba aislada de importación no acredita importación del perfil habitual del
propietario: esa acción requiere su uso visible de la interfaz.

Las operaciones nuevas de guardar/editar se confirman después del commit y una
lectura de vuelta. No se anuncia éxito por escribir solo una caché del navegador.
Cada pestaña conserva la revisión que leyó; ante conflicto se solicita recarga,
sin repetir un POST deportivo. Las lecturas sirven al modo base sin PostgreSQL.

## Respaldo y recuperación

Backup consistente con `sqlite3.Connection.backup`, hash y revisión/corte. Restore
en archivo nuevo, integridad y contenido conciliados; nunca sobre el almacén
vigente desde una petición web. La guía completa debe incluir SQLite, dump de
PostgreSQL, artefactos y configuración privada, con sus cortes independientes.
Las copias del mismo SSD no protegen frente a pérdida física del dispositivo.

## Validación exigida antes de cierre

CRUD/precisión y NULL, CAS simultáneo, idempotencia, límites, permisos reales,
GET sin archivos/escrituras, guardas HTTP, disco lleno/rollback, cierre abrupto,
backup y restore nuevos, dos contextos de navegador y reapertura sin análisis.
Los recibos del control canónico distinguen implementación/pruebas/importación
real y bloqueos; este contrato no acredita esos checks por su mera existencia.

## Resultados verificados de implementación

1887 pruebas backend con PostgreSQL sintético (22 propias incluidas),232 frontend
sin omisiones,lint/build aprobados. Ensayo nativo100consultas/3769845UTF16,
7519878bytes de request:0,450s escritura y0,126s lectura en una medición, noSLA.
La101 devuelve422 sin truncar. Dos contextos independientes, conflicto con
borrador preservado, navegador sin espacio, preview/importación literal,
reapertura tras reinicio y captura1366/390 sin overflow/JS acreditados.
Los intentos intermedios fallidos se conservan en las evidencias del control.

Recuperación nativa: ejecutar con Python del paquete
`producto/scripts/respaldar_personal.py --respaldar`, o `--verificar ARCHIVO`.
Para restaurar: `--restaurar RESPALDO --destino NUEVO_DIRECTORIO/mis_analisis.sqlite3`.
Debe ser un archivo nuevo fuera del producto; no apunta ni sobrescribe el activo.
Para elegirlo como activo, el operador configura su directorio y reinicia la
aplicación tras conciliar el corte. La web no admite rutas enviadas por cliente.

La prueba final restaura el backup de revisión5 con2consultas y preserva íntegros
IDs/snapshots/fechas/notas. El respaldo previo de revisión4 permanece como corte
anterior, no se sustituye ni se hace pasar por el último estado.

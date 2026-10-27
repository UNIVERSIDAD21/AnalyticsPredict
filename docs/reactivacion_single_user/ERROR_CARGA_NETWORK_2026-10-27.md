# Error de carga «Network Error» — 2026-10-27

## Hechos observados

- Interfaz y API activas en 5173/8000; `/salud` devuelve 200 sin comprobar BD.
- Neon rechaza conexiones con «Your account or project has exceeded the quota».
  No se ha acreditado cuál límite concreto del proveedor se agotó.
- Equipos, agenda y competiciones fallan con 503 al agotar la adquisición de
  conexión. El navegador ocultaba algunos errores por falta de cabeceras CORS.
- La sincronización automática también reportó fallo; no se ha repetido la
  ingesta ni se ha modificado el timer previamente autorizado.

## Corrección

1. CORS queda por fuera de los middlewares de trazabilidad y solo lectura;
   se conserva la política de orígenes y se expone `X-Trace-Id`.
2. `PoolTimeout` y `OperationalError`, incluso encapsulados en HTTPException,
   reciben un error público `BASE_DATOS_NO_DISPONIBLE` sin detalles del driver.
3. El extractor del cliente prioriza errores del servidor y clasifica el fallo
   de red antes del mensaje genérico de Axios. La agenda lo utiliza y muestra
   «Datos no disponibles», no un conteo cero ficticio.
4. El botón Reintentar relee los datos; no activa sincronizaciones ni escrituras.

Se integran los prerrequisitos locales estrictamente necesarios: tratamiento
503 de PoolTimeout y eliminación del fallback prematuro de Axios. Otros cambios
locales anteriores quedan fuera de la publicación.

## Verificación y límite pendiente

Regresiones sobre el código previo reproducen el defecto: 16 casos backend y
2 frontend fallan. Corrección: 35 pruebas backend focalizadas aprobadas (incluyen
16 casos CORS), más 14 de contexto y contratos de lecturas HTTP; la prueba que
requiere PostgreSQL sintético fue excluida de esta corrida local (no se ejecuta
contra Neon). 136 pruebas frontend/33 archivos, lint y compilación aprobados.
Sin conexiones reales ni entrenamiento en las pruebas automatizadas. UI y API locales
verificadas con 503 legible y cabeceras de origen; capturas auténticas externas.
Los resultados finales frontend, compilación y CI por SHA constan en el acta
externa; no se deducen de ejecuciones intermedias.

**Estado: corrección de código, no recuperación de Neon.** Recuperar la carga
requiere que el propietario revise el consumo/límites en Neon y restablezca la
disponibilidad. Después, reintentar la agenda. No se ha pagado, cambiado de plan,
restaurado un backup sobre producción, cambiado la BD ni activado un fallback
local con datos potencialmente antiguos. No se acredita carga exitosa de datos
productivos mientras persiste la cuota excedida.

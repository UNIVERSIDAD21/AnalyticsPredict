# Mi espacio, runtime autónomo y consolidación de la continuación — 2026-10-30

## Uso y compatibilidad

- Una entrada principal **Mi espacio** agrupa **Mis análisis** (copias y notas del navegador) y **Seguimiento** (registros y resultados de la BD). No se mezclan almacenamientos, métricas ni identidades.
- Rutas canónicas `/mis-analisis` y `/seguimiento`. Los marcadores `/cuaderno`, `/mi-espacio`, `/bitacora` y `/futbol/bitacora` redirigen preservando parámetros y fragmentos. Las claves de localStorage, formatos de exportación y rutas API `/api/bitacora` no cambian.
- Se mantienen guardado, filtros, notas, respaldo/restauración y registros existentes. Abrir Mis análisis no monta el módulo de Seguimiento ni provoca sus lecturas SQL.
- Las acciones visibles identifican su destino: guardar una copia en Mis análisis es distinto de registrar en Seguimiento. No se crean ni convierten registros por renombrar la interfaz.

## Paquete Windows autónomo para modo base

`scripts/preparar_instalacion_local.py --autonomo` incluye Python 3.12 Windows x64,
la biblioteca estándar necesaria y las dependencias ya instaladas del entorno fuente.
No descarga paquetes, ejecuta pip ni copia una venv que mantenga `home` externo.
Conserva la licencia de Python y los metadatos/licencias de dependencias.

- Ejecutable en `runtime/python/python.exe`, sin `pyvenv.cfg`. `python312._pth` usa rutas relativas y aislamiento de PYTHONHOME/PYTHONPATH y paquetes del usuario.
- `RUNTIME_LOCAL.json` identifica el Python por ruta relativa. Los `.cmd` usan `%~dp0`: pueden abrirse tras trasladar la carpeta completa. Frontend ya compilado; Node/npm no hacen falta para ejecutar el modo base.
- SHA-256 cubre código, build, artefactos y runtime. Se comprueban identidad de producto y estabilidad de fuentes durante la preparación. Las rutas largas usan la API extendida de archivos de Windows sin tocar políticas globales.
- `scripts/verificar_runtime_local.py`, ejecutado con el Python del paquete, verifica aislamiento, ausencia de módulos externos, imports nativos, aritmética mínima y ZoneInfo Colombia. No conecta a BD, red ni ajusta modelos.
- `COMPROBAR_BASE_LOCAL.cmd` comprueba salud y artefactos y cierra únicamente sus procesos. El inicio no libera puertos ocupados.
- El inicio concede hasta 90 segundos al arranque en frío de la API (`--espera-api`, de 1 a 180), con reloj monotónico y salida anticipada si el proceso falla. Python inicia con UTF-8 explícito incluso bajo aislamiento.

**Autonomía de ejecución no significa migración de datos.** El modo base permite
consultar los artefactos publicados y trabajar con las copias del navegador. BD,
agendas/contexto, fútbol dependiente de BD y Seguimiento requieren restauración
verificada. El continuador de migración sigue necesitando PostgreSQL y el origen
autorizado por separado; no se empaquetan credenciales ni una BD vacía como sustituto.

## Control de versiones y preservación

La continuación de Codex (respaldo/Cuaderno, Hoy, multiliga/diagnóstico y preparador)
se integra sobre la rama publicada `78f434ed`, junto con esta orden, en
`mejoras/continuacion-autonoma-2026-10-30`. Los patches originales se conservan externos;
se normaliza solamente su cabecera de archivos nuevos para Git Windows.

`PaginaOperacion` contiene cambios anteriores exclusivos del checkout de trabajo:
se trasladan los cambios de modo base/diagnóstico sin publicar por arrastre el
inventario anterior ajeno a esta continuación. La copia activa conserva su rama,
HEAD e índice y recibe únicamente los deltas nuevos; no se ejecutan reset/clean.
La instalación autónoma integrada puede incluir esos cambios previos locales y
por ello su identidad de working tree se distingue del commit de publicación.

## Validación y límites

El recibo externo final identifica separadamente las pruebas de la rama publicada,
la integración activa y el paquete trasladado. Hay pruebas de redirección y montaje
exclusivo de secciones, contratos congelados sin BD/fit/journal, exclusiones,
licencias, runtime relativo, manipulación del binario y rutas largas.

El ensayo real de autonomía usa el ejecutable incluido desde otra ubicación y con
PATH limitado y PYTHONHOME/PYTHONPATH apuntando a rutas inexistentes. El recorrido
de UI no altera el perfil habitual del usuario ni registra apuestas reales.

No se modifican pesos, versiones, gates o datos de modelos. No se atribuye mejora
predictiva a estas pruebas. Migración `PREPARADO_NO_MIGRADO` y los pendientes del
catálogo científico mantienen sus condiciones de cierre.

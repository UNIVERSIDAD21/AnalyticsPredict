# Migración Windows: aislamiento, procesos propios y reanudación

La ejecución del plan se controla en la carpeta canónica `ejecucion_plan_maestro_2026-10-31` de la copia activa, no en snapshots empaquetados. Un dump de resguardo no significa que la aplicación esté migrada.

El Python autónomo conserva su `._pth` aislado. `scripts/ejecutar_herramienta_local.py` incorpora explícitamente solo el directorio de herramientas del paquete autorizado; no habilita PYTHONPATH, sites del usuario o importaciones desde rutas arbitrarias. Evita el fallo real `ModuleNotFoundError: verificar_bd` del primer export.

`scripts/operar_instalacion_local.py` registra cada hijo inmediatamente al crearlo, con PID, identidad temporal del proceso y log privado, antes de crear el siguiente. La espera HTTP usa reloj monotónico y 90 segundos por defecto (1–180). Ante fallo parcial cierra exclusivamente hijos con identidad coincidente; no libera puertos ocupados ni cierra un PID reutilizado. Conserva registro tanto del fallo como del cierre, y rechaza duplicar operaciones propias vivas.

La plantilla `CONTINUAR_MIGRACION.ps1` delega en `scripts/continuar_migracion_windows.ps1`. Exportación previa y configuración existente requieren reanudación explícita tras conciliar recibos/corte; no se sobrescriben. El camino de errores conserva el destino y detiene solo el clúster propio que intentó iniciar. `-SoloPreflight` no acredita conexión/export/restauración. `-SoloExportar` no arranca PostgreSQL local; `-SoloRestaurar` no inicia API/UI. El cierre sigue requiriendo cotejo final de escrituras del origen, UI auténtica, reinicio y restauración de un backup real.

Pruebas: bootstrap con hermano bajo aislamiento, rechazo de traversal, registro y cierre de hijos reales propios, rechazo de duplicación y PID con identidad distinta, arranque simulado a45s/timeout y limpieza automática si falla el segundo hijo. Sin red externa, BD deportiva o entrenamiento. Repeticiones y resultados definitivos están en los recibos del control.

## Locale de la BD restaurada

La primera restauración heredó libc C del clúster y cambió lower/upper de caracteres acentuados. Se conserva como evidencia, no se activa. Los locales Windows en-US/English_United States.1252 tampoco igualaron las constantes técnicas del origen. PostgreSQL18 builtin C.UTF-8 sí reprodujo esas conversiones; el restaurador versionado pide ese provider/locale explícitamente al crear una BD nueva. La ordenación por defecto puede diferir de en_US.utf8: no afirmar equivalencia universal de collations. Los identificadores, hashes y resultados se cotejan independientemente; el flujo real y los catálogos se validan antes del cierre.

Las herramientas versionadas en scripts/herramientas_windows se incorporan al preparar paquetes nuevos, manteniendo intactas y verificadas las herramientas originales del paquete de referencia. Cambiar locale nunca convierte el dump en otro ni permite sobrescribir la primera restauración.

## Reanudación y controles nativos del 1-nov

El intento inicial de clúster sintético falló antes de ejecutar pytest y su recibo conserva exit_code=null; no se cuenta como suite aprobada. El destino se preservó y se preparó otro directorio vacío. Tras verificar PID/extinción y posible reutilización, la suite global sobre PostgreSQL18 sintético aprobó1865 pruebas, sin fallos ni omisiones. El servicio ajeno5432 y la BD personal quedaron fuera de las pruebas.

Se normalizan separadores de ruta en la inyección de fallos HTTP y se declara explícitamente el directorio del módulo en el hijo de la prueba de locks bajo Python._pth. No se reduce el aislamiento del runtime. La evidencia privada PitchAPI aplica ACL reales usuario/SYSTEM antes de escribir, falla de forma cerrada y no deja temporales si no puede protegerlos; POSIX conserva600. No se ejecutó una consulta al proveedor.

La auditoría detectóGHSA-mrwp-f3q8-3g9p en follow-redirects1.16.1. Se cambia únicamente esa entrada del lock a1.16.2, sin actualizar transitivas no relacionadas. El recibo frontend distingue las225 regresiones completas anteriores al cambio de dependencia, las regresiones de servicios y el build/auditoría posteriores con dependencias propias. La CI del SHA publicado verifica el conjunto final.

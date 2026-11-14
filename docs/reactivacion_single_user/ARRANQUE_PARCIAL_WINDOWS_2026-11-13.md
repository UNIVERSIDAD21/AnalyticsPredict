# Acceso de escritorio con servicios parciales

El acceso manual `AnalyticsPredict.lnk` conserva su destino
`AnalyticsPredict/Abrir AnalyticsPredict.cmd`. El lanzador personal corresponde
a `scripts/abrir_analytics_predict.py`, instalado como
`AnalyticsPredict/Herramientas de arranque/abrir_analytics_predict.py`.
Requiere los operadores ya instalados en `producto/scripts`: no instala,
migra ni reconstruye una base de datos.

## Corrección

Con la interfaz encendida pero API y PostgreSQL apagados, el lanzador anterior
intentaba acreditar SQL sin iniciar la base. El acceso fallaba con
`ConnectionTimeout`, aunque su destino y la interfaz eran correctos.

La recuperación ahora conserva el lock diario, verifica los servicios existentes
y, solo si el puerto local 55433 está libre, inicia el clúster configurado mediante
el operador soportado. Guarda un recibo de la operación y acredita la identidad
SQL antes de recuperar la API. Si el puerto ya está ocupado, exige acreditar su
identidad sin reiniciarlo. No toca procesos ajenos ni reintenta automáticamente.

Los destinos remotos o redirigidos se rechazan antes de actuar. Un fallo de
identidad no autoriza detener procesos. Se conservan el arranque completo para
todos los servicios apagados y la reutilización de los servicios saludables.

## Validación y límites

Nueve pruebas sintéticas cubren recuperación, reutilización, orden PostgreSQL →
SQL → API, destino remoto, puerto ajeno, errores de inicio/identidad y arranque
completo. Ejecutar:

`python -B -m unittest discover -s scripts/tests -p test_abrir_analytics_predict.py -v`

La recuperación real de PostgreSQL y API se acredita por separado, conservando
el frontend anterior. El acceso corregido se prueba con los servicios activos,
sin apagarlos para simular otro fallo. La rama fría de recuperación parcial del
lanzador corregido se verifica sintéticamente; no se atribuye una prueba de
reinicio del PC ni un corte forzado de servicios.

No inicia con Windows, no crea vigilancia, no ingiere datos ni entrena modelos.
Evidencias externas: `Carpeta de Entregas de Borlty/Arranque_y_Acceso_Escritorio_2026-11-13`.

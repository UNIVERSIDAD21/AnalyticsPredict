# Validación estacional y fases NBA — 2026-10-16

Orden: ejecutar el paquete integral y dejar las intervenciones manuales para el
cierre. Estado científico: **NO CERTIFICADO**. Este bloque no reabre KPI/GET ni
introduce modelos avanzados, picks, stakes o recomendaciones NBA.

## Fútbol: protocolo V2 separado de V1

V1 conserva su política y decisión fallida. V2 prepara candidatos Ridge externos,
sin registrar versiones ni activar serving. CAL selecciona alpha, **no calibra
probabilidades**. Se mantienen mínimos de 500 TRAIN, 100 CAL, cinco partidos por
equipo en TRAIN y alpha 1/5/10. CAL toma los últimos 200 partidos candidatos dentro
de 180 días anteriores al corte; incluye todos los empates de instante y nunca
reajusta con CAL. El receso no se rellena con datos inventados.

La evaluación futura exige 100 pares, dos meses UTC con al menos 30 pares cada uno,
cobertura >=90%, mejora pareada frente a baseline y ningún target peor; semilla42,
1.000 réplicas por partido. Las abstenciones y resultados pendientes cuentan en
la cobertura. Una evaluación de laboratorio no activa ni certifica por sí sola.
La disponibilidad histórica y la independencia del proveedor siguen separadas.

La declaración se guarda antes de obtener los nuevos snapshots y de ajustar los
candidatos. Se conservan política, datos, fixtures, coeficientes, features, horas
de fin de ajuste/congelamiento e integridad SHA256. Las salidas son archivos
externos de creación exclusiva, **no** tablas con inmutabilidad acreditada. No
producen probabilidades a partir de un MAE ni reutilizan calibradores históricos.

Desde `backend/`, con rutas de evidencia externas:

```bash
.venv/bin/python scripts/preparar_futbol_sombra.py --politica /RUTA/politica.json --declarar --inicio 2026-10-17T00:00:00+00:00 --fin 2026-11-17T00:00:00+00:00
.venv/bin/python scripts/preparar_futbol_sombra.py --politica /RUTA/politica.json --snapshot /RUTA/datos.json --fixtures /RUTA/calendario.json --salida /RUTA/cohorte.json
.venv/bin/python scripts/evaluar_futbol_sombra.py --cohorte /RUTA/cohorte.json --salida /RUTA/evaluacion_nueva.json
```

El tercer comando consulta exclusivamente finales actuales en READ ONLY. No se
debe retrofechar ni sobrescribir una salida. Una política cuyo periodo ya comenzó
no puede generar nuevas capturas como si fueran previas.

## Recuperación de datos: controles

El censo adicional identificó 367 finales de abril/mayo y los 97 de agosto ya
observados externamente. Se revisaron 464 summaries: goles por mitades explícitos;
358 fallos de conciliación de córners por periodo. **No se incorpora ningún nuevo
desglose de córners de esta cohorte**, ni siquiera se presume que un conteo agregado
coincidente acredite una cronología correcta. FT/tiros se conservan solo cuando el
contrato de ambos equipos está completo; NULL no se convierte en cero.

38 candidatos colisionan con registros canónicos anteriores; quedan retenidos,
sin enlazar por parecido/fecha próxima ni corregir silenciosamente sus horarios.
426 finales nuevos fueron aplicados tras backup privado, ensayo con rollback e
idempotencia; postflight independiente426/426 y huellas del histórico/catálogos/
apuestas/modelos intactas. Se añaden163programados de noviembre con marcadores
NULL, ensayo/idempotencia/backup/postflight163/163. Total canónico24.845partidos.
La primera expectativa del postflight sobre datos_completos=false era incorrecta:
el trigger idéntico al previo lo deriva de golesFT presentes, por lo que true es
correcto en426finales. No hubo DML correctivo; córners por mitades permanecenNULL.
Se conservan fallo/diagnóstico/SQL y regresión. V1 corrió tras ese assert por una
secuencia shell no fail-fast, sin activar nada; su repetición tras reconciliar dio
el mismo snapshot/métricas. Las secuencias posteriores se encadenaron con &&.

La sincronización ya no cambia la competición principal de clubes existentes al
cargar partidos históricos. La afiliación actual exige una operación distinta.
El contador de evidencia funciona también con psycopg pipeline: INSERT RETURNING
evita leer un `rowcount=-1` pendiente. Ambos casos tienen regresión PostgreSQL.

## Resultado de las cohortes futuras, sin ocultar abstenciones

V1 reevaluada con el hash originalcf466ed7…:618EVAL/familia, cobertura79,13%;
ninguna apta. MAE corners1,396027/goles0,667069/disparos2,678567 frente a
1,422752/0,688868/2,906727 de sus referencias en la misma cohorte. Sin versiones
ML fútbol ni calibradores nuevos enNeon; no atribuir eficacia futura al backtest.

La políticaV2 final se declaró antes de extraer snapshots y ajustar:199fixtures
(132octubre/67noviembre), del17oct al17nov. ReservaCAL200:158efectivos, candidatos
por familia y163predicciones puntuales/36abstenciones. Cobertura máxima81,91%,
**ya insuficiente** para90% aunque llegasen todos los outcomes. Diez clubes
carecen de cinco antecedentes enTRAIN; no se usan vectores vacíos ni se ocultan.
La cohorte es laboratorio, no vía de activación automática.

Antes de outcomes se declaró una versiónV3 con reserva100 (mismo mínimo100,
TRAIN500/equipo5/cobertura90% intactos), sin sobrescribirV2 ni elegir por el
rendimiento futuro. CAL efectivo88goles/disparos y78corners: **SIN_CANDIDATO**,
199abstenciones por familia. No se ensayaron más reservas para aparentar aptitud.
Se preservan ambas versiones y la decisión previa a outcomes; V2 conserva su
utilidad de laboratorio. El siguiente ajuste exige nuevos datos y nueva cohorte
anterior a sus eventos, no corregir los snapshots congelados ni bajar mínimos.
El evaluador ya se ejecutó:0outcomes, métricasN/D y todos los límites explícitos.

## NBA: pretemporada útil y visible

API y Estado muestran PRE/REG/POST por separado, finales válidos y última fecha,
además de capturas/resultados/eventos por fase. La pretemporada se conserva y
analiza; no equivale a evidencia de eficacia regular. El reporte de forma reciente
filtra NBA final válido, permite `--fase PRE|REG|POST` y desglosa fases en JSON.
Cuenta registros inválidos en el inventario de calidad, no en las medias por equipo.

Los12snapshotsPRE originales conservan sus hashes. Se añadieron dos finalesPRE
(401908945/401908622), solo filas nuevas y cuartos/FT acreditados, sin reentrenar
el modelo2123. PRE pasa48→50finales en el inventario, con reportes de30equipos y
muestras pequeñas explícitas. La cohorte completa regular20oct, tres eventos,
se congeló realmente con el umbral técnico declaradoQ1=55.5. Ensayo/rollback/
backup/idempotencia/postflight:15hashes y ordenfit<freeze<inicio,12PRE+3REG,
0outcomes; apuestas/modelos/histórico anteriores intactos. No hay
cuotas, picks ni selección por resultados. El inicio regular 20/10 se contrastó
con la publicación oficial NBA; esto no acredita todos los outcomes históricos.

## Visual, dependencias y Git

Navegación local vuelve a ser rechazada por política. No se cambia configuración
global, expone el producto ni emplea otra herramienta para eludirlo. HTTP/tests
de componentes no sustituyen el smoke visual. El agente mantiene la tarea.

Tailwind4 con su plugin PostCSS preparado en laboratorio externo: migración de directivas y
utilities propias, instalación limpia npm10, audit0, 29 tests/lint/build. No se
publica esa migración sin revisión visual; el producto conserva su auditoría real.
H4 conserva ensayo y backup; se prepara una solicitud de soporte sin enviarla,
sin forcepush ni purga parcial de refs. No se inventa gestión exclusiva del titular.

## Evidencias

Fuera del repositorio: `EJECUCION_INTEGRAL_ESTACIONAL_2026-10-16`, en la Carpeta de
Entregas de Borlty. Incluye capturas, rechazos, colisiones, políticas, ensayos,
validaciones, laboratorio completo y expediente H4. Los fallos intermedios no se
borran. Los resultados aplicados y CI se añaden al cierre efectivo.


## Validación y decisiones finales

848backend/0fallos/0skips (dos deprecaciones heredadas),29frontend/lint/build;
CI del código b0361cb4/4verde. CI/commit documental final se registran en acta.
El estado/roadmap/deuda/checklist se actualizan sin reabrir cierres técnicos.

Dos decisiones de alcance se dejan al propietario al terminar: permitir añadir
exactamente127.0.0.1 a browser.ssrfPolicy.allowedHostnames (global por host, no por
puerto; conservar otras entradas y no habilitar toda la red privada), y autorizar
el envío de la solicitud preparada aGitHubSupport. Ninguna se ejecutó. No hay
soportesP&L/login/compra/smoke humano exigidos. Sin automatismos futuros.

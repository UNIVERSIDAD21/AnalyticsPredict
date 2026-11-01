# Resolución analítica por objetivo — implementación local

**Cierre posterior autorizado:** se aplicó el plan de 99 correcciones históricas,
con respaldo/restauración, rollback y postflight independiente. [Alcance y
controles](REPARACION_ANALITICA_99_2026-10-25.md). El texto siguiente documenta la
entrega inicial de código, previa a esa reparación.

Código local sin commit/push ni nueva CI remota. No se aplicó resolución,
reparación, migración ni entrenamiento en la base real.

## Contrato

`motor/resolucion_analitica.py` define `resolucion-analitica-por-objetivo-v1`:
familia, periodo y lado explícitos; valor observado no negativo entero y finito;
NULL permanece ausente. Los 24 mercados canónicos de fútbol usan el mismo
clasificador de elegibilidad del estimador y Estado. Los tiros por mitad siguen
siendo estimaciones y no pueden convertirse en un outcome observado desde FT.
Se reconocen los aliases canónicos `DISPAROS_LOCAL_ARCO_FT` y visitante.

Goles FT son regulación: ET y tanda no se suman al mercado de 90 minutos. Córners
y tiros FT con ET sin desglose quedan pendientes. Parciales incoherentes no se
usan; mercados independientes conservan su soporte.

NBA exige un final válido no ficticio, su dominio y periodo exactos; COMPLETO usa
FT con OT. Euroliga usa regulación. WNBA necesitaría declarar explícitamente el
contrato OT de la emisión; no se importan sus journals al registro legacy ni se
aplica una política NBA por defecto. Un mercado ausente no recurre a goles FT;
un lado inválido no es PUSH. Líneas de cuartos de punto quedan pendientes porque
la liquidación asiática fraccionada no está implementada.

## Tres recorridos corregidos

- Registro analítico legacy: bloqueo por fila, SKIP LOCKED, savepoints, solo
  pendientes sin outcome previo; evidencia separada en `payload.resolucion_analitica`.
  No reabre finalizadas ni altera apuestas financieras. Captura hash del partido,
  valor, mercado, línea, lado, dominio y momento de resolución.
- Predicciones de fútbol: mismo contrato observado; POSPUESTO/SUSPENDIDO no se
  convierten en VOID definitivo. `force=True` se rechaza: reparar cohortes requiere
  una operación explícitamente auditada. Probabilidades/modelo emitidos no se
  sobrescriben por reanálisis (`ON CONFLICT DO NOTHING`); se conserva la primera
  emisión de la llave natural existente, no se crea una nueva cohorte por refresco.
- Predicciones NBA: dominio NBA comprobado, final válido y no futuro, datos del
  periodo sin negativos ni placeholders; validación de lado/línea y savepoint por
  escritura. No resolver WNBA/Euro desde ese ciclo.

Los resúmenes sin selección/probabilidad disponible son `INFORMATIVO`, no falsas
apuestas pendientes. Una probabilidad ausente no recibe confianza MEDIA. La
creación de tablas en runtime queda deshabilitada salvo opt-in explícito previo;
el resolvedor no instala esquemas.

## Diagnóstico sin escribir

`GET /api/bitacora/apuestas-analizadas/diagnostico?limite=1000` ejecuta transacción
READ ONLY. Distingue pendientes resolubles, causas de abstención, discrepancias
comparables e históricos no comparables. Límite por deporte y aviso de posible
truncamiento explícitos. No confundir el número propuesto con filas modificadas.

Desde raíz del repositorio, con Python del backend y credenciales protegidas:

```bash
backend/.venv/bin/python backend/scripts/auditar_resolucion_analitica.py \
  --salida /ruta/externa/archivo_nuevo.json --limite 20000
```

No sobrescribe evidencia ni admite rutas dentro del producto. No tiene modo de
aplicación. La resolución legacy sigue dentro del POST explícito de ciclo de
calidad; los GET no resuelven, no entrenan ni registran apuestas.

## Límites y operación histórica

Un outcome correctamente reproducido no acredita que la predicción fuera anterior
al evento ni que sus datos fueran disponibles entonces. El registro legacy y sus
promedios se identifican como descriptivos, sin certificación de corrección de
todos los outcomes, prospectiva o calibración. Jornals WNBA/Euro y captura Q1 NBA
mantienen contratos separados; esto no es una unificación prospectiva completa.

Las discrepancias históricas detectadas se conservan sin cambios. Una reparación
necesita lista fija de IDs y tablas, backup verificable, fuente/estado/huella
revalidados, ensayo reversible, autorización de escritura y postflight READ ONLY.
No corregir automáticamente al leer ni reemplazar cohortes por datos reconstruidos.

Verificaciones: suite backend global con PostgreSQL sintético, regresiones de
mercados canónicos, ceros/NULL, ET, aliases, simulación, locks, savepoints,
idempotencia, inmutabilidad y dominio. Evidencia completa externa en
`RESOLUCION_ANALITICA_POR_MERCADO_2026-10-25`; cifras y límites en su informe.

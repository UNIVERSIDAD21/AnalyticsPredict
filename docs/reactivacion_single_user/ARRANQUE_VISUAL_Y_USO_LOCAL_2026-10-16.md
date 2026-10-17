# Arranque visual y preparación para uso local — 2026-10-16

## Resultado y alcance

AnalyticsPredict disponible en `http://127.0.0.1:5173` para consulta personal
exploratoria. Backend en loopback8000, modeloNBA2123/30equipos cargado desde
artefacto, sin reentrenar. No hay despliegue público ni certificación analítica.
Esta pasada continúa el WIP previo a la interrupción de contexto y conserva
sus evidencias, errores intermedios y correcciones.

## Cambios técnicos

- Tailwind4 y PostCSS oficial: lock compatible con npm10, utilidades personalizadas,
  tipografías, color de advertencia, fondo oscuro y controles. Auditoría completa
  actual:0vulnerabilidades conocidas; no solo producción.
- Navegación NBA/fútbol sincronizada sin sustituir rutas de detalle; NBA apunta a
  `/app`. Cabecera en análisis interno y título AnalyticsPredict.
- Calendario fútbol publica IDs separados de nombres y admite paginación real;
  selección controlada permite analizar un partido distinto del primero sin
  pedir temporadasNBA. MarcadoresNULL no se convierten en0 y contexto/H2H usa
  identidad exacta del club. Se retira el botón de guardado inerte cuando no hay
  selección canónica registrable, con motivo visible; no se inventa recomendación.
- Registro de predicciones fútbol limita mercados al enum canónico y usa savepoint;
  un error opcional no deja abortada la transacción del análisis. Verificado con
  API y datos artificiales en PostgreSQL exclusivo local, no mediante POST enNeon.
- Bitácora recupera identidad por partido sin reescribir valores históricos,
  preserva fechas sin hora enBogotá y distingue vacío por filtros de historial vacío.
- AnálisisNBA interno aplica fasePRE/REG/POST y corte exclusivo anterior al partido
  tanto enSQL como en fallback; excluye invalidados y fechas ausentes/inválidas.
  Un fallback se advierte explícitamente, sin filtrar errores del proveedor al cliente.
  Sin fechas/cuotas/fuentes de ejemplo presentadas como reales; no picks/stakes.
- Estado distingue outcomes registrados de outcomes independientes; mensajes
  comerciales históricos retirados de las pantallas revisadas.

## Verificación

- Backend global sintético:854aprobadas,0fallos/0omitidas,2deprecaciones conocidas.
- Frontend:36pruebas/16archivos aprobados; lint y build correctos. npm10ci previo
  conservado y CI alojada del commit final se acredita en acta externa.
- Navegador administrado: dashboard,NBA,fútbol,bitácora,configuración,Estado y
  análisisNBA interno; datos reales para lecturas, envío fútbol en base artificial.
  Configuración móvil emulada390px, sin desbordamiento horizontal observado.
- Errores del harness (configVite externo y APIURL por defecto) conservados y
  corregidos antes del envío artificial; no se atribuyen al producto ni pruebanNeon.
- HTTP actual salud/Estado y artefacto2123 verificados, sin entrenamiento/activación.

## Prospectiva y límites científicos

El tramo previo de esta misma pasada resolvió9PRE de las12capturas originales,
con backup privado, ensayo rollback, segunda pasada0 y huellas históricas iguales.
Las15capturas(12PRE+3REG20oct) y el artefacto permanecen intactos. No repetir.
FuenteESPN compartida con captura,0outcomes independientes. Solo diagnósticoPRE:
Brierraw0,2713 frente a0,25de referencia fija; IC95%exploratorio de diferencia
[-0,04985;0,09559],9eventos/1000réplicas/semilla42. No evidencia de mejora ni
calibrador ajustado/activado; no extrapolar aREG. Quedan6outcomes sin resolver
en este corte, no constituyen una tarea automática futura.

FútbolV2/V3 sigue sin outcomes evaluables ni aptitud;0modelosML activos. Conservar
políticas/cohortes/gates, sin reentrenar ni elegir variantes tras ver resultados.
P&Lhistórico sigueN/D por ausencia definitiva de soportes/unidad.

## H4 y continuidad

TicketGitHubSupport#4868445 enviado con autorización y posteriormente cerrado
por el proveedor con remisión a autoservicio; no coordinó retirada de refs/cachés.
Sin purga parcial ni forcepush. H4continúa bloqueado, no impide consulta local.
M08visual/H12técnico se cierran en su alcance tras publicación/CI; global abierto:
independencia/muestra/calibraciónNBA, aptitudfútbol y H4 no se certifican porCIverde.

Evidencia externa: `ARRANQUE_VISUAL_Y_PREPARACION_USO_2026-10-16`, con logs,
JSON, capturas, postflightPRE, acta y manifiestoSHA256. No contiene credenciales.

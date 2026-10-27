# Agenda diaria de fútbol

La entrada `/futbol` muestra Hoy (por defecto), Mañana o una fecha elegida,
mezclando todas las competiciones registradas y ordenando por hora de Colombia.
No hace falta seleccionar país, liga ni temporada para encontrar un partido.

Las tarjetas incluyen competición, equipos, escudos disponibles (o iniciales),
hora, estado y marcador conocido. Buscar equipo y los filtros de país,
competición, estado y partidos guardados son opcionales. La búsqueda y la
paginación se realizan en el servidor; no filtran únicamente la página visible.

Al seleccionar un próximo o un final válido se abre la configuración existente
con sus equipos, competición y fecha. El selector de partido duplicado del
formulario se oculta exclusivamente en fútbol. El botón de volver a la agenda
permite elegir otro encuentro. Los enlaces `partidoId` resuelven su fecha y
competición originales, incluso fuera de la página visible.

## Histórico utilizado en el cálculo

La fecha de la agenda no es un filtro del entrenamiento/histórico. La sección
plegable «Histórico para calcular» pertenece al partido seleccionado. Por defecto
se usa el criterio temporal del backend (temporada del corte y anterior, o su
fallback documentado); se pueden solicitar temporadas concretas o todas las
disponibles de esa competición. Cambiar de partido restablece el modo automático.
Cambiar temporadas invalida el resultado anterior y las solicitudes conservan
su ámbito de competición. Se preserva el corte temporal exclusivo existente.

Los finales se abren con `modo_historico=true`: reconstrucción retrospectiva,
sin apuestas ni registro de pronósticos. Las probabilidades continúan RAW.

## API y estados

`GET /api/futbol/partidos/agenda` recibe fecha (opcional, hoy en America/Bogota),
competicion_id, pais, buscar, estado, partido_ids repetidos, pagina y tamano.
Incluye todo el día local usando límite superior exclusivo. Devuelve una página
ordenada, total filtrado, instante de consulta y máximo actualizado_en de las
filas consultadas. Son fechas de BD; no acreditan una consulta reciente a ESPN.
Se preserva `/catalogo` para consumidores anteriores.

`estado_agenda` clasifica el estado guardado sin modificarlo: PROXIMO,
POR_VERIFICAR, EN_JUEGO, FINALIZADO o NO_DISPONIBLE. Un PROGRAMADO con kickoff
anterior o igual a ahora queda POR_VERIFICAR; no se inventa su resultado ni se
declara que esté en vivo. El cliente reevalúa el reloj cada 15 segundos y al
intentar analizar; el servidor vuelve a comprobarlo siempre.

`POST /api/futbol/analizar` rechaza con HTTP 409 un análisis prepartido fuera
de PROGRAMADO futuro, incluso mediante ID directo. Los finales mantienen su
validación propia y requieren modo histórico. La fuente debe confirmar una
reprogramación antes de que vuelva a ser elegible.

## Verificación y límites

1.720 pruebas backend sobre el runner SQL global en PostgreSQL temporal propio;
128 frontend; lint y TypeScript sin errores ni avisos; build aprobado con el
aviso preexistente de import WNBA. Verificados en navegador real: Hoy/Mañana,
fecha histórica, selección, cálculo, temporadas efectivas y ancho móvil.

No se modificó la BD productiva, no se ejecutaron scrapers, no se publicaron
commits y no se crearon apuestas. La agenda consume calendarios ya cargados.
El refresco de esta vista consulta la BD; la descarga periódica de calendarios,
actualización de resultados y cobertura oficial completa siguen siendo trabajo
operativo pendiente. Una fecha vacía no prueba ausencia global de encuentros.

Preimágenes, diff incremental, resultados y capturas en:
`/home/erik-fuentes/Documents/Codex/2026-10-25/ho/outputs/agenda_futbol_2026-10-26`.

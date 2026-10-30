# Hoy: paginación, favoritos y navegación — 2026-10-30

## Cambios de uso personal

- [x] Cargar más partidos acumula páginas en la misma vista en vez de limitarla a los primeros 50 registros recibidos.
- [x] Activar favoritos busca páginas posteriores de los dominios con preferencias guardadas y datos disponibles. Cada búsqueda lee como máximo diez páginas adicionales; permite continuar o detenerla.
- [x] Se muestra el número de favoritos encontrados y los registros consultados frente al total declarado por la agenda. Un resultado parcial no se presenta como ausencia de favoritos.
- [x] No se realizan búsquedas automáticas de páginas adicionales cuando no hay favoritos del dominio.
- [x] Seleccionar NBA/Euroliga/WNBA no consulta fútbol; seleccionar fútbol no consulta baloncesto. Cambiar entre Todas y fútbol conserva una lectura de fútbol ya disponible sin releerla innecesariamente.
- [x] Reintentar un dominio no relee el otro. Un fallo posterior conserva las páginas ya recibidas y permite reintentar el número de página que falló.
- [x] Fecha anterior/siguiente y accesos Hoy/Mañana, siempre con día colombiano.
- [x] Las consultas recientes enlazan a su entrada exacta del cuaderno y se actualizan al guardar/restaurar sin recargar la portada.

## Contratos de lectura

- [x] Solo GET existentes: no se sincronizan fuentes, ajustan modelos ni escriben datos deportivos.
- [x] Se descartan respuestas canceladas o de una fecha/filtro anterior. Detener conserva lo recibido antes de la cancelación.
- [x] Se rechazan páginas vacías inesperadas, IDs repetidos, conteos inconsistentes o un número de página incompatible cuando la API lo proporciona.
- [x] Si cambia el total o una marca de actualización conocida entre páginas, se conserva lo leído y se pide actualizar la consulta.
- [x] Una marca ausente no permite acreditar snapshot estable. Recorrer todas las páginas no acredita calendario oficial completo ni frescura deportiva.
- [x] Los enlaces de baloncesto incluyen `paginaAgenda` y `ligaAgenda`, separados de la liga del motor; la ficha consulta la misma página/filtro para resolver el encuentro. Los valores inválidos regresan a página 1/agenda global.
- [x] Cambiar de fecha limpia las pistas de origen del enlace. El fútbol conserva su resolución de partido por ID ya existente.

## Pruebas

- [x] 212 pruebas frontend aprobadas, 0 fallidas y 0 omitidas, con un worker; 13 pruebas añadidas frente a la entrega del cuaderno.
- [x] Favoritos en segunda página de baloncesto y por competición de fútbol; independencia de identidades por liga.
- [x] Paginación acotada y continuación, cancelación y respuestas tardías, fallo parcial y reintento sin perder registros.
- [x] Conteos, páginas repetidas, cambios de total y página vacía no se convierten en cobertura completa.
- [x] Enlace de origen y página inválida comprobados en el componente de agenda de baloncesto.
- [x] Cuaderno reciente actualizado y enlace directo a la copia original.
- [x] ESLint, TypeScript y compilación final aprobados. El ajuste final del hook fue una anotación de tipo, sin cambio de comportamiento.
- [x] UI compilada con API de fixtures sintéticos (equipos DEMO): favorito encontrado en página 2, conteo 3/3 y enlace con origen conservado. El registro HTTP confirma que seleccionar NBA no dispara una lectura nueva de fútbol.
- [x] UI con API real en modo base local: ambos dominios muestran N/D y reintentos independientes, sin tratar el acceso a BD deshabilitado como cero partidos. No se conectó a Neon.

## Límites

- [x] La BD deportiva sigue sin restaurarse/verificarse en Windows. Las pruebas de paginación usan fixtures; no prueban cobertura productiva.
- [x] El cambio no reconstruye encuentros faltantes ni actualiza fuentes. Los errores iniciales siguen siendo N/D.
- [x] La página/filtro de origen son una pista de navegación, no un snapshot inmutable: si el calendario se reordena posteriormente puede requerir actualizarlo.
- [x] Se conservan HEAD/índice y el trabajo anterior. El catálogo L01–L30 no se reclasifica ni se activa un modelo nuevo.

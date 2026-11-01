# Seguimiento y configuración de fútbol — 2026-11-01

## Fallos corregidos

- La salida exploratoria de fútbol ocultaba el registro personal en MLS y Argentina. Ahora una selección prepartido válida puede registrarse manualmente sin que se presente como recomendación del motor. Si el proveedor no aporta cuota, el modal exige la cuota decimal real mayor que 1. Probabilidad, confianza y valor esperado ausentes permanecen N/D/NULL.
- El marcador «Guardar partido en Seguimiento» queda visible sin abrir un desplegable. Solo marca el encuentro para revisarlo: no ejecuta un análisis ni crea una apuesta.
- Cambiar la búsqueda desmontaba el formulario y borraba sus campos. Se conserva por ID de partido el mercado/categoría, alcance, periodo, línea, lado, cuotas, temporadas y configuración de contexto. Volver al mismo encuentro restaura sus ajustes sin trasladar cuotas a otra competición.
- Durante el debounce de búsqueda ya no pueden seleccionarse tarjetas de la respuesta anterior: se espera la respuesta que coincide con los filtros vigentes. Así, la consulta pendiente no elimina una selección hecha sobre una tarjeta desactualizada.

## Límites y custodia

Se guardan hasta 50 configuraciones en sessionStorage, durante la sesión de la pestaña y sus recargas. No se almacenan resultados, probabilidades ni recomendaciones como si fueran datos del nuevo encuentro. Si el navegador rechaza escribir, se conserva una copia en memoria mientras siga abierta la aplicación; no se promete persistencia tras cerrar o recargar en ese caso. No es el almacén duradero de «Mis análisis».

«Limpiar» descarta expresamente la configuración del encuentro elegido, no la de los demás. Cambiar parámetros invalida la salida y cierra su modal; una respuesta tardía sigue descartándose mediante la secuencia/AbortController existentes. Se mantienen las restricciones de reconstrucción histórica y de líneas enteras sin soporte push. El marcador de partidos sigue disponible sin convertir una consulta histórica en una predicción prepartido.

## Validación y alcance

Regresiones de MLS/Argentina para selección manual sin recomendación, cuota real, payload exacto y analítica nullable; persistencia entre búsquedas, ligas, encuentros y remontaje; aislamiento de cuotas/temporadas; cuota ausente/inválida, recomendación existente, almacenamiento bloqueado/corrupto y límite de borradores. El guardado real del propietario no se usa como ensayo.

No cambia el backend, contratos SQL, resolución deportiva, modelos, calibradores, campaña NBA ni control maestro de ejecución. Las evidencias finales, SHA publicado, CI y comprobación de la interfaz instalada se entregan fuera del producto.
